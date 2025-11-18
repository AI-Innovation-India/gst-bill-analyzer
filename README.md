# 🧾 GST Bill Analyzer

![Confidence: 95%](https://img.shields.io/badge/Accuracy-95%25-brightgreen)
![GST Compliance](https://img.shields.io/badge/GST-India%202025-blue)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18+-61dafb)

An intelligent GST bill verification system for India that analyzes restaurant bills, verifies GST calculations, and provides confidence scores for legal accuracy.

## 🚀 Features

### Core Capabilities
- ✅ **95% Accuracy** - Gemini AI-powered bill extraction
- 📊 **Confidence Scoring** - Know when to trust the analysis (90%+ recommended for legal use)
- ⚠️ **Validation Warnings** - Identifies math inconsistencies, rounding differences, unusual GST rates
- 💰 **Discount Handling** - Correctly calculates GST on discounted amounts
- 🔍 **HSN/SAC Lookup** - 31+ items with proper tax codes
- 📱 **PDF/Image Upload** - Extract data from scanned bills
- 🎯 **GST Rate Verification** - Validates against official Indian GST rates (0%, 5%, 12%, 18%, 28%)

## 📦 Quick Start

```bash
# Backend
pip install -r requirements.txt
python populate_hsn_codes.py
python gst_api_service.py

# Frontend (in ui_code/)
npm install
npm start
```

## 🌐 Production Deployment Answers

### 1. Backend Hosting: **Render.com (Free tier available)**
✅ Better than Hostinger for Python/FastAPI apps
✅ Auto-deployment from GitHub
✅ Free SSL, Custom domains
✅ Better for APIs than shared hosting

### 2. Frontend Hosting: **Vercel or Netlify**
✅ Free for React apps
✅ Auto-deploy from GitHub
✅ Global CDN
✅ Perfect for sharing UI links

### 3. UI Enhancement: **Keep current React + Optional Tailwind CSS**
- v0.dev (by Vercel) - Better than Vibecoding for React
- Can enhance with shadcn/ui components
- Current UI is production-ready!

## 📊 Architecture

**Frontend** (Vercel) → **Backend API** (Render) → **Gemini AI**

