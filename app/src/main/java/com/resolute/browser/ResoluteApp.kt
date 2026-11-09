package com.resolute.browser

import android.app.Application
import org.mozilla.geckoview.GeckoRuntime
import org.mozilla.geckoview.GeckoRuntimeSettings

class ResoluteApp : Application() {

    /** One engine per app process. Created on first use so app start stays fast. */
    val runtime: GeckoRuntime by lazy {
        val settings = GeckoRuntimeSettings.Builder()
            .aboutConfigEnabled(false)
            .build()
        GeckoRuntime.create(this, settings)
    }
}
