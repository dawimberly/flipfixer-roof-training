<template>
  <div
    class="relative max-w-3xl mx-auto rounded-lg overflow-hidden shadow-xl cursor-col-resize h-[400px]"
    @mousemove="handleMouseMove"
    @touchmove="handleTouchMove"
    ref="container"
  >
    <img
      :src="afterImage"
      :alt="afterAlt"
      class="absolute inset-0 w-full h-full object-cover"
    />
    <img
      :src="beforeImage"
      :alt="beforeAlt"
      class="absolute inset-0 w-full h-full object-cover"
      :style="{
        clipPath: `inset(0 ${100 - (position / containerWidth) * 100}% 0 0)`,
      }"
    />
    <div
      class="absolute top-0 right-0 h-full w-1 bg-white"
      :style="{ left: `${position}px` }"
    ></div>
    <div
      class="absolute top-4 left-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded"
    >
      Before
    </div>
    <div
      class="absolute top-4 right-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded"
    >
      After
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";

const props = defineProps({
  beforeImage: {
    type: String,
    required: true,
  },
  afterImage: {
    type: String,
    required: true,
  },
  beforeAlt: {
    type: String,
    default: "Before",
  },
  afterAlt: {
    type: String,
    default: "After",
  },
});

const position = ref(0);
const container = ref(null);
const containerWidth = ref(0);

onMounted(() => {
  if (container.value) {
    containerWidth.value = container.value.getBoundingClientRect().width;
    position.value = containerWidth.value / 2;
  }
});

const handleMouseMove = (e) => {
  if (!container.value) return;
  const rect = container.value.getBoundingClientRect();
  containerWidth.value = rect.width;
  position.value = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
};

const handleTouchMove = (e) => {
  if (!container.value || !e.touches[0]) return;
  e.preventDefault();
  const rect = container.value.getBoundingClientRect();
  containerWidth.value = rect.width;
  position.value = Math.max(
    0,
    Math.min(e.touches[0].clientX - rect.left, rect.width)
  );
};
</script>

<style scoped>
.before-image {
  transition: width 0.05s ease-out;
}
</style>
