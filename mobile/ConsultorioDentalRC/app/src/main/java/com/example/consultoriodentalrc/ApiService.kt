package com.example.consultoriodentalrc

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {

    @POST("api/token/")
    suspend fun login(@Body loginRequest: LoginRequest): LoginResponse

    @POST("api/token/refresh/")
    suspend fun refresh(@Body refreshRequest: RefreshRequest): RefreshResponse

    @GET("api/servicios/")
    suspend fun getServicios(): List<ServicioDto>

    @GET("api/slots/")
    suspend fun getSlots(
        @Query("fecha") fecha: String,
        @Query("servicio_id") servicioId: Int,
        @Query("dentista_id") dentistaId: Int? = null
    ): SlotsResponse

    @POST("api/chatbot/")
    suspend fun chatbot(@Body chatRequest: ChatRequest): ChatbotResponse

    @POST("api/citas/")
    suspend fun crearCita(@Body request: CrearCitaRequest): CrearCitaResponse

    @GET("api/citas/listar/")
    suspend fun listarCitas(): CitasResponse

    @POST("api/citas/{id}/cancelar/")
    suspend fun cancelarCita(@Path("id") id: Int): CrearCitaResponse

    @POST("api/citas/{id}/reprogramar/")
    suspend fun reprogramarCita(
        @Path("id") id: Int,
        @Body request: ReprogramarCitaRequest
    ): CrearCitaResponse
}
