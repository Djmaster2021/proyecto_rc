package com.example.consultoriodentalrc

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first

private val Context.tokenDataStore by preferencesDataStore(name = "token_store")

/**
 * Guarda y recupera los tokens JWT usando DataStore.
 */
class TokenStore(private val context: Context) {

    private val accessKey = stringPreferencesKey("access_token")
    private val refreshKey = stringPreferencesKey("refresh_token")

    suspend fun saveTokens(access: String, refresh: String) {
        context.tokenDataStore.edit { prefs ->
            prefs[accessKey] = access
            prefs[refreshKey] = refresh
        }
    }

    suspend fun getAccessToken(): String? {
        val prefs = context.tokenDataStore.data.first()
        return prefs[accessKey]
    }

    suspend fun getRefreshToken(): String? {
        val prefs = context.tokenDataStore.data.first()
        return prefs[refreshKey]
    }

    suspend fun clear() {
        context.tokenDataStore.edit { prefs ->
            prefs.remove(accessKey)
            prefs.remove(refreshKey)
        }
    }
}
