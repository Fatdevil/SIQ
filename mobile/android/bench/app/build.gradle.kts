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
        buildConfigField("boolean", "ANDROID_LOCAL_DETECTOR_DEFAULT", "true")
        buildConfigField("String", "ANDROID_DELEGATE_DEFAULT", "\"cpu\"")
        buildConfigField("boolean", "PERF_OVERLAY_DEFAULT", "true")
        buildConfigField("String", "TELEMETRY_BASE_URL", "\"\"")
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
    implementation("org.tensorflow:tensorflow-lite:2.12.0")
    implementation("org.tensorflow:tensorflow-lite-gpu:2.12.0")
    implementation("org.tensorflow:tensorflow-lite-select-tf-ops:2.12.0")
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
