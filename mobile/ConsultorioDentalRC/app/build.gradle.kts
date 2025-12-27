import com.android.build.gradle.internal.cxx.configure.gradleLocalProperties
import java.io.File
import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "com.example.consultoriodentalrc"
    compileSdk = 36

    val keystoreProps = Properties().apply {
        val file = rootProject.file("keystore.properties")
        if (file.exists()) {
            file.inputStream().use { load(it) }
        }
    }

    fun prop(name: String): String? =
        providers.gradleProperty(name).orNull ?: keystoreProps.getProperty(name)

    defaultConfig {
        applicationId = "com.example.consultoriodentalrc"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        val baseUrl: String = gradleLocalProperties(rootDir, providers)
            .getProperty("BASE_URL")
            ?: "http://10.0.2.2:8000/"

        buildConfigField(
            "String",
            "BASE_URL",
            "\"${baseUrl.trimEnd('/')}/\""
        )
    }

    val keystorePath: String? = prop("CONSULTORIO_STORE_FILE")
    val keystorePassword: String? = prop("CONSULTORIO_STORE_PASSWORD")
    val keyAlias: String? = prop("CONSULTORIO_KEY_ALIAS")
    val keyPassword: String? = prop("CONSULTORIO_KEY_PASSWORD")
    val hasReleaseSigning = listOf(keystorePath, keystorePassword, keyAlias, keyPassword).all { !it.isNullOrBlank() }

    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                storeFile = file(keystorePath!!)
                storePassword = keystorePassword
                this.keyAlias = keyAlias
                this.keyPassword = keyPassword
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = if (hasReleaseSigning) {
                signingConfigs.getByName("release")
            } else {
                // En CI/dev, firma con el keystore debug que genera Android por defecto.
                signingConfigs.getByName("debug")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures {
        buildConfig = true
        viewBinding = true
    }
}

dependencies {

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.navigation.fragment.ktx)
    implementation(libs.androidx.navigation.ui.ktx)
    implementation(libs.lifecycle.viewmodel.ktx)
    implementation(libs.lifecycle.runtime.ktx)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.datastore.preferences)
    implementation(libs.okhttp.logging.interceptor)
    implementation(libs.okhttp.core)
    implementation(libs.androidx.browser)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    implementation(libs.retrofit.core)
    implementation(libs.retrofit.converter.gson)
}
