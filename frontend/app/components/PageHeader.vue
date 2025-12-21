<script setup>
import { IconArrowLeft } from "@tabler/icons-vue";

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  icon: {
    required: false,
    default: null,
  },
  titleClass: {
    type: String,
    required: false,
    default: "",
  },
  iconClass: {
    type: String,
    required: false,
    default: "",
  },
  backPath: {
    type: String,
    required: false,
    default: null,
  },
});

const iconIsComponent = () => {
  // Vue components can be objects or functions
  return (
    props.icon &&
    (typeof props.icon === "object" || typeof props.icon === "function")
  );
};

const iconIsString = () => {
  return props.icon && typeof props.icon === "string";
};
</script>
<template>
  <!-- Page Header -->
  <div class="flex justify-between items-center gap-x-6">
    <div class="flex gap-x-2 items-center">
      <NuxtLink
        v-if="backPath"
        :to="backPath"
        class="inline-flex items-center gap-x-2 text-sm font-medium"
      >
        <IconArrowLeft
          :size="24"
          :stroke="2"
          class="text-gray-600 dark:text-gray-400"
        />
      </NuxtLink>
      <!-- vertical divider -->
      <div v-if="backPath" class="w-px h-6 bg-gray-200 dark:bg-gray-500" />
      <component
        v-if="iconIsComponent()"
        :is="icon"
        :stroke="1.5"
        class="size-6 md:size-7 text-gray-600 dark:text-gray-400"
        :class="iconClass"
      />
      <Icon
        v-else-if="iconIsString()"
        :name="icon"
        class="size-6 md:size-7 text-gray-600 dark:text-gray-400"
        :class="iconClass"
      />
      <div class="grow flex flex-col justify-center">
        <h1
          class="font-medium text-lg text-gray-800 dark:text-gray-200"
          :class="titleClass"
        >
          {{ title }}
        </h1>
      </div>
    </div>

    <div class="flex justify-end items-center gap-x-2">
      <slot name="actions" />
    </div>
  </div>
</template>
