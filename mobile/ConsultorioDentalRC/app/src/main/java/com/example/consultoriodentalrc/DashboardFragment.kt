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
import com.example.consultoriodentalrc.databinding.FragmentDashboardBinding
import com.example.consultoriodentalrc.CrearCitaRequest
import kotlinx.coroutines.launch
import retrofit2.HttpException

class DashboardFragment : Fragment() {

    private var _binding: FragmentDashboardBinding? = null
    private val binding get() = _binding!!

    private lateinit var tokenStore: TokenStore
    private lateinit var apiService: ApiService

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        tokenStore = TokenStore(requireContext())
        apiService = ApiClient.create(requireContext())

        binding.btnLogout.setOnClickListener {
            lifecycleScope.launch {
                tokenStore.clear()
                findNavController().navigate(R.id.action_dashboardFragment_to_loginFragment)
            }
        }
        binding.btnLoadServices.setOnClickListener { loadServicios() }
        binding.btnSlots.setOnClickListener { loadSlots() }
        binding.btnSendChat.setOnClickListener { sendChat() }
        binding.btnCrearCita.setOnClickListener { crearCita() }
        binding.btnListarCitas.setOnClickListener { listarCitas() }
        binding.btnCancelarCita.setOnClickListener { cancelarCita() }
        binding.btnReprogramar.setOnClickListener { reprogramarCita() }

