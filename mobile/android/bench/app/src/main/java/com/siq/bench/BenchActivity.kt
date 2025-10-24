package com.siq.bench

import android.os.Bundle
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.lifecycle.lifecycleScope
import com.siq.bench.metrics.LogcatMetricLogger
import com.siq.bench.metrics.MetricLogger
import kotlinx.coroutines.launch

class BenchActivity : ComponentActivity() {
    private val logger: MetricLogger = LogcatMetricLogger()
    private val runner = BenchmarkRunner(logger)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(TextView(this).apply {
            text = "SIQ Edge Bench is running – check logcat for details."
        })

        lifecycleScope.launch {
            FrameSource.assetsClip(applicationContext).use { source ->
                runner.runSweep(source)
            }
        }
    }
}
