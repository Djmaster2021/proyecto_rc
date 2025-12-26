package com.example.consultoriodentalrc

import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.browser.customtabs.CustomTabsIntent
import androidx.fragment.app.Fragment
import com.example.consultoriodentalrc.BuildConfig.BASE_URL
import com.example.consultoriodentalrc.databinding.FragmentWebviewBinding

class WebViewFragment : Fragment() {

    private var _binding: FragmentWebviewBinding? = null
    private val binding get() = _binding!!

    // Por defecto usa la misma URL que consume la app (BuildConfig.BASE_URL)
    private val defaultUrl = BASE_URL
    private val prefsName = "webview_prefs"
    private val keyUrl = "login_url"
    private val prefs by lazy {
        requireContext().getSharedPreferences(prefsName, Context.MODE_PRIVATE)
    }
    private var currentUrl: String = defaultUrl

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentWebviewBinding.inflate(inflater, container, false)

        // Recupera la última URL o usa la del build
        currentUrl = prefs.getString(keyUrl, defaultUrl)?.ensureTrailingSlash() ?: defaultUrl.ensureTrailingSlash()
        binding.inputUrl.setText(currentUrl)

        // Abre la página principal del sitio
        launchCustomTab(currentUrl)

        binding.btnApplyUrl.setOnClickListener {
            val url = binding.inputUrl.text?.toString()?.trim().orEmpty()
            if (url.isNotBlank()) {
                val normalized = url.ensureTrailingSlash()
                currentUrl = normalized
                prefs.edit().putString(keyUrl, currentUrl).apply()
                launchCustomTab(currentUrl)
            }
        }

        // Abrir la raíz del sitio
        binding.btnOpenBrowser.setOnClickListener {
            launchCustomTab(currentUrl)
        }

        // Abrir directo el login del sitio web
        binding.btnOpenLogin.setOnClickListener {
            val loginUrl = currentUrl.ensureTrailingSlash() + "accounts/login/"
            launchCustomTab(loginUrl)
        }

        return binding.root
    }

    private fun launchCustomTab(url: String) {
        val uri = Uri.parse(url)
        val intent = CustomTabsIntent.Builder().build()
        intent.launchUrl(requireContext(), uri)
    }

    private fun String.ensureTrailingSlash(): String =
        if (this.endsWith("/")) this else "$this/"

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
