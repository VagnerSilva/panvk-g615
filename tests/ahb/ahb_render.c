/* Gate G: render and read back through AHB or a host-visible linear image. */
#define VK_USE_PLATFORM_ANDROID_KHR 1
#include <dlfcn.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <vulkan/vulkan.h>
#include <android/hardware_buffer.h>

#ifdef PANVK_ANDROID_APP_LOG
#include <android/log.h>
#define printf(...) __android_log_print(ANDROID_LOG_INFO, "PanVKIdvs", __VA_ARGS__)
#endif

typedef PFN_vkVoidFunction (*icd_gipa_fn)(VkInstance, const char *);

#define CK(expr, what)                                                      \
   do {                                                                     \
      VkResult _r = (expr);                                                  \
      if (_r != VK_SUCCESS) {                                                \
         printf("FAIL %s r=%d line=%d\n", what, _r, __LINE__);                \
         return 1;                                                          \
      }                                                                     \
   } while (0)

#include "../offscreen/tri.vert.spv.h"
#include "../offscreen/tri.frag.spv.h"
#include "idvs_varying.vert.spv.h"
#include "idvs_varying.frag.spv.h"
#include "idvs_multi.vert.spv.h"
#include "idvs_multi.frag.spv.h"
#include "idvs_point.vert.spv.h"

#define W 64
#define H 64

int main(int argc, char **argv)
{
   if (argc < 2) {
      printf("usage: %s <libvulkan_panfrost.so> [varying|multi|point|triangle_psiz] [linear]\n", argv[0]);
      return 2;
   }
   if (argc > 4 || (argc >= 3 && strcmp(argv[2], "varying") &&
                    strcmp(argv[2], "multi") && strcmp(argv[2], "point") &&
                    strcmp(argv[2], "triangle_psiz")) ||
       (argc == 4 && strcmp(argv[3], "linear"))) {
      printf("FAIL invalid mode\n");
      return 2;
   }
   bool linear = argc == 4;
   bool multi = argc >= 3 && !strcmp(argv[2], "multi");
   bool point = argc >= 3 && !strcmp(argv[2], "point");
   bool triangle_psiz = argc >= 3 && !strcmp(argv[2], "triangle_psiz");
   bool varying = argc >= 3 && !strcmp(argv[2], "varying");
   printf("G-driver=%s mode=%s readback=%s PAN_USE_KRAID=%s\n", argv[1],
          argc >= 3 ? argv[2] : "triangle", linear ? "linear" : "ahb",
          getenv("PAN_USE_KRAID") ? getenv("PAN_USE_KRAID") : "(default)");
   setvbuf(stdout, NULL, _IONBF, 0);
   void *h = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
   if (!h) {
      printf("FAIL dlopen %s\n", dlerror());
      return 1;
   }
   icd_gipa_fn gipa = (icd_gipa_fn)dlsym(h, "vk_icdGetInstanceProcAddr");
   if (!gipa)
      gipa = (icd_gipa_fn)dlsym(h, "vkGetInstanceProcAddr");
   if (!gipa) {
      printf("FAIL gipa\n");
      return 1;
   }

#define G0(what, name)                                                      \
   PFN_##name name = (PFN_##name)gipa(NULL, "vk" #what);                     \
   if (!name) {                                                             \
      printf("FAIL missing vk" #what "\n");                                  \
      return 1;                                                             \
   }
   G0(CreateInstance, vkCreateInstance)
   VkApplicationInfo app = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
                            .apiVersion = VK_API_VERSION_1_3};
   const char *exts[] = {
      VK_KHR_EXTERNAL_MEMORY_CAPABILITIES_EXTENSION_NAME,
      VK_KHR_GET_PHYSICAL_DEVICE_PROPERTIES_2_EXTENSION_NAME,
   };
   VkInstanceCreateInfo ici = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                               .pApplicationInfo = &app,
                               .enabledExtensionCount = linear ? 0 : 2,
                               .ppEnabledExtensionNames = linear ? NULL : exts};
   VkInstance inst;
   CK(vkCreateInstance(&ici, NULL, &inst), "CreateInstance");
#undef G0

