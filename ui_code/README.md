# GST Bill Analyzer - React UI

A modern, user-friendly interface for analyzing restaurant bills and detecting GST discrepancies using Google Gemini AI.

## Features

- **Bill Analysis**: Upload or paste restaurant bills to detect GST errors
- **GST Database Lookup**: Search 46+ GST items with rates and HSN codes
- **Discrepancy Detection**: Automatically identifies overcharges/undercharges
- **Beautiful UI**: Modern gradient design with responsive layout
- **Real-time Results**: Instant analysis with detailed breakdowns

## Quick Start

### Option 1: Use in Project IDX (Recommended)

1. Go to https://idx.google.com
2. Create new React + Vite project
3. Copy all files from `ui_code/` folder to your Project IDX workspace:
   ```
   src/
   ├── App.jsx
   ├── App.css
   ├── main.jsx
   ├── components/
   │   ├── BillUploader.jsx
   │   ├── BillAnalyzer.jsx
   │   └── GSTLookup.jsx
   └── services/
       └── api.js
   ```
4. Copy `index.html`, `package.json`, `vite.config.js` to root
5. Run: `npm install`
6. Run: `npm run dev`

### Option 2: Local Development

1. **Prerequisites**:
   - Node.js 18+ installed
   - FastAPI backend running on port 8001

2. **Setup**:
   ```bash
   cd ui_code
   npm install
   npm run dev
   ```

3. **Access**:
   - UI: http://localhost:3000
   - API: http://localhost:8001

## Project Structure

```
ui_code/
├── src/
│   ├── App.jsx              # Main application component
│   ├── App.css              # Global styles
│   ├── main.jsx             # React entry point
│   ├── components/
│   │   ├── BillUploader.jsx     # Upload and input bill text
│   │   ├── BillAnalyzer.jsx     # Display analysis results
│   │   └── GSTLookup.jsx        # Search GST database
│   └── services/
│       └── api.js           # API integration functions
├── index.html               # HTML template
├── package.json             # Dependencies
├── vite.config.js           # Vite configuration
└── .env.example             # Environment variables template
```

## Environment Variables

Create a `.env` file (copy from `.env.example`):

```env
VITE_GOOGLE_API_KEY=your_gemini_api_key
VITE_API_BASE_URL=http://127.0.0.1:8001
```

## Usage

### 1. Bill Analysis Tab

1. Click "Use Sample Bill" or paste your own bill text
2. Click "Analyze Bill"
3. View detailed results with:
   - Item-by-item breakdown
   - GST rate for each item
   - Comparison: Bill charged vs Correct amount
   - Discrepancy alerts

### 2. GST Lookup Tab

1. Search by item name, HSN code, or category
2. Browse all 46 GST items in database
3. View rates, codes, and categories

## API Integration

The UI connects to FastAPI backend running on `http://127.0.0.1:8001`.

**Required Endpoints:**

- `POST /gst/analyze-bill` - Analyze bill text
- `GET /gst/items` - Get all GST items
- `GET /gst/search/{query}` - Search items

See `src/services/api.js` for implementation.

## Making the Backend Work

The FastAPI backend needs CORS enabled. Add this to `gst_api_service.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Customization

### Colors

Edit `App.css` to change the gradient:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### API URL

Update `src/services/api.js`:

```javascript
const API_BASE_URL = 'https://your-api-domain.com';
```

## Building for Production

```bash
npm run build
```

Output in `dist/` folder. Deploy to:
- Firebase Hosting (recommended with Project IDX)
- Vercel
- Netlify
- GitHub Pages

## Troubleshooting

### CORS Errors
- Add CORS middleware to FastAPI backend (see above)
- Check API is running on correct port

### API Connection Failed
- Verify FastAPI is running: `uvicorn gst_api_service:app --host 127.0.0.1 --port 8001`
- Check firewall settings
- Use correct API URL

### Blank Screen
- Check browser console for errors
- Verify all files copied correctly
- Run `npm install` again

### Build Errors
- Delete `node_modules/` and run `npm install` again
- Clear npm cache: `npm cache clean --force`

## Features Coming Soon

- PDF/Image upload (requires backend endpoint)
- Download report as PDF
- Bill history tracking
- Charts and visualizations
- Dark mode toggle

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **FastAPI** - Backend API
- **Google Gemini** - AI analysis
- **SQLite** - GST database

## License

MIT License - Feel free to use and modify!

## Support

For issues or questions:
- Check [PROJECT_IDX_SETUP.md](../PROJECT_IDX_SETUP.md)
- Review [GEMINI_SETUP_GUIDE.md](../GEMINI_SETUP_GUIDE.md)
- Ensure FastAPI backend is running

## Credits

Built with Google Gemini AI and Project IDX

---

**Happy analyzing!** Detect those GST errors! 🔍
