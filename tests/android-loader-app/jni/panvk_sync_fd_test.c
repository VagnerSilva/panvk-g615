#include <jni.h>
#include <android/log.h>
#include <dlfcn.h>
#include <errno.h>
#include <linux/sync_file.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <vulkan/vulkan.h>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "PanVKSyncFd", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "PanVKSyncFd", __VA_ARGS__)

JNIEXPORT jint JNICALL
Java_org_panvk_loadertest_MainActivity_runSyncFdTest(JNIEnv *env, jobject thiz,
                                                    jstring jAppDir, jboolean wait_signal)
{
   const char *app_dir = (*env)->GetStringUTFChars(env, jAppDir, NULL);
   if (!app_dir) {
      LOGE("FAIL reading app directory");
      return 1;
   }
   char path[512];
   int length = snprintf(path, sizeof(path), "%s/libvulkan_panfrost.so", app_dir);
   (*env)->ReleaseStringUTFChars(env, jAppDir, app_dir);
   if (length < 0 || (size_t)length >= sizeof(path)) {
      LOGE("FAIL driver path too long");
      return 1;
   }

   LOGI("START pid=%d driver=%s", getpid(), path);
   void *library = dlopen(path, RTLD_NOW | RTLD_LOCAL);
   if (!library) {
      LOGE("FAIL dlopen: %s", dlerror());
      return 1;
   }
   PFN_vkGetInstanceProcAddr gipa =
      (PFN_vkGetInstanceProcAddr)dlsym(library, "vk_icdGetInstanceProcAddr");
   if (!gipa) {
      LOGE("FAIL missing vk_icdGetInstanceProcAddr");
      dlclose(library);
      return 1;
   }
   PFN_vkCreateInstance create_instance =
      (PFN_vkCreateInstance)gipa(VK_NULL_HANDLE, "vkCreateInstance");
   if (!create_instance) {
      LOGE("FAIL missing vkCreateInstance");
      dlclose(library);
      return 1;
   }
   VkApplicationInfo app = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
                            .apiVersion = VK_API_VERSION_1_3};
   VkInstanceCreateInfo ici = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                               .pApplicationInfo = &app};
   VkInstance inst = VK_NULL_HANDLE;
   VkResult result = create_instance(&ici, NULL, &inst);
   if (result != VK_SUCCESS) {
      LOGE("FAIL vkCreateInstance result=%d", result);
      dlclose(library);
      return 1;
   }

#define LOAD(name) PFN_vk##name name = (PFN_vk##name)gipa(inst, "vk" #name)
   LOAD(DestroyInstance);
   LOAD(EnumeratePhysicalDevices);
   LOAD(GetPhysicalDeviceProperties);
   LOAD(GetPhysicalDeviceFeatures2);
   LOAD(GetPhysicalDeviceQueueFamilyProperties);
   LOAD(GetPhysicalDeviceExternalSemaphoreProperties);
   LOAD(EnumerateDeviceExtensionProperties);
   LOAD(CreateDevice);
   LOAD(DestroyDevice);
   LOAD(GetDeviceProcAddr);
   LOAD(GetDeviceQueue);
   LOAD(CreateSemaphore);
   LOAD(DestroySemaphore);
   LOAD(CreateFence);
   LOAD(DestroyFence);
   LOAD(QueueSubmit);
   LOAD(QueueWaitIdle);
   LOAD(WaitForFences);
