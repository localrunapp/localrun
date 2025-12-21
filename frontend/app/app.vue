<script setup>
const isDark = useState("isDark");

useHead({
  titleTemplate: "%s - LocalRun",
});

useSeoMeta({
  title: "LocalRun",
  description:
    "LocalRun - Secure local tunneling solution. Expose your local services to the internet with multiple provider support and built-in analytics.",
  ogTitle: "LocalRun",
  ogDescription:
    "LocalRun - Secure local tunneling solution. Expose your local services to the internet with multiple provider support and built-in analytics.",
  ogImage: "/dark.png",
  ogUrl: "http://localhost:3000",
  twitterTitle: "LocalRun",
  twitterDescription:
    "LocalRun - Secure local tunneling solution. Expose your local services to the internet with multiple provider support and built-in analytics.",
  twitterImage: "/dark.png",
  twitterCard: "summary_large_image",
});
</script>

<template>
  <NuxtLoadingIndicator />
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <Toast />
</template>
