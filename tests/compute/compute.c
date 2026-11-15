/* Gates D+E: device create, queue, mapped buffer, deterministic compute.
 * Dispatches 1x1x1 compute writing 0x12345678; repeats 10x. PASS = 10/10.
 * Usage: compute <libvulkan_panfrost.so>
 */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>

#ifdef PANVK_ANDROID_APP_LOG
#include <android/log.h>
#define printf(...) __android_log_print(ANDROID_LOG_INFO, "PanVKCompute", __VA_ARGS__)
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

/* Generated from write_magic.comp via glslangValidator (see below). */
static const uint32_t comp_spv[] = {
#include "write_magic.spv.h"
};

static const uint32_t nop_spv[] = {
#include "nop.spv.h"
};

static const uint32_t guarded_spv[] = {
#include "guarded.spv.h"
};

static const uint32_t guarded_bda_spv[] = {
#include "guarded_bda.spv.h"
};

static const uint32_t guarded_texture_spv[] = {
#include "guarded_texture.spv.h"
};

static const uint32_t fau_shift_spv[] = {
#include "fau_shift.spv.h"
};

#define GUARD_WORDS 64u
#define GRID_WIDTH 64u
#define GRID_WORDS (GRID_WIDTH * GRID_WIDTH)
#define GUARDED_WORDS (GRID_WORDS + 2u * GUARD_WORDS)
#define SENTINEL 0x7d7d7d7du

