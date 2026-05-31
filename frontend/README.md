# Revela Frontend

This directory contains the isolated Vite React frontend for Revela.

## Run Locally

**Prerequisites:** Node.js

1. Install dependencies:

   `npm install`

2. Start the Vite development server:

   `npm run dev`

3. Open `http://127.0.0.1:3000`.

## Inference

The frontend uses the local educational mock by default. It does not require Express, Gemini, Hugging Face, or any API secrets for normal local use.

Live Hugging Face inference is optional and runs only when both browser-safe Vite variables are configured:

`VITE_REVELA_INFERENCE_BACKEND_URL="https://revelacap-revela-inference-backend.hf.space"`

`VITE_REVELA_ENABLE_LIVE_INFERENCE="true"`

If live inference is disabled, unavailable, or not configured, demo mode remains available.

## Vercel Deployment

Deploy this directory as a static Vite app. The Hugging Face Space remains the separate inference backend, and the legacy Streamlit app is not the Vercel frontend.

Vercel settings:

- Project root: `frontend`
- Framework preset: `Vite`
- Install command: `npm install`
- Build command: `npm run build`
- Output directory: `dist`
- Local dev command: `npm run dev`

Production environment variables:

```text
VITE_REVELA_INFERENCE_BACKEND_URL=https://revelacap-revela-inference-backend.hf.space
VITE_REVELA_ENABLE_LIVE_INFERENCE=true
```

If either variable is missing or live inference is disabled, the frontend falls back to demo mode without requiring the Hugging Face backend.
