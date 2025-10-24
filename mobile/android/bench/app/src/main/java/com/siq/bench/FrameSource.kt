package com.siq.bench

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

interface FrameSource : AutoCloseable {
    suspend fun next(): Frame
    fun hasNext(): Boolean
    fun reset()

    companion object {
        fun assetsClip(context: Context): FrameSource = InMemoryFrameSource(context)
    }
}

private class InMemoryFrameSource(@Suppress("UNUSED_PARAMETER") context: Context) : FrameSource {
    private val frames = buildList {
        val now = System.nanoTime()
        repeat(300) { idx ->
            add(Frame(now + idx * 33_000_000L))
        }
    }
    private var index = 0

    override suspend fun next(): Frame = withContext(Dispatchers.Default) {
        frames[index++]
    }

    override fun hasNext(): Boolean = index < frames.size

    override fun reset() {
        index = 0
    }

    override fun close() {
        index = 0
    }
}
