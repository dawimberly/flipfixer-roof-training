<template>
  <div class="header-wrap w-6 w-full p-4">
    <header
      class="bg-zinc-950 text-stone-200 p-4 flex justify-between items-center w-full"
    >
      <div class="flex items-center relative">
        <img
          src="assets/images/logo.svg"
          alt="Logo"
          class="h-16 -ml-2 absolute left-0 top-1/2 transform -translate-y-1/2"
        />
        <NuxtLink to="/" class="text-4xl font-bold logo-text pl-16">
          <span class="the-text">The</span>
          Flip&nbsp;Fixer
        </NuxtLink>
      </div>

      <!-- Hamburger button -->
      <button
        @click="isMenuOpen = !isMenuOpen"
        class="lg:hidden z-20 text-stone-200 hover:text-[#dd9f2c]"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-8 w-8"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            v-if="!isMenuOpen"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
          <path
            v-else
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>

      <!-- Desktop Navigation -->
      <nav class="hidden lg:flex space-x-6">
        <NuxtLink
          v-for="(link, index) in navigationLinks"
          :key="index"
          :to="link.to"
          class="header-link"
          :class="{ '': $route.path === link.to }"
        >
          {{ link.text }}
        </NuxtLink>
      </nav>

      <!-- Mobile Navigation -->
      <div
        v-if="isMenuOpen"
        class="fixed inset-0 bg-zinc-950 bg-opacity-95 lg:hidden z-10"
      >
        <nav class="flex flex-col items-center justify-center h-full space-y-8">
          <NuxtLink
            v-for="(link, index) in navigationLinks"
            :key="index"
            :to="link.to"
            class="header-link text-2xl"
            :class="{ '': $route.path === link.to }"
            @click="isMenuOpen = false"
          >
            {{ link.text }}
          </NuxtLink>
        </nav>
      </div>
    </header>
  </div>
</template>

<script lang="ts" setup>
const isMenuOpen = ref(false);

const navigationLinks = [
  { to: "/", text: "Home" },
  { to: "/about", text: "About" },
  { to: "/services", text: "Services" },
  { to: "/gallery", text: "Gallery" },
  { to: "/testimonials", text: "Testimonials" },
  { to: "/contact", text: "Contact" },
];

// Close mobile menu when route changes
watch(
  () => useRoute().path,
  () => {
    isMenuOpen.value = false;
  }
);
</script>

<style scoped>
.header-wrap {
  background-color: #131517;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50; /* Increased z-index to ensure it stays above other content */
}

.header-link {
  @apply uppercase text-lg px-6 font-bold;
  transition: all 0.3s ease-in-out;
}

.logo-text {
  color: #f08330;
  position: relative;
}

.the-text {
  position: absolute;
  font-size: 0.75rem;
  /* transform: rotate(-1deg); */
  left: 4rem;
  top: -20px;
  font-weight: bold;
  opacity: 0.85;
  /* text-transform: uppercase; */
  color: #fff;
}

.header-link:hover {
  color: #dd9f2c;
}

/* Prevent body scroll when mobile menu is open */
:global(body.menu-open) {
  overflow: hidden;
}

/* Adjust the mobile menu transition */
.mobile-menu-enter-active,
.mobile-menu-leave-active {
  transition: opacity 0.3s ease;
}

.mobile-menu-enter-from,
.mobile-menu-leave-to {
  opacity: 0;
}
</style>