#define G(what, name)                                                       \
   PFN_##name name = (PFN_##name)gipa(inst, "vk" #what);                     \
   if (!name) {                                                             \
      printf("FAIL missing vk" #what "\n");                                  \
      return 1;                                                             \
   }
   G(EnumeratePhysicalDevices, vkEnumeratePhysicalDevices)
   G(GetPhysicalDeviceProperties, vkGetPhysicalDeviceProperties)
   G(GetPhysicalDeviceFeatures, vkGetPhysicalDeviceFeatures)
   G(GetPhysicalDeviceQueueFamilyProperties, vkGetPhysicalDeviceQueueFamilyProperties)
   G(GetPhysicalDeviceMemoryProperties, vkGetPhysicalDeviceMemoryProperties)
   G(GetPhysicalDeviceImageFormatProperties, vkGetPhysicalDeviceImageFormatProperties)
   G(CreateDevice, vkCreateDevice)
   G(GetDeviceQueue, vkGetDeviceQueue)
   G(CreateBuffer, vkCreateBuffer)
   G(GetBufferMemoryRequirements, vkGetBufferMemoryRequirements)
   G(CreateImage, vkCreateImage)
   G(GetImageMemoryRequirements2, vkGetImageMemoryRequirements2)
   G(GetImageSubresourceLayout, vkGetImageSubresourceLayout)
   G(AllocateMemory, vkAllocateMemory)
   G(BindBufferMemory, vkBindBufferMemory)
   G(BindImageMemory2, vkBindImageMemory2)
   G(MapMemory, vkMapMemory)
   G(FlushMappedMemoryRanges, vkFlushMappedMemoryRanges)
   G(InvalidateMappedMemoryRanges, vkInvalidateMappedMemoryRanges)
   G(UnmapMemory, vkUnmapMemory)
   G(CreateImageView, vkCreateImageView)
   G(CreateRenderPass, vkCreateRenderPass)
   G(CreateFramebuffer, vkCreateFramebuffer)
   G(CreateShaderModule, vkCreateShaderModule)
   G(CreatePipelineLayout, vkCreatePipelineLayout)
   G(CreateGraphicsPipelines, vkCreateGraphicsPipelines)
   G(CreateCommandPool, vkCreateCommandPool)
   G(AllocateCommandBuffers, vkAllocateCommandBuffers)
   G(BeginCommandBuffer, vkBeginCommandBuffer)
   G(ResetCommandBuffer, vkResetCommandBuffer)
   G(CmdBeginRenderPass, vkCmdBeginRenderPass)
   G(CmdBindPipeline, vkCmdBindPipeline)
   G(CmdBindVertexBuffers, vkCmdBindVertexBuffers)
   G(CmdPushConstants, vkCmdPushConstants)
   G(CmdDraw, vkCmdDraw)
   G(CmdEndRenderPass, vkCmdEndRenderPass)
   G(CmdPipelineBarrier, vkCmdPipelineBarrier)
   G(EndCommandBuffer, vkEndCommandBuffer)
   G(CreateFence, vkCreateFence)
   G(QueueSubmit, vkQueueSubmit)
   G(WaitForFences, vkWaitForFences)
   G(DestroyFence, vkDestroyFence)
   G(FreeCommandBuffers, vkFreeCommandBuffers)
   G(DestroyCommandPool, vkDestroyCommandPool)
   G(DestroyPipeline, vkDestroyPipeline)
   G(DestroyPipelineLayout, vkDestroyPipelineLayout)
   G(DestroyShaderModule, vkDestroyShaderModule)
   G(DestroyFramebuffer, vkDestroyFramebuffer)
   G(DestroyRenderPass, vkDestroyRenderPass)
   G(DestroyImageView, vkDestroyImageView)
   G(FreeMemory, vkFreeMemory)
   G(DestroyImage, vkDestroyImage)
   G(DestroyBuffer, vkDestroyBuffer)
   G(DestroyDevice, vkDestroyDevice)
   G(DestroyInstance, vkDestroyInstance)
   PFN_vkGetAndroidHardwareBufferPropertiesANDROID vkGetAndroidHardwareBufferPropertiesANDROID = NULL;
   if (!linear) {
      vkGetAndroidHardwareBufferPropertiesANDROID =
         (PFN_vkGetAndroidHardwareBufferPropertiesANDROID)
         gipa(inst, "vkGetAndroidHardwareBufferPropertiesANDROID");
      if (!vkGetAndroidHardwareBufferPropertiesANDROID) {
         printf("FAIL missing vkGetAndroidHardwareBufferPropertiesANDROID\n");
         return 1;
      }
   }

   uint32_t n = 0;
   CK(vkEnumeratePhysicalDevices(inst, &n, NULL), "count");
   VkPhysicalDevice *devs = malloc(n * sizeof(*devs));
   CK(vkEnumeratePhysicalDevices(inst, &n, devs), "enum");
   VkPhysicalDevice phys = VK_NULL_HANDLE;
   for (uint32_t i = 0; i < n; i++) {
      VkPhysicalDeviceProperties p;
      vkGetPhysicalDeviceProperties(devs[i], &p);
      if (strstr(p.deviceName, "Mali"))
         phys = devs[i];
   }
   free(devs);
   if (phys == VK_NULL_HANDLE) {
      printf("FAIL no Mali\n");
      return 1;
   }
   if (linear) {
      VkImageFormatProperties props;
      VkResult result = vkGetPhysicalDeviceImageFormatProperties(
         phys, VK_FORMAT_R8G8B8A8_UNORM, VK_IMAGE_TYPE_2D,
         VK_IMAGE_TILING_LINEAR, VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT, 0, &props);
      if (result == VK_ERROR_FORMAT_NOT_SUPPORTED ||
          (result == VK_SUCCESS &&
           (props.maxExtent.width < W || props.maxExtent.height < H ||
            !(props.sampleCounts & VK_SAMPLE_COUNT_1_BIT)))) {
         printf("G-SKIP linear RGBA8 color attachment unavailable\n");
         vkDestroyInstance(inst, NULL);
         return 2;
      }
      if (result != VK_SUCCESS) {
         printf("FAIL linear image format query r=%d\n", result);
         return 1;
      }
   }

   uint32_t qn = 0;
   vkGetPhysicalDeviceQueueFamilyProperties(phys, &qn, NULL);
   VkQueueFamilyProperties *qp = malloc(qn * sizeof(*qp));
   vkGetPhysicalDeviceQueueFamilyProperties(phys, &qn, qp);
   uint32_t qi = ~0u;
   for (uint32_t i = 0; i < qn; i++)
      if (qp[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) {
         qi = i;
         break;
      }
   free(qp);
   if (qi == ~0u) {
      printf("FAIL no graphics queue\n");
      return 1;
   }

   float prio = 1.0f;
   VkPhysicalDeviceFeatures enabled_features = {0};
   if (point || triangle_psiz) {
      VkPhysicalDeviceFeatures supported;
      VkPhysicalDeviceProperties props;
      vkGetPhysicalDeviceFeatures(phys, &supported);
      vkGetPhysicalDeviceProperties(phys, &props);
      if (!supported.largePoints || props.limits.pointSizeRange[0] > 9.0f ||
          props.limits.pointSizeRange[1] < 9.0f) {
         printf("G-SKIP point size 9 unavailable\n");
         vkDestroyInstance(inst, NULL);
         return 2;
      }
      enabled_features.largePoints = VK_TRUE;
   }
   VkDeviceQueueCreateInfo qci = {.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                                  .queueFamilyIndex = qi,
                                  .queueCount = 1,
                                  .pQueuePriorities = &prio};
   const char *dev_exts[] = {
      VK_KHR_EXTERNAL_MEMORY_EXTENSION_NAME,
      VK_KHR_EXTERNAL_MEMORY_FD_EXTENSION_NAME,
      VK_ANDROID_EXTERNAL_MEMORY_ANDROID_HARDWARE_BUFFER_EXTENSION_NAME,
      VK_KHR_BIND_MEMORY_2_EXTENSION_NAME,
      VK_KHR_MAINTENANCE1_EXTENSION_NAME,
      VK_EXT_QUEUE_FAMILY_FOREIGN_EXTENSION_NAME,
   };
   VkDeviceCreateInfo dci = {.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
                             .pEnabledFeatures = point || triangle_psiz ? &enabled_features : NULL,
                             .queueCreateInfoCount = 1,
                             .pQueueCreateInfos = &qci,
                             .enabledExtensionCount = linear ? 0 : 6,
                             .ppEnabledExtensionNames = linear ? NULL : dev_exts};
   VkDevice dev;
   CK(vkCreateDevice(phys, &dci, NULL, &dev), "CreateDevice");
   VkQueue queue;
   vkGetDeviceQueue(dev, qi, 0, &queue);

   /* Allocate AHB when using external-memory readback. */
   AHardwareBuffer_Desc desc = {
      .width = W,
      .height = H,
      .layers = 1,
      .format = AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM,
      .usage = AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT | AHARDWAREBUFFER_USAGE_CPU_READ_RARELY,
   };
   AHardwareBuffer *ahb = NULL;
   AHardwareBuffer_Desc out_desc = {0};
   VkAndroidHardwareBufferPropertiesANDROID ahb_props = {
      .sType = VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_PROPERTIES_ANDROID,
   };
   if (!linear) {
      if (AHardwareBuffer_allocate(&desc, &ahb) != 0 || !ahb) {
         printf("FAIL AHardwareBuffer_allocate\n");
         return 1;
      }
      AHardwareBuffer_describe(ahb, &out_desc);
      printf("G-AHB allocated stride=%u\n", out_desc.stride);
      CK(vkGetAndroidHardwareBufferPropertiesANDROID(dev, ahb, &ahb_props), "AHBProps");
      printf("G-AHB allocSize=%llu memTypeBits=0x%x\n",
             (unsigned long long)ahb_props.allocationSize, ahb_props.memoryTypeBits);
   }

   /* Create Image for AHB */
   VkExternalMemoryImageCreateInfo emici = {
      .sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO,
      .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_ANDROID_HARDWARE_BUFFER_BIT_ANDROID,
   };
   VkImageCreateInfo ici2 = {
      .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
      .pNext = linear ? NULL : &emici,
      .imageType = VK_IMAGE_TYPE_2D,
      .format = VK_FORMAT_R8G8B8A8_UNORM,
      .extent = {W, H, 1},
      .mipLevels = 1,
      .arrayLayers = 1,
      .samples = VK_SAMPLE_COUNT_1_BIT,
      .tiling = linear ? VK_IMAGE_TILING_LINEAR : VK_IMAGE_TILING_OPTIMAL,
      .usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
      .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
      .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
   };
   VkImage img;
   CK(vkCreateImage(dev, &ici2, NULL, &img), "Image");

   /* Import AHB into VkDeviceMemory */
   VkImportAndroidHardwareBufferInfoANDROID imp = {
      .sType = VK_STRUCTURE_TYPE_IMPORT_ANDROID_HARDWARE_BUFFER_INFO_ANDROID,
      .buffer = ahb,
   };
   VkMemoryDedicatedAllocateInfo dai = {
      .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
      .pNext = &imp,
      .image = img,
   };
   VkPhysicalDeviceMemoryProperties image_mp;
   vkGetPhysicalDeviceMemoryProperties(phys, &image_mp);
   VkMemoryRequirements2 image_req = {.sType = VK_STRUCTURE_TYPE_MEMORY_REQUIREMENTS_2};
   if (linear) {
      VkImageMemoryRequirementsInfo2 req_info = {
         .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_REQUIREMENTS_INFO_2, .image = img};
      vkGetImageMemoryRequirements2(dev, &req_info, &image_req);
   }
   uint32_t type_bits = linear ? image_req.memoryRequirements.memoryTypeBits :
                                 ahb_props.memoryTypeBits;
   uint32_t chosen_mi = ~0u;
   for (uint32_t i = 0; i < image_mp.memoryTypeCount; i++) {
      if ((type_bits & (1u << i)) &&
          (!linear || (image_mp.memoryTypes[i].propertyFlags &
                       VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT))) {
         chosen_mi = i;
         break;
      }
   }
   if (chosen_mi == ~0u) {
      printf(linear ? "G-SKIP no host-visible linear image memory\n" :
                      "FAIL no AHB memory type\n");
      vkDestroyImage(dev, img, NULL);
      vkDestroyDevice(dev, NULL);
      vkDestroyInstance(inst, NULL);
      if (ahb)
         AHardwareBuffer_release(ahb);
      return linear ? 2 : 1;
   }
   VkMemoryAllocateInfo mai = {
      .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
      .pNext = linear ? NULL : &dai,
      .allocationSize = linear ? image_req.memoryRequirements.size : ahb_props.allocationSize,
      .memoryTypeIndex = chosen_mi,
   };
   VkDeviceMemory imem;
   CK(vkAllocateMemory(dev, &mai, NULL, &imem), linear ? "AllocMemory(linear)" : "AllocMemory(import)");
   printf(linear ? "G-linear allocation OK\n" : "G-import OK\n");

   /* Bind image memory */
   VkBindImageMemoryInfo bmi = {
      .sType = VK_STRUCTURE_TYPE_BIND_IMAGE_MEMORY_INFO,
      .image = img,
      .memory = imem,
      .memoryOffset = 0,
   };
   CK(vkBindImageMemory2(dev, 1, &bmi), "BindImageMemory2");

   /* Create ImageView */
   VkImageViewCreateInfo ivci = {
      .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
      .image = img,
      .viewType = VK_IMAGE_VIEW_TYPE_2D,
      .format = VK_FORMAT_R8G8B8A8_UNORM,
      .subresourceRange = {.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT, .levelCount = 1, .layerCount = 1},
   };
   VkImageView view;
   CK(vkCreateImageView(dev, &ivci, NULL, &view), "View");

   /* Render Pass: clear to blue */
   VkAttachmentDescription att = {
      .format = VK_FORMAT_R8G8B8A8_UNORM,
      .samples = VK_SAMPLE_COUNT_1_BIT,
      .loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
      .storeOp = VK_ATTACHMENT_STORE_OP_STORE,
      .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
      .finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
   };
   VkAttachmentReference ref = {.attachment = 0, .layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
   VkSubpassDescription sp = {.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS, .colorAttachmentCount = 1, .pColorAttachments = &ref};
   VkRenderPassCreateInfo rpci = {.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO, .attachmentCount = 1, .pAttachments = &att, .subpassCount = 1, .pSubpasses = &sp};
   VkRenderPass rp;
   CK(vkCreateRenderPass(dev, &rpci, NULL, &rp), "RP");

   VkFramebufferCreateInfo fbci = {
      .sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
      .renderPass = rp,
      .attachmentCount = 1,
      .pAttachments = &view,
      .width = W,
      .height = H,
      .layers = 1,
   };
   VkFramebuffer fb;
   CK(vkCreateFramebuffer(dev, &fbci, NULL, &fb), "FB");

   /* Vertex buffer for red triangle */
   float verts[] = {-1.0f, -1.0f, -0.25f, -1.0f, -1.0f, -0.25f};
   if (point)
      verts[0] = verts[1] = 0.0f;
   VkBufferCreateInfo vbci = {.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, .size = sizeof(verts), .usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, .sharingMode = VK_SHARING_MODE_EXCLUSIVE};
   VkBuffer vbuf;
   CK(vkCreateBuffer(dev, &vbci, NULL, &vbuf), "VBuffer");
   VkMemoryRequirements vmr;
   vkGetBufferMemoryRequirements(dev, vbuf, &vmr);
   VkPhysicalDeviceMemoryProperties mp;
   vkGetPhysicalDeviceMemoryProperties(phys, &mp);
   uint32_t host_mi = ~0u;
   for (uint32_t i = 0; i < mp.memoryTypeCount; i++) {
      if ((vmr.memoryTypeBits & (1u << i)) &&
          (mp.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)) {
         host_mi = i;
         break;
      }
   }
   if (host_mi == ~0u) {
      printf("FAIL no host-visible vertex memory\n");
      return 1;
   }
   VkMemoryAllocateInfo vmai = {.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, .allocationSize = vmr.size, .memoryTypeIndex = host_mi};
   VkDeviceMemory vmem;
   CK(vkAllocateMemory(dev, &vmai, NULL, &vmem), "VMem");
   CK(vkBindBufferMemory(dev, vbuf, vmem, 0), "VBind");
   void *vp;
   CK(vkMapMemory(dev, vmem, 0, VK_WHOLE_SIZE, 0, &vp), "VMap");
   memcpy(vp, verts, sizeof(verts));
   if (!(mp.memoryTypes[host_mi].propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
      VkMappedMemoryRange range = {.sType = VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE,
                                   .memory = vmem, .offset = 0, .size = VK_WHOLE_SIZE};
      CK(vkFlushMappedMemoryRanges(dev, 1, &range), "VFlush");
   }
   vkUnmapMemory(dev, vmem);

   /* Shaders and Pipeline */
   VkShaderModuleCreateInfo vsmci = {.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
      .codeSize = point || triangle_psiz ? sizeof(idvs_point_vert_spv) :
                  multi ? sizeof(idvs_multi_vert_spv) :
                  varying ? sizeof(idvs_varying_vert_spv) : sizeof(tri_vert_spv),
      .pCode = point || triangle_psiz ? idvs_point_vert_spv :
               multi ? idvs_multi_vert_spv :
               varying ? idvs_varying_vert_spv : tri_vert_spv};
   VkShaderModule vsm;
   CK(vkCreateShaderModule(dev, &vsmci, NULL, &vsm), "VSM");
   VkShaderModuleCreateInfo fsmci = {.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
      .codeSize = multi ? sizeof(idvs_multi_frag_spv) :
                  varying ? sizeof(idvs_varying_frag_spv) : sizeof(tri_frag_spv),
      .pCode = multi ? idvs_multi_frag_spv :
               varying ? idvs_varying_frag_spv : tri_frag_spv};
   VkShaderModule fsm;
   CK(vkCreateShaderModule(dev, &fsmci, NULL, &fsm), "FSM");

   VkPipelineShaderStageCreateInfo stages[2] = {
      {.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, .stage = VK_SHADER_STAGE_VERTEX_BIT, .module = vsm, .pName = "main"},
      {.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO, .stage = VK_SHADER_STAGE_FRAGMENT_BIT, .module = fsm, .pName = "main"},
   };
   VkVertexInputBindingDescription vibd = {.binding = 0, .stride = 2 * sizeof(float), .inputRate = VK_VERTEX_INPUT_RATE_VERTEX};
   VkVertexInputAttributeDescription viad = {.location = 0, .binding = 0, .format = VK_FORMAT_R32G32_SFLOAT, .offset = 0};
   VkPipelineVertexInputStateCreateInfo pvisi = {.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO, .vertexBindingDescriptionCount = 1, .pVertexBindingDescriptions = &vibd, .vertexAttributeDescriptionCount = 1, .pVertexAttributeDescriptions = &viad};
   VkPipelineInputAssemblyStateCreateInfo piasi = {.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO, .topology = point ? VK_PRIMITIVE_TOPOLOGY_POINT_LIST : VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST};
   VkViewport vp_ = {.x = 0, .y = 0, .width = (float)W, .height = (float)H, .minDepth = 0.0f, .maxDepth = 1.0f};
   VkRect2D sc_ = {.offset = {0, 0}, .extent = {W, H}};
   VkPipelineViewportStateCreateInfo pvsi = {.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO, .viewportCount = 1, .pViewports = &vp_, .scissorCount = 1, .pScissors = &sc_};
   VkPipelineRasterizationStateCreateInfo prsi = {.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO, .polygonMode = VK_POLYGON_MODE_FILL, .cullMode = VK_CULL_MODE_NONE, .frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE, .lineWidth = 1.0f};
   VkPipelineMultisampleStateCreateInfo pmsi = {.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO, .rasterizationSamples = VK_SAMPLE_COUNT_1_BIT};
   VkPipelineColorBlendAttachmentState pcbas = {.blendEnable = VK_FALSE, .colorWriteMask = 0xf};
   VkPipelineColorBlendStateCreateInfo pcbsi = {.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO, .attachmentCount = 1, .pAttachments = &pcbas};
   VkPushConstantRange push_range = {.stageFlags = VK_SHADER_STAGE_VERTEX_BIT,
                                     .offset = 0, .size = 2 * sizeof(float)};
   VkPipelineLayoutCreateInfo plci = {
      .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
      .pushConstantRangeCount = multi ? 1 : 0,
      .pPushConstantRanges = multi ? &push_range : NULL,
   };
   VkPipelineLayout layout;
   CK(vkCreatePipelineLayout(dev, &plci, NULL, &layout), "Layout");

   VkGraphicsPipelineCreateInfo gpci = {
      .sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
      .stageCount = 2,
      .pStages = stages,
      .pVertexInputState = &pvisi,
      .pInputAssemblyState = &piasi,
      .pViewportState = &pvsi,
      .pRasterizationState = &prsi,
      .pMultisampleState = &pmsi,
      .pColorBlendState = &pcbsi,
      .layout = layout,
      .renderPass = rp,
      .subpass = 0,
   };
   VkPipeline pipe;
   CK(vkCreateGraphicsPipelines(dev, VK_NULL_HANDLE, 1, &gpci, NULL, &pipe), "GfxPipe");
   printf("G-pipeline ready\n");

   /* Command buffer */
   VkCommandPoolCreateInfo cpoci = {.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, .queueFamilyIndex = qi};
   VkCommandPool cpool;
   CK(vkCreateCommandPool(dev, &cpoci, NULL, &cpool), "Pool");
   VkCommandBufferAllocateInfo cbai = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, .commandPool = cpool, .commandBufferCount = 1};
   VkCommandBuffer cmd;
   CK(vkAllocateCommandBuffers(dev, &cbai, &cmd), "Cmd");
   VkFenceCreateInfo fci = {.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
   VkFence fence;
   CK(vkCreateFence(dev, &fci, NULL, &fence), "Fence");

   VkCommandBufferBeginInfo bbi = {.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};
   CK(vkBeginCommandBuffer(cmd, &bbi), "Begin");
   VkClearValue clear = {.color = {{0.0f, 0.0f, 1.0f, 1.0f}}};
   VkRenderPassBeginInfo rpbi = {
      .sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
      .renderPass = rp,
      .framebuffer = fb,
      .renderArea = {{0, 0}, {W, H}},
      .clearValueCount = 1,
      .pClearValues = &clear,
   };
   vkCmdBeginRenderPass(cmd, &rpbi, VK_SUBPASS_CONTENTS_INLINE);
   vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipe);
   if (multi) {
      const float params[] = {0.125f, 0.5f};
      vkCmdPushConstants(cmd, layout, VK_SHADER_STAGE_VERTEX_BIT, 0,
                         sizeof(params), params);
   }
   VkDeviceSize off = 0;
   vkCmdBindVertexBuffers(cmd, 0, 1, &vbuf, &off);
   vkCmdDraw(cmd, point ? 1 : 3, 1, 0, 0);
   vkCmdEndRenderPass(cmd);
   if (linear) {
      VkImageMemoryBarrier barrier = {
         .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
         .srcAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
         .dstAccessMask = VK_ACCESS_HOST_READ_BIT,
         .oldLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
         .newLayout = VK_IMAGE_LAYOUT_GENERAL,
         .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
         .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
         .image = img,
         .subresourceRange = {.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
                              .levelCount = 1, .layerCount = 1},
      };
      vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                           VK_PIPELINE_STAGE_HOST_BIT, 0, 0, NULL, 0, NULL,
                           1, &barrier);
   }
   CK(vkEndCommandBuffer(cmd), "End");

   VkSubmitInfo si = {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO, .commandBufferCount = 1, .pCommandBuffers = &cmd};
   CK(vkQueueSubmit(queue, 1, &si, fence), "Submit");
   CK(vkWaitForFences(dev, 1, &fence, VK_TRUE, 30 * 1000 * 1000 * 1000ULL), "Wait");
   printf("G-submit complete\n");

   void *data = NULL;
   VkDeviceSize row_pitch;
   uint8_t *px;
   if (linear) {
      VkImageSubresource subresource = {.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT};
      VkSubresourceLayout sublayout;
      vkGetImageSubresourceLayout(dev, img, &subresource, &sublayout);
      if (sublayout.rowPitch < W * 4 ||
          sublayout.offset > mai.allocationSize ||
          mai.allocationSize - sublayout.offset < W * 4 ||
          sublayout.rowPitch >
             (mai.allocationSize - sublayout.offset - W * 4) / (H - 1)) {
         printf("FAIL invalid linear image layout\n");
         return 1;
      }
      CK(vkMapMemory(dev, imem, 0, VK_WHOLE_SIZE, 0, &data), "ImageMap");
      if (!(image_mp.memoryTypes[chosen_mi].propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
         VkMappedMemoryRange range = {.sType = VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE,
                                      .memory = imem, .offset = 0, .size = VK_WHOLE_SIZE};
         CK(vkInvalidateMappedMemoryRanges(dev, 1, &range), "ImageInvalidate");
      }
      px = (uint8_t *)data + sublayout.offset;
      row_pitch = sublayout.rowPitch;
      printf("G-linear offset=%llu rowPitch=%llu\n",
             (unsigned long long)sublayout.offset, (unsigned long long)row_pitch);
   } else {
      int32_t lock_r = AHardwareBuffer_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_READ_RARELY, -1, NULL, &data);
      if (lock_r != 0 || !data) {
         printf("FAIL AHB lock r=%d\n", lock_r);
         return 1;
      }
      px = data;
      row_pitch = (VkDeviceSize)out_desc.stride * 4;
   }
   uint8_t *in_px = px + (point ? 32 : 8) * row_pitch + (point ? 32 : 8) * 4;
   uint8_t *in_px2 = px + (point ? 32 : 8) * row_pitch + (point ? 28 : 12) * 4;
   uint8_t *point_px3 = px + 32 * row_pitch + 35 * 4;
   uint8_t *point_outside = px + 32 * row_pitch + 26 * 4;
   uint8_t *clear_px = px + 55 * row_pitch + 55 * 4;
   printf("G-interior RGBA=%u %u %u %u\n", in_px[0], in_px[1], in_px[2], in_px[3]);
   if (multi || point)
      printf("G-interior2 RGBA=%u %u %u %u\n", in_px2[0], in_px2[1], in_px2[2], in_px2[3]);
   if (point) {
      printf("G-point-interior3 RGBA=%u %u %u %u\n", point_px3[0], point_px3[1], point_px3[2], point_px3[3]);
      printf("G-point-outside RGBA=%u %u %u %u\n", point_outside[0], point_outside[1], point_outside[2], point_outside[3]);
   }
   printf("G-clear    RGBA=%u %u %u %u\n", clear_px[0], clear_px[1], clear_px[2], clear_px[3]);
   int ok = (point ?
             (in_px[0] > 200 && in_px[1] < 60 && in_px[2] < 60 &&
              in_px2[0] > 200 && in_px2[1] < 60 && in_px2[2] < 60 &&
              in_px2[3] == 255 &&
              point_px3[0] > 200 && point_px3[1] < 60 &&
              point_px3[2] < 60 && point_px3[3] == 255 &&
              point_outside[0] < 60 && point_outside[1] < 60 &&
              point_outside[2] > 200 && point_outside[3] == 255) :
             multi ?
             (in_px[0] >= 15 && in_px[0] <= 21 &&
              in_px[1] >= 64 && in_px[1] <= 72 &&
              in_px[2] >= 60 && in_px[2] <= 68 &&
              in_px2[0] >= 31 && in_px2[0] <= 37 &&
              in_px2[1] >= 64 && in_px2[1] <= 72 &&
              in_px2[2] >= 60 && in_px2[2] <= 68 && in_px2[3] == 255) :
             varying ?
             (in_px[0] >= 60 && in_px[0] <= 76 &&
              in_px[1] >= 60 && in_px[1] <= 76 && in_px[2] < 10) :
             (in_px[0] > 200 && in_px[1] < 60 && in_px[2] < 60)) &&
            in_px[3] == 255 &&
            clear_px[2] > 200 && clear_px[0] < 60 &&
            clear_px[1] < 60 && clear_px[3] == 255;
   if (linear) {
      vkUnmapMemory(dev, imem);
   } else {
      int32_t unlock_r = AHardwareBuffer_unlock(ahb, NULL);
      if (unlock_r != 0) {
         printf("FAIL AHB unlock r=%d\n", unlock_r);
         ok = 0;
      }
   }

   vkDestroyFence(dev, fence, NULL);
   vkFreeCommandBuffers(dev, cpool, 1, &cmd);
   vkDestroyCommandPool(dev, cpool, NULL);
   vkDestroyPipeline(dev, pipe, NULL);
   vkDestroyPipelineLayout(dev, layout, NULL);
   vkDestroyShaderModule(dev, vsm, NULL);
   vkDestroyShaderModule(dev, fsm, NULL);
   vkDestroyFramebuffer(dev, fb, NULL);
   vkDestroyRenderPass(dev, rp, NULL);
   vkDestroyImageView(dev, view, NULL);
   vkDestroyImage(dev, img, NULL);
   vkFreeMemory(dev, imem, NULL);
   vkDestroyBuffer(dev, vbuf, NULL);
   vkFreeMemory(dev, vmem, NULL);
   vkDestroyDevice(dev, NULL);
   vkDestroyInstance(inst, NULL);
   if (ahb)
      AHardwareBuffer_release(ahb);

   if (ok) {
      printf("G-PASS\n");
      return 0;
   }
   printf("G-FAIL (pixel check)\n");
   return 1;
}
