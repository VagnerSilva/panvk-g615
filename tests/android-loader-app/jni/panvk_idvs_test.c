#include <android/log.h>
#include <jni.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int panvk_idvs_main(int argc, char **argv);

JNIEXPORT jint JNICALL
Java_org_panvk_loadertest_MainActivity_runIdvsTest(JNIEnv *env, jobject thiz,
                                                  jstring jAppDir,
                                                  jboolean legacy_control,
                                                  jint variant,
                                                  jboolean linear)
{
   (void)thiz;
   if (variant < 0 || variant > 3) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKIdvs", "FAIL invalid variant=%d", variant);
      return 1;
   }
   if (setenv("MESA_SHADER_CACHE_DISABLE", "true", 1) != 0) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKIdvs",
                          "FAIL could not disable shader disk cache");
      return 1;
   }
   if (legacy_control && setenv("PAN_USE_KRAID", "fs", 1) != 0) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKIdvs",
                          "FAIL could not set legacy vertex control");
      return 1;
   }
   const char *app_dir = (*env)->GetStringUTFChars(env, jAppDir, NULL);
   if (!app_dir) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKIdvs",
                          "FAIL could not read app directory");
      return 1;
   }
   char so_path[512];
   int length = snprintf(so_path, sizeof(so_path), "%s/libvulkan_panfrost.so",
                         app_dir);
   (*env)->ReleaseStringUTFChars(env, jAppDir, app_dir);
   if (length < 0 || (size_t)length >= sizeof(so_path)) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKIdvs", "FAIL driver path too long");
      return 1;
   }
   char *modes[] = {"varying", "multi", "point", "triangle_psiz"};
   char *argv[] = {"panvk-idvs", so_path, modes[variant],
                   linear ? "linear" : NULL, NULL};
   __android_log_print(ANDROID_LOG_INFO, "PanVKIdvs",
                       "START pid=%d driver=%s control=%d variant=%d linear=%d", getpid(), so_path,
                       legacy_control, variant, linear);
   int result = panvk_idvs_main(linear ? 4 : 3, argv);
   __android_log_print(ANDROID_LOG_INFO, "PanVKIdvs", "RESULT=%d", result);
   return result;
}