#undef LOAD
   if (!DestroyInstance || !EnumeratePhysicalDevices || !GetPhysicalDeviceProperties ||
       (wait_signal && !GetPhysicalDeviceFeatures2) ||
       !GetPhysicalDeviceQueueFamilyProperties || !GetPhysicalDeviceExternalSemaphoreProperties ||
       !EnumerateDeviceExtensionProperties || !CreateDevice || !DestroyDevice || !GetDeviceProcAddr ||
       !GetDeviceQueue || !CreateSemaphore || !DestroySemaphore || !CreateFence ||
       !DestroyFence || !QueueSubmit || !QueueWaitIdle || !WaitForFences) {
      LOGE("FAIL missing core Vulkan function");
      if (DestroyInstance) DestroyInstance(inst, NULL);
      dlclose(library);
      return 1;
   }

   int outcome = 1;
   VkDevice dev = VK_NULL_HANDLE;
   VkSemaphore semaphore = VK_NULL_HANDLE;
   VkSemaphore wait_semaphore = VK_NULL_HANDLE;
   VkFence fence = VK_NULL_HANDLE;
   uint32_t count = 0;
   result = EnumeratePhysicalDevices(inst, &count, NULL);
   if (result != VK_SUCCESS || !count) {
      LOGE("FAIL physical device count result=%d count=%u", result, count);
      goto done;
   }
   VkPhysicalDevice *devices = calloc(count, sizeof(*devices));
   if (!devices) {
      LOGE("FAIL physical device allocation");
      goto done;
   }
   result = EnumeratePhysicalDevices(inst, &count, devices);
   VkPhysicalDevice physical = VK_NULL_HANDLE;
   uint32_t api_version = 0;
   if (result == VK_SUCCESS) {
      for (uint32_t i = 0; i < count; i++) {
         VkPhysicalDeviceProperties properties;
         GetPhysicalDeviceProperties(devices[i], &properties);
         if (strstr(properties.deviceName, "Mali")) {
            physical = devices[i];
            api_version = properties.apiVersion;
            LOGI("DEVICE=%s vendor=0x%x", properties.deviceName, properties.vendorID);
            break;
         }
      }
   }
   free(devices);
   if (result != VK_SUCCESS || physical == VK_NULL_HANDLE) {
      LOGE("FAIL physical device selection result=%d", result);
      goto done;
   }

   VkPhysicalDeviceExternalSemaphoreInfo external_info = {
      .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_SEMAPHORE_INFO,
      .handleType = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_SYNC_FD_BIT,
   };
   VkExternalSemaphoreProperties external_properties = {
      .sType = VK_STRUCTURE_TYPE_EXTERNAL_SEMAPHORE_PROPERTIES,
   };
   GetPhysicalDeviceExternalSemaphoreProperties(physical, &external_info,
                                                &external_properties);
   LOGI("SYNC_FD properties features=0x%x compatible=0x%x",
        external_properties.externalSemaphoreFeatures,
        external_properties.compatibleHandleTypes);

   count = 0;
   result = EnumerateDeviceExtensionProperties(physical, NULL, &count, NULL);
   if (result != VK_SUCCESS) {
      LOGE("FAIL extension count result=%d", result);
      goto done;
   }
   VkExtensionProperties *extensions = count ? calloc(count, sizeof(*extensions)) : NULL;
   if (count && !extensions) {
      LOGE("FAIL extension allocation");
      goto done;
   }
   result = count ? EnumerateDeviceExtensionProperties(physical, NULL, &count, extensions)
                  : VK_SUCCESS;
   int has_fd_extension = 0;
   for (uint32_t i = 0; result == VK_SUCCESS && i < count; i++)
      if (!strcmp(extensions[i].extensionName, VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME))
         has_fd_extension = 1;
   free(extensions);
   if (result != VK_SUCCESS) {
      LOGE("FAIL extension enumeration result=%d", result);
      goto done;
   }
   if (!has_fd_extension ||
       !(external_properties.externalSemaphoreFeatures & VK_EXTERNAL_SEMAPHORE_FEATURE_EXPORTABLE_BIT) ||
       !(external_properties.compatibleHandleTypes & VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_SYNC_FD_BIT)) {
      LOGI("SKIP SYNC_FD export unsupported extension=%d", has_fd_extension);
      outcome = 2;
      goto done;
   }

   count = 0;
   GetPhysicalDeviceQueueFamilyProperties(physical, &count, NULL);
   VkQueueFamilyProperties *families = count ? calloc(count, sizeof(*families)) : NULL;
   if (!families) {
      LOGE("FAIL queue family allocation or empty list");
      goto done;
   }
   GetPhysicalDeviceQueueFamilyProperties(physical, &count, families);
   uint32_t family = UINT32_MAX;
   for (uint32_t i = 0; i < count; i++) {
      if (families[i].queueCount && (families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)) {
         family = i;
         break;
      }
   }
   free(families);
   if (family == UINT32_MAX) {
      LOGE("FAIL no graphics queue");
      goto done;
   }
   float priority = 1.0f;
   VkDeviceQueueCreateInfo qci = {.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                                  .queueFamilyIndex = family, .queueCount = 1,
                                  .pQueuePriorities = &priority};
   VkPhysicalDeviceSynchronization2Features sync2 = {
      .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SYNCHRONIZATION_2_FEATURES,
   };
   if (wait_signal) {
      if (api_version < VK_API_VERSION_1_3) {
         LOGI("SKIP wait-signal requires Vulkan 1.3");
         outcome = 2;
         goto done;
      }
      VkPhysicalDeviceFeatures2 features = {
         .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2,
         .pNext = &sync2,
      };
      GetPhysicalDeviceFeatures2(physical, &features);
      if (!sync2.synchronization2) {
         LOGI("SKIP wait-signal synchronization2 unsupported");
         outcome = 2;
         goto done;
      }
   }
   const char *extension = VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME;
   VkDeviceCreateInfo dci = {.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
                             .pNext = wait_signal ? &sync2 : NULL,
                             .queueCreateInfoCount = 1, .pQueueCreateInfos = &qci,
                             .enabledExtensionCount = 1, .ppEnabledExtensionNames = &extension};
   result = CreateDevice(physical, &dci, NULL, &dev);
   if (result != VK_SUCCESS) {
      LOGE("FAIL vkCreateDevice result=%d", result);
      goto done;
   }
   PFN_vkGetSemaphoreFdKHR GetSemaphoreFdKHR =
      (PFN_vkGetSemaphoreFdKHR)GetDeviceProcAddr(dev, "vkGetSemaphoreFdKHR");
   if (!GetSemaphoreFdKHR) {
      LOGE("FAIL missing vkGetSemaphoreFdKHR for enabled extension");
      goto done;
   }
   PFN_vkQueueSubmit2 QueueSubmit2 =
      (PFN_vkQueueSubmit2)GetDeviceProcAddr(dev, "vkQueueSubmit2");
   if (wait_signal && !QueueSubmit2) {
      LOGE("FAIL missing vkQueueSubmit2");
      goto done;
   }
   VkQueue queue;
   GetDeviceQueue(dev, family, 0, &queue);
   VkExportSemaphoreCreateInfo export_info = {
      .sType = VK_STRUCTURE_TYPE_EXPORT_SEMAPHORE_CREATE_INFO,
      .handleTypes = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_SYNC_FD_BIT,
   };
   VkSemaphoreCreateInfo sci = {.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
                                .pNext = &export_info};
   result = CreateSemaphore(dev, &sci, NULL, &semaphore);
   if (result != VK_SUCCESS) {
      LOGE("FAIL vkCreateSemaphore result=%d", result);
      goto done;
   }
   VkFenceCreateInfo fci = {.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
   result = CreateFence(dev, &fci, NULL, &fence);
   if (result != VK_SUCCESS) {
      LOGE("FAIL vkCreateFence result=%d", result);
      goto done;
   }
   if (wait_signal) {
      VkSemaphoreCreateInfo wait_sci = {.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
      result = CreateSemaphore(dev, &wait_sci, NULL, &wait_semaphore);
      if (result != VK_SUCCESS) {
         LOGE("FAIL wait semaphore creation result=%d", result);
         goto done;
      }
      VkSemaphoreSubmitInfo signals[2] = {
         {.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO,
          .semaphore = wait_semaphore, .stageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT},
         {.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO,
          .semaphore = semaphore, .stageMask = VK_PIPELINE_STAGE_2_TRANSFER_BIT},
      };
      VkSubmitInfo2 submits[2] = {
         {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO_2,
          .signalSemaphoreInfoCount = 1, .pSignalSemaphoreInfos = &signals[0]},
         {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO_2,
          .waitSemaphoreInfoCount = 1, .pWaitSemaphoreInfos = &signals[0],
          .signalSemaphoreInfoCount = 1, .pSignalSemaphoreInfos = &signals[1]},
      };
      result = QueueSubmit2(queue, 1, &submits[0], VK_NULL_HANDLE);
      LOGI("SYNC_WAIT_SIGNAL first submit result=%d", result);
      if (result != VK_SUCCESS)
         goto done;
      result = QueueSubmit2(queue, 1, &submits[1], fence);
      LOGI("SYNC_WAIT_SIGNAL wait-and-signal submit result=%d", result);
      if (result != VK_SUCCESS) {
         VkResult idle_result = QueueWaitIdle(queue);
         LOGI("SYNC_WAIT_SIGNAL queue idle after failure result=%d", idle_result);
         if (idle_result != VK_SUCCESS) {
            LOGE("FAIL pending queue work; retaining Vulkan objects until process exit");
            return 1;
         }
         goto done;
      }
   } else {
      VkSubmitInfo submit = {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
                             .signalSemaphoreCount = 1, .pSignalSemaphores = &semaphore};
      result = QueueSubmit(queue, 1, &submit, fence);
   }
   LOGI("SYNC_FD submit result=%d", result);
   if (result != VK_SUCCESS)
      goto done;

   VkSemaphoreGetFdInfoKHR get_fd = {
      .sType = VK_STRUCTURE_TYPE_SEMAPHORE_GET_FD_INFO_KHR,
      .semaphore = semaphore,
      .handleType = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_SYNC_FD_BIT,
   };
   int fd = -1;
   result = GetSemaphoreFdKHR(dev, &get_fd, &fd);
   LOGI("SYNC_FD export result=%d fd=%d", result, fd);
   int fd_ok = result == VK_SUCCESS && fd == -1;
   if (result == VK_SUCCESS && fd >= 0) {
      struct sync_file_info info = {0};
      int info_result = ioctl(fd, SYNC_IOC_FILE_INFO, &info);
      int info_errno = info_result < 0 ? errno : 0;
      struct pollfd poll_fd = {.fd = fd, .events = POLLIN};
      int poll_result;
      do {
         poll_result = poll(&poll_fd, 1, 5000);
      } while (poll_result < 0 && errno == EINTR);
      int poll_errno = poll_result < 0 ? errno : 0;
      struct sync_file_info completed = {0};
      int completed_result = ioctl(fd, SYNC_IOC_FILE_INFO, &completed);
      int completed_errno = completed_result < 0 ? errno : 0;
      LOGI("SYNC_FD verify ioctl=%d errno=%d status=%d fences=%u poll=%d revents=0x%x poll_errno=%d final_ioctl=%d final_errno=%d final_status=%d",
           info_result, info_errno, info.status, info.num_fences, poll_result,
           poll_fd.revents, poll_errno, completed_result, completed_errno, completed.status);
      fd_ok = info_result == 0 && info.status >= 0 && poll_result == 1 &&
              (poll_fd.revents & POLLIN) && !(poll_fd.revents & (POLLERR | POLLNVAL)) &&
              completed_result == 0 && completed.status == 1;
      close(fd);
   }
   VkResult wait_result = WaitForFences(dev, 1, &fence, VK_TRUE, 5000000000ULL);
   LOGI("SYNC_FD fence wait result=%d", wait_result);
   if (wait_result != VK_SUCCESS) {
      LOGE("FAIL pending queue work; retaining Vulkan objects until process exit");
      return 1;
   }
   if (result == VK_SUCCESS && fd_ok) {
      LOGI("PASS SYNC_FD export");
      outcome = 0;
   } else {
      LOGE("FAIL SYNC_FD export or verification result=%d fd_ok=%d", result, fd_ok);
   }

done:
   if (fence) DestroyFence(dev, fence, NULL);
   if (wait_semaphore) DestroySemaphore(dev, wait_semaphore, NULL);
   if (semaphore) DestroySemaphore(dev, semaphore, NULL);
   if (dev) DestroyDevice(dev, NULL);
   DestroyInstance(inst, NULL);
   dlclose(library);
   return outcome;
}
