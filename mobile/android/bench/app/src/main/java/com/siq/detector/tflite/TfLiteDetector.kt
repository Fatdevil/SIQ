package com.siq.detector.tflite

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.RectF
import android.util.Log
import android.util.Size
import java.io.Closeable
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel
import kotlin.math.min
import org.tensorflow.lite.Delegate
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.gpu.GpuDelegate

class TfLiteDetector(
    context: Context,
    modelPath: String,
    delegate: String = "cpu"
) : Closeable {
    private val interpreter: Interpreter
    private val delegateInstance: Delegate?
    private val delegateUsed: String
    private val inputSize = Size(320, 320)
    private val inputBuffer: ByteBuffer =
        ByteBuffer.allocateDirect(4 * inputSize.width * inputSize.height * 3).apply {
            order(ByteOrder.nativeOrder())
        }
    private val intValues = IntArray(inputSize.width * inputSize.height)
    private val bitmap =
        Bitmap.createBitmap(inputSize.width, inputSize.height, Bitmap.Config.ARGB_8888)
    private val canvas = Canvas(bitmap)
    private val matrix = Matrix()
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)

    init {
        val options = Interpreter.Options().apply {
            setNumThreads(Runtime.getRuntime().availableProcessors().coerceAtMost(4))
        }
        var actualDelegate = delegate.lowercase()
        delegateInstance = when (actualDelegate) {
            "gpu" -> try {
                GpuDelegate().also { options.addDelegate(it) }
            } catch (t: Throwable) {
                Log.w(TAG, "Falling back to CPU delegate", t)
                actualDelegate = "cpu"
                null
            }
            "nnapi" -> {
                options.setUseNNAPI(true)
                null
            }
            else -> null
        }
        delegateUsed = actualDelegate

        val fd = context.assets.openFd(modelPath)
        val channel = FileInputStream(fd.fileDescriptor).channel
        val mapped = channel.map(FileChannel.MapMode.READ_ONLY, fd.startOffset, fd.declaredLength)
        interpreter = Interpreter(mapped, options)
    }

    fun inputSize(): Size = inputSize

    fun detect(src: Bitmap, scoreThreshold: Float = 0.25f, iouThreshold: Float = 0.45f): List<Detection> {
        val scale = min(
            inputSize.width.toFloat() / src.width.toFloat(),
            inputSize.height.toFloat() / src.height.toFloat()
        )
        val scaledWidth = src.width * scale
        val scaledHeight = src.height * scale
        val dx = (inputSize.width - scaledWidth) * 0.5f
        val dy = (inputSize.height - scaledHeight) * 0.5f

        matrix.reset()
        matrix.setScale(scale, scale)
        matrix.postTranslate(dx, dy)

        canvas.drawColor(0xFF000000.toInt())
        canvas.drawBitmap(src, matrix, paint)

        bitmap.getPixels(intValues, 0, inputSize.width, 0, 0, inputSize.width, inputSize.height)
        inputBuffer.rewind()
        for (pixel in intValues) {
            val r = (pixel shr 16 and 0xFF) / 255.0f
            val g = (pixel shr 8 and 0xFF) / 255.0f
            val b = (pixel and 0xFF) / 255.0f
            inputBuffer.putFloat(r)
            inputBuffer.putFloat(g)
            inputBuffer.putFloat(b)
        }
        inputBuffer.rewind()

        val outputTensor = interpreter.getOutputTensor(0)
        val shape = outputTensor.shape()
        val numDetections: Int
        val attributes: Int
        when (shape.size) {
            2 -> {
                numDetections = shape[0]
                attributes = shape[1]
            }
            3 -> {
                numDetections = shape[1]
                attributes = shape[2]
            }
            else -> throw IllegalStateException("Unexpected output tensor shape: ${shape.contentToString()}")
        }

        val output = Array(1) { Array(numDetections) { FloatArray(attributes) } }
        interpreter.run(inputBuffer, output)

        val boxes = ArrayList<RectF>()
        val scores = ArrayList<Float>()
        val classes = ArrayList<Int>()
        val maxDet = min(numDetections, 300)

        for (i in 0 until numDetections) {
            val row = output[0][i]
            if (row.size < 5) continue
            val objScore = if (row.size > 5) row[4] else 1f
            var maxClass = -1
            var maxClassScore = 0f
            if (row.size > 5) {
                for (c in 5 until row.size) {
                    val clsScore = row[c]
                    if (clsScore > maxClassScore) {
                        maxClassScore = clsScore
                        maxClass = c - 5
                    }
                }
            } else {
                maxClassScore = objScore
                maxClass = 0
            }
            val finalScore = objScore * maxClassScore
            if (finalScore < scoreThreshold || maxClass < 0) continue

            val normalized = row[2] <= 1.0f && row[3] <= 1.0f && row[0] <= 1.0f && row[1] <= 1.0f
            val cx = if (normalized) row[0] * inputSize.width else row[0]
            val cy = if (normalized) row[1] * inputSize.height else row[1]
            val w = if (normalized) row[2] * inputSize.width else row[2]
            val h = if (normalized) row[3] * inputSize.height else row[3]

            val x1 = cx - w / 2f
            val y1 = cy - h / 2f
            val x2 = cx + w / 2f
            val y2 = cy + h / 2f

            val mappedLeft = ((x1 - dx) / scale).coerceIn(0f, src.width.toFloat())
            val mappedTop = ((y1 - dy) / scale).coerceIn(0f, src.height.toFloat())
            val mappedRight = ((x2 - dx) / scale).coerceIn(0f, src.width.toFloat())
            val mappedBottom = ((y2 - dy) / scale).coerceIn(0f, src.height.toFloat())

            if (mappedRight <= mappedLeft || mappedBottom <= mappedTop) continue

            boxes.add(RectF(mappedLeft, mappedTop, mappedRight, mappedBottom))
            scores.add(finalScore)
            classes.add(maxClass)
        }

        if (boxes.isEmpty()) {
            return emptyList()
        }

        val boxesArray = FloatArray(boxes.size * 4)
        val scoresArray = FloatArray(scores.size)
        for (i in boxes.indices) {
            val rect = boxes[i]
            boxesArray[i * 4] = rect.left
            boxesArray[i * 4 + 1] = rect.top
            boxesArray[i * 4 + 2] = rect.right
            boxesArray[i * 4 + 3] = rect.bottom
            scoresArray[i] = scores[i]
        }

        val keep = YoloPostprocess.nms(
            boxesArray,
            scoresArray,
            iouThresh = iouThreshold,
            scoreThresh = scoreThreshold,
            maxDet = maxDet
        )

        val detections = ArrayList<Detection>(keep.size)
        for (idx in keep) {
            detections.add(Detection(classes[idx], scores[idx], boxes[idx]))
        }
        return detections
    }

    fun delegate(): String = delegateUsed

    override fun close() {
        try {
            interpreter.close()
        } catch (_: Throwable) {
        }
        try {
            delegateInstance?.close()
        } catch (_: Throwable) {
        }
    }

    data class Detection(val classId: Int, val score: Float, val rect: RectF)

    companion object {
        private const val TAG = "TfLiteDetector"
    }
}
