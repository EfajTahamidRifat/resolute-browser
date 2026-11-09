package com.resolute.browser

import android.content.Intent
import android.os.Bundle
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.EditText
import android.widget.PopupMenu
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.resolute.browser.databinding.ActivityMainBinding
import org.mozilla.geckoview.GeckoResult
import org.mozilla.geckoview.GeckoRuntime
import org.mozilla.geckoview.GeckoSession
import org.mozilla.geckoview.WebExtension
import org.mozilla.geckoview.WebExtensionController
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var runtime: GeckoRuntime
    private lateinit var session: GeckoSession
    private var canGoBack = false
    private val io = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        runtime = (application as ResoluteApp).runtime
        runtime.webExtensionController.setPromptDelegate(installPrompt)

        session = GeckoSession().apply {
            progressDelegate = progress
            navigationDelegate = navigation
            open(runtime)
        }
        binding.geckoView.setSession(session)

        setupToolbar()
        setupBack()

        val start = intent?.dataString ?: UrlUtils.HOME_URL
        load(start)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        intent.dataString?.let { load(it) }
    }

    override fun onDestroy() {
        io.shutdownNow()
        session.close()
        super.onDestroy()
    }

    // ---------------------------------------------------------------- browsing

    private fun load(input: String) {
        session.loadUri(UrlUtils.toUrl(input))
        binding.geckoView.requestFocus()
    }

    private val progress = object : GeckoSession.ProgressDelegate {
        override fun onPageStart(session: GeckoSession, url: String) {
            if (!binding.urlBar.hasFocus()) binding.urlBar.setText(url)
            binding.progress.visibility = View.VISIBLE
        }

        override fun onPageStop(session: GeckoSession, success: Boolean) {
            binding.progress.visibility = View.GONE
        }

        override fun onProgressChange(session: GeckoSession, progress: Int) {
            binding.progress.progress = progress
            binding.progress.visibility = if (progress in 1..99) View.VISIBLE else View.GONE
        }
    }

    private val navigation = object : GeckoSession.NavigationDelegate {
        override fun onCanGoBack(session: GeckoSession, canGoBack: Boolean) {
            this@MainActivity.canGoBack = canGoBack
        }
    }

    private fun setupToolbar() {
        binding.urlBar.setOnEditorActionListener { v, actionId, event ->
            val go = actionId == EditorInfo.IME_ACTION_GO ||
                (event?.keyCode == KeyEvent.KEYCODE_ENTER && event.action == KeyEvent.ACTION_DOWN)
            if (go) {
                load(v.text.toString())
                hideKeyboard(v)
                v.clearFocus()
            }
            go
        }
        binding.btnBack.setOnClickListener { if (canGoBack) session.goBack() }
        binding.btnReload.setOnClickListener { session.reload() }
        binding.btnMenu.setOnClickListener { showMenu(it) }
    }

    private fun setupBack() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (canGoBack) {
                    session.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                    isEnabled = true
                }
            }
        })
    }

    private fun hideKeyboard(v: View) {
        getSystemService(InputMethodManager::class.java)?.hideSoftInputFromWindow(v.windowToken, 0)
    }

    // -------------------------------------------------------------- extensions

    private fun showMenu(anchor: View) {
        PopupMenu(this, anchor).apply {
            menu.add(0, 1, 0, R.string.menu_install_extension)
            menu.add(0, 2, 1, R.string.menu_extensions)
            menu.add(0, 3, 2, R.string.menu_get_addons)
            setOnMenuItemClickListener {
                when (it.itemId) {
                    1 -> askInstallExtension()
                    2 -> showExtensions()
                    3 -> load("https://addons.mozilla.org/android/")
                }
                true
            }
            show()
        }
    }

    private fun askInstallExtension() {
        val input = EditText(this).apply {
            hint = getString(R.string.install_extension_hint)
            setSingleLine()
            // Prefill with the current page when the user is on an add-on page.
            val current = binding.urlBar.text.toString()
            if (current.contains("addons.mozilla.org")) setText(current)
        }
        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.menu_install_extension)
            .setView(input)
            .setPositiveButton(R.string.install) { _, _ -> installExtension(input.text.toString()) }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun installExtension(link: String) {
        io.execute {
            val xpi = try {
                AddonResolver.resolveXpiUrl(link)
            } catch (e: Exception) {
                runOnUiThread { toast(getString(R.string.install_failed, e.message ?: "unknown error")) }
                return@execute
            }
            runOnUiThread {
                runtime.webExtensionController.install(xpi).accept(
                    { ext -> toast(getString(R.string.installed_x, ext?.metaData?.name ?: "extension")) },
                    { err -> toast(getString(R.string.install_failed, err?.message ?: "unknown error")) }
                )
            }
        }
    }

    private fun showExtensions() {
        runtime.webExtensionController.list().accept({ list ->
            val exts = list.orEmpty().filter { !it.isBuiltIn }
            if (exts.isEmpty()) {
                toast(getString(R.string.no_extensions))
                return@accept
            }
            val names = exts.map { it.metaData.name ?: it.id }.toTypedArray()
            MaterialAlertDialogBuilder(this)
                .setTitle(R.string.menu_extensions)
                .setItems(names) { _, which -> confirmRemove(exts[which]) }
                .setNegativeButton(R.string.close, null)
                .show()
        }, { err -> toast(err?.message ?: "error") })
    }

    private fun confirmRemove(ext: WebExtension) {
        val name = ext.metaData.name ?: ext.id
        MaterialAlertDialogBuilder(this)
            .setTitle(name)
            .setPositiveButton(R.string.remove) { _, _ ->
                runtime.webExtensionController.uninstall(ext).accept(
                    { toast(getString(R.string.removed_x, name)) },
                    { err -> toast(err?.message ?: "error") }
                )
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    /** Asks the user before any extension is added, showing what it can access. */
    private val installPrompt = object : WebExtensionController.PromptDelegate {
        override fun onInstallPromptRequest(
            extension: WebExtension,
            permissions: Array<String>,
            origins: Array<String>,
            dataCollectionPermissions: Array<String>
        ): GeckoResult<WebExtension.PermissionPromptResponse> {
            val result = GeckoResult<WebExtension.PermissionPromptResponse>()
            val all = (permissions + origins).distinct()
            val body = if (all.isEmpty()) getString(R.string.install_prompt_no_perms)
            else getString(R.string.install_prompt_body, all.joinToString("\n") { "• $it" })

            MaterialAlertDialogBuilder(this@MainActivity)
                .setTitle(getString(R.string.install_prompt_title, extension.metaData.name ?: extension.id))
                .setMessage(body)
                .setCancelable(false)
                .setPositiveButton(R.string.add) { _, _ ->
                    result.complete(WebExtension.PermissionPromptResponse(true, false, false))
                }
                .setNegativeButton(R.string.cancel) { _, _ ->
                    result.complete(WebExtension.PermissionPromptResponse(false, false, false))
                }
                .show()
            return result
        }
    }

    private fun toast(msg: String) = Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()
}
