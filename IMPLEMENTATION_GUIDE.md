# GST Data Extraction & Management System
## Complete Implementation & Deployment Guide

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [API Documentation](#api-documentation)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)
10. [Production Deployment](#production-deployment)

---

## System Architecture

### Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                  GST Data Management System                      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│   Extraction   │    │    Storage     │    │      API       │
│     Layer      │───▶│     Layer      │◀───│     Layer      │
└────────────────┘    └────────────────┘    └────────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│  Web Scraper   │    │  PostgreSQL/   │    │   FastAPI      │
│  Change        │    │  SQLite        │    │   REST API     │
│  Detector      │    │  Redis Cache   │    │   Swagger UI   │
└────────────────┘    └────────────────┘    └────────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌──────────────┐    ┌──────────────┐
            │  Scheduler   │    │  Monitoring  │
            │(APScheduler) │    │   & Alerts   │
            └──────────────┘    └──────────────┘
```

### Component Details

#### 1. Extraction Layer (`gst_extraction_system.py`)
- **Purpose**: Scrapes and parses GST data from ClearTax and government sources
- **Key Features**:
  - Multi-source data extraction
  - HTML table parsing
  - JSON-LD structured data extraction
  - HSN/SAC code validation
  - Category enrichment
  - Change detection

#### 2. Storage Layer
- **Primary Database**: SQLite (upgradable to PostgreSQL)
- **Cache**: Redis (optional but recommended)
- **Backup**: Automated daily backups
- **Schema**:
  - `gst_items`: Main GST data
  - `rate_history`: Historical rate changes
  - `users`: API authentication
  - `api_usage`: Usage tracking

#### 3. API Layer (`gst_api_service.py`)
- **Framework**: FastAPI
- **Authentication**: JWT tokens
- **Rate Limiting**: Redis-based
- **Documentation**: Auto-generated Swagger/ReDoc
- **Endpoints**: 15+ REST endpoints

#### 4. Scheduling Layer (`gst_scheduler.py`)
- **Framework**: APScheduler
- **Jobs**:
  - Daily extraction (3 AM)
  - Weekly comprehensive update (Sunday 2 AM)
  - Hourly health checks
  - Daily backups (4 AM)
  - Weekly cleanup (Monday 1 AM)

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 22.04+), macOS, or Windows with WSL2
- **Python**: 3.10 or higher
- **RAM**: Minimum 2GB, Recommended 4GB
- **Storage**: 1GB free space
- **Network**: Unrestricted access to ClearTax and GST portal

### Optional Services
- **Redis**: For caching and rate limiting (recommended)
- **PostgreSQL**: For production deployments
- **Nginx**: For reverse proxy in production
- **Docker**: For containerized deployment

---

## Installation

### Step 1: Clone or Download the System
```bash
# Create project directory
mkdir gst-data-system
cd gst-data-system

# Copy all Python files to this directory
# - gst_extraction_system.py
# - gst_api_service.py
# - gst_scheduler.py
# - requirements.txt
```

### Step 2: Set Up Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import bs4; import pandas; print('All dependencies installed!')"
```

### Step 4: Install Redis (Optional but Recommended)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS (Homebrew)
brew install redis
brew services start redis

# Verify Redis
redis-cli ping
# Should return: PONG
```

### Step 5: Initial Setup
```bash
# Create necessary directories
mkdir -p backups logs data

# Set permissions
chmod +x gst_extraction_system.py
chmod +x gst_api_service.py
chmod +x gst_scheduler.py
```

---

## Configuration

### 1. Environment Variables
Create a `.env` file:

```bash
# .env
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./gst_data.db
REDIS_HOST=localhost
REDIS_PORT=6379
LOG_LEVEL=INFO
```

### 2. Scheduler Configuration
Create `scheduler_config.json`:

```json
{
  "db_path": "gst_data.db",
  "previous_data_file": "gst_data.json",
  "backup_enabled": true,
  "backup_dir": "./backups",
  "email_enabled": false,
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "from": "your-email@gmail.com",
    "to": ["recipient@example.com"],
    "username": "your-email@gmail.com",
    "password": "your-app-password"
  },
  "webhook_enabled": false,
  "webhook_url": "https://your-webhook-url.com/gst-updates"
}
```

### 3. Email Notifications (Optional)
To enable email notifications:

1. For Gmail:
   - Enable 2-Factor Authentication
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Use App Password in `scheduler_config.json`

2. Update config:
```json
{
  "email_enabled": true,
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "from": "your-email@gmail.com",
    "to": ["recipient1@example.com", "recipient2@example.com"],
    "username": "your-email@gmail.com",
    "password": "your-16-char-app-password"
  }
}
```

---

## Running the System

### Option 1: Run Each Component Separately

#### A. Initial Data Extraction
```bash
# First time: Extract GST data
python gst_extraction_system.py

