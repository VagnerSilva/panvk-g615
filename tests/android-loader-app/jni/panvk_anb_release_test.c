#include <android/log.h>
#include <jni.h>
#include <stdio.h>
#include <unistd.h>

int panvk_anb_release_main(int argc, char **argv);

JNIEXPORT jint JNICALL
Java_org_panvk_loadertest_MainActivity_runAnbReleaseTest(JNIEnv *env, jobject thiz,
                                                        jstring jAppDir, jint waits)
{
   (void)thiz;
   if (waits != 1 && waits != 2) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKAnbRelease", "FAIL invalid waits=%d", waits);
      return 1;
   }
   const char *app_dir = (*env)->GetStringUTFChars(env, jAppDir, NULL);
   if (!app_dir) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKAnbRelease", "FAIL app directory");
      return 1;
   }
   char path[512];
   int length = snprintf(path, sizeof(path), "%s/libvulkan_panfrost.so", app_dir);
   (*env)->ReleaseStringUTFChars(env, jAppDir, app_dir);
   if (length < 0 || (size_t)length >= sizeof(path)) {
      __android_log_print(ANDROID_LOG_ERROR, "PanVKAnbRelease", "FAIL driver path too long");
      return 1;
   }
   char *argv[] = {"panvk-anb-release", path, waits == 1 ? "1" : "2", NULL};
   __android_log_print(ANDROID_LOG_INFO, "PanVKAnbRelease",
                       "START pid=%d driver=%s waits=%d", getpid(), path, waits);
   int result = panvk_anb_release_main(3, argv);
   __android_log_print(ANDROID_LOG_INFO, "PanVKAnbRelease", "RESULT=%d", result);
   return result;
}
