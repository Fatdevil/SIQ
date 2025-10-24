package com.siq.bench

import android.util.Log
import com.siq.bench.metrics.MetricLogger
import kotlinx.coroutines.delay
import kotlin.time.Duration
import kotlin.time.Duration.Companion.nanoseconds
import kotlin.time.Duration.Companion.milliseconds

private const val TAG = "SIQBench"

class BenchmarkRunner(private val logger: MetricLogger) {
    suspend fun runSweep(source: FrameSource) {
        val delegates = listOf(
            RuntimeConfig("TFLite", "CPU"),
            RuntimeConfig("TFLite", "GPU"),
            RuntimeConfig("TFLite", "NNAPI"),
            RuntimeConfig("NCNN", "CPU"),
            RuntimeConfig("NCNN", "VULKAN"),
        )
        for (delegate in delegates) {
            runSingle(source, delegate)
        }
    }

    private suspend fun runSingle(source: FrameSource, config: RuntimeConfig) {
        Log.i(TAG, "Starting run for ${config.runtime} ${config.accelerator}")
        val metrics = MutableMetrics()
        val start = System.nanoTime()

        source.reset()
        var frames = 0
        while (source.hasNext()) {
            val frameStart = System.nanoTime()
            source.next()
            delay(2) // simulate preprocessing
            delay(10) // simulate inference work
            frames += 1
            val frameDuration = Duration.nanoseconds(System.nanoTime() - frameStart)
            metrics.recordFrame(frameDuration)
            metrics.recordMemory(210.0 + frames) // placeholder memory consumption
        }

        val coldStart = 120.milliseconds
        val wall = Duration.nanoseconds(System.nanoTime() - start)
        logger.logRun(
            config = config,
            frameCount = frames,
            p50 = metrics.p50,
            p95 = metrics.p95,
            fps = metrics.fps(wall),
            coldStart = coldStart,
            memoryMb = metrics.maxMemory,
            batteryDrainPercent = estimateBatteryDrain(wall),
        )
    }

    private fun estimateBatteryDrain(duration: Duration): Double {
        val minutes = duration.inWholeMinutes.coerceAtLeast(1)
        return (minutes / 15.0) * 4.0
    }
}

data class RuntimeConfig(val runtime: String, val accelerator: String)

data class Frame(val timestampNanos: Long)

class MutableMetrics {
    private val frameDurations = mutableListOf<Duration>()
    private val memoryReadings = mutableListOf<Double>()

    val p50: Duration
        get() = percentile(0.5)

    val p95: Duration
        get() = percentile(0.95)

    val maxMemory: Double
        get() = memoryReadings.maxOrNull() ?: 0.0

    fun recordFrame(duration: Duration) {
        frameDurations += duration
    }

    fun recordMemory(megabytes: Double) {
        memoryReadings += megabytes
    }

    fun fps(elapsed: Duration): Double {
        val totalSeconds = elapsed.inWholeMilliseconds / 1000.0
        return if (totalSeconds <= 0.0) 0.0 else frameDurations.size / totalSeconds
    }

    private fun percentile(p: Double): Duration {
        if (frameDurations.isEmpty()) return 0.milliseconds
        val sorted = frameDurations.sorted()
        val index = ((sorted.size - 1) * p).toInt()
        return sorted[index]
    }
}
