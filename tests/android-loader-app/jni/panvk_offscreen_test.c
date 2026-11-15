#include <jni.h>
#include <android/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int panvk_offscreen_main(int argc, char **argv);

JNIEXPORT jint JNICALL
Java_org_panvk_loadertest_MainActivity_runOffscreenTest(JNIEnv *env, jobject thiz,
                                                       jstring jAppDir,
                                                       jboolean fragment_control)
{
   (void)thiz;
   if (setenv("MESA_SHADER_CACHE_DISABLE", "true", 1) != 0) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKOffscreen",
                          "FAIL could not disable shader disk cache");
      return 1;
   }
   if (fragment_control && setenv("PAN_USE_KRAID", "fs", 1) != 0) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKOffscreen",
                          "FAIL could not set fragment-only control");
      return 1;
   }
   const char *app_dir = (*env)->GetStringUTFChars(env, jAppDir, NULL);
   if (!app_dir) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKOffscreen",
                          "FAIL could not read app directory");
      return 1;
   }
   char so_path[512];
   int length = snprintf(so_path, sizeof(so_path), "%s/libvulkan_panfrost.so",
                         app_dir);
   (*env)->ReleaseStringUTFChars(env, jAppDir, app_dir);
   if (length < 0 || (size_t)length >= sizeof(so_path)) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKOffscreen",
                          "FAIL driver path too long");
      return 1;
   }
   char *argv[] = {"panvk-offscreen", so_path, NULL};
   __android_log_print(ANDROID_LOG_INFO, "PanVKOffscreen",
                       "START pid=%d driver=%s mode=%s", getpid(), so_path,
                       fragment_control ? "fragment-only-control" : "default");
   int result = panvk_offscreen_main(2, argv);
   __android_log_print(ANDROID_LOG_INFO, "PanVKOffscreen",
                       "RESULT=%d", result);
   return result;
}
