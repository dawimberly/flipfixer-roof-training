<template>
  <div class="min-h-screen bg-[#131517] py-16 px-4">
    <div class="container mx-auto max-w-5xl">
      <!-- Hero Section -->
      <div class="text-center mb-16">
        <h1 class="text-4xl md:text-5xl font-bold mb-6 text-[#f08330]">
          Our Story
        </h1>
      </div>

      <!-- Main Content -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
        <!-- Left Column -->
        <div class="space-y-8">
          <div class="about-card">
            <h2 class="text-2xl font-semibold mb-4 text-[#f08330]">
              How We Started
            </h2>
            <p class="text-gray-300 leading-relaxed">
              Flip Fixer was founded on a passion for quality craftsmanship and
              customer satisfaction. After years of professional installation
              work for major home improvement retailers, our owner, Jon, decided
              to start his own company—one that would focus on personalized
              service, honesty, and efficiency.
            </p>
          </div>

          <div class="about-card">
            <h2 class="text-2xl font-semibold mb-4 text-[#f08330]">
              Our Mission
            </h2>
            <p class="text-gray-300 leading-relaxed">
              Our mission is to transform properties into beautiful, functional
              spaces—whether you're an investor looking to flip a house or a
              homeowner dreaming of a stylish upgrade. We stay up-to-date with
              the latest construction trends and home design ideas to help you
              maximize your investment and enjoyment.
            </p>
          </div>
        </div>

        <!-- Right Column -->
        <div class="space-y-8">
          <div class="about-card">
            <h2 class="text-2xl font-semibold mb-4 text-[#f08330]">
              Our Values
            </h2>
            <ul class="space-y-4">
              <li
                v-for="(value, index) in values"
                :key="index"
                class="flex gap-3"
              >
                <CheckCircle class="flex-shrink-0 w-6 h-6 text-[#f08330]" />
                <div>
                  <h3 class="font-semibold text-white">{{ value.title }}</h3>
                  <p class="text-gray-300">{{ value.description }}</p>
                </div>
              </li>
            </ul>
          </div>

          <div class="about-card">
            <h2 class="text-2xl font-semibold mb-4 text-[#f08330]">
              Why We're Different
            </h2>
            <p class="text-gray-300 leading-relaxed">
              Unlike large corporations, we treat each client's home or property
              as if it were our own. Eighty percent of our business comes from
              fixing unfinished projects left by other contractors—demonstrating
              our commitment to getting the job done right, every single time.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CheckCircle } from "lucide-vue-next";
import { useHead } from "#imports";

const values = [
  {
    title: "Quality",
    description: "We take pride in our work and never cut corners.",
  },
  {
    title: "Integrity",
    description:
      "Every project starts with an honest quote and transparent communication.",
  },
  {
    title: "Professionalism",
    description:
      "Cleanliness, timeliness, and respect for your property are standard practice.",
  },
  {
    title: "Education",
    description:
      "We believe in empowering our clients with knowledge—whether that's tips on flipping a home or explaining why a particular material choice is best.",
  },
];

useHead({
  title: "About",
  meta: [
    {
      name: "description",
      content:
        "Learn about FlipFixer's story, mission, and values. Over 20 years of experience in home improvement and renovation services in San Antonio.",
    },
  ],
});
</script>

<style scoped>
.about-card {
  background-color: #1a1d20;
  border: 1px solid #2d3238;
  border-radius: 0.5rem;
  padding: 2rem;
  transition: transform 0.3s ease;
}

.about-card:hover {
  transform: translateY(-2px);
}
</style>
