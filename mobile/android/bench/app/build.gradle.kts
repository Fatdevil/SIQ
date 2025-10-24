plugins {
    id("com.android.application")
    kotlin("android")
}

android {
    namespace = "com.siq.bench"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.siq.bench"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    buildTypes {
        getByName("debug") {
            isDebuggable = true
        }
        getByName("release") {
            isMinifyEnabled = false
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.camera:camera-core:1.3.2")
    implementation("androidx.camera:camera-camera2:1.3.2")
    implementation("androidx.camera:camera-lifecycle:1.3.2")
    implementation("androidx.camera:camera-view:1.3.2")
    implementation("com.google.android.material:material:1.11.0")
    // Placeholders for inference runtimes. Swap in the real dependencies when available.
    implementation("org.tensorflow:tensorflow-lite:2.14.0")
    implementation("com.tencent:ncnn-android:20240116")
}