# Output files:
# - gst_data_2025.json  (JSON format)
# - gst_data_2025.csv   (CSV format)
# - gst_scraper.log     (Extraction logs)
```

#### B. Start API Server
```bash
# Development mode with auto-reload
uvicorn gst_api_service:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn gst_api_service:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Access API documentation:
# http://localhost:8000/api/v1/docs
```

#### C. Start Scheduler (Background)
```bash
# Run scheduler
python gst_scheduler.py

# Or run in background (Linux/macOS)
nohup python gst_scheduler.py > scheduler.log 2>&1 &

# Check scheduler logs
tail -f scheduler.log
```

### Option 2: Run All Components with Supervisor

Install Supervisor:
```bash
sudo apt install supervisor
```

Create Supervisor configuration `/etc/supervisor/conf.d/gst-system.conf`:
```ini
[program:gst-api]
command=/path/to/venv/bin/gunicorn gst_api_service:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
directory=/path/to/gst-data-system
user=your-username
autostart=true
autorestart=true
stderr_logfile=/var/log/gst-api.err.log
stdout_logfile=/var/log/gst-api.out.log

[program:gst-scheduler]
command=/path/to/venv/bin/python gst_scheduler.py
directory=/path/to/gst-data-system
user=your-username
autostart=true
autorestart=true
stderr_logfile=/var/log/gst-scheduler.err.log
stdout_logfile=/var/log/gst-scheduler.out.log
```

Start services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start gst-api
sudo supervisorctl start gst-scheduler

# Check status
sudo supervisorctl status
```

### Option 3: Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .
COPY scheduler_config.json .

# Create directories
RUN mkdir -p backups logs data

# Expose API port
EXPOSE 8000

# Run API server
CMD ["uvicorn", "gst_api_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  gst-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - DATABASE_URL=sqlite:///./data/gst_data.db
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
      - ./logs:/app/logs
    depends_on:
      - redis

  gst-scheduler:
    build: .
    command: python gst_scheduler.py
    environment:
      - REDIS_HOST=redis
      - DATABASE_URL=sqlite:///./data/gst_data.db
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
      - ./logs:/app/logs
    depends_on:
      - redis

volumes:
  redis_data:
```

Run with Docker:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Key Endpoints

#### 1. Get Item by HSN Code
```bash
GET /api/v1/gst/hsn/{hsn_code}

# Example
curl http://localhost:8000/api/v1/gst/hsn/0713

# Response
{
  "hsn_code": "0713",
  "item_name": "Pulses",
  "gst_rate": 0.0,
  "cgst_rate": 0.0,
  "sgst_rate": 0.0,
  "igst_rate": 0.0,
  ...
}
```

#### 2. Search Items
```bash
POST /api/v1/gst/search

# Example
curl -X POST http://localhost:8000/api/v1/gst/search \
  -H "Content-Type: application/json" \
  -d '{"query": "rice", "limit": 10}'

# Response
[
  {
    "hsn_code": "1006",
    "item_name": "Rice",
    "gst_rate": 5.0,
    ...
  }
]
```

#### 3. Calculate Tax
```bash
POST /api/v1/gst/calculate

# Example
curl -X POST http://localhost:8000/api/v1/gst/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "hsn_code": "8414",
    "taxable_value": 10000,
    "transaction_type": "intrastate"
  }'

# Response
{
  "hsn_code": "8414",
  "item_name": "Ceiling Fan",
  "gst_rate": 18.0,
  "taxable_value": 10000,
  "cgst": 900.0,
  "sgst": 900.0,
  "igst": null,
  "total_tax": 1800.0,
  "total_value": 11800.0,
  "transaction_type": "intrastate"
}
```

#### 4. Get Statistics
```bash
GET /api/v1/gst/stats

# Example
curl http://localhost:8000/api/v1/gst/stats

# Response
{
  "total_items": 5432,
  "items_by_rate": {
    "0": 1234,
    "5": 2345,
    "18": 1567,
    "40": 286
  },
  "top_categories": {
    "Vegetable Products": 456,
    "Textiles": 389,
    ...
  }
}
```

### Interactive Documentation
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

---

## Monitoring & Maintenance

### Log Files
```bash
# API logs
tail -f logs/gst_api.log

# Scraper logs
tail -f gst_scraper.log

# Scheduler logs
tail -f gst_scheduler.log
```

### Database Maintenance
```bash
# Check database size
ls -lh gst_data.db

# Vacuum database (optimize)
sqlite3 gst_data.db "VACUUM;"

# Check item count
sqlite3 gst_data.db "SELECT COUNT(*) FROM gst_items;"

# View recent updates
sqlite3 gst_data.db "SELECT hsn_code, item_name, last_updated FROM gst_items ORDER BY last_updated DESC LIMIT 10;"
```

### Backup Management
```bash
# Manual backup
cp gst_data.db backups/gst_data_manual_$(date +%Y%m%d).db

# List backups
ls -lh backups/

# Restore from backup
cp backups/gst_data_20251115.db gst_data.db
```

### Redis Monitoring
```bash
# Check Redis connection
redis-cli ping

# Check memory usage
redis-cli INFO memory

