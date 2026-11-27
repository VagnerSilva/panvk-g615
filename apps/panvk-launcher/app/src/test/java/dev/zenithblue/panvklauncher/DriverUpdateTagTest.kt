package dev.zenithblue.panvklauncher

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class DriverUpdateTagTest {
    private fun release(tag: String) =
        """{"tag_name":"$tag","draft":false,"html_url":"u","body":"b","assets":[{"name":"libvulkan_panfrost-g615-v11-csf-android-aarch64.so","browser_download_url":"https://x/y.so","size":1}]}"""

    @Test fun rcTagsParse() {
        assertNotNull(DriverUpdate.versionKey("0.1.0-rc4"))
        assertNotNull(DriverUpdate.versionKey("0.1.0-rc4-lowmem"))
        assertEquals(DriverUpdate.versionKey("0.1.0-rc4"), DriverUpdate.versionKey("0.1.0-rc4-lowmem"))
        assertEquals("rc4", DriverUpdate.label("0.1.0-rc4-lowmem"))
    }
    @Test fun rcOrdering() {
        assertTrue(DriverUpdate.isNewer("0.1.0-rc4", "0.1.0-rc3"))
        assertFalse(DriverUpdate.isNewer("0.1.0-rc3", "0.1.0-rc4"))
        assertTrue(DriverUpdate.isNewer("0.1.0", "0.1.0-rc4"))
    }
    @Test fun newestPicksG615Rc() {
        val json = "[" + listOf("panvk-g615-v11-csf-v27.0.0-rc1", "panvk-g615-v11-csf-v27.0.0-rc2", "panvk-kbase-v99.0.0").joinToString(",") { release(it) } + "]"
        val n = DriverUpdate.newest(json)
        assertNotNull(n)
        assertEquals("panvk-g615-v11-csf-v27.0.0-rc2", n!!.first.tag)
    }
    @Test fun historicalTagsAndGenericAssetsAreNotUpdates() {
        assertNull(DriverUpdate.newest("[" + release("panvk-kbase-v99.0.0") + "]"))
        assertNull(DriverUpdate.newest("[" + release("g615-v11-csf-v99.0.0") + "]"))
        val generic = release("panvk-g615-v11-csf-v27.0.0").replace(
            "libvulkan_panfrost-g615-v11-csf-android-aarch64.so",
            "libvulkan_panfrost-android-aarch64.so"
        )
        assertNull(DriverUpdate.newest("[$generic]"))
    }
    @Test fun mesaStyleInstalledVersion() {
        // bundled-driver.json packageVersion from build 115 on: shown as is; the RC releases are not offered as updates.
        assertEquals("26.3.0-devel", DriverUpdate.label("26.3.0-devel"))
        assertFalse(DriverUpdate.isNewer("0.1.0-rc4-lowmem", "26.3.0-devel"))
        assertTrue(DriverUpdate.isNewer("26.4.0-devel", "26.3.0-devel"))
    }
}
