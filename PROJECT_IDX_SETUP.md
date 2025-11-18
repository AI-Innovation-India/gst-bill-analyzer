# 🎨 Project IDX Setup Guide - GST Bill Analyzer UI

## What is Project IDX?

Project IDX is Google's AI-powered cloud development environment. It's perfect for building your GST Bill Analyzer UI because:

- ✅ **Free to use** (no credit card required)
- ✅ **AI coding assistant built-in** (like having me help you code!)
- ✅ **Zero setup** - works in your browser
- ✅ **Preview apps instantly**
- ✅ **Integrated with Firebase** (for easy deployment)

---

## 🚀 Step 1: Access Project IDX

1. Go to: **https://idx.google.com**
2. Sign in with your Google account
3. Click **"Create New Project"** or **"Import from GitHub"**

---

## 🎯 Step 2: Choose Your Tech Stack

### Recommended: **React + Vite** (Fast, Modern)

**Why React?**
- ✅ Easy to learn
- ✅ Great for forms and interactive UIs
- ✅ Perfect for file uploads (bill PDFs/images)
- ✅ Huge community support

**Alternative Options:**
- **Next.js** (if you want server-side rendering)
- **Vue** (simpler than React)
- **Angular** (more structured)

**For your use case, I recommend React + Vite!**

---

## 📁 Step 3: Project Structure

Here's what your GST Bill Analyzer UI will look like:

```
gst-bill-analyzer-ui/
├── src/
│   ├── App.jsx              # Main app component
│   ├── main.jsx             # Entry point
│   ├── components/
│   │   ├── BillUploader.jsx     # Upload bill (PDF/image/text)
│   │   ├── BillAnalyzer.jsx     # Show analysis results
│   │   ├── GSTLookup.jsx        # Search GST database
│   │   └── DiscrepancyReport.jsx # Show GST errors
│   ├── services/
│   │   └── api.js           # API calls to your FastAPI backend
│   └── styles/
│       └── App.css          # Styling
├── public/
│   └── index.html
├── package.json
└── vite.config.js
```

---

## 💻 Step 4: Create Your First UI Component

### Option A: In Project IDX

1. Click **"New Project"** → **"React + Vite"**
2. Wait for workspace to initialize
3. Project IDX will create the base template automatically!

### Option B: Manual Setup (if needed)

If you want to set it up yourself:

```bash
npm create vite@latest gst-bill-analyzer-ui -- --template react
cd gst-bill-analyzer-ui
npm install
npm install axios  # For API calls
```

---

## 🎨 Step 5: UI Features You'll Build

### Feature 1: Bill Upload
- Upload PDF, image, or paste text
- Preview the uploaded bill
- Send to Gemini analyzer

### Feature 2: GST Lookup
- Search by item name
- Show HSN code, GST rate, category
- Browse all 46 items in database

### Feature 3: Bill Analysis Results
- Display extracted items
- Show correct vs charged GST
- Highlight discrepancies in red

### Feature 4: Discrepancy Report
- Visual comparison table
- Amount overcharged/undercharged
- Downloadable PDF report

---

## 🔌 Step 6: Connect to Your Backend

Your FastAPI backend is running on `http://127.0.0.1:8001`

**API Endpoints to use:**

1. **GET /gst/{hsn_code}** - Lookup single item
2. **GET /gst/items** - Get all items
3. **GET /gst/search/{query}** - Search items
4. **POST /gst/analyze-bill** - Analyze bill with Gemini

Example API call in React:

```javascript
// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8001';

export const analyzeBill = async (billText) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/gst/analyze-bill`, {
      bill_text: billText
    });
    return response.data;
  } catch (error) {
    console.error('Error analyzing bill:', error);
    throw error;
  }
};

export const searchGST = async (query) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/gst/search/${query}`);
    return response.data;
  } catch (error) {
    console.error('Error searching GST:', error);
    throw error;
  }
};
```

---

## 🎯 Step 7: Using AI in Project IDX

Project IDX has **Gemini Code Assist** built-in!

**How to use it:**

1. **Press `Ctrl + I`** (or `Cmd + I` on Mac) to open AI chat
2. **Ask questions like:**
   - "Create a file upload component for PDFs and images"
   - "Add a table to display bill items with GST rates"
   - "Style this component to look like a receipt"
   - "Add error handling for failed API calls"

3. **AI will generate code for you!** Just like I would!

---

## 📝 Step 8: Example - Simple Bill Uploader Component

Here's what your first component might look like:

```jsx
// src/components/BillUploader.jsx
import React, { useState } from 'react';
import axios from 'axios';

function BillUploader() {
  const [billText, setBillText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://127.0.0.1:8001/gst/analyze-bill', {
        bill_text: billText
      });
      setResult(response.data);
    } catch (error) {
      alert('Error analyzing bill: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bill-uploader">
      <h2>📄 Upload Your Bill</h2>

      <textarea
        value={billText}
        onChange={(e) => setBillText(e.target.value)}
        placeholder="Paste your restaurant bill here..."
        rows={10}
        style={{ width: '100%', padding: '10px', fontSize: '14px' }}
      />

      <button
        onClick={handleAnalyze}
        disabled={loading || !billText}
        style={{ marginTop: '10px', padding: '10px 20px' }}
      >
        {loading ? 'Analyzing...' : 'Analyze Bill'}
      </button>

      {result && (
        <div className="results" style={{ marginTop: '20px' }}>
          <h3>Results:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default BillUploader;
```

