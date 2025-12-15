package com.example.consultoriodentalrc // <-- Asegúrate que esto coincida con tu paquete

import com.google.gson.annotations.SerializedName

/**
 * Modelo de datos para ENVIAR las credenciales en el login.
 * El JSON se verá así: {"username": "...", "password": "..."}
 */
data class LoginRequest(
    val username: String,
    val password: String
)

/**
 * Modelo de datos para RECIBIR los tokens del servidor.
 * El JSON se verá así: {"access": "...", "refresh": "..."}
 */
data class LoginResponse(
    // @SerializedName le dice a GSON cómo se llama el campo en el JSON real
    @SerializedName("access")
    val accessToken: String,

    @SerializedName("refresh")
    val refreshToken: String
)

data class RefreshRequest(
    val refresh: String
)

data class RefreshResponse(
    @SerializedName("access")
    val accessToken: String
)

data class ServicioDto(
    val id: Int,
    val nombre: String,
    val precio: Double?,
    @SerializedName("duracion_estimada")
    val duracionEstimada: Int?,
    val activo: Boolean
)

data class SlotsResponse(
    val slots: List<String>?,
    val detail: String?
)

data class ChatRequest(
    val query: String
)

data class ChatbotResponse(
    val message: String,
    val source: String?,
    @SerializedName("source_detail")
    val sourceDetail: String? = null
)

data class CrearCitaRequest(
    @SerializedName("servicio_id")
    val servicioId: Int,
    val fecha: String,
    val hora: String
)

data class CrearCitaResponse(
    val id: Int,
    val servicio: ServicioInfo,
    val fecha: String,
    val hora: String,
    val estado: String,
    val dentista: DentistaInfo
)

data class ServicioInfo(
    val id: Int,
    val nombre: String
)

data class DentistaInfo(
    val id: Int,
    val nombre: String
)

data class CitaDto(
    val id: Int,
    val servicio: ServicioInfo,
    val fecha: String,
    val hora: String,
    val estado: String,
    val dentista: DentistaInfo,
    @SerializedName("puede_reprogramar")
    val puedeReprogramar: Boolean,
    @SerializedName("puede_cancelar")
    val puedeCancelar: Boolean
)

data class CitasResponse(
    val proximas: List<CitaDto>,
    val historial: List<CitaDto>
)

data class ReprogramarCitaRequest(
    val fecha: String,
    val hora: String
)
