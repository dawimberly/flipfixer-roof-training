// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss", "@nuxt/fonts"],
  app: {
    pageTransition: { name: "page", mode: "out-in" },
  },
  runtimeConfig: {
    smtpUser: process.env.SMTP_USER || "",
    smtpAppPassword: process.env.SMTP_APP_PASSWORD || "",
    contactTo: process.env.CONTACT_TO || "jon@theflipfixer.com",
  },
});
