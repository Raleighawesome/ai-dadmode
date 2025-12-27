# Contact Form & Hidden Booking Page Design

**Date:** 2025-12-27
**Status:** Approved

## Overview

Replace the public Cal.com booking page with a contact form. Move the booking functionality to a hidden, unlisted page for sharing directly with potential clients.

## Page Structure

```
/consulting          → Contact form (public, indexed)
/book/clients        → Cal.com booking (hidden, noindex)
```

Header nav "Work With Me" continues to link to `/consulting`.

## Contact Form Page (`/consulting`)

### Layout
- Keep existing "What You'll Get" benefit cards section
- Replace Cal.com embed with contact form

### Form Fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Name | text | yes | |
| Email | email | yes | validated |
| What do you need help with? | select | yes | dropdown |
| Message | textarea | yes | placeholder: "Tell me about your project..." |

### Dropdown Options
1. AI Workflow Setup
2. Custom Automation
3. Training/Consulting
4. Other

### Form Behavior
- Submit button shows loading state while sending
- Success: Form replaced with confirmation message ("Thanks! I'll get back to you soon.")
- Error: Inline error message, form stays filled for retry

### Styling
- Uses existing `.card`, `.btn-primary` components
- Form inputs: `bg-surface`, `border-border`, focus `border-accent`

## Email Backend

### API Route
`src/pages/api/contact.ts` (Astro API route)

### Request Flow
1. Form POSTs JSON to `/api/contact`
2. API validates fields
3. Sends email via Resend
4. Returns JSON response

### Email Format
- **To:** `RESEND_TO_EMAIL` env var
- **From:** `noreply@ai.dadmode.cc` or Resend default sender
- **Subject:** `[AI Tools] New inquiry: {project type}`
- **Body:** Formatted with name, email, project type, message

### Environment Variables
- `RESEND_API_KEY` - Resend API key
- `RESEND_TO_EMAIL` - Destination email address

## Hidden Booking Page (`/book/clients`)

### Protection
- `<meta name="robots" content="noindex, nofollow">`
- No internal links to this page
- Not in sitemap

### Content
- Header: "Book a Call"
- Brief intro text
- Cal.com inline embed (existing code)
- Back link to homepage

### Usage
Share this URL directly with clients after initial contact form inquiry.

## Implementation Files

### New Files
- `src/pages/api/contact.ts` - Resend API route
- `src/pages/book/clients.astro` - Hidden booking page
- `src/components/ContactForm.astro` - Contact form component

### Modified Files
- `src/pages/consulting.astro` - Replace Cal.com with ContactForm

### Dependencies
- `resend` npm package
