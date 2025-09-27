// Supabase Edge Function for sending emails via Resend.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { Resend } from "resend";

// Initialize Resend with the API key from your Supabase project secrets
const resend = new Resend(Deno.env.get("RESEND_API_KEY"));

serve(async (req) => {
  // This function will be invoked with a POST request
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    // Parse the JSON payload from the request
    const { to, from, subject, html_content } = await req.json();

    // Validate the payload
    if (!to || !from || !subject || !html_content) {
      return new Response("Missing required fields in payload", { status: 400 });
    }

    // Send the email using Resend
    const { data, error } = await resend.emails.send({
      from: from,
      to: to,
      subject: subject,
      html: html_content,
    });

    if (error) {
      console.error("Error sending email:", error);
      return new Response(JSON.stringify(error), { status: 500 });
    }

    return new Response(JSON.stringify(data), { status: 200 });
  } catch (error) {
    console.error("An unexpected error occurred:", error);
    return new Response(`Error: ${error.message}`, { status: 500 });
  }
});