int
main(int argc, char **argv)
{
   if (argc < 2 || argc > 3) {
      printf("usage: %s <libvulkan_panfrost.so> [nop|big|guarded-0..guarded-21]\n", argv[0]);
      return 2;
   }
   int guarded = argc > 2 && !strncmp(argv[2], "guarded-", 8);
   uint32_t guarded_case = 0;
   if (guarded) {
      char *end;
      unsigned long value = strtoul(argv[2] + 8, &end, 10);
      if (end == argv[2] + 8 || *end != '\0' || value > 21) {
         printf("FAIL invalid guarded case: %s\n", argv[2]);
         return 2;
      }
      guarded_case = (uint32_t)value;
   } else if (argc == 3 && strcmp(argv[2], "nop") && strcmp(argv[2], "big")) {
      printf("FAIL invalid mode: %s\n", argv[2]);
      return 2;
   }
   int bda_test = guarded && guarded_case == 13;
   int texture_test = guarded && guarded_case == 14;
   int fau_test = guarded && guarded_case >= 15;
   int use_buf = !(argc > 2 && !strcmp(argv[2], "nop"));
   setvbuf(stdout, NULL, _IONBF, 0);
   const uint32_t *spv = fau_test ? fau_shift_spv :
                         bda_test ? guarded_bda_spv :
                         texture_test ? guarded_texture_spv :
                         guarded ? guarded_spv : use_buf ? comp_spv : nop_spv;
   size_t spv_size = fau_test ? sizeof(fau_shift_spv) :
                     bda_test ? sizeof(guarded_bda_spv) :
                     texture_test ? sizeof(guarded_texture_spv) :
                     guarded ? sizeof(guarded_spv) :
                     use_buf ? sizeof(comp_spv) : sizeof(nop_spv);
   printf("COMPUTE driver=%s mode=%s PAN_USE_KRAID=%s\n", argv[1],
          argc > 2 ? argv[2] : "magic",
          getenv("PAN_USE_KRAID") ? getenv("PAN_USE_KRAID") : "(default)");
   void *h = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
   if (!h) {
      printf("FAIL dlopen %s\n", dlerror());
      return 1;
   }
   icd_gipa_fn gipa = (icd_gipa_fn)dlsym(h, "vk_icdGetInstanceProcAddr");
   if (!gipa) {
      printf("FAIL gipa\n");
      return 1;
   }
#define GIPA(what, name)                                                    \
   PFN_##name name = (PFN_##name)gipa(NULL, "vk" #what);                     \
   if (!name) {                                                             \
      printf("FAIL missing vk" #what "\n");                                  \
      return 1;                                                             \
   }
   GIPA(CreateInstance, vkCreateInstance)

   VkApplicationInfo app = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
                            .apiVersion = VK_API_VERSION_1_3};
   VkInstanceCreateInfo ici = {.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                               .pApplicationInfo = &app};
   VkInstance inst;
   CK(vkCreateInstance(&ici, NULL, &inst), "CreateInstance");
   fprintf(stderr, "T-after-CreateInstance\n");

#undef GIPA
#define GIPA(what, name)                                                    \
   PFN_##name name = (PFN_##name)gipa(inst, "vk" #what);                     \
   if (!name) {                                                             \
      printf("FAIL missing vk" #what "\n");                                  \
      return 1;                                                             \
   }
   GIPA(EnumeratePhysicalDevices, vkEnumeratePhysicalDevices)
   GIPA(GetPhysicalDeviceProperties, vkGetPhysicalDeviceProperties)
   GIPA(GetPhysicalDeviceQueueFamilyProperties,
        vkGetPhysicalDeviceQueueFamilyProperties)
   GIPA(GetPhysicalDeviceMemoryProperties, vkGetPhysicalDeviceMemoryProperties)
   GIPA(CreateDevice, vkCreateDevice)
   GIPA(GetDeviceQueue, vkGetDeviceQueue)
   GIPA(CreateBuffer, vkCreateBuffer)
   GIPA(GetBufferMemoryRequirements, vkGetBufferMemoryRequirements)
   GIPA(AllocateMemory, vkAllocateMemory)
   GIPA(BindBufferMemory, vkBindBufferMemory)
   GIPA(MapMemory, vkMapMemory)
   GIPA(UnmapMemory, vkUnmapMemory)
   GIPA(CreateDescriptorSetLayout, vkCreateDescriptorSetLayout)
   GIPA(CreateDescriptorPool, vkCreateDescriptorPool)
   GIPA(AllocateDescriptorSets, vkAllocateDescriptorSets)
   GIPA(UpdateDescriptorSets, vkUpdateDescriptorSets)
   GIPA(CreateShaderModule, vkCreateShaderModule)
   GIPA(CreatePipelineLayout, vkCreatePipelineLayout)
   GIPA(CreateComputePipelines, vkCreateComputePipelines)
   GIPA(CreateCommandPool, vkCreateCommandPool)
   GIPA(AllocateCommandBuffers, vkAllocateCommandBuffers)
   GIPA(BeginCommandBuffer, vkBeginCommandBuffer)
   GIPA(ResetCommandBuffer, vkResetCommandBuffer)
   GIPA(CmdBindPipeline, vkCmdBindPipeline)
   GIPA(CmdBindDescriptorSets, vkCmdBindDescriptorSets)
   GIPA(CmdDispatch, vkCmdDispatch)
   GIPA(CmdPipelineBarrier, vkCmdPipelineBarrier)
   GIPA(EndCommandBuffer, vkEndCommandBuffer)
   GIPA(CreateFence, vkCreateFence)
   GIPA(QueueSubmit, vkQueueSubmit)
   GIPA(WaitForFences, vkWaitForFences)
   GIPA(ResetFences, vkResetFences)
   GIPA(DestroyFence, vkDestroyFence)
   GIPA(FreeCommandBuffers, vkFreeCommandBuffers)
   GIPA(DestroyCommandPool, vkDestroyCommandPool)
   GIPA(DestroyPipeline, vkDestroyPipeline)
   GIPA(DestroyPipelineLayout, vkDestroyPipelineLayout)
   GIPA(DestroyShaderModule, vkDestroyShaderModule)
   GIPA(DestroyDescriptorPool, vkDestroyDescriptorPool)
   GIPA(DestroyDescriptorSetLayout, vkDestroyDescriptorSetLayout)
   GIPA(FreeMemory, vkFreeMemory)
   GIPA(DestroyBuffer, vkDestroyBuffer)
   GIPA(DestroyDevice, vkDestroyDevice)
   GIPA(DestroyInstance, vkDestroyInstance)

   /* pick Mali */
   uint32_t n = 0;
   CK(vkEnumeratePhysicalDevices(inst, &n, NULL), "count");
   fprintf(stderr, "T-after-count n=%u\n", n);
   VkPhysicalDevice *devs = malloc(n * sizeof(*devs));
   CK(vkEnumeratePhysicalDevices(inst, &n, devs), "enum");
   fprintf(stderr, "T-after-enum\n");
   VkPhysicalDevice phys = VK_NULL_HANDLE;
   for (uint32_t i = 0; i < n; i++) {
      fprintf(stderr, "T-loop %u\n", i);
      VkPhysicalDeviceProperties p;
      vkGetPhysicalDeviceProperties(devs[i], &p);
      fprintf(stderr, "T-gpp %u: %s\n", i, p.deviceName);
      if (strstr(p.deviceName, "Mali"))
         phys = devs[i];
   }
   free(devs);
   if (phys == VK_NULL_HANDLE) {
      printf("FAIL no Mali\n");
      return 1;
   }
   printf("D-OK physical device\n");
   PFN_vkGetPhysicalDeviceFeatures2 vkGetPhysicalDeviceFeatures2 = NULL;
   PFN_vkGetBufferDeviceAddress vkGetBufferDeviceAddress = NULL;
   PFN_vkCmdPushConstants vkCmdPushConstants = NULL;
   if (bda_test) {
      VkPhysicalDeviceProperties props;
      vkGetPhysicalDeviceProperties(phys, &props);
      if (props.apiVersion < VK_API_VERSION_1_2) {
         printf("D+E-SKIP Vulkan 1.2 required for bufferDeviceAddress\n");
         vkDestroyInstance(inst, NULL);
         return 2;
      }
      vkGetPhysicalDeviceFeatures2 = (PFN_vkGetPhysicalDeviceFeatures2)
         gipa(inst, "vkGetPhysicalDeviceFeatures2");
      vkGetBufferDeviceAddress = (PFN_vkGetBufferDeviceAddress)
         gipa(inst, "vkGetBufferDeviceAddress");
      vkCmdPushConstants = (PFN_vkCmdPushConstants)
         gipa(inst, "vkCmdPushConstants");
      if (!vkGetPhysicalDeviceFeatures2 || !vkGetBufferDeviceAddress ||
          !vkCmdPushConstants) {
         printf("FAIL missing buffer device address entry point\n");
         return 1;
      }
   }
   if (fau_test) {
      vkCmdPushConstants = (PFN_vkCmdPushConstants)gipa(inst, "vkCmdPushConstants");
      if (!vkCmdPushConstants) {
         printf("FAIL missing vkCmdPushConstants\n");
         return 1;
      }
   }
   PFN_vkGetPhysicalDeviceFormatProperties vkGetPhysicalDeviceFormatProperties = NULL;
   PFN_vkCreateImage vkCreateImage = NULL;
   PFN_vkGetImageMemoryRequirements vkGetImageMemoryRequirements = NULL;
   PFN_vkBindImageMemory vkBindImageMemory = NULL;
   PFN_vkCreateImageView vkCreateImageView = NULL;
   PFN_vkCreateSampler vkCreateSampler = NULL;
   PFN_vkCmdCopyBufferToImage vkCmdCopyBufferToImage = NULL;
   PFN_vkDestroyImage vkDestroyImage = NULL;
   PFN_vkDestroyImageView vkDestroyImageView = NULL;
   PFN_vkDestroySampler vkDestroySampler = NULL;
   if (texture_test) {
#define LOAD_TEXTURE(name) do { \
      vk##name = (PFN_vk##name)gipa(inst, "vk" #name); \
      if (!vk##name) { printf("FAIL missing vk" #name "\n"); return 1; } \
   } while (0)
      LOAD_TEXTURE(GetPhysicalDeviceFormatProperties);
      LOAD_TEXTURE(CreateImage);
      LOAD_TEXTURE(GetImageMemoryRequirements);
      LOAD_TEXTURE(BindImageMemory);
      LOAD_TEXTURE(CreateImageView);
      LOAD_TEXTURE(CreateSampler);
      LOAD_TEXTURE(CmdCopyBufferToImage);
      LOAD_TEXTURE(DestroyImage);
      LOAD_TEXTURE(DestroyImageView);
      LOAD_TEXTURE(DestroySampler);
#undef LOAD_TEXTURE
      VkFormatProperties format;
      vkGetPhysicalDeviceFormatProperties(phys, VK_FORMAT_R32_UINT, &format);
      VkFormatFeatureFlags needed = VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT |
                                    VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
      if ((format.optimalTilingFeatures & needed) != needed) {
         printf("D+E-SKIP R32_UINT sampled transfer destination unsupported\n");
         vkDestroyInstance(inst, NULL);
         return 2;
      }
   }

   /* queue family with COMPUTE */
   uint32_t qn = 0;
   fprintf(stderr, "T-before-qfams\n");
   vkGetPhysicalDeviceQueueFamilyProperties(phys, &qn, NULL);
   fprintf(stderr, "T-after-qfams qn=%u\n", qn);
   VkQueueFamilyProperties *qp = malloc(qn * sizeof(*qp));
   fprintf(stderr, "T-before-qfams2\n");
   vkGetPhysicalDeviceQueueFamilyProperties(phys, &qn, qp);
   fprintf(stderr, "T-after-qfams2\n");
   uint32_t qi = ~0u;
   for (uint32_t i = 0; i < qn; i++)
      if (qp[i].queueFlags & VK_QUEUE_COMPUTE_BIT) {
         qi = i;
         break;
      }
   free(qp);
   if (qi == ~0u) {
      printf("FAIL no compute queue\n");
      return 1;
   }

   float prio = 1.0f;
   VkPhysicalDeviceBufferDeviceAddressFeatures bda = {
      .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BUFFER_DEVICE_ADDRESS_FEATURES,
   };
   if (bda_test) {
      VkPhysicalDeviceFeatures2 features = {
         .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2,
         .pNext = &bda,
      };
      vkGetPhysicalDeviceFeatures2(phys, &features);
      if (!bda.bufferDeviceAddress) {
         printf("D+E-SKIP bufferDeviceAddress unsupported\n");
         vkDestroyInstance(inst, NULL);
         return 2;
      }
      bda.bufferDeviceAddressCaptureReplay = VK_FALSE;
      bda.bufferDeviceAddressMultiDevice = VK_FALSE;
   }
   VkDeviceQueueCreateInfo qci = {.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                                  .queueFamilyIndex = qi,
                                  .queueCount = 1,
                                  .pQueuePriorities = &prio};
   VkDeviceCreateInfo dci = {.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
                             .pNext = bda_test ? &bda : NULL,
                             .queueCreateInfoCount = 1,
                             .pQueueCreateInfos = &qci};
   VkDevice dev;
   fprintf(stderr, "T-before-CreateDevice qi=%u\n", qi);
   CK(vkCreateDevice(phys, &dci, NULL, &dev), "CreateDevice");
   fprintf(stderr, "T-after-CreateDevice\n");
   printf("D-OK vkCreateDevice\n");
   VkQueue queue;
   vkGetDeviceQueue(dev, qi, 0, &queue);

   /* storage buffer; argv[2]=="big" uses 16KB like the AHB test */
   VkDeviceSize bufsize = guarded ? GUARDED_WORDS * sizeof(uint32_t) :
                          (argc > 2 && !strcmp(argv[2], "big")) ? 16384 : 4;
   VkBufferCreateInfo bci = {.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
                             .size = bufsize,
                             .usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                                      (bda_test ? VK_BUFFER_USAGE_SHADER_DEVICE_ADDRESS_BIT : 0) |
                                      (texture_test ? VK_BUFFER_USAGE_TRANSFER_SRC_BIT : 0),
                             .sharingMode = VK_SHARING_MODE_EXCLUSIVE};
   VkBuffer buf;
   CK(vkCreateBuffer(dev, &bci, NULL, &buf), "CreateBuffer");
   VkMemoryRequirements mr;
   vkGetBufferMemoryRequirements(dev, buf, &mr);
   VkPhysicalDeviceMemoryProperties mp;
   fprintf(stderr, "T-before-memprops\n");
   vkGetPhysicalDeviceMemoryProperties(phys, &mp);
   fprintf(stderr, "T-after-memprops types=%u heaps=%u\n", mp.memoryTypeCount,
           mp.memoryHeapCount);
   uint32_t mi = ~0u;
   for (uint32_t i = 0; i < mp.memoryTypeCount; i++)
      if ((mr.memoryTypeBits & (1u << i)) &&
          (mp.memoryTypes[i].propertyFlags &
           (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
            VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
             (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
              VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
         mi = i;
         break;
      }
   if (mi == ~0u) {
      printf("FAIL no host-coherent memory\n");
      return 1;
   }
   VkMemoryAllocateFlagsInfo alloc_flags = {
      .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO,
      .flags = VK_MEMORY_ALLOCATE_DEVICE_ADDRESS_BIT,
   };
   VkMemoryAllocateInfo mai = {.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
                               .pNext = bda_test ? &alloc_flags : NULL,
                               .allocationSize = mr.size,
                               .memoryTypeIndex = mi};
   VkDeviceMemory mem;
   fprintf(stderr, "T-before-AllocMem size=%llu mi=%u\n",
           (unsigned long long)mr.size, mi);
   CK(vkAllocateMemory(dev, &mai, NULL, &mem), "AllocateMemory");
   fprintf(stderr, "T-after-AllocMem\n");
   CK(vkBindBufferMemory(dev, buf, mem, 0), "BindBufferMemory");
   VkDeviceAddress address = 0;
   if (bda_test) {
      VkBufferDeviceAddressInfo info = {
         .sType = VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO,
         .buffer = buf,
      };
      address = vkGetBufferDeviceAddress(dev, &info);
      if (!address) {
         printf("FAIL GetBufferDeviceAddress returned zero\n");
         return 1;
      }
   }
   fprintf(stderr, "T-after-Bind\n");
   printf("D-OK memory+bind (Gate D device side done)\n");

   VkImage image = VK_NULL_HANDLE;
   VkDeviceMemory image_memory = VK_NULL_HANDLE;
   VkImageView image_view = VK_NULL_HANDLE;
   VkSampler sampler = VK_NULL_HANDLE;
   if (texture_test) {
      VkImageCreateInfo image_info = {
         .sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
         .imageType = VK_IMAGE_TYPE_2D, .format = VK_FORMAT_R32_UINT,
         .extent = {64, 32, 1}, .mipLevels = 1, .arrayLayers = 1,
         .samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_OPTIMAL,
         .usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
         .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
         .initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
      };
      CK(vkCreateImage(dev, &image_info, NULL, &image), "CreateImage");
      VkMemoryRequirements image_req;
      vkGetImageMemoryRequirements(dev, image, &image_req);
      uint32_t image_mi = ~0u;
      for (uint32_t i = 0; i < mp.memoryTypeCount; i++)
         if (image_req.memoryTypeBits & (1u << i)) {
            image_mi = i;
            break;
         }
      if (image_mi == ~0u) {
         printf("FAIL no image memory type\n");
         return 1;
      }
      VkMemoryAllocateInfo image_alloc = {
         .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
         .allocationSize = image_req.size, .memoryTypeIndex = image_mi,
      };
      CK(vkAllocateMemory(dev, &image_alloc, NULL, &image_memory), "ImageMemory");
      CK(vkBindImageMemory(dev, image, image_memory, 0), "BindImageMemory");
      VkImageViewCreateInfo view_info = {
         .sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
         .image = image, .viewType = VK_IMAGE_VIEW_TYPE_2D,
         .format = VK_FORMAT_R32_UINT,
         .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1},
      };
      CK(vkCreateImageView(dev, &view_info, NULL, &image_view), "ImageView");
      VkSamplerCreateInfo sampler_info = {
         .sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
         .magFilter = VK_FILTER_NEAREST, .minFilter = VK_FILTER_NEAREST,
         .mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST,
         .addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
         .addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
         .addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
      };
      CK(vkCreateSampler(dev, &sampler_info, NULL, &sampler), "Sampler");
   }

   /* descriptor + pipeline (built once) */
   VkDescriptorSetLayout dsl = VK_NULL_HANDLE;
   VkDescriptorPool pool = VK_NULL_HANDLE;
   VkDescriptorSet set = VK_NULL_HANDLE;
   if (use_buf) {
   VkDescriptorSetLayoutBinding bind[] = {
      {.binding = 0, .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
       .descriptorCount = 1, .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT},
      {.binding = 1, .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
       .descriptorCount = 1, .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT},
   };
   VkDescriptorSetLayoutCreateInfo dlci = {
      .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
      .bindingCount = texture_test ? 2 : 1,
      .pBindings = bind};
   CK(vkCreateDescriptorSetLayout(dev, &dlci, NULL, &dsl), "DSL");
   VkDescriptorPoolSize psz[] = {
      {.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, .descriptorCount = 1},
      {.type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, .descriptorCount = 1},
   };
   VkDescriptorPoolCreateInfo dpci = {
      .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
      .maxSets = 1,
      .poolSizeCount = texture_test ? 2 : 1,
      .pPoolSizes = psz};
   CK(vkCreateDescriptorPool(dev, &dpci, NULL, &pool), "Pool");
   VkDescriptorSetAllocateInfo dsai = {
      .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
      .descriptorPool = pool,
      .descriptorSetCount = 1,
      .pSetLayouts = &dsl};
   CK(vkAllocateDescriptorSets(dev, &dsai, &set), "AllocSets");
   VkDescriptorBufferInfo dbi = {.buffer = buf, .offset = 0,
                                 .range = guarded ? bufsize : 4};
   VkWriteDescriptorSet wds = {.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
                               .dstSet = set,
                               .dstBinding = 0,
                               .descriptorCount = 1,
                               .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                               .pBufferInfo = &dbi};
   vkUpdateDescriptorSets(dev, 1, &wds, 0, NULL);
   if (texture_test) {
      VkDescriptorImageInfo image_descriptor = {
         .sampler = sampler, .imageView = image_view,
         .imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
      };
      VkWriteDescriptorSet image_write = {
         .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
         .dstSet = set, .dstBinding = 1, .descriptorCount = 1,
         .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
         .pImageInfo = &image_descriptor,
      };
      vkUpdateDescriptorSets(dev, 1, &image_write, 0, NULL);
   }
   } /* use_buf */

   VkShaderModuleCreateInfo smci = {.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
                                    .codeSize = spv_size,
                                    .pCode = spv};
   VkShaderModule mod;
   fprintf(stderr, "T-before-ShaderModule size=%zu\n", spv_size);
   CK(vkCreateShaderModule(dev, &smci, NULL, &mod), "ShaderModule");
   fprintf(stderr, "T-after-ShaderModule\n");
   VkPushConstantRange range = {.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT,
                                .offset = 0,
                                .size = fau_test ? sizeof(uint32_t) : sizeof(address)};
   VkPipelineLayoutCreateInfo plci = {
      .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
      .setLayoutCount = use_buf ? 1 : 0,
      .pSetLayouts = use_buf ? &dsl : NULL,
      .pushConstantRangeCount = bda_test || fau_test ? 1 : 0,
      .pPushConstantRanges = bda_test || fau_test ? &range : NULL};
   VkPipelineLayout layout;
   CK(vkCreatePipelineLayout(dev, &plci, NULL, &layout), "Layout");
   uint32_t values[] = {guarded_case < 3 ? guarded_case :
                        guarded_case == 5 ? 3 : guarded_case == 9 ? 4 :
                        guarded_case == 10 ? 5 : guarded_case == 11 ? 6 :
                        guarded_case == 12 ? 7 : 0,
                        guarded_case == 3 || guarded_case == 5 ? 1 :
                        guarded_case >= 6 && guarded_case <= 8 ?
                           1u << (guarded_case - 5) : 16,
                        guarded_case >= 3 ? 1 : 16};
   VkSpecializationMapEntry map[] = {
      {.constantID = 0, .offset = 0, .size = sizeof(uint32_t)},
      {.constantID = 1, .offset = sizeof(uint32_t), .size = sizeof(uint32_t)},
      {.constantID = 2, .offset = 2 * sizeof(uint32_t), .size = sizeof(uint32_t)},
   };
   VkSpecializationInfo spec = {.mapEntryCount = 3, .pMapEntries = map,
                                .dataSize = sizeof(values), .pData = values};
   uint32_t fau_case = guarded_case - (fau_test ? 15u : 0u);
   VkSpecializationInfo fau_spec = {.mapEntryCount = 1, .pMapEntries = map,
                                    .dataSize = sizeof(fau_case), .pData = &fau_case};
   VkComputePipelineCreateInfo cpci = {
      .sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
      .stage = {.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                .stage = VK_SHADER_STAGE_COMPUTE_BIT,
                .module = mod,
                .pName = "main",
                .pSpecializationInfo = fau_test ? &fau_spec :
                   guarded && !bda_test && !texture_test ? &spec : NULL},
      .layout = layout};
   VkPipeline pipe;
   fprintf(stderr, "T-before-ComputePipeline\n");
   CK(vkCreateComputePipelines(dev, VK_NULL_HANDLE, 1, &cpci, NULL, &pipe),
      "ComputePipeline");
   fprintf(stderr, "T-after-ComputePipeline\n");

   VkCommandPoolCreateInfo cpoci = {
      .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
      .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
      .queueFamilyIndex = qi};
   VkCommandPool cpool;
   CK(vkCreateCommandPool(dev, &cpoci, NULL, &cpool), "CmdPool");
   VkCommandBufferAllocateInfo cbai = {
      .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
      .commandPool = cpool,
      .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
      .commandBufferCount = 1};
   VkCommandBuffer cmd;
   CK(vkAllocateCommandBuffers(dev, &cbai, &cmd), "AllocCmd");
   VkFenceCreateInfo fci = {.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
   VkFence fence;
   CK(vkCreateFence(dev, &fci, NULL, &fence), "Fence");

   int pass = 0;
   for (int iter = 0; iter < 10; iter++) {
      void *p;
      CK(vkMapMemory(dev, mem, 0, guarded ? bufsize : 4, 0, &p), "Map");
      fprintf(stderr, "T-mapped p=%p\n", p);
      if (guarded) {
         for (uint32_t i = 0; i < GUARDED_WORDS; i++)
            ((uint32_t *)p)[i] = SENTINEL;
         if (bda_test || texture_test)
            for (uint32_t i = 0; i < GRID_WORDS / 2; i++)
               ((uint32_t *)p)[GUARD_WORDS + i] = i ^ 0x12345678u;
         if (guarded_case == 9 || guarded_case == 10 || guarded_case == 12)
            for (uint32_t i = 0; i < (guarded_case == 9 ? 256u : GRID_WORDS); i++)
               ((uint32_t *)p)[GUARD_WORDS + i] = 0;
      } else {
         *(volatile uint32_t *)p = 0u;
      }
      vkUnmapMemory(dev, mem);

      VkCommandBufferBeginInfo bbi = {
         .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
         .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};
      CK(vkResetCommandBuffer(cmd, 0), "ResetCmd");
      CK(vkBeginCommandBuffer(cmd, &bbi), "Begin");
      if (texture_test) {
         VkImageMemoryBarrier image_barrier = {
            .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
            .dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
            .oldLayout = VK_IMAGE_LAYOUT_UNDEFINED,
            .newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            .image = image,
            .subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1},
         };
         vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                              VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL,
                              0, NULL, 1, &image_barrier);
         VkBufferImageCopy copy = {
            .bufferOffset = GUARD_WORDS * sizeof(uint32_t),
            .imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1},
            .imageExtent = {64, 32, 1},
         };
         vkCmdCopyBufferToImage(cmd, buf, image,
                                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &copy);
         image_barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
         image_barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
         image_barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
         image_barrier.newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
         vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT,
                              VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, 0, NULL,
                              0, NULL, 1, &image_barrier);
      }
      vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipe);
      if (use_buf)
         vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, layout,
                                 0, 1, &set, 0, NULL);
      if (bda_test)
         vkCmdPushConstants(cmd, layout, VK_SHADER_STAGE_COMPUTE_BIT, 0,
                            sizeof(address), &address);
      uint32_t fau_value = guarded_case >= 19 ? (uint32_t)iter :
                           0x12345678u + (uint32_t)iter * 0x1020304u;
      if (guarded_case == 21) {
         float fau_float = (float)iter * 0.5f;
         memcpy(&fau_value, &fau_float, sizeof(fau_value));
      }
      if (fau_test)
         vkCmdPushConstants(cmd, layout, VK_SHADER_STAGE_COMPUTE_BIT, 0,
                            sizeof(fau_value), &fau_value);
      vkCmdDispatch(cmd, fau_test ? 1 : guarded ? GRID_WIDTH / values[1] : 1,
                    fau_test ? 1 : bda_test || texture_test ? GRID_WIDTH / 16 :
                    guarded ? GRID_WIDTH / values[2] : 1, 1);
      if (use_buf) {
         VkMemoryBarrier barrier = {
            .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
            .srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT,
            .dstAccessMask = VK_ACCESS_HOST_READ_BIT,
         };
         vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                              VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &barrier,
                              0, NULL, 0, NULL);
      }
      CK(vkEndCommandBuffer(cmd), "End");
      VkSubmitInfo si = {.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
                         .commandBufferCount = 1,
                         .pCommandBuffers = &cmd};
      CK(vkQueueSubmit(queue, 1, &si, fence), "Submit");
      CK(vkWaitForFences(dev, 1, &fence, VK_TRUE, 30 * 1000 * 1000 * 1000ULL),
         "WaitFences");
      CK(vkResetFences(dev, 1, &fence), "ResetFences");

      CK(vkMapMemory(dev, mem, 0, guarded ? bufsize : 4, 0, &p), "Map2");
      if (guarded) {
         unsigned mismatches = 0;
         for (uint32_t i = 0; i < GUARDED_WORDS; i++) {
            uint32_t expected = SENTINEL;
            if (i >= GUARD_WORDS && i < GUARD_WORDS + GRID_WORDS) {
               uint32_t index = i - GUARD_WORDS;
               uint32_t x = index % GRID_WIDTH, y = index / GRID_WIDTH;
               if (fau_test) {
                  if (index < 16) {
                     uint32_t value = guarded_case == 15 ? fau_value << 4 :
                                      guarded_case == 16 ? fau_value >> 2 :
                                      guarded_case == 17 ? fau_value * 17u :
                                      guarded_case == 18 ? (fau_value << 4) ^ 1u :
                                      guarded_case == 19 ? fau_value > 4u :
                                      guarded_case == 20 ? fau_value == 4u :
                                      iter > 2;
                     expected = value;
                  }
               } else if (bda_test || texture_test) {
                  expected = (index % (GRID_WORDS / 2)) ^ 0x12345678u;
               } else if (guarded_case == 9 && index < 256) {
                  expected = 16;
               } else if (guarded_case == 10) {
                  expected = 1;
               } else if (guarded_case == 12) {
                  expected = x + 1;
               } else if (guarded_case != 9 &&
                          (guarded_case != 2 || (x < 61 && y < 59))) {
                  uint32_t mask = guarded_case == 1 && ((x + y) & 1) ?
                                  0x87654321u : 0x12345678u;
                  expected = index ^ mask;
               }
            }
            uint32_t actual = ((const uint32_t *)p)[i];
            if (actual != expected) {
               if (mismatches < 4)
                  printf("E-iter %d word=%u got=0x%08x expected=0x%08x\n",
                         iter, i, actual, expected);
               mismatches++;
            }
         }
         printf("E-iter %d case=%u mismatches=%u/%u\n", iter, guarded_case,
                mismatches, GUARDED_WORDS);
         if (!mismatches)
            pass++;
      } else if (!use_buf) {
         pass++;
      } else {
         uint32_t v = *(volatile uint32_t *)p;
         if (v == 0x12345678u)
            pass++;
         else
            printf("E-iter %d: got 0x%08x (want 0x12345678)\n", iter, v);
      }
      vkUnmapMemory(dev, mem);
   }
   printf("E-compute %d/10\n", pass);

   vkDestroyFence(dev, fence, NULL);
   vkFreeCommandBuffers(dev, cpool, 1, &cmd);
   vkDestroyCommandPool(dev, cpool, NULL);
   vkDestroyPipeline(dev, pipe, NULL);
   vkDestroyPipelineLayout(dev, layout, NULL);
   vkDestroyShaderModule(dev, mod, NULL);
   if (use_buf) {
      vkDestroyDescriptorPool(dev, pool, NULL);
      vkDestroyDescriptorSetLayout(dev, dsl, NULL);
   }
   if (texture_test) {
      vkDestroySampler(dev, sampler, NULL);
      vkDestroyImageView(dev, image_view, NULL);
      vkDestroyImage(dev, image, NULL);
      vkFreeMemory(dev, image_memory, NULL);
   }
   vkDestroyBuffer(dev, buf, NULL);
   vkFreeMemory(dev, mem, NULL);
   vkDestroyDevice(dev, NULL);
   vkDestroyInstance(inst, NULL);

   if (pass == 10) {
      printf("D+E-PASS\n");
      return 0;
   }
   printf("D+E-FAIL\n");
   return 1;
}
