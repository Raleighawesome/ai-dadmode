# Contact Form Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace public Cal.com booking with contact form, move booking to hidden page.

**Architecture:** Astro page with client-side form JS submits to `/api/contact` serverless endpoint. Resend handles email delivery. Hidden booking page at `/book/clients` with noindex meta tag.

**Tech Stack:** Astro (hybrid output for API routes), Resend SDK, Vercel serverless

---

## Task 1: Configure Astro for Hybrid Output

**Files:**
- Modify: `astro.config.mjs`
- Modify: `package.json`

**Step 1: Install Vercel adapter**

Run: `npm install @astrojs/vercel`

**Step 2: Update Astro config for hybrid output**

Replace contents of `astro.config.mjs`:

```javascript
// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import vercel from '@astrojs/vercel';

// https://astro.build/config
export default defineConfig({
  output: 'hybrid',
  adapter: vercel(),
  vite: {
    plugins: [tailwindcss()]
  }
});
```

**Step 3: Verify build works**

Run: `npm run build`
Expected: Build succeeds with hybrid output

**Step 4: Commit**

```bash
git add astro.config.mjs package.json package-lock.json
git commit -m "chore: configure Astro hybrid output with Vercel adapter"
```

---

## Task 2: Install Resend and Create API Route

**Files:**
- Create: `src/pages/api/contact.ts`

**Step 1: Install Resend**

Run: `npm install resend`

**Step 2: Create the API route**

Create `src/pages/api/contact.ts`:

```typescript
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
```

**Step 3: Create `.env.example`**

Create `.env.example`:

```
RESEND_API_KEY=re_xxxxxxxxxxxxx
RESEND_TO_EMAIL=your@email.com
```

**Step 4: Commit**

```bash
git add src/pages/api/contact.ts .env.example
git commit -m "feat: add contact form API route with Resend"
```

---

## Task 3: Create ContactForm Component

**Files:**
- Create: `src/components/ContactForm.astro`

**Step 1: Create the component**

Create `src/components/ContactForm.astro`:

```astro
---

---

<div id="contact-form-container">
  <form id="contact-form" class="space-y-6">
    <div>
      <label for="name" class="block text-sm font-medium text-text-primary mb-2">Name</label>
      <input
        type="text"
        id="name"
        name="name"
        required
        class="w-full px-4 py-3 bg-surface border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors"
        placeholder="Your name"
      />
    </div>

    <div>
      <label for="email" class="block text-sm font-medium text-text-primary mb-2">Email</label>
      <input
        type="email"
        id="email"
        name="email"
        required
        class="w-full px-4 py-3 bg-surface border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors"
        placeholder="you@example.com"
      />
    </div>

    <div>
      <label for="projectType" class="block text-sm font-medium text-text-primary mb-2">What do you need help with?</label>
      <select
        id="projectType"
        name="projectType"
        required
        class="w-full px-4 py-3 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:border-accent transition-colors"
      >
        <option value="">Select an option...</option>
        <option value="AI Workflow Setup">AI Workflow Setup</option>
        <option value="Custom Automation">Custom Automation</option>
        <option value="Training/Consulting">Training/Consulting</option>
        <option value="Other">Other</option>
      </select>
    </div>

    <div>
      <label for="message" class="block text-sm font-medium text-text-primary mb-2">Message</label>
      <textarea
        id="message"
        name="message"
        required
        rows="5"
        class="w-full px-4 py-3 bg-surface border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-accent transition-colors resize-none"
        placeholder="Tell me about your project..."
      ></textarea>
    </div>

    <div id="form-error" class="hidden p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm"></div>

    <button
      type="submit"
      id="submit-btn"
      class="btn-primary w-full"
    >
      <span id="submit-text">Send Message</span>
      <span id="submit-loading" class="hidden">Sending...</span>
    </button>
  </form>

  <div id="form-success" class="hidden text-center py-8">
    <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
      <svg class="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
    </div>
    <h3 class="text-xl font-semibold text-text-primary mb-2">Thanks for reaching out!</h3>
    <p class="text-text-secondary">I'll get back to you soon.</p>
  </div>
</div>

<script>
  const form = document.getElementById('contact-form') as HTMLFormElement;
  const formContainer = document.getElementById('contact-form-container');
  const formSuccess = document.getElementById('form-success');
  const formError = document.getElementById('form-error');
  const submitBtn = document.getElementById('submit-btn') as HTMLButtonElement;
  const submitText = document.getElementById('submit-text');
  const submitLoading = document.getElementById('submit-loading');

  function setLoading(loading: boolean) {
    submitBtn.disabled = loading;
    submitText?.classList.toggle('hidden', loading);
    submitLoading?.classList.toggle('hidden', !loading);
  }

  function showError(message: string) {
    if (formError) {
      formError.textContent = message;
      formError.classList.remove('hidden');
    }
  }

  function hideError() {
    formError?.classList.add('hidden');
  }

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    setLoading(true);

    const formData = new FormData(form);
    const data = {
      name: formData.get('name'),
      email: formData.get('email'),
      projectType: formData.get('projectType'),
      message: formData.get('message'),
    };

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to send message');
      }

      // Success - show confirmation
      form.classList.add('hidden');
      formSuccess?.classList.remove('hidden');

      // Track in Umami
      if (typeof umami !== 'undefined') {
        umami.track('contact-form-submit');
      }
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  });
</script>
```

