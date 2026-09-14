<template>
  <div class="min-h-screen bg-[#131517] py-16 px-4">
    <div class="container mx-auto max-w-5xl">
      <!-- Hero Section -->
      <div class="text-center mb-16">
        <h1 class="text-4xl md:text-5xl font-bold mb-6 text-[#f08330]">
          Get in Touch
        </h1>
        <p class="text-gray-300 text-lg max-w-2xl mx-auto">
          Have questions, need a free estimate, or want to discuss a unique
          project idea? We're here to help. Reach out using any of the methods
          below, and let's get started!
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
        <!-- Contact Information -->
        <div class="space-y-8">
          <div class="about-card">
            <h2 class="text-2xl font-semibold mb-6 text-[#f08330]">
              Contact Information
            </h2>
            <div class="space-y-4">
              <div class="flex items-start gap-3">
                <Phone class="w-6 h-6 text-[#f08330] flex-shrink-0 mt-1" />
                <div>
                  <h3 class="font-semibold text-white">Phone</h3>
                  <p class="text-gray-300">210-436-9117</p>
                </div>
              </div>
              <div class="flex items-start gap-3">
                <Mail class="w-6 h-6 text-[#f08330] flex-shrink-0 mt-1" />
                <div>
                  <h3 class="font-semibold text-white">Email</h3>
                  <p class="text-gray-300">info@flipfixer.com</p>
                </div>
              </div>
              <div class="flex items-start gap-3">
                <MapPin class="w-6 h-6 text-[#f08330] flex-shrink-0 mt-1" />
                <div>
                  <h3 class="font-semibold text-white">Service Areas</h3>
                  <p class="text-gray-300">
                    San Antonio and surrounding communities
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Contact Form -->
        <div class="about-card">
          <h2 class="text-2xl font-semibold mb-6 text-[#f08330]">
            Contact Form
          </h2>
          <form @submit.prevent="handleSubmit" class="space-y-6">
            <div>
              <label for="name" class="block text-white mb-2">Name *</label>
              <input
                type="text"
                id="name"
                v-model="formData.name"
                required
                class="w-full px-4 py-2 bg-[#131517] border border-[#2d3238] rounded-lg text-white focus:outline-none focus:border-[#f08330] transition-colors"
              />
            </div>

            <div>
              <label for="email" class="block text-white mb-2">Email *</label>
              <input
                type="email"
                id="email"
                v-model="formData.email"
                required
                class="w-full px-4 py-2 bg-[#131517] border border-[#2d3238] rounded-lg text-white focus:outline-none focus:border-[#f08330] transition-colors"
              />
            </div>

            <div>
              <label for="phone" class="block text-white mb-2">Phone</label>
              <input
                type="tel"
                id="phone"
                v-model="formData.phone"
                class="w-full px-4 py-2 bg-[#131517] border border-[#2d3238] rounded-lg text-white focus:outline-none focus:border-[#f08330] transition-colors"
              />
            </div>

            <div>
              <label for="message" class="block text-white mb-2"
                >Message / Project Details *</label
              >
              <textarea
                id="message"
                v-model="formData.message"
                required
                rows="4"
                class="w-full px-4 py-2 bg-[#131517] border border-[#2d3238] rounded-lg text-white focus:outline-none focus:border-[#f08330] transition-colors"
              ></textarea>
            </div>

            <button
              type="submit"
              class="w-full bg-[#f08330] hover:bg-[#ca5e11] text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-300"
            >
              Send Message
            </button>

            <p class="text-sm text-gray-400 text-center mt-4">
              We'll get back to you within 24-48 hours.
            </p>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { Phone, Mail, MapPin } from "lucide-vue-next";

const formData = ref({
  name: "",
  email: "",
  phone: "",
  message: "",
});

const handleSubmit = () => {
  // Handle form submission logic here
  console.log("Form submitted:", formData.value);
};

useHead({
  title: "Contact",
  meta: [
    {
      name: "description",
      content:
        "Get in touch with FlipFixer for your home improvement needs. Free estimates for remodeling and renovation services in San Antonio.",
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
