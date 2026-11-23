#define _POSIX_C_SOURCE 200809L
#include <dirent.h>
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/sync_file.h>
#include <poll.h>
#include <stdatomic.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <vulkan/vulkan.h>

#include "drm-uapi/mali_kbase_ioctl.h"

#define CHECK(call) do { \
   VkResult result = (call); \
   if (result != VK_SUCCESS) { \
      fprintf(stderr, "FAIL %s: %d\n", #call, result); \
      return 1; \
   } \
} while (0)

#define LOAD(name, address) \
   PFN_vk##name vk##name = (PFN_vk##name)(address); \
   if (!vk##name) { \
      fprintf(stderr, "FAIL missing vk%s\n", #name); \
      return 1; \
   }

#define INSTANCE(name) LOAD(name, gipa(instance, "vk" #name))
#define DEVICE(name) LOAD(name, vkGetDeviceProcAddr(device, "vk" #name))

static int
fd_count(void)
{
   DIR *dir = opendir("/proc/self/fd");
   if (!dir)
      return -1;
   int count = 0;
   struct dirent *entry;
   errno = 0;
   while ((entry = readdir(dir)))
      count += entry->d_name[0] != '.';
   int error = errno;
   return closedir(dir) || error ? -1 : count - 1;
}

static int
make_sync_file(int mali, uint8_t queue, _Atomic uint64_t *point, uint64_t before)
{
   struct base_cqs_wait_operation_info wait = {
      .addr = (uintptr_t)point, .val = before,
      .operation = BASEP_CQS_WAIT_OPERATION_GT, .data_type = BASEP_CQS_DATA_TYPE_U64,
   };
   struct base_fence fence = {.basep = {.fd = -1, .stream_fd = -1}};
   struct base_kcpu_command commands[] = {
      {.type = BASE_KCPU_COMMAND_TYPE_CQS_WAIT_OPERATION,
       .info.cqs_wait_operation = {.objs = (uintptr_t)&wait, .nr_objs = 1}},
      {.type = BASE_KCPU_COMMAND_TYPE_FENCE_SIGNAL,
       .info.fence = {.fence = (uintptr_t)&fence}},
   };
   for (unsigned i = 0; i < 2; i++) {
      struct kbase_ioctl_kcpu_queue_enqueue enqueue = {
         .addr = (uintptr_t)&commands[i], .nr_commands = 1, .id = queue,
      };
      if (ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_ENQUEUE, &enqueue)) {
         perror(i ? "KCPU FENCE_SIGNAL" : "KCPU CQS_WAIT_OPERATION");
         return -1;
      }
   }
   return fence.basep.fd;
}

