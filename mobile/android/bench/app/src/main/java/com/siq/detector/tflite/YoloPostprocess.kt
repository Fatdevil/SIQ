package com.siq.detector.tflite

import kotlin.math.max
import kotlin.math.min

object YoloPostprocess {
    fun nms(
        boxes: FloatArray,
        scores: FloatArray,
        iouThresh: Float = 0.45f,
        scoreThresh: Float = 0.25f,
        maxDet: Int = 100
    ): IntArray {
        require(boxes.size == scores.size * 4) {
            "Boxes must be a flattened array of size scores.size * 4"
        }
        if (scores.isEmpty()) return IntArray(0)

        val sorted = scores.indices
            .filter { scores[it] >= scoreThresh }
            .sortedByDescending { scores[it] }

        val keep = ArrayList<Int>(min(maxDet, sorted.size))
        for (idx in sorted) {
            var shouldKeep = true
            for (kept in keep) {
                val iou = iou(boxes, idx, kept)
                if (iou > iouThresh) {
                    shouldKeep = false
                    break
                }
            }
            if (shouldKeep) {
                keep.add(idx)
                if (keep.size >= maxDet) break
            }
        }
        return keep.toIntArray()
    }

    private fun iou(boxes: FloatArray, a: Int, b: Int): Float {
        val ax1 = boxes[a * 4]
        val ay1 = boxes[a * 4 + 1]
        val ax2 = boxes[a * 4 + 2]
        val ay2 = boxes[a * 4 + 3]
        val bx1 = boxes[b * 4]
        val by1 = boxes[b * 4 + 1]
        val bx2 = boxes[b * 4 + 2]
        val by2 = boxes[b * 4 + 3]

        val interX1 = max(ax1, bx1)
        val interY1 = max(ay1, by1)
        val interX2 = min(ax2, bx2)
        val interY2 = min(ay2, by2)
        val interArea = max(0f, interX2 - interX1) * max(0f, interY2 - interY1)
        if (interArea <= 0f) return 0f

        val areaA = max(0f, ax2 - ax1) * max(0f, ay2 - ay1)
        val areaB = max(0f, bx2 - bx1) * max(0f, by2 - by1)
        if (areaA <= 0f || areaB <= 0f) return 0f

        return interArea / (areaA + areaB - interArea)
    }
}
