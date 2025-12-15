package com.example.consultoriodentalrc

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.consultoriodentalrc.databinding.FragmentLoginBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException

class LoginFragment : Fragment() {

    private var _binding: FragmentLoginBinding? = null
    private val binding get() = _binding!!

    private lateinit var tokenStore: TokenStore
    private lateinit var apiService: ApiService

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentLoginBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        tokenStore = TokenStore(requireContext())
        apiService = ApiClient.create(requireContext())

        binding.btnLogin.setOnClickListener { performLogin() }

        lifecycleScope.launch {
            val token = tokenStore.getAccessToken()
            if (!token.isNullOrBlank()) {
                findNavController().navigate(R.id.action_loginFragment_to_dashboardFragment)
            }
        }
    }

    private fun performLogin() {
        val username = binding.inputUsername.text?.toString().orEmpty()
        val password = binding.inputPassword.text?.toString().orEmpty()

        if (username.isBlank() || password.isBlank()) {
            Toast.makeText(requireContext(), "Ingresa usuario y contraseña", Toast.LENGTH_SHORT).show()
            return
        }

        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val response = apiService.login(LoginRequest(username, password))
                tokenStore.saveTokens(response.accessToken, response.refreshToken)
                findNavController().navigate(R.id.action_loginFragment_to_dashboardFragment)
            } catch (e: HttpException) {
                val msg = if (e.code() == 401) "Credenciales inválidas" else "Error ${e.code()}"
                Toast.makeText(requireContext(), msg, Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "Error de conexión: ${e.localizedMessage}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progress.isVisible = false
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
