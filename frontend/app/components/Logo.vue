<script setup>
const props = defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  }
});

const sizeMap = {
  sm: 20,
  md: 32,
  lg: 42
};

const logoSize = computed(() => sizeMap[props.size]);
</script>

<template>
  <NuxtLink to="/">
    <div class="flex items-center gap-x-2 justify-center sm:justify-start">
      <!-- imagen en /public/dark.png o white.png, usar nuxt image -->
      <img
        src="/light.png"
        alt="LocalRun Logo"
        :width="logoSize"
        :height="logoSize"
        class="flex-shrink-0 hidden dark:block"
      />
      <img
        src="/dark.png"
        alt="LocalRun Logo"
        :width="logoSize"
        :height="logoSize"
        class="flex-shrink-0 block dark:hidden"
      />
      <p
        class="text-2xl mb-1 font-bold text-gray-800 dark:text-gray-200 localrun-font leading-none hidden sm:block"
      >
        LocalRun
      </p>
    </div>
  </NuxtLink>
</template>
