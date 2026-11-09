package com.resolute.browser

import android.net.Uri
import android.util.Patterns

object UrlUtils {
    const val HOME_URL = "https://duckduckgo.com/"
    private const val SEARCH_URL = "https://duckduckgo.com/?q="

    /** Turns whatever the user typed into a URL: a web address, or a search. */
    fun toUrl(input: String): String {
        val text = input.trim()
        if (text.isEmpty()) return HOME_URL
        if (text.startsWith("http://") || text.startsWith("https://") ||
            text.startsWith("about:") || text.startsWith("moz-extension://")
        ) return text
        if (!text.contains(' ') && Patterns.WEB_URL.matcher(text).matches()) return "https://$text"
        return SEARCH_URL + Uri.encode(text)
    }

    /** "https://addons.mozilla.org/en-US/android/addon/ublock-origin/" -> "ublock-origin" */
    fun amoSlug(input: String): String? {
        val text = input.trim()
        if (text.isEmpty()) return null
        if (!text.contains('/')) return text
        val uri = Uri.parse(text)
        if (uri.host?.endsWith("addons.mozilla.org") != true) return null
        val parts = uri.pathSegments
        val i = parts.indexOf("addon")
        return if (i >= 0 && i + 1 < parts.size) parts[i + 1] else null
    }
}
