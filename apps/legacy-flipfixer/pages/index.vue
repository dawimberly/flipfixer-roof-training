<template>
  <div class="bg-[#131517]">
    <!-- Hero Section -->
    <div class="px-4">
      <div class="hero-section homebg bg-cover">
        <h1 class="text-4xl md:text-6xl font-bold mb-4">
          Flip Fixer: We Can Fix It.
        </h1>
        <p class="text-xl md:text-2xl mb-8">
          Remodels, Make-Readys, and Handyman Services for San Antonio and
          Beyond
        </p>
        <NuxtLink to="/contact">
          <button class="cta-button px-8 py-4 text-lg rounded-lg">
            Schedule a Free Estimate
          </button></NuxtLink
        >
      </div>
    </div>

    <!-- Overview Section -->
    <section class="overview-section py-16 px-4 bg-[#131517]">
      <div class="container mx-auto max-w-3xl text-center">
        <p class="text-xl leading-relaxed text-gray-200">
          At Flip Fixer, we believe in delivering high-quality work with a
          professional attitude and a personal touch. With over 20 years of
          hands-on experience, we work efficiently to transform your space—on
          time and on budget.
        </p>
      </div>
    </section>

    <!-- Featured Services Section -->
    <section class="featured-services py-16 px-4 bg-[#131517]">
      <div class="container mx-auto max-w-6xl">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <!-- Each service card -->
          <div class="service-card-wrapper">
            <div class="icon-box">
              <ShowerHead size="42" strokeWidth="{1}" class="text-white" />
            </div>
            <div class="service-card">
              <h3>KITCHEN &amp; BATH REMODELS</h3>
              <p>
                Complete kitchen renovations including cabinets, countertops,
                flooring, and appliance installation. Modern designs with
                quality craftsmanship.
              </p>
            </div>
          </div>

          <div class="service-card-wrapper">
            <div class="icon-box">
              <PencilRuler size="42" strokeWidth="{1}" class="text-white" />
            </div>
            <div class="service-card">
              <h3>HANDYMAN SERVICES &amp; SMALL REPAIRS</h3>
              <p>
                From drywall patches to minor plumbing fixes, our team is ready
                to help.
              </p>
            </div>
          </div>

          <div class="service-card-wrapper">
            <div class="icon-box">
              <Hammer size="42" strokeWidth="{1}" class="text-white" />
            </div>
            <div class="service-card">
              <h3>FLOORING INSTALLATION</h3>
              <p>
                Professional installation of hardwood, laminate, tile, and vinyl
                flooring. Quality materials and precise installation.
              </p>
            </div>
          </div>

          <div class="service-card-wrapper">
            <div class="icon-box">
              <PaintRoller size="42" strokeWidth="{1}" class="text-white" />
            </div>
            <div class="service-card">
              <h3>INTERIOR &amp; EXTERIOR PAINTING</h3>
              <p>
                Interior and exterior painting with proper preparation and
                premium materials. Clean lines and lasting results.
              </p>
            </div>
          </div>

          <div class="service-card-wrapper">
            <div class="icon-box">
              <TreePalm size="42" strokeWidth="{1}" class="text-white" />
            </div>
            <div class="service-card">
              <h3>OUTDOOR PROJECTS</h3>
              <p>
                Decks, patios, landscaping elements — enhance your curb appeal
                and enjoy the outdoors in style. Custom lighting installations
                and more.
              </p>
            </div>
          </div>

          <div class="service-card-wrapper">
            <div class="icon-box">
              <HousePlus size="42" strokeWidth="{1}" class="text-white" />
            </div>
            <div class="service-card">
              <h3>MAKE-READY SERVICE</h3>
              <p>
                Need a quick turnaround for your rental or a house you're about
                to sell? We specialize in fast, efficient make-ready solutions.
              </p>
            </div>
          </div>
        </div>

        <!-- View All Services Button -->
        <div class="text-center mt-12">
          <NuxtLink to="/services">
            <button class="outline-button px-8 py-4 text-lg rounded-lg">
              View All Services
              <ChevronRight class="inline-block ml-2" size="20" />
            </button>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- Our Work Samples Section -->
    <section
      class="work-samples py-16 px-4 showcase-divider"
      style="background-color: #1c1e22; position: relative"
    >
      <div class="container mx-auto max-w-5xl">
        <h2 class="text-3xl font-bold text-center mb-12 text-[#f08330]">
          Our Work Showcase
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="gallery-preview">
            <img
              src="~/assets/images/kitchen2.jpg"
              alt="Kitchen Remodel"
              class="w-full h-80 object-cover rounded-lg"
            />
          </div>

          <div class="gallery-preview">
            <img
              src="~/assets/images/flooring.jpg"
              alt="Flooring Project"
              class="w-full h-80 object-cover rounded-lg"
            />
          </div>

          <div class="gallery-preview">
            <img
              src="~/assets/images/staircase.jpg"
              alt="Bathroom Project"
              class="w-full h-80 object-cover rounded-lg"
            />
          </div>

          <div class="gallery-preview">
            <img
              src="~/assets/images/patio.jpg"
              alt="Exterior Project"
              class="w-full h-80 object-cover rounded-lg"
            />
          </div>
        </div>

        <!-- Gallery Link Button -->
        <div class="text-center mt-12">
          <NuxtLink to="/gallery">
            <button class="outline-button px-8 py-4 text-lg rounded-lg">
              View Full Gallery
              <ChevronRight class="inline-block ml-2" size="20" />
            </button>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- Why Choose Us Section -->
    <section class="why-choose-us py-16 px-4 bg-stone-900">
      <div class="container mx-auto max-w-6xl">
        <h2 class="text-3xl font-bold text-center mb-12 text-gray-100">
          Why Choose Us
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div class="feature-card">
            <ShieldCheck size="64" class="mx-auto mb-4" color="#f08330" />
            <h3 class="text-xl font-semibold mb-2">Skilled and Trustworthy</h3>
            <p>
              Our team consists of licensed, insured, and experienced tradesmen.
            </p>
          </div>
          <div class="feature-card">
            <Timer size="64" class="mx-auto mb-4" color="#f08330" />
            <h3 class="text-xl font-semibold mb-2">Fast and Efficient</h3>
            <p>
              From quick repair jobs to full-scale remodels, we complete
              projects swiftly without compromising quality.
            </p>
          </div>
          <div class="feature-card">
            <BadgeDollarSign size="64" class="mx-auto mb-4" color="#f08330" />
            <h3 class="text-xl font-semibold mb-2">Competitive Pricing</h3>
            <p>
              By cutting out the middleman, we pass the savings on to you—so you
              get top-notch work at an affordable rate.
            </p>
          </div>
          <div class="feature-card">
            <Handshake size="64" class="mx-auto mb-4" color="#f08330" />
            <h3 class="text-xl font-semibold mb-2">Personalized Approach</h3>
            <p>
              We keep you informed every step of the way, ensuring the final
              result matches your vision.
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  Hammer,
  Timer,
  Wrench,
  ShieldCheck,
  Handshake,
  BadgeDollarSign,
  PaintRoller,
  HousePlus,
  TreePalm,
  PencilRuler,
  ShowerHead,
  ChevronRight,
} from "lucide-vue-next";

