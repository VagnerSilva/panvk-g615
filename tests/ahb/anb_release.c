/* Exercise Android native-buffer acquire and release without a surface. */
#define VK_USE_PLATFORM_ANDROID_KHR 1
#include <android/hardware_buffer.h>
#include <dlfcn.h>
#include <errno.h>
#include <linux/sync_file.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <vulkan/vulkan.h>
#include <vulkan/vk_android_native_buffer.h>

#ifdef PANVK_ANDROID_APP_LOG
#include <android/log.h>
#define printf(...) __android_log_print(ANDROID_LOG_INFO, "PanVKAnbRelease", __VA_ARGS__)
#define fprintf(stream, ...) __android_log_print(ANDROID_LOG_ERROR, "PanVKAnbRelease", __VA_ARGS__)
#endif

const native_handle_t *AHardwareBuffer_getNativeHandle(const AHardwareBuffer *);

#define REQUIRE(expr, label) do { \
   VkResult r_ = (expr); \
   printf("%s result=%d\n", label, r_); \
   if (r_ != VK_SUCCESS) goto done; \
} while (0)

int main(int argc, char **argv)
{
#ifndef PANVK_ANDROID_APP_LOG
   setvbuf(stdout, NULL, _IONBF, 0);
#endif
   if (argc < 2 || argc > 3 ||
       (argc == 3 && strcmp(argv[2], "1") && strcmp(argv[2], "2"))) {
      fprintf(stderr, "usage: %s <driver.so> [1|2 wait semaphores]\n", argv[0]);
      return 2;
   }
   uint32_t wait_count = argc == 3 && !strcmp(argv[2], "2") ? 2 : 1;
   int outcome = 1, fd = -1;
   void *library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
   VkInstance instance = VK_NULL_HANDLE;
   VkDevice device = VK_NULL_HANDLE;
   VkImage image = VK_NULL_HANDLE;
   VkSemaphore acquired = VK_NULL_HANDLE, rendered[2] = {VK_NULL_HANDLE, VK_NULL_HANDLE};
   VkFence fence = VK_NULL_HANDLE;
   AHardwareBuffer *buffer = NULL;
   int pending = 0;
   if (!library) {
      fprintf(stderr, "FAIL dlopen: %s\n", dlerror());
      return 1;
   }
   PFN_vkGetInstanceProcAddr gipa =
      (PFN_vkGetInstanceProcAddr)dlsym(library, "vk_icdGetInstanceProcAddr");
   if (!gipa) {
      fprintf(stderr, "FAIL missing ICD entrypoint\n");
      goto done;
   }
#define LOAD_GLOBAL(name) \
   PFN_vk##name name = (PFN_vk##name)gipa(VK_NULL_HANDLE, "vk" #name); \
   if (!name) { fprintf(stderr, "FAIL missing vk" #name "\n"); goto done; }
   LOAD_GLOBAL(CreateInstance)
#undef LOAD_GLOBAL
   VkApplicationInfo app = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
                            .apiVersion = VK_API_VERSION_1_3};
   VkInstanceCreateInfo ici = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                               .pApplicationInfo = &app};
   REQUIRE(CreateInstance(&ici, NULL, &instance), "CreateInstance");

#define LOAD_INSTANCE(name) \
   PFN_vk##name name = (PFN_vk##name)gipa(instance, "vk" #name); \
   if (!name) { fprintf(stderr, "FAIL missing vk" #name "\n"); goto done; }
   LOAD_INSTANCE(EnumeratePhysicalDevices)
   LOAD_INSTANCE(GetPhysicalDeviceProperties)
   LOAD_INSTANCE(GetPhysicalDeviceQueueFamilyProperties)
   LOAD_INSTANCE(EnumerateDeviceExtensionProperties)
   LOAD_INSTANCE(CreateDevice)
   LOAD_INSTANCE(GetDeviceProcAddr)
#undef LOAD_INSTANCE
   uint32_t count = 0;
   REQUIRE(EnumeratePhysicalDevices(instance, &count, NULL), "physical count");
   if (!count) {
      fprintf(stderr, "FAIL no physical device\n");
      goto done;
   }
   VkPhysicalDevice *devices = calloc(count, sizeof(*devices));
   if (!devices) {
      fprintf(stderr, "FAIL physical device allocation\n");
      goto done;
   }
   VkResult result = EnumeratePhysicalDevices(instance, &count, devices);
   VkPhysicalDevice physical = VK_NULL_HANDLE;
   for (uint32_t i = 0; result == VK_SUCCESS && i < count; i++) {
      VkPhysicalDeviceProperties props;
      GetPhysicalDeviceProperties(devices[i], &props);
      if (strstr(props.deviceName, "Mali")) {
         physical = devices[i];
         printf("DEVICE=%s\n", props.deviceName);
         break;
      }
   }
   free(devices);
   if (result != VK_SUCCESS || physical == VK_NULL_HANDLE) {
      fprintf(stderr, "FAIL physical device selection result=%d\n", result);
      goto done;
   }
   count = 0;
   REQUIRE(EnumerateDeviceExtensionProperties(physical, NULL, &count, NULL),
           "extension count");
   VkExtensionProperties *extensions = calloc(count, sizeof(*extensions));
   if (!extensions) {
      fprintf(stderr, "FAIL extension allocation\n");
      goto done;
   }
   result = EnumerateDeviceExtensionProperties(physical, NULL, &count, extensions);
   int has_anb = 0, has_fd = 0;
   for (uint32_t i = 0; result == VK_SUCCESS && i < count; i++) {
      has_anb |= !strcmp(extensions[i].extensionName, VK_ANDROID_NATIVE_BUFFER_EXTENSION_NAME);
      has_fd |= !strcmp(extensions[i].extensionName, VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME);
   }
   free(extensions);
   if (result != VK_SUCCESS || !has_anb || !has_fd) {
      fprintf(stderr, "FAIL required extensions anb=%d semaphore_fd=%d result=%d\n",
              has_anb, has_fd, result);
      goto done;
   }
   count = 0;
   GetPhysicalDeviceQueueFamilyProperties(physical, &count, NULL);
   VkQueueFamilyProperties *families = calloc(count, sizeof(*families));
   if (!families) {
      fprintf(stderr, "FAIL queue family allocation\n");
      goto done;
   }
   GetPhysicalDeviceQueueFamilyProperties(physical, &count, families);
   uint32_t family = UINT32_MAX;
   for (uint32_t i = 0; i < count; i++)
      if (families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) { family = i; break; }
   free(families);
   if (family == UINT32_MAX) {
      fprintf(stderr, "FAIL no graphics queue\n");
      goto done;
   }
   float priority = 1.0f;
   VkDeviceQueueCreateInfo qci = {.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                                  .queueFamilyIndex = family, .queueCount = 1,
                                  .pQueuePriorities = &priority};
   const char *names[] = {VK_ANDROID_NATIVE_BUFFER_EXTENSION_NAME,
                          VK_KHR_EXTERNAL_SEMAPHORE_FD_EXTENSION_NAME};
   VkDeviceCreateInfo dci = {.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
                             .queueCreateInfoCount = 1, .pQueueCreateInfos = &qci,
                             .enabledExtensionCount = 2, .ppEnabledExtensionNames = names};
   REQUIRE(CreateDevice(physical, &dci, NULL, &device), "CreateDevice");
#define LOAD_DEVICE(name) \
   PFN_vk##name name = (PFN_vk##name)GetDeviceProcAddr(device, "vk" #name); \
   if (!name) { fprintf(stderr, "FAIL missing vk" #name "\n"); goto done; }
   LOAD_DEVICE(GetDeviceQueue)
   LOAD_DEVICE(CreateImage)
   LOAD_DEVICE(CreateSemaphore)
   LOAD_DEVICE(CreateFence)
   LOAD_DEVICE(AcquireImageANDROID)
   LOAD_DEVICE(QueueSubmit)
   LOAD_DEVICE(QueueSignalReleaseImageANDROID)
   LOAD_DEVICE(WaitForFences)
#undef LOAD_DEVICE
   VkQueue queue;
   GetDeviceQueue(device, family, 0, &queue);
   AHardwareBuffer_Desc desc = {
      .width = 64, .height = 64, .layers = 1,
      .format = AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM,
      .usage = AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT |
               AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE,
   };
   int ahb_result = AHardwareBuffer_allocate(&desc, &buffer);
   if (ahb_result || !buffer) {
      fprintf(stderr, "FAIL AHardwareBuffer_allocate result=%d\n", ahb_result);
      goto done;
   }
   AHardwareBuffer_describe(buffer, &desc);
   const native_handle_t *handle = AHardwareBuffer_getNativeHandle(buffer);
   if (!handle) {
      fprintf(stderr, "FAIL native handle\n");
      goto done;
   }
   VkNativeBufferANDROID native = {
      .sType = VK_STRUCTURE_TYPE_NATIVE_BUFFER_ANDROID,
      .handle = handle, .stride = (int)desc.stride, .format = (int)desc.format,
      .usage3 = desc.usage, .ahb = buffer,
   };
   VkImageCreateInfo image_info = {
      .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .pNext = &native,
      .imageType = VK_IMAGE_TYPE_2D, .format = VK_FORMAT_R8G8B8A8_UNORM,
      .extent = {64, 64, 1}, .mipLevels = 1, .arrayLayers = 1,
      .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
      .usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
      .sharingMode = VK_SHARING_MODE_EXCLUSIVE, .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
   };
   REQUIRE(CreateImage(device, &image_info, NULL, &image), "CreateImage native-buffer");
   VkSemaphoreCreateInfo sci = {.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
   REQUIRE(CreateSemaphore(device, &sci, NULL, &acquired), "CreateSemaphore acquired");
   for (uint32_t i = 0; i < wait_count; i++)
      REQUIRE(CreateSemaphore(device, &sci, NULL, &rendered[i]), "CreateSemaphore rendered");
   VkFenceCreateInfo fci = {.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
   REQUIRE(CreateFence(device, &fci, NULL, &fence), "CreateFence");
   REQUIRE(AcquireImageANDROID(device, image, -1, acquired, VK_NULL_HANDLE),
           "AcquireImageANDROID");
   VkPipelineStageFlags stage = VK_PIPELINE_STAGE_ALL_COMMANDS_BIT;
   VkSubmitInfo submit = {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
                          .waitSemaphoreCount = 1, .pWaitSemaphores = &acquired,
                          .pWaitDstStageMask = &stage,
                          .signalSemaphoreCount = wait_count, .pSignalSemaphores = rendered};
   REQUIRE(QueueSubmit(queue, 1, &submit, fence), "QueueSubmit");
   pending = 1;
   result = QueueSignalReleaseImageANDROID(queue, wait_count, rendered, image, &fd);
   printf("QueueSignalReleaseImageANDROID wait_count=%u result=%d fd=%d\n",
          wait_count, result, fd);
   if (result == VK_SUCCESS && fd >= 0) {
      struct sync_file_info info = {0};
      struct pollfd poll_fd = {.fd = fd, .events = POLLIN};
      int valid = ioctl(fd, SYNC_IOC_FILE_INFO, &info);
      int polled;
      do { polled = poll(&poll_fd, 1, 5000); } while (polled < 0 && errno == EINTR);
      struct sync_file_info completed = {0};
      int final_result = ioctl(fd, SYNC_IOC_FILE_INFO, &completed);
      printf("sync_file ioctl=%d poll=%d revents=0x%x final_ioctl=%d status=%d\n",
             valid, polled, poll_fd.revents, final_result, completed.status);
      if (valid || info.status < 0 || polled != 1 || !(poll_fd.revents & POLLIN) ||
          (poll_fd.revents & (POLLERR | POLLNVAL)) ||
          final_result || completed.status != 1)
         result = VK_ERROR_UNKNOWN;
   } else if (result == VK_SUCCESS && fd != -1) {
      result = VK_ERROR_UNKNOWN;
   }
   VkResult wait_result = WaitForFences(device, 1, &fence, VK_TRUE, 5000000000ULL);
   printf("WaitForFences result=%d\n", wait_result);
   if (wait_result != VK_SUCCESS) {
      fprintf(stderr, "FAIL work still pending; process exit without object destruction\n");
      return 1;
   }
   pending = 0;
   if (result == VK_SUCCESS) {
      printf("PASS native-buffer release sync\n");
      outcome = 0;
   }
done:
   if (fd >= 0) close(fd);
   if (pending) {
      fprintf(stderr, "FAIL pending work; process exit without object destruction\n");
      return 1;
   }
   if (device && gipa) {
      PFN_vkGetDeviceProcAddr gdpa =
         (PFN_vkGetDeviceProcAddr)gipa(instance, "vkGetDeviceProcAddr");
      if (gdpa) {
         PFN_vkDestroyFence destroy_fence = (PFN_vkDestroyFence)gdpa(device, "vkDestroyFence");
         PFN_vkDestroySemaphore destroy_semaphore = (PFN_vkDestroySemaphore)gdpa(device, "vkDestroySemaphore");
         PFN_vkDestroyImage destroy_image = (PFN_vkDestroyImage)gdpa(device, "vkDestroyImage");
         PFN_vkDestroyDevice destroy_device = (PFN_vkDestroyDevice)gdpa(device, "vkDestroyDevice");
         if (fence && destroy_fence) destroy_fence(device, fence, NULL);
         if (acquired && destroy_semaphore) destroy_semaphore(device, acquired, NULL);
         if (destroy_semaphore)
            for (uint32_t i = 0; i < wait_count; i++)
               if (rendered[i]) destroy_semaphore(device, rendered[i], NULL);
         if (image && destroy_image) destroy_image(device, image, NULL);
         if (destroy_device) destroy_device(device, NULL);
      }
   }
   if (buffer) AHardwareBuffer_release(buffer);
   if (instance && gipa) {
      PFN_vkDestroyInstance destroy = (PFN_vkDestroyInstance)gipa(instance, "vkDestroyInstance");
      if (destroy) destroy(instance, NULL);
   }
   dlclose(library);
   return outcome;
}