        lifecycleScope.launch {
            val token = tokenStore.getAccessToken()
            if (token.isNullOrBlank()) {
                findNavController().navigate(R.id.action_dashboardFragment_to_loginFragment)
                return@launch
            }
            binding.textSession.text = "Sesión activa (Bearer...${token.takeLast(8)})"
        }
    }

    private fun loadServicios() {
        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val servicios = apiService.getServicios()
                val listado = servicios.joinToString("\n") {
                    val precio = it.precio?.let { p -> "$p" } ?: "-"
                    "• ${it.id} - ${it.nombre} ($precio)"
                }.ifBlank { "Sin servicios disponibles" }
                binding.textServicios.text = listado
            } catch (e: HttpException) {
                binding.textServicios.text = "Error ${e.code()} al consultar servicios"
            } catch (e: Exception) {
                binding.textServicios.text = "Error de conexión: ${e.localizedMessage}"
            } finally {
                binding.progress.isVisible = false
            }
        }
    }

    private fun loadSlots() {
        val fecha = binding.inputFecha.text?.toString().orEmpty()
        val servicioId = binding.inputServicioId.text?.toString().orEmpty()
        val dentistaId = binding.inputDentistaId.text?.toString().orEmpty()

        if (fecha.isBlank() || servicioId.isBlank()) {
            Toast.makeText(requireContext(), "Fecha y servicio son obligatorios", Toast.LENGTH_SHORT).show()
            return
        }

        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val response = apiService.getSlots(
                    fecha = fecha,
                    servicioId = servicioId.toInt(),
                    dentistaId = dentistaId.toIntOrNull()
                )
                val resultado = response.slots?.takeIf { it.isNotEmpty() }?.joinToString(", ")
                    ?: (response.detail ?: "Sin horarios disponibles")
                binding.textSlots.text = resultado
            } catch (e: HttpException) {
                binding.textSlots.text = "Error ${e.code()} al consultar slots"
            } catch (e: Exception) {
                binding.textSlots.text = "Error: ${e.localizedMessage}"
            } finally {
                binding.progress.isVisible = false
            }
        }
    }

    private fun sendChat() {
        val query = binding.inputChat.text?.toString().orEmpty()
        if (query.isBlank()) {
            Toast.makeText(requireContext(), "Escribe un mensaje", Toast.LENGTH_SHORT).show()
            return
        }

        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val response = apiService.chatbot(ChatRequest(query))
                binding.textChatResponse.text = response.message
            } catch (e: HttpException) {
                binding.textChatResponse.text = "Error ${e.code()} en el chatbot"
            } catch (e: Exception) {
                binding.textChatResponse.text = "Error: ${e.localizedMessage}"
            } finally {
                binding.progress.isVisible = false
            }
        }
    }

    private fun listarCitas() {
        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val resp = apiService.listarCitas()
                val proximas = resp.proximas.joinToString("\n") {
                    "#${it.id} ${it.fecha} ${it.hora} (${it.estado}) - ${it.servicio.nombre}"
                }.ifBlank { "Sin próximas" }
                val historial = resp.historial.joinToString("\n") {
                    "#${it.id} ${it.fecha} ${it.hora} (${it.estado}) - ${it.servicio.nombre}"
                }.ifBlank { "Sin historial" }
                binding.textCitas.text = "Próximas:\n$proximas\n\nHistorial:\n$historial"
            } catch (e: HttpException) {
                binding.textCitas.text = "Error ${e.code()} al listar citas"
            } catch (e: Exception) {
                binding.textCitas.text = "Error: ${e.localizedMessage}"
            } finally {
                binding.progress.isVisible = false
            }
        }
    }

    private fun cancelarCita() {
        val citaId = binding.inputCitaId.text?.toString()?.toIntOrNull()
        if (citaId == null) {
            Toast.makeText(requireContext(), "Ingresa el ID de la cita", Toast.LENGTH_SHORT).show()
            return
        }
        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val resp = apiService.cancelarCita(citaId)
                binding.textAccionCita.text = "Cita #${resp.id} cancelada (${resp.fecha} ${resp.hora})"
            } catch (e: HttpException) {
                binding.textAccionCita.text = "Error ${e.code()} al cancelar"
            } catch (e: Exception) {
                binding.textAccionCita.text = "Error: ${e.localizedMessage}"
            } finally {
                binding.progress.isVisible = false
            }
        }
    }

    private fun reprogramarCita() {
        val citaId = binding.inputCitaId.text?.toString()?.toIntOrNull()
        val fecha = binding.inputReprogFecha.text?.toString().orEmpty()
        val hora = binding.inputReprogHora.text?.toString().orEmpty()
        if (citaId == null || fecha.isBlank() || hora.isBlank()) {
            Toast.makeText(requireContext(), "Cita ID, nueva fecha y hora son obligatorios", Toast.LENGTH_SHORT).show()
            return
        }
        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val resp = apiService.reprogramarCita(
                    citaId,
                    ReprogramarCitaRequest(fecha = fecha, hora = hora)
                )
                binding.textAccionCita.text = "Cita #${resp.id} reprogramada a ${resp.fecha} ${resp.hora}"
            } catch (e: HttpException) {
                val msg = if (e.code() == 409) "Horario no disponible" else "Error ${e.code()}"
                binding.textAccionCita.text = msg
            } catch (e: Exception) {
                binding.textAccionCita.text = "Error: ${e.localizedMessage}"
            } finally {
                binding.progress.isVisible = false
            }
        }
    }

    private fun crearCita() {
        val fecha = binding.inputFecha.text?.toString().orEmpty()
        val servicioId = binding.inputServicioId.text?.toString().orEmpty()
        val hora = binding.inputHora.text?.toString().orEmpty()

        if (fecha.isBlank() || servicioId.isBlank() || hora.isBlank()) {
            Toast.makeText(requireContext(), "Fecha, servicio y hora son obligatorios", Toast.LENGTH_SHORT).show()
            return
        }

        binding.progress.isVisible = true
        lifecycleScope.launch {
            try {
                val response = apiService.crearCita(
                    CrearCitaRequest(
                        servicioId = servicioId.toInt(),
                        fecha = fecha,
                        hora = hora,
                    )
                )
                binding.textCita.text =
                    "Cita #${response.id} ${response.fecha} ${response.hora} con ${response.dentista.nombre} (${response.servicio.nombre})"
            } catch (e: HttpException) {
                val msg = if (e.code() == 409) {
                    "Horario no disponible"
                } else {
                    "Error ${e.code()} al crear cita"
                }
                binding.textCita.text = msg
            } catch (e: Exception) {
                binding.textCita.text = "Error: ${e.localizedMessage}"
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
