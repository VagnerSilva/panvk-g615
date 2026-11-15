#include <android/log.h>
#include <jni.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int panvk_compute_main(int argc, char **argv);

JNIEXPORT jint JNICALL
Java_org_panvk_loadertest_MainActivity_runComputeTest(JNIEnv *env, jobject thiz,
                                                     jstring jAppDir,
                                                     jint test_case,
                                                     jboolean legacy_control)
{
   (void)thiz;
   if (test_case < 0 || test_case > 21) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKCompute", "FAIL invalid case=%d",
                          test_case);
      return 1;
   }
   if (setenv("MESA_SHADER_CACHE_DISABLE", "true", 1) != 0) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKCompute",
                          "FAIL could not disable shader disk cache");
      return 1;
   }
   if (legacy_control && setenv("PAN_USE_KRAID", "vs,fs", 1) != 0) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKCompute",
                          "FAIL could not set legacy compute control");
      return 1;
   }
   const char *app_dir = (*env)->GetStringUTFChars(env, jAppDir, NULL);
   if (!app_dir) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKCompute",
                          "FAIL could not read app directory");
      return 1;
   }
   char so_path[512], mode[16];
   int length = snprintf(so_path, sizeof(so_path), "%s/libvulkan_panfrost.so",
                         app_dir);
   (*env)->ReleaseStringUTFChars(env, jAppDir, app_dir);
   if (length < 0 || (size_t)length >= sizeof(so_path)) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKCompute",
                          "FAIL driver path too long");
      return 1;
   }
   snprintf(mode, sizeof(mode), "guarded-%d", test_case);
   char *argv[] = {"panvk-compute", so_path, mode, NULL};
   __android_log_print(ANDROID_LOG_INFO, "PanVKCompute",
                       "START pid=%d driver=%s control=%d case=%d", getpid(),
                       so_path, legacy_control, test_case);
   int result = panvk_compute_main(3, argv);
   __android_log_print(ANDROID_LOG_INFO, "PanVKCompute", "RESULT=%d", result);
   return result;
}
