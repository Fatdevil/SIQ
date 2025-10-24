package com.siq.detector.ui

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View
import java.util.ArrayDeque

class PerfOverlayView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 36f
    }
    private val bgPaint = Paint().apply {
        color = Color.argb(160, 0, 0, 0)
    }
    private val latWindow = ArrayDeque<Float>()
    private var fps = 0f
    private var p50 = 0f
    private var p95 = 0f

    fun update(latMs: Float, fpsNow: Float) {
        latWindow.addLast(latMs)
        if (latWindow.size > 120) {
            latWindow.removeFirst()
        }
        val sorted = latWindow.sorted()
        if (sorted.isNotEmpty()) {
            p50 = sorted[(sorted.size * 0.5f).toInt().coerceAtMost(sorted.size - 1)]
            p95 = sorted[(sorted.size * 0.95f).toInt().coerceAtMost(sorted.size - 1)]
        }
        fps = fpsNow
        postInvalidateOnAnimation()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val lines = listOf(
            "FPS: %.1f".format(fps),
            "p50: %.1f ms".format(p50),
            "p95: %.1f ms".format(p95)
        )
        val padding = 24f
        val lineHeight = paint.textSize + 12f
        val boxWidth = lines.maxOf { paint.measureText(it) } + padding * 2
        val boxHeight = lineHeight * lines.size + padding
        canvas.drawRoundRect(
            padding,
            padding,
            padding + boxWidth,
            padding + boxHeight,
            16f,
            16f,
            bgPaint
        )
        var y = padding + lineHeight
        for (line in lines) {
            canvas.drawText(line, padding * 1.5f, y, paint)
            y += lineHeight
        }
    }
}