int
main(int argc, char **argv)
{
   if (argc != 2) {
      fprintf(stderr, "usage: %s <libvulkan_panfrost.so>\n", argv[0]);
      return 2;
   }
   setvbuf(stdout, NULL, _IONBF, 0);
   void *lib = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
   if (!lib) {
      fprintf(stderr, "FAIL dlopen: %s\n", dlerror());
      return 1;
   }
   PFN_vkGetInstanceProcAddr gipa = (PFN_vkGetInstanceProcAddr)
      dlsym(lib, "vk_icdGetInstanceProcAddr");
   if (!gipa) {
      fprintf(stderr, "FAIL missing ICD entrypoint\n");
      return 1;
   }
   VkInstance instance = VK_NULL_HANDLE;
   INSTANCE(CreateInstance);
   const VkApplicationInfo app = {
      .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO, .apiVersion = VK_API_VERSION_1_1,
   };
   const VkInstanceCreateInfo ici = {
      .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &app,
   };
   CHECK(vkCreateInstance(&ici, NULL, &instance));
   INSTANCE(DestroyInstance);
   INSTANCE(EnumeratePhysicalDevices);
   INSTANCE(GetPhysicalDeviceProperties);
   INSTANCE(GetPhysicalDeviceQueueFamilyProperties);
   INSTANCE(GetPhysicalDeviceExternalFenceProperties);
   INSTANCE(CreateDevice);
   INSTANCE(GetDeviceProcAddr);

   VkPhysicalDevice gpu;
   uint32_t count = 1;
   VkResult enumeration = vkEnumeratePhysicalDevices(instance, &count, &gpu);
   if (enumeration != VK_SUCCESS || count != 1) {
      fprintf(stderr, "FAIL expected exactly one physical device: result=%d count=%u\n",
              enumeration, count);
      return 1;
   }
   VkPhysicalDeviceProperties props;
   vkGetPhysicalDeviceProperties(gpu, &props);
   printf("GPU %s\n", props.deviceName);
   const VkExternalFenceHandleTypeFlagBits handle = VK_EXTERNAL_FENCE_HANDLE_TYPE_SYNC_FD_BIT;
   const VkPhysicalDeviceExternalFenceInfo external = {
      .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_FENCE_INFO, .handleType = handle,
   };
   VkExternalFenceProperties support = {.sType = VK_STRUCTURE_TYPE_EXTERNAL_FENCE_PROPERTIES};
   vkGetPhysicalDeviceExternalFenceProperties(gpu, &external, &support);
   const VkExternalFenceFeatureFlags needed = VK_EXTERNAL_FENCE_FEATURE_IMPORTABLE_BIT;
   if ((support.externalFenceFeatures & needed) != needed) {
      fprintf(stderr, "BLOCKED SYNC_FD fence features: %#x\n", support.externalFenceFeatures);
      vkDestroyInstance(instance, NULL);
      dlclose(lib);
      return 77;
   }

   vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, NULL);
   VkQueueFamilyProperties families[32];
   if (count > sizeof(families) / sizeof(families[0]) || !count) {
      fprintf(stderr, "FAIL unexpected queue family count: %u\n", count);
      return 1;
   }
   vkGetPhysicalDeviceQueueFamilyProperties(gpu, &count, families);
   uint32_t family = 0;
   while (family < count && !(families[family].queueFlags & VK_QUEUE_COMPUTE_BIT))
      family++;
   if (family == count) {
      fprintf(stderr, "FAIL no compute queue family\n");
      return 1;
   }
   const float priority = 1;
   const VkDeviceQueueCreateInfo qci = {
      .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, .queueFamilyIndex = family,
      .queueCount = 1, .pQueuePriorities = &priority,
   };
   const char *ext[] = { VK_KHR_EXTERNAL_FENCE_FD_EXTENSION_NAME };
   const VkDeviceCreateInfo dci = {
      .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, .queueCreateInfoCount = 1,
      .pQueueCreateInfos = &qci, .enabledExtensionCount = 1, .ppEnabledExtensionNames = ext,
   };
   VkDevice device;
   CHECK(vkCreateDevice(gpu, &dci, NULL, &device));
   DEVICE(DestroyDevice);
   DEVICE(CreateFence);
   DEVICE(DestroyFence);
   DEVICE(ImportFenceFdKHR);
   DEVICE(WaitForFences);
   DEVICE(ResetFences);
   const VkFenceCreateInfo dst_info = {.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};

   int mali = open("/dev/mali0", O_RDWR | O_CLOEXEC);
   if (mali < 0) {
      perror("BLOCKED open /dev/mali0");
      return 77;
   }
   struct kbase_ioctl_version_check version = {0};
   if (ioctl(mali, KBASE_IOCTL_VERSION_CHECK_CSF, &version) ||
       version.major != 1 || version.minor != 21 || sysconf(_SC_PAGESIZE) != 4096) {
      fprintf(stderr, "BLOCKED producer requires Kbase CSF UAPI 1.21 and 4 KiB pages (got %u.%u)\n",
              version.major, version.minor);
      return 77;
   }
   struct kbase_ioctl_set_flags flags = {0};
   if (ioctl(mali, KBASE_IOCTL_SET_FLAGS, &flags)) {
      perror("KBASE SET_FLAGS");
      return 1;
   }
   void *tracking = mmap(NULL, 4096, PROT_NONE, MAP_SHARED, mali, BASE_MEM_MAP_TRACKING_HANDLE);
   if (tracking == MAP_FAILED) {
      perror("KBASE tracking mmap");
      return 1;
   }
   union kbase_ioctl_mem_alloc_ex alloc = {.in = {
      .va_pages = 1, .commit_pages = 1,
      .flags = BASE_MEM_PROT_CPU_RD | BASE_MEM_PROT_CPU_WR | BASE_MEM_PROT_GPU_RD |
               BASE_MEM_PROT_GPU_WR | BASE_MEM_SAME_VA | BASE_MEM_CSF_EVENT,
   }};
   if (ioctl(mali, KBASE_IOCTL_MEM_ALLOC_EX, &alloc)) {
      perror("KBASE MEM_ALLOC_EX");
      return 1;
   }
   _Atomic uint64_t *point = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED,
                                  mali, alloc.out.gpu_va);
   if (point == MAP_FAILED) {
      perror("KBASE CQS mmap");
      return 1;
   }
   atomic_init(point, 0);
   struct kbase_ioctl_kcpu_queue_new producer = {0};
   if (ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_CREATE, &producer)) {
      perror("KBASE KCPU_QUEUE_CREATE");
      return 1;
   }

   const int baseline = fd_count();
   for (unsigned i = 0; i < 12; i++) {
      VkFence dst;
      CHECK(vkCreateFence(device, &dst_info, NULL, &dst));
      int fd = make_sync_file(mali, producer.id, point, i);
      struct sync_file_info info = {0};
      if (fd < 0 || ioctl(fd, SYNC_IOC_FILE_INFO, &info) || info.status != 0) {
         fprintf(stderr, "FAIL export not a pending sync_file: fd=%d status=%d errno=%d\n",
                 fd, info.status, errno);
         if (fd >= 0)
            close(fd);
         return 1;
      }
      const VkImportFenceFdInfoKHR import = {
         .sType = VK_STRUCTURE_TYPE_IMPORT_FENCE_FD_INFO_KHR, .fence = dst,
         .flags = VK_FENCE_IMPORT_TEMPORARY_BIT, .handleType = handle, .fd = dup(fd),
      };
      if (import.fd < 0) {
         perror("dup sync_file");
         return 1;
      }
      VkResult result = vkImportFenceFdKHR(device, &import);
      if (result != VK_SUCCESS) {
         close(import.fd);
         fprintf(stderr, "FAIL vkImportFenceFdKHR: %d\n", result);
         return 1;
      }
      result = vkWaitForFences(device, 1, &dst, VK_TRUE, 10000000);
      info = (struct sync_file_info){0};
      int status_result = ioctl(fd, SYNC_IOC_FILE_INFO, &info);
      if (status_result || info.status != 0) {
         fprintf(stderr, "FAIL producer did not hold sync_file pending: status=%d ioctl=%d wait=%d\n",
                 info.status, status_result, result);
         return 1;
      }
      if (result != VK_TIMEOUT) {
         fprintf(stderr, "FAIL expected VK_TIMEOUT, got %d\n", result);
         return 1;
      }
      atomic_store_explicit(point, i + 1, memory_order_release);
      if (ioctl(mali, KBASE_IOCTL_CS_EVENT_SIGNAL)) {
         perror("KBASE CS_EVENT_SIGNAL");
         return 1;
      }

      if (i % 3 == 0)
         CHECK(vkWaitForFences(device, 1, &dst, VK_TRUE, 2000000000));
      struct pollfd pfd = {.fd = fd, .events = POLLIN};
      info = (struct sync_file_info){0};
      int ready = poll(&pfd, 1, 2000);
      if (ready != 1 || pfd.revents != POLLIN ||
          ioctl(fd, SYNC_IOC_FILE_INFO, &info) || info.status != 1) {
         fprintf(stderr, "FAIL external fence completion: poll=%d revents=%#x status=%d errno=%d\n",
                 ready, (unsigned)pfd.revents, info.status, errno);
         return 1;
      }
      if (i % 3 == 1)
         CHECK(vkResetFences(device, 1, &dst));

      close(fd);
      vkDestroyFence(device, dst, NULL);
      int fds = fd_count();
      printf("SYNC-FILE cycle=%u mode=%s fd=%d baseline=%d\n", i,
             i % 3 == 0 ? "rewait" : i % 3 == 1 ? "reset" : "destroy", fds, baseline);
      if (fds < 0 || fds != baseline) {
         fprintf(stderr, "FAIL FD count changed after fence cleanup\n");
         return 1;
      }
   }
   struct kbase_ioctl_kcpu_queue_delete delete = {.id = producer.id};
   if (ioctl(mali, KBASE_IOCTL_KCPU_QUEUE_DELETE, &delete)) {
      perror("KBASE KCPU_QUEUE_DELETE");
      return 1;
   }
   munmap(point, 4096);
   munmap(tracking, 4096);
   close(mali);
   vkDestroyDevice(device, NULL);
   vkDestroyInstance(instance, NULL);
   dlclose(lib);
   puts("SYNC-FILE-PASS 12 cycles");
   return 0;
}
