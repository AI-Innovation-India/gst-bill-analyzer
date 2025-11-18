# GST System Quick Reference Card

## 🚀 Quick Start Commands

```bash
# 1. Setup (one-time)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Initial extraction
python gst_extraction_system.py

# 3. Start API
uvicorn gst_api_service:app --reload

# 4. Start scheduler (background)
nohup python gst_scheduler.py > scheduler.log 2>&1 &

# 5. Access API docs
# http://localhost:8000/api/v1/docs
```

---

## 📡 Common API Calls

### Get Item by HSN
```bash
curl http://localhost:8000/api/v1/gst/hsn/8414
```

### Search Items
```bash
curl -X POST http://localhost:8000/api/v1/gst/search \
  -H "Content-Type: application/json" \
  -d '{"query": "rice", "limit": 10}'
```

### Calculate Tax
```bash
curl -X POST http://localhost:8000/api/v1/gst/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "hsn_code": "8414",
    "taxable_value": 10000,
    "transaction_type": "intrastate"
  }'
```

### Get Statistics
```bash
curl http://localhost:8000/api/v1/gst/stats
```

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

---

## 🔧 Maintenance Commands

### Check Logs
```bash
tail -f gst_scraper.log      # Scraper logs
tail -f gst_scheduler.log    # Scheduler logs
tail -f logs/gst_api.log     # API logs
```

### Manual Data Update
```bash
python gst_extraction_system.py
```

### Data Validation
```bash
python gst_data_validator.py
cat validation_report.txt
```

### Database Queries
```bash
# Check item count
sqlite3 gst_data.db "SELECT COUNT(*) FROM gst_items;"

# View recent updates
sqlite3 gst_data.db "SELECT hsn_code, item_name, gst_rate, last_updated FROM gst_items ORDER BY last_updated DESC LIMIT 10;"

# Items by rate
sqlite3 gst_data.db "SELECT gst_rate, COUNT(*) FROM gst_items GROUP BY gst_rate;"
```

### Backup & Restore
```bash
# Manual backup
cp gst_data.db backups/gst_data_$(date +%Y%m%d).db

# Restore
cp backups/gst_data_20251115.db gst_data.db

# List backups
ls -lh backups/
```

---

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f gst-api
docker-compose logs -f gst-scheduler

# Restart services
docker-compose restart

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## 🔒 Production Commands

### Start Services (Systemd)
```bash
sudo systemctl start gst-api
sudo systemctl start gst-scheduler
sudo systemctl status gst-api
```

### Nginx
```bash
# Test configuration
sudo nginx -t

# Reload
sudo systemctl reload nginx

# View logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### SSL Certificate (Let's Encrypt)
```bash
# Initial setup
sudo certbot --nginx -d your-domain.com

# Renew
sudo certbot renew

# Auto-renew (add to crontab)
0 0 * * * certbot renew --quiet
```

---

## 🐛 Troubleshooting

### API Not Starting
```bash
# Check port
lsof -i :8000

# Kill process
kill -9 $(lsof -t -i:8000)

# Use different port
uvicorn gst_api_service:app --port 8001
```

### Redis Issues
```bash
# Start Redis
sudo systemctl start redis-server

# Check Redis
redis-cli ping

# View Redis data
redis-cli KEYS "*"
```

### Database Locked
```bash
# Check connections
lsof gst_data.db

# Vacuum database
sqlite3 gst_data.db "VACUUM;"
```

### Scraper Not Working
```bash
# Test connectivity
ping cleartax.in
curl -I https://cleartax.in/s/gst-rates

# Check logs
tail -50 gst_scraper.log

# Manual run with debug
python -v gst_extraction_system.py
```

---

## 📊 GST Rate Quick Reference

| Rate | Category | Common Items |
|------|----------|-------------|
| 0% | Nil | Vegetables, milk, education |
| 3% | Gold/Silver | Jewelry, precious stones |
| 5% | Merit | Rice, medicine, transport |
| 18% | Standard | Electronics, cement |
| 40% | Demerit | Luxury cars, tobacco |

---

## 🔑 Environment Variables

```bash
# .env file
JWT_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./gst_data.db
REDIS_HOST=localhost
REDIS_PORT=6379
LOG_LEVEL=INFO
API_PORT=8000
```

---

## 📈 Monitoring

### Check System Health
```bash
# API health
curl http://localhost:8000/api/v1/health

# Database size
du -h gst_data.db

# Memory usage
ps aux | grep python

# Disk space
df -h
```

### Performance Metrics
```bash
# API response time
time curl http://localhost:8000/api/v1/gst/hsn/8414

# Database query time
time sqlite3 gst_data.db "SELECT * FROM gst_items LIMIT 1000;"

# Redis ping
redis-cli --latency
```

---

## 🧪 Testing

```bash
# Test extraction
python gst_extraction_system.py

# Test API endpoint
curl http://localhost:8000/api/v1/health

# Test calculation
curl -X POST http://localhost:8000/api/v1/gst/calculate \
  -H "Content-Type: application/json" \
  -d '{"hsn_code": "8414", "taxable_value": 100, "transaction_type": "intrastate"}'

# Run validation
python gst_data_validator.py
```

---

## 📞 Common Errors & Solutions

| Error | Solution |
|-------|----------|
| Port 8000 in use | Kill process: `kill -9 $(lsof -t -i:8000)` |
| Redis connection failed | Start Redis: `sudo systemctl start redis-server` |
| Database locked | Close all connections, restart services |
| Empty scraper output | Check internet, verify URLs accessible |
| 401 Unauthorized | Check JWT token, regenerate if expired |
| 429 Too Many Requests | Wait 60s or increase rate limit |

---

## 📝 File Locations

```
Project Root/
├── gst_extraction_system.py   # Scraper
├── gst_api_service.py          # API server
├── gst_scheduler.py            # Scheduler
├── gst_data_validator.py       # Validator
├── gst_data.db                 # Database
├── gst_data.json               # JSON export
├── gst_data.csv                # CSV export
├── gst_scraper.log             # Scraper logs
├── gst_scheduler.log           # Scheduler logs
├── scheduler_config.json       # Config
├── .env                        # Environment
├── backups/                    # Backups
│   └── gst_data_YYYYMMDD.db
└── logs/                       # API logs
    └── gst_api.log
```

---

## 🎯 Daily Checklist

### Morning (Automated)
- [ ] Data extraction ran (check logs)
- [ ] Backup completed
- [ ] No alerts received

### Weekly (5 minutes)
- [ ] Review validation report
- [ ] Check API uptime
- [ ] Verify backup count

### Monthly (30 minutes)
- [ ] Review change reports
- [ ] Check for GST Council updates
- [ ] Update documentation if needed

---

## 💡 Pro Tips

1. **Cache Everything**: Enable Redis for 10x speedup
2. **Monitor Logs**: Set up log aggregation (ELK/Splunk)
3. **Automate Backups**: Daily to S3/cloud storage
4. **Use Webhooks**: Get instant notifications on Slack
5. **Version Control**: Keep code in Git
6. **Load Test**: Use `locust` or `ab` before production
7. **Security**: Change default secrets immediately
8. **Documentation**: Keep API docs updated

---

## 📱 Contact

- Health Check: `curl localhost:8000/api/v1/health`
- API Docs: http://localhost:8000/api/v1/docs
- Logs: `tail -f *.log`

---

**Last Updated**: November 15, 2025  
**System Version**: 1.0.0