# Clear cache (if needed)
redis-cli FLUSHDB
```

---

## Troubleshooting

### Common Issues

#### 1. Scraper Not Extracting Data
**Symptoms**: Empty JSON/CSV files, zero items extracted

**Solutions**:
```bash
# Check internet connectivity
ping cleartax.in

# Verify URL accessibility
curl -I https://cleartax.in/s/gst-rates

# Check logs
tail -f gst_scraper.log

# Increase timeout in code
# Edit gst_extraction_system.py:
response = self.session.get(url, timeout=60)  # Increase from 30
```

#### 2. API Not Starting
**Symptoms**: Port 8000 already in use

**Solutions**:
```bash
# Check what's using port 8000
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Or use different port
uvicorn gst_api_service:app --port 8001
```

#### 3. Redis Connection Failed
**Symptoms**: "Redis not available" warnings

**Solutions**:
```bash
# Start Redis
sudo systemctl start redis-server

# Check Redis status
redis-cli ping

# If Redis not needed, system works without it (caching disabled)
```

#### 4. Database Locked
**Symptoms**: "database is locked" error

**Solutions**:
```bash
# Check for multiple connections
lsof gst_data.db

# Wait and retry, or restart services
sudo supervisorctl restart gst-api gst-scheduler
```

#### 5. Scheduler Jobs Not Running
**Symptoms**: No updates, stale data

**Solutions**:
```bash
# Check scheduler status
ps aux | grep gst_scheduler

# View scheduler logs
tail -f gst_scheduler.log

# Manually trigger extraction
python gst_extraction_system.py
```

---

## Advanced Configuration

### Using PostgreSQL Instead of SQLite

1. Install PostgreSQL:
```bash
sudo apt install postgresql postgresql-contrib
```

2. Create database:
```bash
sudo -u postgres psql
CREATE DATABASE gst_data;
CREATE USER gst_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gst_data TO gst_user;
\q
```

3. Install Python driver:
```bash
pip install psycopg2-binary
```

4. Update `gst_api_service.py`:
```python
# Replace SQLite connection with PostgreSQL
import psycopg2

class GSTDatabase:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or "postgresql://gst_user:your_password@localhost/gst_data"
    
    def get_connection(self):
        return psycopg2.connect(self.db_url)
```

### Custom Scraping Patterns

To add new data sources, edit `gst_extraction_system.py`:

```python
def extract_custom_source(self, url: str) -> List[GSTItem]:
    """
    Add custom extraction logic for new sources
    """
    soup = self.fetch_page(url)
    items = []
    
    # Your custom parsing logic here
    # ...
    
    return items
```

### Webhook Integration

Configure webhooks in `scheduler_config.json`:
```json
{
  "webhook_enabled": true,
  "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
}
```

The system will POST JSON to your webhook on:
- Rate changes detected
- Daily updates completed
- Errors/alerts

---

## Production Deployment

### 1. Security Checklist
- [ ] Change default JWT secret key
- [ ] Use strong database passwords
- [ ] Enable HTTPS (use Nginx + Let's Encrypt)
- [ ] Set up firewall (UFW)
- [ ] Restrict API access (IP whitelist/VPN)
- [ ] Enable rate limiting
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log rotation
- [ ] Set up automated backups to remote storage

### 2. Nginx Reverse Proxy
Create `/etc/nginx/sites-available/gst-api`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/gst-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 4. Performance Tuning

**API Workers**:
```bash
# Calculate workers: (2 x CPU cores) + 1
gunicorn gst_api_service:app -w 9 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Redis Configuration**:
```bash
# Edit /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

**Database Optimization**:
```sql
-- Add indexes
CREATE INDEX idx_hsn_code ON gst_items(hsn_code);
CREATE INDEX idx_item_name ON gst_items(item_name);
CREATE INDEX idx_gst_rate ON gst_items(gst_rate);
```

---

## Next Steps

1. **Initial Setup** (Day 1):
   - Install dependencies
   - Run initial extraction
   - Verify data quality
   - Test API endpoints

2. **Integration** (Week 1):
   - Connect to your billing system
   - Implement tax calculation logic
   - Set up automated updates
   - Configure notifications

3. **Optimization** (Week 2):
   - Fine-tune scraping patterns
   - Add custom data sources
   - Optimize database queries
   - Set up monitoring

4. **Production** (Week 3):
   - Deploy to production server
   - Configure SSL/security
   - Set up backups
   - Enable monitoring/alerting

---

## Support & Resources

### Official Documentation
- GST Portal: https://www.gst.gov.in
- CBIC Notifications: https://www.cbic.gov.in
- ClearTax: https://cleartax.in

### Python Libraries
- FastAPI: https://fastapi.tiangolo.com
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
- APScheduler: https://apscheduler.readthedocs.io

### Contact
For issues or questions:
- Check logs: `gst_scraper.log`, `gst_scheduler.log`
- Review API docs: http://localhost:8000/api/v1/docs
- Validate data: Run health check endpoints

---

**System Version**: 1.0  
**Last Updated**: November 2025  
**Effective GST Rates**: As of September 22, 2025
