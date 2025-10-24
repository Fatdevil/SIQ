package com.siq.detector.camera

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class YuvIndexTest {
    @Test
    fun `u and v use their own row strides`() {
        val row = 6
        val col = 8

        val uRowStride = 64
        val vRowStride = 80
        val uPixelStride = 2
        val vPixelStride = 1

        val uIndex = YuvIndex.chromaIndex(row, col, uRowStride, uPixelStride)
        val vIndex = YuvIndex.chromaIndex(row, col, vRowStride, vPixelStride)

        assertNotEquals(uIndex, vIndex)

        val expectedV = vRowStride * (row / 2) + (col / 2) * vPixelStride
        assertEquals(expectedV, vIndex)
    }

    @Test
    fun `indexing matches 4_2_0 subsampling semantics`() {
        val row = 3
        val col = 10
        val rowStride = 40
        val pixelStride = 2

        val index0 = YuvIndex.chromaIndex(row, col, rowStride, pixelStride)
        val index1 = YuvIndex.chromaIndex(row, col + 1, rowStride, pixelStride)

        assertEquals(index0, index1)
    }
}
