<template>
  <div class="bg-[#131517] min-h-screen">
    <!-- Hero Section -->
    <div class="px-4">
      <div class="text-center py-16">
        <h1 class="text-4xl md:text-6xl font-bold text-[#f08330] mb-4">
          Our Services
        </h1>
        <p class="text-xl text-gray-200 max-w-3xl mx-auto">
          Professional solutions for every project, delivered with expertise and
          care
        </p>
      </div>
    </div>

    <!-- Section 1: Remodels -->
    <section class="py-16 px-4 bg-[#131517]">
      <div class="container mx-auto max-w-6xl">
        <h2 class="text-3xl font-bold text-[#f08330] text-center mb-12">
          Remodels
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="service-card">
            <div class="relative">
              <img
                src="~/assets/images/kitchen2.jpg"
                alt="Kitchen & Bath"
                class="w-full h-48 object-cover"
              />
              <Kitchen class="absolute bottom-4 right-4 w-8 h-8 text-white" />
            </div>
            <div class="p-6">
              <h3 class="text-xl font-semibold mb-3">
                Kitchen & Bathroom Upgrades
              </h3>
              <p>
                We handle everything from cabinetry and countertops to plumbing
                and lighting.
              </p>
            </div>
          </div>
          <div class="service-card">
            <div class="relative">
              <img
                src="~/assets/images/flooring.jpg"
                alt="Flooring"
                class="w-full h-48 object-cover"
              />
            </div>
            <div class="p-6">
              <h3 class="text-xl font-semibold mb-3">Flooring & Finishes</h3>
              <p>
                Upgrade your space with hardwood, laminate, tile, or luxury
                vinyl—installed professionally for a flawless finish.
              </p>
            </div>
          </div>
          <div class="service-card">
            <div class="relative">
              <img
                src="~/assets/images/painter.jpg"
                alt="Paint"
                class="w-full h-48 object-cover"
              />
              <Paint class="absolute bottom-4 right-4 w-8 h-8 text-white" />
            </div>
            <div class="p-6">
              <h3 class="text-xl font-semibold mb-3">
                Interior & Exterior Paint
              </h3>
              <p>
                Give your home a fresh look inside and out with our expert
                painting services.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 2: Make-Ready Services -->
    <section class="py-16 px-4 bg-stone-900">
      <div class="container mx-auto max-w-6xl">
        <h2 class="text-3xl font-bold text-[#f08330] text-center mb-12">
          Make-Ready Services
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="feature-card">
            <Building2 class="w-16 h-16 mx-auto mb-4 text-[#f08330]" />
            <h3 class="text-xl font-semibold mb-3">Property Preparation</h3>
            <p>
              Need a quick turnaround for your rental or a house you're about to
              sell? We specialize in fast, efficient make-ready solutions.
            </p>
          </div>
          <div class="feature-card">
            <Warehouse class="w-16 h-16 mx-auto mb-4 text-[#f08330]" />
            <h3 class="text-xl font-semibold mb-3">Investor-Friendly</h3>
            <p>
              We understand ROI. Our team identifies cost-effective improvements
              to boost your property's market appeal.
            </p>
          </div>
          <div class="feature-card">
            <ClipboardCheck class="w-16 h-16 mx-auto mb-4 text-[#f08330]" />
            <h3 class="text-xl font-semibold mb-3">Customized Approach</h3>
            <p>
              Every property is unique; we'll create a tailored plan that
              maximizes your budget and timeline.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 3: Handyman Services -->
    <section class="py-16 px-4 bg-[#131517]">
      <div class="container mx-auto max-w-6xl">
        <h2 class="text-3xl font-bold text-[#f08330] text-center mb-12">
          Handyman Services
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="service-card">
            <div class="relative">
              <img
                src="~/assets/images/punchout.jpg"
                alt="Small Repairs"
                class="w-full h-48 object-cover"
              />
            </div>
            <div class="p-6">
              <h3 class="text-xl font-semibold mb-3">Small Repairs</h3>
              <p>
                From drywall patches to minor plumbing fixes, our team is ready
                to help.
              </p>
            </div>
          </div>
          <div class="service-card">
            <div class="relative">
              <img
                src="~/assets/images/repair.jpg"
                alt="Punch-Out Lists"
                class="w-full h-48 object-cover"
              />
            </div>
            <div class="p-6">
              <h3 class="text-xl font-semibold mb-3">Punch-Out Lists</h3>
              <p>
                Let us knock out those last-minute details—doors, windows, trim,
                and more.
              </p>
            </div>
          </div>
          <div class="service-card">
            <div class="relative">
              <img
                src="~/assets/images/installer.jpg"
                alt="Appliance Installation"
                class="w-full h-48 object-cover"
              />
            </div>
            <div class="p-6">
              <h3 class="text-xl font-semibold mb-3">Appliance Installation</h3>
              <p>
                We install cabinets, fixtures, TVs, entertainment systems, and
                more—quickly and correctly.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 4: Additional Services -->
    <section class="py-16 px-4 bg-stone-900">
      <div class="container mx-auto max-w-6xl">
        <h2 class="text-3xl font-bold text-[#f08330] text-center mb-12">
          Additional Services & Specialties
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="feature-card">
            <Ruler class="w-16 h-16 mx-auto mb-4 text-[#f08330]" />
            <h3 class="text-xl font-semibold mb-3">
              Custom Carpentry & Fabrication
            </h3>
            <p>
              From one-of-a-kind woodwork to artistic finishes, our background
              in custom fabrication sets us apart.
            </p>
          </div>
          <div class="feature-card">
            <TreePine class="w-16 h-16 mx-auto mb-4 text-[#f08330]" />
            <h3 class="text-xl font-semibold mb-3">Outdoor Projects</h3>
            <p>
              Decks, patios, landscaping elements—enhance your curb appeal and
              enjoy the outdoors in style.
            </p>
          </div>
          <div class="feature-card">
            <GraduationCap class="w-16 h-16 mx-auto mb-4 text-[#f08330]" />
            <h3 class="text-xl font-semibold mb-3">Consultation & Education</h3>
            <p>
              Want to flip a house on your own? Hire us to show you the ropes
              with easy-to-learn steps the "pros" don't want you to know.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-16 px-4 bg-stone-900">
      <div class="container mx-auto max-w-4xl text-center">
        <h2 class="text-3xl font-bold text-[#f08330] mb-6">
          Ready to Get Started?
        </h2>
        <p class="text-xl text-gray-200 mb-8">
          Call us today or fill out our online form for a free estimate. We'll
          walk you through every step, ensuring you get the most value out of
          your investment.
        </p>
        <NuxtLink
          to="/contact"
          class="inline-block bg-[#d4681b] hover:bg-[#ca5e11] text-white font-semibold py-4 px-8 rounded-lg transition-colors duration-300"
        >
          Contact Us
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import {
  Hammer,
  Home,
  Wrench,
  Warehouse,
  Building2,
  ClipboardCheck,
  Tv,
  Ruler,
  TreePine,
  GraduationCap,
} from "lucide-vue-next";

useHead({
  title: "Services",
  meta: [
    {
      name: "description",
      content:
        "Comprehensive home improvement services including remodels, make-ready services, and handyman solutions in San Antonio and surrounding areas.",
    },
  ],
});
</script>

<style scoped>
.services-hero {
  position: relative;
}

.services-hero::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
    url("https://placehold.co/1920x400/f08330/white?text=Services");
  background-size: cover;
  background-position: center;
  z-index: 0;
}

.services-hero > div {
  position: relative;
  z-index: 1;
}

.service-card {
  background-color: #131517;
  border: 1px solid #2d3238;
  border-radius: 0.5rem;
  overflow: hidden;
  transition: transform 0.3s ease-in-out;
}

.service-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
}

.feature-card {
  padding: 2rem;
  background-color: #131517;
  border: 1px solid #2d3238;
  border-radius: 0.5rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.cta-button {
  background-color: #f08330;
  color: #131517;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
}

.cta-button:hover {
  background-color: #ca5e11;
  transform: translateY(-2px);
}

h3 {
  color: #f08330;
}
</style>
