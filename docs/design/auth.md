# Auth Page — Design Brief (Figma Make)

Design brief for the **Auth** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a responsive **authentication page** for **Mission Control System**, a drone fleet management platform for military units. The visual tone is **serious, tactical, and trustworthy** — a dark command-center aesthetic with high contrast, clean sans-serif type, and restrained accent color. Not playful. Think defense/aerospace operations software.

Build it as a **single centered card (max-width ~440px)** floating over a full-bleed dark background (subtle topographic/grid texture or a dimmed drone/field photo with a dark overlay). The card holds a logo mark + "Mission Control System" wordmark at the top, and swaps its body content across **five states** (design all five as frames):

### State 1 — Login (default)
- Heading: "Sign in"
- Fields: **Email** (text input, envelope icon), **Password** (input with show/hide toggle)
- Primary button (full-width): "Sign in"
- Secondary link, right-aligned under password: "Forgot password?"
- Inline error banner slot above the form (red, for "Invalid email or password")
- Footer note: small muted text, e.g. "Authorized personnel only"

### State 2 — Forgot Password (request reset)
- Heading: "Reset password"
- Supporting line: "Enter your email and we'll send you a reset link."
- Field: **Email**
- Primary button: "Send reset link"
- Back link: "← Back to sign in"
- Success confirmation variant: green banner "If that email exists, a reset link has been sent."

### State 3 — Reset Password Confirm (from email link)
- Heading: "Set a new password"
- Fields: **New password**, **Confirm new password** (both with show/hide)
- **Password strength meter** + requirements checklist (min length, etc.)
- Primary button: "Update password"
- Expired/invalid-token variant: error state with "This reset link is invalid or has expired" + "Request a new link" button

### State 4 — Account Activation
- Heading: "Activate your account"
- Loading variant: spinner + "Activating your account…"
- Success variant: green checkmark + "Your account is active" + "Continue to sign in" button
- Failure variant: error icon + "Activation link is invalid or expired"

### State 5 — Force Password Change (blocking)
- Shown after login when the account is flagged to change password.
- Heading: "Update your password to continue"
- Supporting line: "For security, you must set a new password before proceeding."
- Fields: **Current password**, **New password**, **Confirm new password** + strength meter
- Primary button: "Save and continue"
- No skip/close option (this screen is mandatory).

## Components & states to include
- Text input: default / focus / filled / error / disabled
- Primary button: default / hover / loading (spinner) / disabled
- Password field with show/hide eye toggle
- Alert banner: error (red), success (green), info (neutral)
- Password strength meter (weak → strong) with requirements checklist
- Loading spinner
- Logo/wordmark lockup

## Visual system
- **Theme:** dark mode primary. Background `#0B0F14`–`#111820`; card surface slightly lighter `#161D26` with 1px subtle border and soft shadow.
- **Accent:** a single tactical accent — muted amber/gold `#C8A24A` **or** signal green `#3FB950` for primary actions and focus rings (pick one; amber reads more military).
- **Text:** near-white `#E6EAF0` primary, muted `#8A94A6` secondary.
- **Status colors:** error `#E5484D`, success `#3FB950`.
- **Type:** Inter or IBM Plex Sans. Heading ~24px semibold, body 14–15px, labels 13px with optional uppercase tracking.
- **Radius:** 8px inputs/buttons, 12px card. Generous padding (24–32px inside card).
- **Layout:** vertically centered, single column, 16px field spacing. Mobile: card goes full-width with 16px side margins.

## Behavior notes (annotations, not visuals)
- Login authenticates via session + CSRF (email + password).
- Forgot/reset and activation are reached via emailed token links.
- Force-password-change is a mandatory interstitial triggered by the `must_change_password` flag — no navigation away until resolved.
