package org.panvk.loadertest;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.WindowManager;
import android.widget.TextView;

public class MainActivity extends Activity implements SurfaceHolder.Callback {
    private static final String TAG = "PanVKLoaderApp";
    private TextView statusText;
    private SurfaceView surfaceView;
    private boolean testStarted = false;

    static {
        System.loadLibrary("panvk_loader_test");
        System.loadLibrary("panvk_offscreen_test");
        System.loadLibrary("panvk_sync_fd_test");
        System.loadLibrary("panvk_compute_test");
        System.loadLibrary("panvk_idvs_test");
        System.loadLibrary("panvk_anb_release_test");
    }

    public native String runPanvkTest(Surface surface, String appDir, String zipPath,
                                      boolean forceWsiDraw, boolean recreateSwapchain);
    public native int runOffscreenTest(String appDir, boolean fragmentControl);
    public native int runSyncFdTest(String appDir, boolean waitSignal);
    public native int runComputeTest(String appDir, int testCase, boolean legacyControl);
    public native int runIdvsTest(String appDir, boolean legacyControl, int variant,
                                  boolean linear);
    public native int runAnbReleaseTest(String appDir, int waits);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(
            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
            | WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
            | WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD);
        setContentView(R.layout.activity_main);
        statusText = findViewById(R.id.status_text);
        surfaceView = findViewById(R.id.surface_view);
        surfaceView.getHolder().addCallback(this);
        Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " MainActivity.onCreate");
    }

    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " surfaceCreated valid=" + holder.getSurface().isValid());
    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        Log.i(TAG, "PID_SELF=" + android.os.Process.myPid()
            + " surfaceChanged " + width + "x" + height + " valid=" + holder.getSurface().isValid());
        if (testStarted) return;
        if (width <= 0 || height <= 0) return;
        if (!holder.getSurface().isValid()) return;
        testStarted = true;
        statusText.setText("Surface ready " + width + "x" + height + ". Starting tests...");
        final Surface surface = holder.getSurface();
        final String appDir = getFilesDir().getAbsolutePath();
        new Thread(() -> {
            String testMode = getIntent().getStringExtra("test_mode");
            if ("anb_release_1".equals(testMode) || "anb_release_2".equals(testMode)) {
                int result = runAnbReleaseTest(appDir, testMode.endsWith("_1") ? 1 : 2);
                Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " ANB release result=" + result);
                runOnUiThread(() -> {
                    statusText.setText(result == 0 ? "ANB release PASS" : "ANB release FAIL");
                    finish();
                });
                return;
            }
            if (testMode != null &&
                testMode.matches("idvs_(varying|multi|point|triangle_psiz)(_linear)?(_control)?")) {
                int variant = testMode.startsWith("idvs_multi") ? 1 :
                              testMode.startsWith("idvs_point") ? 2 :
                              testMode.startsWith("idvs_triangle_psiz") ? 3 : 0;
                int result = runIdvsTest(appDir, testMode.endsWith("_control"),
                                         variant, testMode.contains("_linear"));
                Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " IDVS result=" + result);
                runOnUiThread(() -> {
                    statusText.setText(result == 0 ? "IDVS PASS" : result == 2 ? "IDVS SKIP" : "IDVS FAIL");
                    finish();
                });
                return;
            }
            if (testMode != null && testMode.matches("compute_(control_)?([0-9]|1[0-9]|2[01])")) {
                boolean control = testMode.startsWith("compute_control_");
                int testCase = Integer.parseInt(testMode.substring(testMode.lastIndexOf('_') + 1));
                int result = runComputeTest(appDir, testCase, control);
                Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " Compute result=" + result);
                runOnUiThread(() -> {
                    statusText.setText(result == 0 ? "Compute PASS" : result == 2 ? "Compute SKIP" : "Compute FAIL");
                    finish();
                });
                return;
            }
            if ("sync_fd".equals(testMode) || "sync_wait_signal".equals(testMode)) {
                int result = runSyncFdTest(appDir, "sync_wait_signal".equals(testMode));
                Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " Sync FD result=" + result);
                runOnUiThread(() -> {
                    statusText.setText(result == 0 ? "Sync FD PASS" : result == 2 ? "Sync FD SKIP" : "Sync FD FAIL");
                    finish();
                });
                return;
            }
            if ("offscreen".equals(testMode) || "offscreen_fs_control".equals(testMode)) {
                Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " Starting offscreen test");
                int result = runOffscreenTest(appDir, "offscreen_fs_control".equals(testMode));
                Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " Offscreen result=" + result);
                runOnUiThread(() -> {
                    statusText.setText(result == 0 ? "Offscreen PASS" : "Offscreen FAIL");
                    finish();
                });
                return;
            }
            String zipPath = "/data/local/tmp/PanVK-Kbase-Android-g615-v11-csf-v0.1.0-beta.1-5a07217f.adpkg.zip";
            Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " Starting runPanvkTest with zip=" + zipPath);
            boolean forceWsiDraw = "wsi_draw".equals(testMode);
            final String result = runPanvkTest(surface, appDir, zipPath, forceWsiDraw,
                                               "wsi_recreate".equals(testMode));
            Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " runPanvkTest completed: " + result);
            runOnUiThread(() -> {
                statusText.setText(result);
                finish();
            });
        }).start();
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {
        Log.i(TAG, "PID_SELF=" + android.os.Process.myPid() + " surfaceDestroyed");
    }
}
