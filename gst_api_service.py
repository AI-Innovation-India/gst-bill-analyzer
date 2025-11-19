"""
GST Data API Service
Version: 1.0
Purpose: RESTful API for querying GST rates, HSN codes, and tax calculations
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Security, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

# Optional dependencies for authentication (not needed for basic deployment)
try:
    from jose import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

try:
    from passlib.context import CryptContext
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None
import logging
from enum import Enum
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_VERSION = "v1"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Initialize FastAPI app
app = FastAPI(
    title="GST Data API",
    description="Comprehensive API for GST rates, HSN codes, and tax calculations (India 2025)",
    version="1.0.0",
    docs_url=f"/api/{API_VERSION}/docs",
    redoc_url=f"/api/{API_VERSION}/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security (optional - only if dependencies are available)
security = HTTPBearer()
if HAS_PASSLIB:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None
    logger.warning("Passlib not available - authentication disabled")

# Redis for rate limiting and caching (optional)
redis_client = None
if HAS_REDIS and redis is not None:
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        redis_client = None
        logger.warning(f"Redis not available - caching and rate limiting disabled: {e}")
else:
    logger.warning("Redis module not installed - caching and rate limiting disabled")


# ==================== MODELS ====================

class GSTSlabEnum(str, Enum):
    NIL = "0"
    GOLD = "3"
    MERIT = "5"
    STANDARD = "18"
    DEMERIT = "40"


class GSTItemResponse(BaseModel):
    id: Optional[int] = None
    hsn_code: Optional[str] = None
    sac_code: Optional[str] = None
    item_name: str
    item_category: Optional[str] = None
    gst_rate: float
    cgst_rate: Optional[float] = None
    sgst_rate: Optional[float] = None
    igst_rate: Optional[float] = None
    cess_rate: Optional[float] = 0.0
    effective_from: Optional[str] = None
    remarks: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "hsn_code": "0713",
                "sac_code": None,
                "item_name": "Pulses (Dried leguminous vegetables)",
                "item_category": "Vegetable Products",
                "remarks": "Dried leguminous vegetables, shelled",
                "gst_rate": 5.0,
                "cgst_rate": 2.5,
                "sgst_rate": 2.5,
                "igst_rate": 5.0,
                "cess_rate": 0.0,
                "effective_date": "2025-09-22",
                "chapter": "07",
                "exemptions": "Essential food items",
                "conditions": None,
                "last_updated": "2025-11-15T10:30:00"
            }
        }


class TaxCalculationRequest(BaseModel):
    hsn_code: Optional[str] = Field(None, description="HSN code of the item")
    item_name: Optional[str] = Field(None, description="Name of the item")
    taxable_value: float = Field(..., gt=0, description="Taxable value before GST")
    transaction_type: str = Field("intrastate", description="'intrastate' or 'interstate'")

    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        if v not in ['intrastate', 'interstate']:
            raise ValueError('transaction_type must be "intrastate" or "interstate"')
        return v


class TaxCalculationResponse(BaseModel):
    hsn_code: str
    item_name: str
    gst_rate: float
    taxable_value: float
    cgst: Optional[float]
    sgst: Optional[float]
    igst: Optional[float]
    total_tax: float
    total_value: float
    transaction_type: str


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=2, description="Search term")
    limit: int = Field(10, ge=1, le=100)
    category: Optional[str] = None


class BulkTaxRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(..., max_items=100)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ==================== DATABASE ====================

class GSTDatabase:
    """SQLite database handler for GST data"""

    def __init__(self, db_path: str = "gst_data.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Main GST items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gst_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hsn_code TEXT UNIQUE,
                sac_code TEXT,
                item_name TEXT NOT NULL,
                item_category TEXT,
                description TEXT,
                gst_rate REAL NOT NULL,
                cgst_rate REAL,
                sgst_rate REAL,
                igst_rate REAL,
                previous_rate REAL,
                effective_date TEXT,
                chapter TEXT,
                exemptions TEXT,
                conditions TEXT,
                last_updated TEXT,
                data_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Search index table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hsn_code TEXT,
                search_text TEXT,
                FOREIGN KEY (hsn_code) REFERENCES gst_items(hsn_code)
            )
        """)

        # Rate change history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hsn_code TEXT,
                old_rate REAL,
                new_rate REAL,
                change_date TEXT,
                notification_ref TEXT,
                FOREIGN KEY (hsn_code) REFERENCES gst_items(hsn_code)
            )
        """)

        # Users table (for API authentication)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # API usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def insert_gst_item(self, item: Dict):
        """Insert or update GST item"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO gst_items 
            (hsn_code, sac_code, item_name, item_category, description, 
             gst_rate, cgst_rate, sgst_rate, igst_rate, previous_rate,
             effective_date, chapter, exemptions, conditions, last_updated, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get('hsn_code'),
            item.get('sac_code'),
            item.get('item_name'),
            item.get('item_category'),
            item.get('description'),
            item.get('gst_rate'),
            item.get('cgst_rate'),
            item.get('sgst_rate'),
            item.get('igst_rate'),
            item.get('previous_rate'),
            item.get('effective_date'),
            item.get('chapter'),
            item.get('exemptions'),
            item.get('conditions'),
            item.get('last_updated'),
            item.get('data_hash')
        ))

        conn.commit()
        conn.close()

    def bulk_insert(self, items: List[Dict]):
        """Bulk insert GST items"""
        conn = self.get_connection()
        cursor = conn.cursor()

        for item in items:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO gst_items 
                    (hsn_code, sac_code, item_name, item_category, description, 
                     gst_rate, cgst_rate, sgst_rate, igst_rate, previous_rate,
                     effective_date, chapter, exemptions, conditions, last_updated, data_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('hsn_code'),
                    item.get('sac_code'),
                    item.get('item_name'),
                    item.get('item_category'),
                    item.get('description'),
                    item.get('gst_rate'),
                    item.get('cgst_rate'),
                    item.get('sgst_rate'),
                    item.get('igst_rate'),
                    item.get('previous_rate'),
                    item.get('effective_date'),
                    item.get('chapter'),
                    item.get('exemptions'),
                    item.get('conditions'),
                    item.get('last_updated'),
                    item.get('data_hash')
                ))
            except Exception as e:
                logger.error(f"Error inserting item {item.get('hsn_code')}: {str(e)}")

        conn.commit()
        conn.close()
        logger.info(f"Bulk inserted {len(items)} items")

    def get_by_hsn(self, hsn_code: str) -> Optional[Dict]:
        """Get item by HSN code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gst_items WHERE hsn_code = ?", (hsn_code,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def search_items(self, query: str, limit: int = 10, category: Optional[str] = None) -> List[Dict]:
        """Search items by name, HSN, or description"""
        conn = self.get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"
        
        if category:
            cursor.execute("""
                SELECT * FROM gst_items 
                WHERE (item_name LIKE ? OR hsn_code LIKE ? OR description LIKE ?)
                AND item_category = ?
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, category, limit))
        else:
            cursor.execute("""
                SELECT * FROM gst_items 
                WHERE item_name LIKE ? OR hsn_code LIKE ? OR description LIKE ?
                LIMIT ?
            """, (search_pattern, search_pattern, search_pattern, limit))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_categories(self) -> List[str]:
        """Get all unique categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT item_category FROM gst_items WHERE item_category IS NOT NULL")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

    def get_items_by_rate(self, rate: float) -> List[Dict]:
        """Get all items with specific GST rate"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gst_items WHERE gst_rate = ?", (rate,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


# Initialize database
db = GSTDatabase()


# ==================== AUTHENTICATION ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# ==================== RATE LIMITING ====================

def rate_limit(max_requests: int = 100, window: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if redis_client is None:
                return await func(*args, **kwargs)
            
            # Get client identifier (in production, use user ID or API key)
            client_id = "default"  # Simplified for example
            
            key = f"rate_limit:{client_id}"
            current = redis_client.get(key)
            
            if current and int(current) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            pipe.execute()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ==================== API ENDPOINTS ====================

@app.get(f"/api/{API_VERSION}/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": API_VERSION
    }


@app.post(f"/api/{API_VERSION}/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login endpoint (simplified - implement proper authentication)"""
    # In production, verify credentials against database
    access_token = create_access_token(data={"sub": user_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get(f"/api/{API_VERSION}/gst/hsn/{{hsn_code}}", response_model=GSTItemResponse)
@rate_limit(max_requests=100, window=60)
async def get_by_hsn_code(hsn_code: str):
    """
    Get GST item details by HSN code
    
    - **hsn_code**: 4, 6, or 8 digit HSN code
    """
    # Check cache first
    if redis_client:
        cached = redis_client.get(f"hsn:{hsn_code}")
        if cached:
            import json
            return json.loads(cached)
    
    item = db.get_by_hsn(hsn_code)
    
    if not item:
        raise HTTPException(status_code=404, detail=f"HSN code {hsn_code} not found")
    
    # Cache result
    if redis_client:
        import json
        redis_client.setex(f"hsn:{hsn_code}", 3600, json.dumps(item))
    
    return item


@app.post(f"/api/{API_VERSION}/gst/search", response_model=List[GSTItemResponse])
@rate_limit(max_requests=50, window=60)
async def search_gst_items(search_query: SearchQuery):
    """
    Search GST items by name, HSN code, or description
    
    - **query**: Search term (minimum 2 characters)
    - **limit**: Maximum results (default 10, max 100)
    - **category**: Optional category filter
    """
    results = db.search_items(search_query.query, search_query.limit, search_query.category)
    return results


@app.get(f"/api/{API_VERSION}/gst/categories", response_model=List[str])
async def get_categories():
    """Get all available item categories"""
    return db.get_all_categories()


@app.get(f"/api/{API_VERSION}/gst/rate/{{rate}}", response_model=List[GSTItemResponse])
async def get_items_by_rate(rate: float = Path(..., ge=0, le=40)):
    """
    Get all items with a specific GST rate
    
    - **rate**: GST rate (0, 3, 5, 18, or 40)
    """
    items = db.get_items_by_rate(rate)
    return items


@app.post(f"/api/{API_VERSION}/gst/calculate", response_model=TaxCalculationResponse)
@rate_limit(max_requests=200, window=60)
async def calculate_tax(request: TaxCalculationRequest):
    """
    Calculate GST for a given item and taxable value
    
    - **hsn_code** or **item_name**: Item identifier
    - **taxable_value**: Value before tax
    - **transaction_type**: 'intrastate' or 'interstate'
    """
    # Find item
    item = None
    if request.hsn_code:
        item = db.get_by_hsn(request.hsn_code)
    elif request.item_name:
        results = db.search_items(request.item_name, limit=1)
        item = results[0] if results else None
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    gst_rate = item['gst_rate']
    taxable_value = request.taxable_value
    
    # Calculate tax components
    if request.transaction_type == 'intrastate':
        cgst = sgst = (taxable_value * gst_rate) / 200
        igst = None
        total_tax = cgst + sgst
    else:  # interstate
        cgst = sgst = None
        igst = (taxable_value * gst_rate) / 100
        total_tax = igst
    
    return TaxCalculationResponse(
        hsn_code=item['hsn_code'],
        item_name=item['item_name'],
        gst_rate=gst_rate,
        taxable_value=taxable_value,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        total_tax=total_tax,
        total_value=taxable_value + total_tax,
        transaction_type=request.transaction_type
    )


@app.post(f"/api/{API_VERSION}/gst/calculate/bulk")
@rate_limit(max_requests=20, window=60)
async def bulk_calculate_tax(request: BulkTaxRequest):
    """
    Calculate GST for multiple items in a single request
    
    Maximum 100 items per request
    """
    results = []
    
    for item_data in request.items:
        try:
            calc_request = TaxCalculationRequest(**item_data)
            result = await calculate_tax(calc_request)
            results.append(result.dict())
        except Exception as e:
            results.append({"error": str(e), "item": item_data})
    
    return {"results": results, "total_items": len(results)}


@app.get(f"/api/{API_VERSION}/gst/stats")
async def get_statistics():
    """Get GST database statistics"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total items
    cursor.execute("SELECT COUNT(*) FROM gst_items")
    stats['total_items'] = cursor.fetchone()[0]
    
    # Items by rate
    cursor.execute("""
        SELECT gst_rate, COUNT(*) as count 
        FROM gst_items 
        GROUP BY gst_rate 
        ORDER BY gst_rate
    """)
    stats['items_by_rate'] = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Items by category
    cursor.execute("""
        SELECT item_category, COUNT(*) as count 
        FROM gst_items 
        WHERE item_category IS NOT NULL
        GROUP BY item_category 
        ORDER BY count DESC 
        LIMIT 10
    """)
    stats['top_categories'] = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    return stats


# ==================== ADMIN ENDPOINTS ====================

@app.post(f"/api/{API_VERSION}/admin/import", dependencies=[Depends(verify_token)])
async def import_data(data: List[Dict]):
    """
    Import GST data (protected endpoint)

    Requires authentication token
    """
    try:
        db.bulk_insert(data)
        return {"status": "success", "imported": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SIMPLIFIED ENDPOINTS FOR UI ====================
# These endpoints are simplified versions without versioning for easier UI integration

@app.get("/health")
async def health_check_simple():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": API_VERSION
    }


# More specific routes must come BEFORE parameterized routes
@app.get("/gst/items", response_model=List[GSTItemResponse])
async def get_all_items():
    """Get all GST items (prioritizes items with HSN/SAC codes)"""
    conn = db.get_connection()
    cursor = conn.cursor()
    # Sort to show items WITH HSN/SAC codes first, then by GST rate
    cursor.execute("""
        SELECT id, hsn_code, sac_code, item_name, item_category,
               gst_rate, cgst_rate, sgst_rate, igst_rate, cess_rate,
               effective_from, remarks, created_at, updated_at
        FROM gst_items
        ORDER BY
            CASE
                WHEN hsn_code IS NOT NULL OR sac_code IS NOT NULL THEN 0
                ELSE 1
            END,
            gst_rate ASC,
            item_name ASC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    conn.close()

    # Convert Row objects to dicts
    items = []
    for row in rows:
        items.append({
            'id': row[0],
            'hsn_code': row[1],
            'sac_code': row[2],
            'item_name': row[3],
            'item_category': row[4],
            'gst_rate': row[5],
            'cgst_rate': row[6],
            'sgst_rate': row[7],
            'igst_rate': row[8],
            'cess_rate': row[9],
            'effective_from': row[10],
            'remarks': row[11],
            'created_at': row[12],
            'updated_at': row[13]
        })
    return items


@app.get("/gst/search/{query}", response_model=List[GSTItemResponse])
async def search_gst_simple(query: str):
    """Search GST items (simplified endpoint)"""
    results = db.search_items(query, limit=50)
    return results


@app.get("/gst/{hsn_code}", response_model=GSTItemResponse)
async def get_gst_by_hsn_simple(hsn_code: str):
    """Get GST item by HSN code (simplified endpoint)"""
    item = db.get_by_hsn(hsn_code)
    if not item:
        raise HTTPException(status_code=404, detail=f"HSN code {hsn_code} not found")
    return item


class BillAnalysisRequest(BaseModel):
    bill_text: str = Field(..., description="The text content of the bill to analyze")


@app.post("/gst/analyze-bill")
async def analyze_bill(request: BillAnalysisRequest):
    """
    Analyze a bill using Gemini AI to detect GST discrepancies

    This endpoint integrates with the Gemini bill analyzer
    """
    try:
        # Import the Gemini analyzer
        import os
        import sys

        # Check if Gemini analyzer is available
        try:
            from gst_bill_analyzer_gemini import GeminiGSTAnalyzer
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Gemini bill analyzer not configured. Please set GOOGLE_API_KEY environment variable."
            )

        # Get API key from environment
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="Google API key not configured. Set GOOGLE_API_KEY environment variable."
            )

        # Analyze the bill
        analyzer = GeminiGSTAnalyzer(api_key=api_key, db_path='gst_data.db')
        result = analyzer.analyze_bill(bill_text=request.bill_text)

        # Return the analysis as dict
        return result.to_dict()

    except ImportError as e:
        import traceback
        error_detail = f"Gemini analyzer not available: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(
            status_code=503,
            detail=error_detail
        )
    except Exception as e:
        import traceback
        error_detail = f"Bill analysis failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


@app.post("/gst/analyze-bill-file")
async def analyze_bill_file(file: UploadFile = File(...)):
    """
    Analyze a bill from uploaded PDF or image file

    Supports: PDF, JPG, JPEG, PNG
    """
    try:
        # Check file type
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png']):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload PDF, JPG, JPEG, or PNG files."
            )

        # Import the Gemini analyzer
        try:
            from gst_bill_analyzer_gemini import GeminiGSTAnalyzer
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Gemini bill analyzer not configured. Please set GOOGLE_API_KEY environment variable."
            )

        # Get API key from environment
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="Google API key not configured. Set GOOGLE_API_KEY environment variable."
            )

        # Read file content
        content = await file.read()

        # Use Gemini File API to upload and analyze directly
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Save temporarily for Gemini upload
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Upload file to Gemini
            uploaded_file = genai.upload_file(tmp_file_path, mime_type=file.content_type)

            # Use Gemini to extract text from the file
            model = genai.GenerativeModel('gemini-1.5-flash')

            extraction_prompt = """Extract ALL text from this bill/receipt/invoice EXACTLY as shown.
Include:
- Store/restaurant name and address
- Bill number and date
- ALL items with their names, quantities, and prices
- Subtotal, taxes (GST/CGST/SGST/IGST), service charges, discounts
- Final total amount
- Any other visible text

Return the complete extracted text."""

            response = model.generate_content([extraction_prompt, uploaded_file])
            bill_text = response.text

            # Now analyze the extracted text
            analyzer = GeminiGSTAnalyzer(api_key=api_key, db_path='gst_data.db')
            result = analyzer.analyze_bill(bill_text=bill_text)

            # Return the analysis as dict
            return result.to_dict()

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"File analysis failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