**Step 2: Commit**

```bash
git add src/components/ContactForm.astro
git commit -m "feat: add ContactForm component with validation and loading states"
```

---

## Task 4: Create Hidden Booking Page

**Files:**
- Create: `src/pages/book/clients.astro`

**Step 1: Create the hidden booking page**

Create `src/pages/book/clients.astro`:

```astro
---
import BaseLayout from '../../layouts/BaseLayout.astro';
---

<BaseLayout title="Book a Call">
  <head slot="head">
    <meta name="robots" content="noindex, nofollow" />
  </head>

  <section class="pt-32 pb-20">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <h1 class="text-4xl sm:text-5xl font-bold text-text-primary mb-6">
          Book a Call
        </h1>
        <p class="text-lg text-text-secondary max-w-2xl mx-auto">
          Pick a time that works for you. Looking forward to chatting!
        </p>
      </div>

      <!-- Cal.com Embed -->
      <div class="card">
        <div
          id="cal-embed"
          class="rounded-lg overflow-hidden"
          style="width:100%"
        ></div>
      </div>

      <!-- Back link -->
      <div class="text-center mt-12">
        <a href="/" class="text-accent hover:text-accent-hover transition-colors">
          ← Back to Home
        </a>
      </div>
    </div>
  </section>

  <!-- Cal.com embed script -->
  <script is:inline>
    (function (C, A, L) {
      let p = function (a, ar) {
        a.q.push(ar);
      };
      let d = C.document;
      C.Cal =
        C.Cal ||
        function () {
          let cal = C.Cal;
          let ar = arguments;
          if (!cal.loaded) {
            cal.ns = {};
            cal.q = cal.q || [];
            d.head.appendChild(d.createElement("script")).src = A;
            cal.loaded = true;
          }
          if (ar[0] === L) {
            const api = function () {
              p(api, arguments);
            };
            const namespace = ar[1];
            api.q = api.q || [];
            if (typeof namespace === "string") {
              cal.ns[namespace] = cal.ns[namespace] || api;
              p(cal.ns[namespace], ar);
              p(cal, ["initNamespace", namespace]);
            } else p(cal, ar);
            return;
          }
          p(cal, ar);
        };
    })(window, "https://app.cal.com/embed/embed.js", "init");

    Cal("init", "ai-tools", { origin: "https://cal.com" });

    Cal.ns["ai-tools"]("inline", {
      elementOrSelector: "#cal-embed",
      calLink: "eriknewby",
      layout: "month_view",
      config: {
        theme: "dark",
      },
    });

    Cal.ns["ai-tools"]("ui", {
      theme: "dark",
      styles: {
        branding: { brandColor: "#3b82f6" },
      },
      hideEventTypeDetails: false,
      layout: "month_view",
    });
  </script>
</BaseLayout>
```

