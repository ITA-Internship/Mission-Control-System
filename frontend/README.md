# Mission Control Frontend

React and TypeScript frontend for the Mission Control System.

## Requirements

Before starting the frontend, make sure the following tools are installed:

- Node.js LTS
- npm

Check the installed versions:

```bash
node --version
npm --version
```

## Local setup

Open the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create a local frontend environment file.

### PowerShell

```powershell
Copy-Item .env.example .env.local
```

### Git Bash

```bash
cp .env.example .env.local
```

Start the development server:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

## Backend connection

Frontend API requests use relative `/api` URLs by default.

During local development, the Vite development server proxies these requests to:

```text
http://127.0.0.1:8000
```

The proxy target is configured in `.env.local`:

```dotenv
API_PROXY_TARGET=http://127.0.0.1:8000
```

For the default local setup, leave `VITE_API_BASE_URL` empty:

```dotenv
VITE_API_BASE_URL=
```

This produces requests such as:

```text
http://localhost:5173/api/accounts/users/password-reset/
```

Vite then proxies them to the Django backend:

```text
http://127.0.0.1:8000/api/accounts/users/password-reset/
```

When the frontend must call a backend hosted on another origin directly, set the full backend URL:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Session-based requests use:

```text
credentials: include
```

Unsafe requests include the Django CSRF token when the CSRF cookie is available.

## Frontend environment variables

The frontend supports the following variables:

```dotenv
# Leave empty to call the API through the same origin.
VITE_API_BASE_URL=

# Used by the Vite development server as the local API proxy target.
API_PROXY_TARGET=http://127.0.0.1:8000

# Django CSRF cookie name.
VITE_CSRF_COOKIE_NAME=csrftoken

# Header used to send the Django CSRF token.
VITE_CSRF_HEADER_NAME=X-CSRFToken
```

Local values should be stored in:

```text
frontend/.env.local
```

Do not commit `.env.local` because it is intended for local configuration.

The reusable template is stored in:

```text
frontend/.env.example
```

## Backend environment configuration

The backend root `.env` file should contain the frontend URL:

```dotenv
FRONTEND_URL=http://localhost:5173
```

It should also trust both the backend and frontend local origins:

```dotenv
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173
```

`FRONTEND_URL` is used by the backend when generating password-reset and account-activation links.

For local development, those links should point to routes such as:

```text
http://localhost:5173/reset-password/<uid>/<token>
http://localhost:5173/activate/<userId>/<token>
```

## Available authentication routes

```text
/login
/forgot-password
/reset-password/:uid/:token
/activate/:userId/:token
/change-password/required
```

## Available commands

Start the development server:

```bash
npm run dev
```

Run ESLint:

```bash
npm run lint
```

Run TypeScript checks:

```bash
npm run typecheck
```

Create a production build:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

## Required checks before committing

Run all frontend checks:

```bash
npm run lint
npm run typecheck
npm run build
```

All commands must complete successfully before creating a commit.