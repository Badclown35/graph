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
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private val filePickerRequest = 4107

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
                view: WebView?,
                callback: ValueCallback<Array<Uri>>?,
                params: FileChooserParams?
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
                    val encoded = URLEncoder.encode(username, "UTF-8")
                    val profile = request("https://myanimelist.net/profile/$encoded")
                    if (profile.contains("error404") || profile.contains("Page Not Found", true)) {
                        throw IllegalArgumentException("MAL username was not found.")
                    }
                    val anime = request("https://myanimelist.net/malappinfo.php?u=$encoded&status=all&type=anime")
                    val manga = request("https://myanimelist.net/malappinfo.php?u=$encoded&status=all&type=manga")
                    result.put("profileHtml", profile)
                    result.put("animeXml", anime)
                    result.put("mangaXml", manga)
                } catch (error: Exception) {
                    result.put("error", error.message ?: "Could not retrieve public MAL data.")
                }
                runOnUiThread {
                    val quoted = JSONObject.quote(result.toString())
                    webView.evaluateJavascript(
                        "window.onMalLookupResult && window.onMalLookupResult($quoted);",
                        null
                    )
                }
            }.start()
        }
    }

    private fun request(address: String): String {
        val connection = (URL(address).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 15000
            readTimeout = 30000
            instanceFollowRedirects = true
            setRequestProperty("User-Agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36")
            setRequestProperty("Accept", "text/html,application/xml,application/xhtml+xml,*/*")
            setRequestProperty("Referer", "https://myanimelist.net/")
        }
        try {
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            if (code !in 200..299) {
                if (code == 403) throw IllegalStateException("MAL denied access to this public list (it may be private, or MAL is rate-limiting requests).")
                throw IllegalStateException("MAL returned HTTP $code.")
            }
            return body
        } finally {
            connection.disconnect()
        }
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
