package com.siq.detector

import com.siq.bench.BuildConfig

object FeatureFlags {
    private fun env(name: String): String? = try {
        System.getenv(name)
    } catch (_: SecurityException) {
        null
    }

    private fun envBoolean(name: String, default: Boolean): Boolean {
        val raw = env(name)?.lowercase()?.trim() ?: return default
        return when (raw) {
            "1", "true", "yes", "on" -> true
            "0", "false", "no", "off" -> false
            else -> default
        }
    }

    private fun envString(name: String, default: String): String {
        val raw = env(name)?.trim()
        return if (raw.isNullOrBlank()) default else raw
    }

    val ANDROID_LOCAL_DETECTOR: Boolean =
        envBoolean("ANDROID_LOCAL_DETECTOR", BuildConfig.ANDROID_LOCAL_DETECTOR_DEFAULT)

    val ANDROID_DELEGATE: String =
        envString("ANDROID_DELEGATE", BuildConfig.ANDROID_DELEGATE_DEFAULT).lowercase()

    val PERF_OVERLAY: Boolean =
        envBoolean("ANDROID_PERF_OVERLAY", BuildConfig.PERF_OVERLAY_DEFAULT)

    val TELEMETRY_BASE_URL: String =
        envString("ANDROID_TELEMETRY_BASE_URL", BuildConfig.TELEMETRY_BASE_URL)
}
