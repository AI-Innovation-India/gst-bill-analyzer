# Deploy Frontend to Vercel

## Quick Deploy (5 minutes)

### Step 1: Sign up/Login to Vercel
1. Go to https://vercel.com
2. Click "Sign Up" or "Login"
3. Choose "Continue with GitHub"
4. Authorize Vercel to access your GitHub account

### Step 2: Import Project
1. Click "Add New..." → "Project"
2. Find "gst-bill-analyzer" in the list
3. Click "Import"

### Step 3: Configure Build Settings
Vercel will auto-detect the settings, but verify:

- **Framework Preset**: Vite
- **Root Directory**: `ui_code`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### Step 4: Add Environment Variables
Click "Environment Variables" and add:

**Variable Name**: `VITE_API_BASE_URL`
**Value**: `https://gst-analyzer-api.onrender.com`

### Step 5: Deploy
1. Click "Deploy"
2. Wait 2-3 minutes for build to complete
3. You'll get a URL like: `https://gst-bill-analyzer.vercel.app`

### Step 6: Test Your Deployment
1. Open the Vercel URL
2. Upload a bill (PDF or image)
3. Check if analysis shows GST breakdown
4. Verify HSN/SAC codes display correctly
5. Test GST Lookup tab

## 🎉 Done!

Your GST Bill Analyzer is now live and you can share the URL with anyone!

**Backend**: https://gst-analyzer-api.onrender.com
**Frontend**: https://gst-bill-analyzer.vercel.app (your actual URL)

## Troubleshooting

### CORS Errors
If you see CORS errors in browser console:
- Backend already has `ALLOWED_ORIGINS: "*"` in render.yaml
- Should work automatically

### API Connection Failed
1. Check backend is live: https://gst-analyzer-api.onrender.com/gst/items
2. Verify environment variable in Vercel dashboard
3. Check browser console for exact error

### Build Fails
1. Check Node.js version (Vercel uses Node 18 by default)
2. Ensure `ui_code/package.json` exists
3. Check build logs in Vercel dashboard

## Custom Domain (Optional)

To use your own domain:
1. Go to Project Settings → Domains
2. Add your domain
3. Configure DNS records as shown
4. SSL certificate auto-generated
