<template>
  <div class="bg-[#131517]">
    <!-- Hero Section -->
    <div class="px-4">
      <div class="text-center py-16">
        <h1 class="text-4xl md:text-6xl font-bold text-[#f08330] mb-6">
          Testimonials
        </h1>
        <p class="text-xl text-gray-200 max-w-3xl mx-auto">
          Our clients' satisfaction is the heart of everything we do. Hear it
          straight from the homeowners, investors, and property managers who've
          experienced our commitment to quality and customer service.
        </p>
      </div>
    </div>

    <!-- Testimonials Grid -->
    <section class="py-16 px-4">
      <div class="container mx-auto max-w-6xl">
        <div class="grid md:grid-cols-3 gap-8">
          <!-- Testimonial Cards -->
          <div class="testimonial-card">
            <div class="quote-mark">"</div>
            <p class="text-gray-200 mb-6 mt-3">
              Jon and his team have been awesome to work with. The value they
              provide for the cost is unbeatable. Jon is talented and
              responsive. I highly recommend him for all your home repair needs!
            </p>
            <div class="testimonial-author">
              <h3 class="font-bold text-xl">Michael M.</h3>
              <p class="text-gray-500">San Antonio, TX</p>
            </div>
          </div>

          <div class="testimonial-card">
            <div class="quote-mark">"</div>
            <p class="text-gray-200 mb-6 mt-3">
              Flip Fixer transformed my outdated rental property within my
              budget. Jon's attention to detail and craftsmanship is
              outstanding. I had multiple offers after just one open house!
            </p>
            <div class="testimonial-author">
              <h3 class="font-bold text-xl">Clark P.</h3>
              <p class="text-gray-500">Alamo Heights, TX</p>
            </div>
          </div>

          <div class="testimonial-card">
            <div class="quote-mark">"</div>
            <p class="text-gray-200 mb-6 mt-3">
              I approached Jon with several repairs needed throughout my home.
              He was professional, efficient, and the quality of work was
              exceptional. Will definitely be calling him again.
            </p>
            <div class="testimonial-author">
              <h3 class="font-bold text-xl">Scott S.</h3>
              <p class="text-gray-500">Hollywood Park, TX</p>
            </div>
          </div>

          <div class="testimonial-card">
            <div class="quote-mark">"</div>
            <p class="text-gray-200 mb-6 mt-3">
              The kitchen renovation exceeded all our expectations. Jon and his
              team were fast, clean, and incredibly professional. My new kitchen
              is exactly what I envisioned!
            </p>
            <div class="testimonial-author">
              <h3 class="font-bold text-xl">Jennifer R.</h3>
              <p class="text-gray-500">Stone Oak, TX</p>
            </div>
          </div>

          <div class="testimonial-card">
            <div class="quote-mark">"</div>
            <p class="text-gray-200 mb-6 mt-3">
              Their make-ready service saved us time and money—enabling our
              tenant to move in sooner than expected. Jon's team handled
              everything from repairs to painting flawlessly.
            </p>
            <div class="testimonial-author">
              <h3 class="font-bold text-xl">David K.</h3>
              <p class="text-gray-500">Austin, TX</p>
            </div>
          </div>

          <div class="testimonial-card">
            <div class="quote-mark">"</div>
            <p class="text-gray-200 mb-6 mt-3">
              As a property manager, I need reliable contractors I can trust.
              Flip Fixer has become our go-to for all maintenance and renovation
              needs. Always professional and on time.
            </p>
            <div class="testimonial-author">
              <h3 class="font-bold text-xl">Sarah M.</h3>
              <p class="text-gray-500">San Antonio, TX</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Call to Action Section -->
    <section class="py-16 px-4 bg-stone-900">
      <div class="container mx-auto max-w-4xl text-center">
        <h2 class="text-3xl font-bold text-[#f08330] mb-6">
          Ready to Join Our Satisfied Clients?
        </h2>
        <p class="text-xl text-gray-200 mb-8">
          Contact us today and let us show you why 80% of our business is from
          returning customers or word-of-mouth referrals.
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
useHead({
  title: "Testimonials",
  meta: [
    {
      name: "description",
      content:
        "Read what our clients say about FlipFixer. Real reviews from homeowners and investors in San Antonio and surrounding areas.",
    },
  ],
});
</script>

<style scoped>
h1,
h2 {
  color: #f08330;
}

.testimonial-card {
  padding: 2rem;
  background-color: #1a1c1e;
  border-radius: 0.5rem;
  position: relative;
  transition: transform 0.3s ease-in-out;
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  min-height: 320px;
}

.quote-mark {
  display: block;
  font-size: 6rem;
  line-height: 0.5;
  color: #f08330;
  opacity: 0.42;
  font-family: serif;
  pointer-events: none;
  position: relative;
  left: -6px;
  top: 10px;
}

.testimonial-card p {
  font-size: 1rem;
  line-height: 1.6;
  flex: 1;
}

.testimonial-author {
  margin-top: 0;
  padding-top: 0.5rem;
}

.testimonial-author h3 {
  font-size: 1.25rem;
  font-weight: 600;
}

.testimonial-author p {
  padding-top: 0;
  font-size: 1rem;
}

.cta-button {
  background-color: #d4681b;
  color: #fff;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
}

.cta-button:hover {
  background-color: #ca5e11;
  transform: translateY(-2px);
}
</style>
