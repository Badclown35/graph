package plus.anime.graphachievements

import android.app.Activity
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.content.Intent
import android.net.Uri
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private val filePickerRequest = 4107
    private val pageSize = 300
    private val maxPages = 100

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.allowFileAccess = true
        webView.settings.allowContentAccess = true
        webView.addJavascriptInterface(MalBridge(), "GraphMal")
        webView.webViewClient = WebViewClient()
        webView.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                view: WebView?, callback: ValueCallback<Array<Uri>>?, params: FileChooserParams?
            ): Boolean {
                filePathCallback?.onReceiveValue(null)
                filePathCallback = callback
                val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "*/*"
                    putExtra(Intent.EXTRA_MIME_TYPES, arrayOf(
                        "application/xml", "text/xml", "application/octet-stream",
                        "text/csv", "text/plain", "*/*"
                    ))
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                return try {
                    startActivityForResult(intent, filePickerRequest)
                    true
                } catch (_: Exception) {
                    filePathCallback = null
                    false
                }
            }
        }
        setContentView(webView)
        webView.loadUrl("file:///android_asset/index.html")
    }

    private inner class MalBridge {
        @JavascriptInterface
        fun lookup(username: String) {
            Thread {
                val result = JSONObject().put("username", username)
                try {
                    val safeName = username.trim()
                    require(safeName.matches(Regex("^[A-Za-z0-9_-]{1,64}$"))) {
                        "Enter a valid MyAnimeList username."
                    }
                    val encoded = URLEncoder.encode(safeName, "UTF-8")
                    val profile = request("https://myanimelist.net/profile/$encoded")
                    if (profile.contains("error404") || profile.contains("Page Not Found", true)) {
                        throw IllegalArgumentException("MAL username was not found.")
                    }
                    result.put("anime", fetchList("animelist", encoded))
                    result.put("manga", fetchList("mangalist", encoded))
                    result.put("profileHtml", profile)
                } catch (error: Exception) {
                    result.put("error", error.message ?: "Could not retrieve public MAL data.")
                }
                runOnUiThread {
                    val quoted = JSONObject.quote(result.toString())
                    webView.evaluateJavascript(
                        "window.onMalLookupResult && window.onMalLookupResult($quoted);", null
                    )
                }
            }.start()
        }
    }

    // Graph's newer scraper uses this public endpoint, requesting 300 entries per page.
    // Requests are sequential and paced; 403 responses are not retried or bypassed.
    private fun fetchList(listPath: String, encodedUsername: String): JSONArray {
        val all = JSONArray()
        for (page in 0 until maxPages) {
            val offset = page * pageSize
            val address = "https://myanimelist.net/$listPath/$encodedUsername/load.json?status=7&offset=$offset"
            val body = request(address)
            val rows = try {
                JSONArray(body.removePrefix("\uFEFF").removePrefix("<?xml encoding=\"utf-8\"?>").trim())
            } catch (_: Exception) {
                throw IllegalStateException("MAL returned an unexpected $listPath response. Its public-list format may have changed.")
            }
            for (i in 0 until rows.length()) all.put(rows.getJSONObject(i))
            if (rows.length() < pageSize) return all
            Thread.sleep(1100)
        }
        throw IllegalStateException("This MAL list exceeds the safe import limit of 30000 entries.")
    }

    private fun request(address: String): String {
        var lastError: Exception? = null
        for (attempt in 0..2) {
            val connection = (URL(address).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 15000
                readTimeout = 30000
                instanceFollowRedirects = true
                setRequestProperty("User-Agent", "GraphAchievements/1.0 (public MAL list reader)")
                setRequestProperty("Accept", "application/json,text/html,*/*")
            }
            try {
                val code = connection.responseCode
                val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
                if (code in 200..299) return body
                if (code == 403) {
                    throw IllegalStateException("MAL denied this public-list request. The list may be private, or MAL may be temporarily restricting access. Try the XML/CSV import instead.")
                }
                if (code == 429 || code >= 500) {
                    lastError = IllegalStateException("MAL returned HTTP $code.")
                    if (attempt < 2) Thread.sleep(1500L * (attempt + 1))
                } else {
                    throw IllegalStateException("MAL returned HTTP $code.")
                }
            } finally {
                connection.disconnect()
            }
        }
        throw lastError ?: IllegalStateException("MAL could not be reached.")
    }

    @Deprecated("Deprecated in Android")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == filePickerRequest) {
            val result = if (resultCode == RESULT_OK && data?.data != null) arrayOf(data.data!!) else null
            filePathCallback?.onReceiveValue(result)
            filePathCallback = null
        }
    }

    @Deprecated("Deprecated in Android")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
