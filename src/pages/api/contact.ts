import type { APIRoute } from 'astro';
import { Resend } from 'resend';

export const prerender = false;

interface ContactForm {
  name: string;
  email: string;
  projectType: string;
  message: string;
}

function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateForm(data: unknown): { valid: true; form: ContactForm } | { valid: false; error: string } {
  if (!data || typeof data !== 'object') {
    return { valid: false, error: 'Invalid request body' };
  }

  const { name, email, projectType, message } = data as Record<string, unknown>;

  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    return { valid: false, error: 'Name is required' };
  }

  if (!email || typeof email !== 'string' || !validateEmail(email)) {
    return { valid: false, error: 'Valid email is required' };
  }

  if (!projectType || typeof projectType !== 'string') {
    return { valid: false, error: 'Project type is required' };
  }

  if (!message || typeof message !== 'string' || message.trim().length === 0) {
    return { valid: false, error: 'Message is required' };
  }

  return {
    valid: true,
    form: {
      name: name.trim(),
      email: email.trim(),
      projectType,
      message: message.trim(),
    },
  };
}

export const POST: APIRoute = async ({ request }) => {
  const apiKey = import.meta.env.RESEND_API_KEY;
  const toEmail = import.meta.env.RESEND_TO_EMAIL;

  if (!apiKey || !toEmail) {
    console.error('Missing RESEND_API_KEY or RESEND_TO_EMAIL environment variables');
    return new Response(JSON.stringify({ error: 'Server configuration error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const validation = validateForm(body);
  if (!validation.valid) {
    return new Response(JSON.stringify({ error: validation.error }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const { name, email, projectType, message } = validation.form;

  const resend = new Resend(apiKey);

  try {
    await resend.emails.send({
      from: 'AI Tools <onboarding@resend.dev>',
      to: toEmail,
      replyTo: email,
      subject: `[AI Tools] New inquiry: ${projectType}`,
      text: `New contact form submission:

Name: ${name}
Email: ${email}
Project Type: ${projectType}

Message:
${message}
`,
    });

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Failed to send email:', error);
    return new Response(JSON.stringify({ error: 'Failed to send message' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
