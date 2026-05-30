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

The frontend currently uses an isolated local educational mock for case analysis. It does not require Express, Gemini, or any API secrets for normal local use.

Future production inference should be wired through a Revela Hugging Face backend API client.
