package com.siq.detector.camera

import android.graphics.Bitmap
import android.os.SystemClock
import android.util.Log
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.siq.detector.tflite.TfLiteDetector
import java.util.concurrent.atomic.AtomicBoolean

class CameraXAnalyzer(
    private val detector: TfLiteDetector?,
    private val onResult: (List<TfLiteDetector.Detection>, Long, Float) -> Unit
) : ImageAnalysis.Analyzer {
    private val converter = YuvToRgbConverter()
    private var bitmapBuffer: Bitmap? = null
    private var lastTs = 0L
    private val running = AtomicBoolean(false)

    override fun analyze(image: ImageProxy) {
        if (!running.compareAndSet(false, true)) {
            image.close()
            return
        }
        try {
            val start = SystemClock.elapsedRealtimeNanos()
            val bitmap = bitmapBuffer?.takeIf {
                it.width == image.width && it.height == image.height
            } ?: Bitmap.createBitmap(image.width, image.height, Bitmap.Config.ARGB_8888).also {
                bitmapBuffer = it
            }
            converter.yuvToRgb(image, bitmap)
            val detections = detector?.detect(bitmap).orEmpty()
            val end = SystemClock.elapsedRealtimeNanos()
            val latMs = ((end - start) / 1e6f).toLong()
            val fps = if (lastTs != 0L) {
                val delta = end - lastTs
                if (delta > 0) (1e9f / delta).coerceAtMost(120f) else 0f
            } else {
                0f
            }
            lastTs = end
            onResult(detections, latMs, fps)
        } catch (t: Throwable) {
            Log.e(TAG, "Analyzer failure", t)
        } finally {
            image.close()
            running.set(false)
        }
    }

    companion object {
        private const val TAG = "CameraXAnalyzer"
    }
}
