# Sahayak AI — Global Hosting & Deployment Guide

This guide explains how to host and share the **Sahayak AI Touch Screen Kiosk** and **Citizen Mobile Companion Dashboard** with a public link so anyone anywhere in the world can access it.

---

## ⚡ Option 1: Instant Live Link (Active Right Now!)

A high-speed **Cloudflare Global Tunnel** is already running live for your local server with zero password requirements, zero interstitial screens, and SSL encryption.

- 🖥️ **Touch Screen Kiosk:**
  [https://postposted-banana-license-english.trycloudflare.com/kiosk/](https://postposted-banana-license-english.trycloudflare.com/kiosk/)
- 📱 **Citizen Mobile Dashboard (GIGW 3.0 Portal):**
  [https://postposted-banana-license-english.trycloudflare.com/mobile/](https://postposted-banana-license-english.trycloudflare.com/mobile/)
- ⚙️ **Admin Monitoring UI:**
  [https://postposted-banana-license-english.trycloudflare.com/admin-ui/](https://postposted-banana-license-english.trycloudflare.com/admin-ui/)

> **How to run this tunnel anytime on your machine:**
> 1. Start the backend: `cd backend; .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
> 2. In another terminal, run: `npx cloudflared tunnel --url http://localhost:8000`

---

## 🌐 Option 2: Permanent 24/7 Cloud Hosting on Render (Recommended & Free)

To host your project 24/7 so it stays online even when your computer is turned off:

### Step 1: Push Project to GitHub
1. Create a new repository on [GitHub](https://github.com/new) (e.g. `sahayak-ai`).
2. In your project directory, push your code:
   ```bash
   git init
   git add .
   git commit -m "feat: complete sahayak-ai kiosk & mobile platform"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/sahayak-ai.git
   git push -u origin main
   ```

### Step 2: Deploy on Render.com (Free)
1. Go to [Render.com](https://render.com) and sign up / log in with GitHub.
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select your **`sahayak-ai`** GitHub repository.
4. Render will auto-detect the configuration:
   - **Environment:** `Docker` (uses our optimized [`Dockerfile`](./Dockerfile))
   - **Plan:** `Free`
5. Click **Create Web Service**.
6. Render will automatically build and deploy your app. Within 2–3 minutes, you will get a permanent public link:
   - `https://sahayak-ai.onrender.com/kiosk/`
   - `https://sahayak-ai.onrender.com/mobile/`

---

## 🚀 Option 3: Deploy on Railway / Fly.io / Hugging Face Spaces

The project is pre-configured with:
- [`Dockerfile`](./Dockerfile) for universal container hosting.
- [`Procfile`](./Procfile) for web process runners.
- [`render.yaml`](./render.yaml) for infrastructure-as-code deployments.

### Railway (Instant 1-Click)
1. Visit [railway.app](https://railway.app).
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select `sahayak-ai` $\rightarrow$ Railway builds the Docker image and generates a live public domain.

### Hugging Face Spaces (Free Docker 24/7)
1. Create a new Space on [huggingface.co/spaces](https://huggingface.co/spaces).
2. Select **Docker** SDK.
3. Push this repository $\rightarrow$ instantly accessible at `https://huggingface.co/spaces/<user>/sahayak-ai`.