---

## 🚀 Step 9: Run Your UI

In Project IDX terminal:

```bash
npm run dev
```

Project IDX will show you a **live preview** of your app!

---

## 🎨 Step 10: Make It Look Good

### CSS Frameworks to Use:

**Option 1: Tailwind CSS** (Recommended)
```bash
npm install -D tailwindcss
npx tailwindcss init
```

**Option 2: Material-UI** (Google's design)
```bash
npm install @mui/material @emotion/react @emotion/styled
```

**Option 3: Bootstrap**
```bash
npm install bootstrap
```

**Pro tip:** Ask Project IDX AI to style your components!
- "Style this component using Tailwind CSS"
- "Make this look like a modern dashboard"

---

## 🔐 Step 11: Environment Variables

Store your Gemini API key securely:

1. Create `.env` file in Project IDX:
```
VITE_GOOGLE_API_KEY=your_api_key_here
VITE_API_BASE_URL=http://127.0.0.1:8001
```

2. Use in your code:
```javascript
const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY;
```

---

## 📱 Step 12: Features to Build (Priority Order)

### Phase 1: Basic (Start Here)
1. ✅ Text bill input + analyze button
2. ✅ Display results in table
3. ✅ Show GST discrepancies

### Phase 2: Enhanced
4. ✅ PDF/image upload support
5. ✅ GST database search
6. ✅ Item-by-item breakdown

### Phase 3: Advanced
7. ✅ Download report as PDF
8. ✅ Save analysis history
9. ✅ Charts/graphs for GST breakdown
10. ✅ Mobile responsive design

---

## 🎁 Step 13: Project IDX Tips & Tricks

1. **Use AI copilot constantly**
   - Type a comment describing what you want, AI will generate code
   - Example: `// Create a table showing bill items with GST rates`

2. **Preview updates live**
   - Changes appear instantly in preview pane
   - No need to refresh browser

3. **Terminal access**
   - Run `npm` commands
   - Install packages
   - Run your FastAPI backend (if needed)

4. **Version control**
   - Project IDX has Git built-in
   - Commit your changes as you go

5. **Share your app**
   - Click "Preview" → Get shareable URL
   - Share with others to test

---

## 🐛 Troubleshooting

### CORS Errors
If you get CORS errors when calling your API:

**Fix in FastAPI** (add to `gst_api_service.py`):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origin from Project IDX
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Connection Failed
- Make sure your FastAPI is running: `uvicorn gst_api_service:app --host 127.0.0.1 --port 8001`
- Check if Project IDX can reach `127.0.0.1:8001`
- If not, you might need to deploy your API to a public URL

### Project IDX Won't Load
- Clear browser cache
- Try incognito mode
- Use Chrome (works best)

---

## 🚀 Next Steps After Setup

1. **Test the basic UI** with sample bills
2. **Add file upload** for PDFs/images
3. **Improve styling** with Tailwind/Material-UI
4. **Deploy to Firebase** (Project IDX makes this easy!)
5. **Add user authentication** (optional)

---

## 📚 Learning Resources

- **Project IDX Docs**: https://developers.google.com/idx
- **React Tutorial**: https://react.dev/learn
- **Vite Docs**: https://vitejs.dev/guide/
- **Material-UI**: https://mui.com/material-ui/getting-started/

---

## 🎯 Quick Start Checklist

- [ ] Open https://idx.google.com
- [ ] Create new React + Vite project
- [ ] Install axios: `npm install axios`
- [ ] Copy `BillUploader.jsx` component (from Step 8)
- [ ] Add CORS to FastAPI backend
- [ ] Run `npm run dev`
- [ ] Test with sample bill!

---

## 💡 Pro Tips

1. **Use Project IDX AI for everything!**
   - Stuck on a component? Ask AI
   - Need styling? Ask AI
   - Bug? Ask AI

2. **Start simple, iterate fast**
   - Don't try to build everything at once
   - Get basic bill analysis working first
   - Add features one by one

3. **Test with real bills early**
   - Use your actual restaurant bills
   - Find edge cases
   - Improve Gemini prompts as needed

4. **Keep your FastAPI running**
   - UI needs the backend to work
   - Consider deploying to Render/Railway for 24/7 access

---

## 🎊 You're Ready!

Your Project IDX workspace is ready to build an amazing GST Bill Analyzer UI!

**Remember:**
- Project IDX AI is like having me help you code in real-time
- Start with the basic BillUploader component
- Test frequently
- Ask AI when stuck

**Happy coding!** 🚀

---

**Estimated Time:**
- Setup Project IDX: 5 minutes
- Basic UI working: 30 minutes
- Full-featured app: 2-3 hours

**Cost:**
- Project IDX: FREE
- Gemini API: ~$15-25/month for 100 bills
- FastAPI hosting: FREE (Render.com free tier)
