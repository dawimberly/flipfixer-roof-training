<template>
  <footer class="bg-[#131517] text-white py-16">
    <div class="container mx-auto max-w-6xl px-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-12">
        <!-- About Section -->
        <div>
          <h3 class="text-xl font-semibold mb-4 text-[#f08330]">
            About Flip Fixer
          </h3>
          <p class="text-gray-300 leading-relaxed text-sm">
            With over 20 years of hands-on experience, we're San Antonio's
            trusted partner for home improvements and renovations. Our
            commitment to quality craftsmanship and customer satisfaction sets
            us apart in everything we do.
          </p>
        </div>

        <!-- Service Areas -->
        <div>
          <h3 class="text-xl font-semibold mb-4 text-[#f08330]">
            Service Areas
          </h3>
          <p class="text-gray-300 text-sm">
            San Antonio <span class="text-gray-600 px-1">▪</span> New Braunfels
            <span class="text-gray-600 px-1">▪</span> Schertz
            <span class="text-gray-600 px-1">▪</span> Cibolo
            <span class="text-gray-600 px-1">▪</span> Boerne
          </p>
        </div>

        <!-- Contact Info -->
        <div>
          <h3 class="text-xl font-semibold mb-4 text-[#f08330]">Contact Us</h3>
          <div class="space-y-4 text-gray-300">
            <div class="flex items-center gap-3">
              <Phone class="w-5 h-5 text-[#f08330]" />
              <a
                href="tel:210-436-9117"
                class="hover:text-white transition-colors"
              >
                210-436-9117
              </a>
            </div>
            <div class="flex items-center gap-3">
              <Mail class="w-5 h-5 text-[#f08330]" />
              <a
                href="mailto:info@flipfixer.com"
                class="hover:text-white transition-colors"
              >
                info@flipfixer.com
              </a>
            </div>
            <!-- <div class="flex items-center gap-3">
              <Clock class="w-5 h-5 text-[#f08330]" />
              <p>Mon-Fri: 8am-6pm</p>
            </div>
            <div class="flex items-center gap-3">
              <MapPin class="w-5 h-5 text-[#f08330]" />
              <p>San Antonio, TX</p>
            </div> -->
          </div>
        </div>
      </div>

      <div class="mt-12 pt-8 text-center text-gray-400">
        <p>
          &copy; {{ new Date().getFullYear() }} Flip Fixer. All rights reserved.
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { Phone, Mail, Clock, MapPin } from "lucide-vue-next";
</script>

<style scoped>
/* Any additional styles can go here */
</style>
