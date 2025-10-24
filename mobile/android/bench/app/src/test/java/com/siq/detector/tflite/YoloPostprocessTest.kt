package com.siq.detector.tflite

import org.junit.Assert.assertArrayEquals
import org.junit.Test

class YoloPostprocessTest {
    @Test
    fun `nms keeps highest scoring boxes`() {
        val boxes = floatArrayOf(
            0f, 0f, 10f, 10f,
            1f, 1f, 9f, 9f,
            20f, 20f, 30f, 30f
        )
        val scores = floatArrayOf(0.9f, 0.8f, 0.95f)
        val keep = YoloPostprocess.nms(boxes, scores, iouThresh = 0.5f, scoreThresh = 0.0f)
        assertArrayEquals(intArrayOf(2, 0), keep)
    }
}
