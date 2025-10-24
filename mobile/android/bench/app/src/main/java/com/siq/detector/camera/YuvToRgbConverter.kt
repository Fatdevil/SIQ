package com.siq.detector.camera

import android.graphics.Bitmap
import android.graphics.Color
import androidx.camera.core.ImageProxy
import kotlin.math.max

class YuvToRgbConverter {
    private var yBuffer = ByteArray(0)
    private var uBuffer = ByteArray(0)
    private var vBuffer = ByteArray(0)
    private var outBuffer = IntArray(0)

    fun yuvToRgb(image: ImageProxy, output: Bitmap) {
        val yPlane = image.planes[0]
        val uPlane = image.planes[1]
        val vPlane = image.planes[2]

        if (yBuffer.size != yPlane.buffer.remaining()) {
            yBuffer = ByteArray(yPlane.buffer.remaining())
        }
        if (uBuffer.size != uPlane.buffer.remaining()) {
            uBuffer = ByteArray(uPlane.buffer.remaining())
        }
        if (vBuffer.size != vPlane.buffer.remaining()) {
            vBuffer = ByteArray(vPlane.buffer.remaining())
        }

        yPlane.buffer.rewind()
        yPlane.buffer.get(yBuffer)
        uPlane.buffer.rewind()
        uPlane.buffer.get(uBuffer)
        vPlane.buffer.rewind()
        vPlane.buffer.get(vBuffer)

        val width = image.width
        val height = image.height
        if (outBuffer.size != width * height) {
            outBuffer = IntArray(width * height)
        }

        val yRowStride = yPlane.rowStride
        val uvRowStride = uPlane.rowStride
        val uPixelStride = uPlane.pixelStride
        val vPixelStride = vPlane.pixelStride

        var offset = 0
        for (row in 0 until height) {
            val yRow = yRowStride * row
            val uvRow = uvRowStride * (row / 2)
            for (col in 0 until width) {
                val yVal = (yBuffer[yRow + col].toInt() and 0xFF)
                val uIndex = uvRow + (col / 2) * uPixelStride
                val vIndex = uvRow + (col / 2) * vPixelStride
                val uVal = (uBuffer[uIndex].toInt() and 0xFF)
                val vVal = (vBuffer[vIndex].toInt() and 0xFF)
                outBuffer[offset++] = yuvToRgbPixel(yVal, uVal, vVal)
            }
        }
        output.setPixels(outBuffer, 0, width, 0, 0, width, height)
    }

    private fun yuvToRgbPixel(y: Int, u: Int, v: Int): Int {
        val yf = max(y - 16, 0)
        val uf = u - 128
        val vf = v - 128
        var r = (1.164f * yf + 1.596f * vf).toInt()
        var g = (1.164f * yf - 0.813f * vf - 0.391f * uf).toInt()
        var b = (1.164f * yf + 2.018f * uf).toInt()
        r = r.coerceIn(0, 255)
        g = g.coerceIn(0, 255)
        b = b.coerceIn(0, 255)
        return Color.rgb(r, g, b)
    }
}
