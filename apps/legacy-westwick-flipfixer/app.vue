<template>
  <div>
    <AppHeader />
    <main class="page-wrap">
      <NuxtPage />
    </main>
    <AppFooter />
  </div>
</template>

<script setup>
useHead({
  titleTemplate: (titleChunk) => {
    return titleChunk ? `Flip Fixer | ${titleChunk}` : "Flip Fixer";
  },
  link: [
    {
      rel: "icon",
      type: "image/png",
      href: "/favicon-96x96.png",
      sizes: "96x96",
    },
    {
      rel: "icon",
      type: "image/svg+xml",
      href: "/favicon.svg",
    },
    {
      rel: "shortcut icon",
      href: "/favicon.ico",
    },
    {
      rel: "apple-touch-icon",
      sizes: "180x180",
      href: "/apple-touch-icon.png",
    },
    {
      rel: "manifest",
      href: "/site.webmanifest",
    },
  ],
  meta: [
    {
      name: "apple-mobile-web-app-title",
      content: "FlipFixer",
    },
  ],
});
</script>

<style>
html,
body {
  @apply bg-stone-900 text-stone-100;
  font-family: "Montserrat", sans-serif;
}

.page-wrap {
  background-color: #131517;
  min-height: 70vh;
  max-width: 100%;
  overflow-x: hidden;
  margin-top: 88px;
}

.page-enter-active,
.page-leave-active {
  transition: all 0.31s;
}
.page-enter-from,
.page-leave-to {
  opacity: 0;
  translate: 50px 0px;
}
</style>
