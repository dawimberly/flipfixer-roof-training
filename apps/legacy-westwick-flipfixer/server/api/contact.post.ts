import nodemailer from "nodemailer";

type ContactBody = {
  name?: string;
  email?: string;
  phone?: string;
  message?: string;
};

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const body = await readBody<ContactBody>(event);

  const name = body.name?.trim();
  const email = body.email?.trim();
  const phone = body.phone?.trim() || "Not provided";
  const message = body.message?.trim();

  if (!name || !email || !message) {
    throw createError({
      statusCode: 400,
      statusMessage: "Name, email, and message are required.",
    });
  }

  if (!config.smtpUser || !config.smtpAppPassword) {
    throw createError({
      statusCode: 503,
      statusMessage:
        "Contact form email is not configured yet. Please call 210-436-9117.",
    });
  }

  const transporter = nodemailer.createTransport({
    host: "smtp.gmail.com",
    port: 587,
    secure: false,
    auth: {
      user: config.smtpUser,
      pass: config.smtpAppPassword,
    },
  });

  const to = config.contactTo || config.smtpUser;

  await transporter.sendMail({
    from: `"Flip Fixer Website" <${config.smtpUser}>`,
    to,
    replyTo: email,
    subject: `Website contact form — ${name}`,
    text: [
      `Name: ${name}`,
      `Email: ${email}`,
      `Phone: ${phone}`,
      "",
      "Message:",
      message,
    ].join("\n"),
  });

  return { ok: true };
});