useHead({
  title: "Professional Home Improvement Services",
  meta: [
    {
      name: "description",
      content:
        "San Antonio's trusted partner for home improvements, remodels, and renovations. Professional solutions delivered with expertise and care.",
    },
  ],
});
</script>

<style scoped>
.homebg {
  background-image: url("assets/images/kitchen.jpg");
  height: 63vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
  color: white;
  position: relative;
  text-align: center;
  margin-top: 1rem;
  margin-bottom: 1rem;
}

.homebg::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.665); /* Dark overlay */
  z-index: 1;
}

.hero-section {
  position: relative;
}

/* Make sure the content appears above the overlay */
.hero-section > * {
  position: relative;
  z-index: 2;
}

h1 {
  color: #f08330;
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
  background-color: #ca5e11; /* Darker shade of the new orange */
  transform: translateY(-2px);
}

.feature-card {
  padding: 2rem;
  background-color: #131517;
  border: 1px solid #2d3238;
  border-radius: 0.5rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  color: #e5e5e5;
}

.service-card {
  transition: transform 0.3s ease-in-out;
  color: #e5e5e5;
}

.service-card h3 {
  color: #f08330;
}

.service-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
}

/* Add these new styles for better text contrast */
h2 {
  color: #f08c3f;
}

.text-xl {
  color: #e5e5e5;
}

p {
  color: #9ca3af;
}

.service-card-wrapper {
  position: relative;
  padding-top: 2rem;
  height: 100%;
}

.icon-box {
  position: absolute;
  top: 30px;
  left: 2rem;
  background-color: #c05b18;
  width: 80px;
  height: 80px;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transform: translateY(-50%);
}

.service-card {
  background-color: #0b0c0c;
  padding: 3rem 2rem 2rem;
  text-align: left;
  border-radius: 0.5rem;
  margin-top: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.service-card h3 {
  color: white;
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 1rem;
  margin-bottom: 1rem;
  letter-spacing: 0.025em;
}

.service-card p {
  color: #9ca3af;
  margin-bottom: 0;
  line-height: 1.6;
  flex-grow: 1;
}

.service-link {
  color: white;
  text-decoration: underline;
  font-weight: 500;
  display: inline-block;
}

/* Remove hover effects */
.service-card:hover {
  transform: none;
  box-shadow: none;
}

.gallery-preview {
  overflow: hidden;
  border-radius: 0.5rem;
  background-color: #0b0c0c;
  transition: transform 0.3s ease-in-out;
}

.gallery-preview img {
  transition: transform 0.5s ease-in-out;
}

.gallery-preview:hover img {
  transform: scale(1.05);
}

.gallery-preview h3 {
  color: #f08330;
  text-align: center;
  padding: 0 1rem 1.5rem;
}

.outline-button {
  background-color: transparent;
  color: #f08330;
  font-weight: 600;
  border: 2px solid #f08330;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.outline-button:hover {
  background-color: rgba(240, 131, 48, 0.1);
  transform: translateY(-2px);
}

.showcase-bg {
  background: linear-gradient(to bottom, #131517, #1a1c1e, #131517);
  position: relative;
}

.showcase-bg::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    rgba(240, 131, 48, 0.3),
    transparent
  );
}

.showcase-bg::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    rgba(240, 131, 48, 0.3),
    transparent
  );
}

.showcase-image-bg {
  /*background-image: url("assets/images/pattern-bg.jpg");*/
  background-size: cover;
  background-position: center;
  position: relative;
}

.showcase-image-bg::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(19, 21, 23, 0.92);
  z-index: 1;
}

.showcase-image-bg > div {
  position: relative;
  z-index: 2;
}

.showcase-divider::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    rgba(240, 131, 48, 0.3),
    transparent
  );
}

.showcase-divider::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    rgba(240, 131, 48, 0.3),
    transparent
  );
}
</style>
