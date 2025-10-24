package com.siq.bench.metrics

import android.util.Log
import com.siq.bench.RuntimeConfig
import kotlin.time.Duration

interface MetricLogger {
    fun logRun(
        config: RuntimeConfig,
        frameCount: Int,
        p50: Duration,
        p95: Duration,
        fps: Double,
        coldStart: Duration,
        memoryMb: Double,
        batteryDrainPercent: Double,
    )
}

class LogcatMetricLogger : MetricLogger {
    override fun logRun(
        config: RuntimeConfig,
        frameCount: Int,
        p50: Duration,
        p95: Duration,
        fps: Double,
        coldStart: Duration,
        memoryMb: Double,
        batteryDrainPercent: Double,
    ) {
        Log.i(
            "SIQBench",
            "${config.runtime}-${config.accelerator}: frames=$frameCount p50=${p50.inWholeMilliseconds}ms p95=${p95.inWholeMilliseconds}ms fps=${"%.1f".format(fps)} " +
                "coldStart=${coldStart.inWholeMilliseconds}ms mem=${"%.1f".format(memoryMb)}MB battery=${"%.2f".format(batteryDrainPercent)}%",
        )
    }
}
