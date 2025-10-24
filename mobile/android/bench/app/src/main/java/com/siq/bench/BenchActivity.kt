package com.siq.bench

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.util.Size
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.siq.bench.metrics.LogcatMetricLogger
import com.siq.bench.metrics.MetricLogger
import com.siq.detector.FeatureFlags
import com.siq.detector.camera.CameraXAnalyzer
import com.siq.detector.net.TelemetryClient
import com.siq.detector.tflite.TfLiteDetector
import com.siq.detector.ui.PerfOverlayView
import java.util.concurrent.ExecutionException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import kotlinx.coroutines.launch
import org.json.JSONObject

class BenchActivity : ComponentActivity() {
    private val logger: MetricLogger = LogcatMetricLogger()
    private val runner = BenchmarkRunner(logger)

    private var detector: TfLiteDetector? = null
    private var overlay: PerfOverlayView? = null
    private lateinit var previewView: PreviewView
    private lateinit var cameraExecutor: ExecutorService
    private var telemetryBaseUrl: String = FeatureFlags.TELEMETRY_BASE_URL
    private var delegateInUse: String = FeatureFlags.ANDROID_DELEGATE
    private var remoteBenchmarkStarted = false
    private var lastTelemetryAt = 0L

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) {
                startCamera()
            } else {
                Log.w(TAG, "Camera permission denied; falling back to remote path")
                startRemoteBenchmark()
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        cameraExecutor = Executors.newSingleThreadExecutor()

        if (!FeatureFlags.ANDROID_LOCAL_DETECTOR) {
            Log.i(TAG, "Local detector flag disabled; using remote pipeline")
            startRemoteBenchmark()
            return
        }

        detector = try {
            TfLiteDetector(applicationContext, MODEL_PATH, delegateInUse).also {
                delegateInUse = it.delegate()
            }
        } catch (t: Throwable) {
            Log.e(TAG, "Failed to initialize local detector", t)
            null
        }

        if (detector == null) {
            startRemoteBenchmark()
            return
        }

        setupCameraUi()
        when {
            ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED ->
                startCamera()
            shouldShowRequestPermissionRationale(Manifest.permission.CAMERA) -> {
                Log.w(TAG, "Camera permission rationale required; using remote pipeline")
                startRemoteBenchmark()
            }
            else -> permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    private fun setupCameraUi() {
        previewView = PreviewView(this).apply {
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
        }
        val root = FrameLayout(this).apply {
            addView(
                previewView,
                FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.MATCH_PARENT,
                    FrameLayout.LayoutParams.MATCH_PARENT
                )
            )
        }
        if (FeatureFlags.PERF_OVERLAY) {
            overlay = PerfOverlayView(this)
            root.addView(
                overlay,
                FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.WRAP_CONTENT,
                    FrameLayout.LayoutParams.WRAP_CONTENT
                ).apply { gravity = Gravity.TOP or Gravity.START }
            )
        }
        setContentView(root)
    }

    private fun startCamera() {
        val providerFuture = ProcessCameraProvider.getInstance(this)
        providerFuture.addListener({
            try {
                val provider = providerFuture.get()
                bindCamera(provider)
            } catch (ex: ExecutionException) {
                Log.e(TAG, "Failed to obtain camera provider", ex)
                startRemoteBenchmark()
            } catch (ex: InterruptedException) {
                Log.e(TAG, "Camera provider interrupted", ex)
                startRemoteBenchmark()
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun bindCamera(provider: ProcessCameraProvider) {
        val preview = Preview.Builder().build().also {
            it.setSurfaceProvider(previewView.surfaceProvider)
        }
        val analyzer = ImageAnalysis.Builder()
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .setTargetResolution(detector?.inputSize() ?: Size(320, 320))
            .build()
        analyzer.setAnalyzer(
            cameraExecutor,
            CameraXAnalyzer(detector) { detections, latMs, fps ->
                overlay?.update(latMs.toFloat(), fps)
                logDetections(detections, latMs, fps)
                sendTelemetry(latMs, fps)
            }
        )
        provider.unbindAll()
        provider.bindToLifecycle(
            this,
            CameraSelector.DEFAULT_BACK_CAMERA,
            preview,
            analyzer
        )
    }

    private fun logDetections(
        detections: List<TfLiteDetector.Detection>,
        latMs: Long,
        fps: Float
    ) {
        if (detections.isEmpty()) {
            Log.d(TAG, "No detections. latency=${latMs}ms fps=${"%.1f".format(fps)}")
        } else {
            val summary = detections.joinToString(limit = 5) { det ->
                "#${'$'}{det.classId}@${'$'}{"%.2f".format(det.score)}(${det.rect.left.toInt()},${det.rect.top.toInt()},${det.rect.width().toInt()}x${det.rect.height().toInt()})"
            }
            Log.d(
                TAG,
                "Detections=${detections.size} latency=${latMs}ms fps=${"%.1f".format(fps)} => ${'$'}summary"
            )
        }
    }

    private fun sendTelemetry(latMs: Long, fps: Float) {
        if (telemetryBaseUrl.isBlank()) return
        val now = System.currentTimeMillis()
        if (now - lastTelemetryAt < 500) return
        lastTelemetryAt = now
        val payload = JSONObject()
            .put("timestampMs", System.currentTimeMillis())
            .put("device", "android")
            .put("buildId", BuildConfig.VERSION_NAME)
            .put("localDetector", true)
            .put("delegate", delegateInUse)
            .put("frameLatencyMs", latMs.toDouble())
            .put("fps", fps.toDouble())
        TelemetryClient.postTelemetry(telemetryBaseUrl, payload)
    }

    private fun startRemoteBenchmark() {
        if (remoteBenchmarkStarted) return
        remoteBenchmarkStarted = true
        detector?.close()
        detector = null
        setContentView(
            TextView(this).apply {
                text = "SIQ Edge Bench is running – check logcat for details."
            }
        )
        lifecycleScope.launch {
            FrameSource.assetsClip(applicationContext).use { source ->
                runner.runSweep(source)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        detector?.close()
        cameraExecutor.shutdown()
    }

    companion object {
        private const val TAG = "BenchActivity"
        private const val MODEL_PATH = "models/detector.tflite"
    }
}
