# My Profile — Design Brief (Figma Make)

Design brief for the **My Profile** page from the [Client Pages Proposal](../client_pages_proposal.md). Written to be pasted into Figma Make.

## Prompt (paste into Figma Make)

Design a **user profile & account settings page** for **Mission Control System**, a drone fleet management platform for military units. Serious, tactical command-center aesthetic — dark theme, high contrast, clean and orderly. Think defense/aerospace operations software, not a consumer social profile.

Use the shared **app shell** (left sidebar nav + top bar; see Dashboard brief). The profile lives in the main content area, reached from the top-bar user menu.

### Page header
- Page title: "My Profile".
- A **profile summary band** at the top: circular **avatar** (with an edit/upload overlay on hover), full name, **rank**, a **role badge** (Admin / Commander / Dispatcher / Operator / Technician / Viewer), and the assigned **military unit**. Email shown as secondary muted text.

### Layout
A two-column layout on desktop (stacks to one column on mobile): a left **section nav / anchor list** and a right content area with cards. Sections:

### Section 1 — Profile Details (card)
- **Read view:** avatar, full name, rank, contact info, email (read-only, muted — email is the login identity), military unit (read-only), role (read-only).
- **Edit view:** editable fields for rank, contact; avatar upload control. Email/unit/role are display-only (managed by administrators). Primary "Save changes" + "Cancel".
- Success toast/banner on save.

### Section 2 — Avatar (within Profile Details or its own card)
- Current avatar preview with an **Upload / Replace** control (dropzone or file picker) and a **Remove** action.
- Accepted formats note (image types) and a small crop/preview step.
- States: idle / uploading / success / error (invalid type or too large).

### Section 3 — Change Password (card)
- Fields: **Current password**, **New password**, **Confirm new password** (all with show/hide toggles).
- **Password strength meter** + requirements checklist (min length, etc.).
- Primary button: "Update password".
- Inline error banner (e.g. "Current password is incorrect") and success banner.

### Section 4 — Account & Security info (read-only card)
- Account status (Active pill), date joined / created-by (if available), last login.
- Muted, informational — no editable controls.

## Components & states to include
- Avatar with hover edit overlay; upload control: idle / dragging / uploading / success / error
- Role badge (one variant per role) and unit chip
- Read-only field vs. editable input (with label)
- Text input: default / focus / filled / error / disabled
- Password field with show/hide toggle + strength meter + requirements checklist
- Primary / secondary buttons: default / hover / loading / disabled
- Alert banner: error (red), success (green), info (neutral); toast on save
- Card/section container with header
- Loading skeleton and empty/placeholder avatar state

## Visual system
- **Theme:** dark mode. App background `#0B0F14`; cards `#161D26` with 1px subtle border; profile summary band slightly elevated.
- **Accent:** muted amber/gold `#C8A24A` for primary actions, links, focus rings.
- **Text:** primary `#E6EAF0`, secondary/muted `#8A94A6`; read-only values in muted tone.
- **Status colors:** error `#E5484D`, success `#3FB950`; Active status pill green.
- **Role badges:** distinct but restrained — e.g. Admin amber, Commander blue `#4C8DFF`, others neutral grey `#8A94A6`; keep consistent with app-wide usage.
- **Type:** Inter or IBM Plex Sans. Name ~20–24px semibold, section titles 16px semibold, labels 13px, body 14px.
- **Radius:** 12px cards, 8px inputs/buttons, avatar fully round, badges/pills fully rounded.
- **Layout:** max content width ~960px, 24px padding, 16px field spacing.

## Behavior notes (annotations, not visuals)
- Reads/writes own profile via `users/me/`; avatar via `users/<id>/profile-picture/` (protected image).
- Change-password posts to `users/me/change-password/`.
- Email, military unit, and role are **not** self-editable — they are administrator-managed; show them read-only.
- This page reuses the password strength meter and change-password form pattern from the [Auth](auth.md) brief.
