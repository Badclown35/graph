package plus.anime.graphachievements

import android.app.Activity
import android.os.Bundle
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.content.Intent
import android.net.Uri

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
        webView.webViewClient = WebViewClient()
        webView.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                view: WebView?,
                callback: ValueCallback<Array<Uri>>?,
                params: FileChooserParams?
            ): Boolean {
                filePathCallback?.onReceiveValue(null)
                filePathCallback = callback

                // Do not trust the WebView-provided MIME filter: some Android file
                // providers classify MAL XML exports as application/octet-stream.
                // A broad document picker lets the user select .xml and .csv files.
                val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "*/*"
                    putExtra(Intent.EXTRA_MIME_TYPES, arrayOf(
                        "application/xml",
                        "text/xml",
                        "application/octet-stream",
                        "text/csv",
                        "text/plain",
                        "*/*"
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

    @Deprecated("Deprecated in Android")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == filePickerRequest) {
            val result = if (resultCode == RESULT_OK && data?.data != null) {
                arrayOf(data.data!!)
            } else null
            filePathCallback?.onReceiveValue(result)
            filePathCallback = null
        }
    }

    @Deprecated("Deprecated in Android")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
