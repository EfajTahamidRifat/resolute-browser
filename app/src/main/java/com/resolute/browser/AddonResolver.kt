package com.resolute.browser

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Finds the installable .xpi file for a Firefox add-on, using the public
 * addons.mozilla.org API. No Resolute server involved.
 */
object AddonResolver {

    /** Blocking: call from a background thread. Returns an .xpi URL. */
    fun resolveXpiUrl(input: String): String {
        val text = input.trim()
        if (text.endsWith(".xpi") || text.contains("/downloads/file/")) return text

        val slug = UrlUtils.amoSlug(text)
            ?: throw IllegalArgumentException("Not a Firefox add-on link")

        val conn = URL("https://addons.mozilla.org/api/v5/addons/addon/$slug/")
            .openConnection() as HttpURLConnection
        conn.connectTimeout = 15_000
        conn.readTimeout = 15_000
        try {
            if (conn.responseCode != 200) throw IllegalStateException("Add-on not found ($slug)")
            val body = conn.inputStream.bufferedReader().use { it.readText() }
            return JSONObject(body)
                .getJSONObject("current_version")
                .getJSONObject("file")
                .getString("url")
        } finally {
            conn.disconnect()
        }
    }
}
