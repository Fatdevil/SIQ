package com.siq.detector.tflite

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TfLiteDetectorInstrumentedTest {
    @Test
    fun detectorInitializesWhenModelAvailable() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val hasModel = try {
            context.assets.openFd(MODEL_PATH).close()
            true
        } catch (_: Throwable) {
            false
        }
        assumeTrue("detector.tflite missing in assets/models; skipping", hasModel)
        TfLiteDetector(context, MODEL_PATH).use {
            // Success if initialization does not throw.
        }
    }

    companion object {
        private const val MODEL_PATH = "models/detector.tflite"
    }
}