**Step 2: Update BaseLayout to support head slot**

Modify `src/layouts/BaseLayout.astro` - add slot inside head tag after existing content:

Find this line:
```astro
    <title>{title} | AI Tools</title>
```

Add after it:
```astro
    <slot name="head" />
```

**Step 3: Commit**

```bash
git add src/pages/book/clients.astro src/layouts/BaseLayout.astro
git commit -m "feat: add hidden booking page at /book/clients with noindex"
```

---

## Task 5: Update Consulting Page

**Files:**
- Modify: `src/pages/consulting.astro`

**Step 1: Replace Cal.com embed with ContactForm**

Replace the entire contents of `src/pages/consulting.astro`:

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import ContactForm from '../components/ContactForm.astro';
---

<BaseLayout title="Work With Me">
  <section class="pt-32 pb-20">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <h1 class="text-4xl sm:text-5xl font-bold text-text-primary mb-6">
          Let's Build Your AI Workflow
        </h1>
        <p class="text-lg text-text-secondary max-w-2xl mx-auto">
          Get personalized help setting up AI tools and automation. I'll guide you through the entire process and customize it for your specific needs.
        </p>
      </div>

      <!-- What You Get -->
      <div class="mb-16">
        <h2 class="text-2xl font-bold text-text-primary mb-6 text-center">What You'll Get</h2>
        <div class="grid md:grid-cols-2 gap-6">
          <div class="card">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-text-primary mb-1">Custom Configuration</h3>
                <p class="text-text-secondary text-sm">Tailored setup for your tools, AI provider, and workflow preferences.</p>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-text-primary mb-1">Fast Implementation</h3>
                <p class="text-text-secondary text-sm">Skip the trial-and-error. Get up and running in hours, not weeks.</p>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-text-primary mb-1">Ongoing Support</h3>
                <p class="text-text-secondary text-sm">Get answers to questions and troubleshoot issues as they arise.</p>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 class="font-semibold text-text-primary mb-1">Best Practices</h3>
                <p class="text-text-secondary text-sm">Learn the workflows and techniques that make AI automation actually useful.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Contact Form -->
      <div class="card">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-text-primary mb-2">Get in Touch</h2>
          <p class="text-text-secondary">
            Tell me about your project and I'll get back to you soon.
          </p>
        </div>

        <ContactForm />
      </div>

      <!-- Back link -->
      <div class="text-center mt-12">
        <a href="/" class="text-accent hover:text-accent-hover transition-colors">
          ← Back to Home
        </a>
      </div>
    </div>
  </section>
</BaseLayout>
```

**Step 2: Verify the page renders**

Run: `npm run dev`
Visit: `http://localhost:4321/consulting`
Expected: Page shows benefit cards and contact form

**Step 3: Commit**

```bash
git add src/pages/consulting.astro
git commit -m "feat: replace Cal.com booking with contact form on consulting page"
```

---

## Task 6: Test End-to-End

**Step 1: Create local `.env` file**

Create `.env` with your Resend credentials:

```
RESEND_API_KEY=re_your_actual_key
RESEND_TO_EMAIL=your@email.com
```

**Step 2: Test the form locally**

Run: `npm run dev`
Visit: `http://localhost:4321/consulting`
- Fill out the form with test data
- Submit
- Expected: Success message appears, email received

**Step 3: Test the hidden booking page**

Visit: `http://localhost:4321/book/clients`
- Expected: Cal.com calendar loads
- View page source, confirm `<meta name="robots" content="noindex, nofollow">` is present

**Step 4: Build for production**

Run: `npm run build`
Expected: Build succeeds

**Step 5: Final commit**

```bash
git add .env.example
git commit -m "docs: update .env.example with Resend variables"
```

---

## Post-Implementation: Vercel Configuration

After deploying to Vercel:

1. Add environment variables in Vercel dashboard:
   - `RESEND_API_KEY`
   - `RESEND_TO_EMAIL`

2. (Optional) For custom from address, verify domain in Resend:
   - Add `ai.dadmode.cc` to Resend
   - Update API route `from` field to `AI Tools <noreply@ai.dadmode.cc>`
