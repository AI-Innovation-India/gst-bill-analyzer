"""
GST Data Update Scheduler
Version: 1.0
Purpose: Automated scheduling for periodic data extraction, change detection, and notifications
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from typing import Dict, List, Optional
import requests
from pathlib import Path

# Import our extraction modules
import sys
sys.path.append(str(Path(__file__).parent))
from gst_extraction_system import GSTDataExtractor, GSTChangeDetector
from gst_api_service import GSTDatabase

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gst_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GSTUpdateScheduler:
    """
    Manages scheduled tasks for GST data updates
    """

    def __init__(self, config: Dict):
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.db = GSTDatabase(config.get('db_path', 'gst_data.db'))
        self.extractor = GSTDataExtractor()
        self.change_detector = GSTChangeDetector(config.get('previous_data_file', 'gst_data.json'))
        
        # Email configuration
        self.email_enabled = config.get('email_enabled', False)
        self.smtp_config = config.get('smtp', {})
        
        # Webhook configuration
        self.webhook_enabled = config.get('webhook_enabled', False)
        self.webhook_url = config.get('webhook_url')
        
        # Backup configuration
        self.backup_enabled = config.get('backup_enabled', True)
        self.backup_dir = Path(config.get('backup_dir', './backups'))
        self.backup_dir.mkdir(exist_ok=True)

    def start(self):
        """Start all scheduled jobs"""
        logger.info("Starting GST Update Scheduler...")
        
        # Job 1: Daily data extraction (3 AM)
        self.scheduler.add_job(
            self.daily_extraction_job,
            CronTrigger(hour=3, minute=0),
            id='daily_extraction',
            name='Daily GST Data Extraction',
            replace_existing=True
        )
        
        # Job 2: Weekly comprehensive update (Sunday 2 AM)
        self.scheduler.add_job(
            self.weekly_comprehensive_update,
            CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='weekly_update',
            name='Weekly Comprehensive Update',
            replace_existing=True
        )
        
        # Job 3: Hourly health check
        self.scheduler.add_job(
            self.health_check_job,
            CronTrigger(minute='0'),  # Every hour
            id='health_check',
            name='Hourly Health Check',
            replace_existing=True
        )
        
        # Job 4: Daily backup (4 AM)
        if self.backup_enabled:
            self.scheduler.add_job(
                self.backup_job,
                CronTrigger(hour=4, minute=0),
                id='daily_backup',
                name='Daily Backup',
                replace_existing=True
            )
        
        # Job 5: Weekly cleanup (Monday 1 AM)
        self.scheduler.add_job(
            self.cleanup_job,
            CronTrigger(day_of_week='mon', hour=1, minute=0),
            id='weekly_cleanup',
            name='Weekly Cleanup',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Print next run times
        for job in self.scheduler.get_jobs():
            logger.info(f"Job: {job.name} - Next run: {job.next_run_time}")

    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    # ==================== SCHEDULED JOBS ====================

    def daily_extraction_job(self):
        """
        Daily job to extract GST data and detect changes
        """
        logger.info("=" * 80)
        logger.info("STARTING DAILY EXTRACTION JOB")
        logger.info("=" * 80)
        
        try:
            # Load previous data for comparison
            self.change_detector.load_previous_data()
            
            # Run extraction
            logger.info("Extracting GST data from sources...")
            items = self.extractor.run_full_extraction()
            
            if not items:
                logger.error("No data extracted. Aborting update.")
                self.send_alert("GST Update Failed", "No data was extracted from sources.")
                return
            
            # Detect changes
            logger.info("Detecting changes...")
            changes = self.change_detector.detect_changes(items)
            
            # Log change summary
            change_summary = {
                'new_items': len(changes['new_items']),
                'rate_changes': len(changes['rate_changes']),
                'removed_items': len(changes['removed_items']),
                'modified_items': len(changes['modified_items']),
                'total_items': len(items)
            }
            logger.info(f"Change summary: {change_summary}")
            
            # Update database if there are changes
            if any(len(v) > 0 for v in changes.values()):
                logger.info("Updating database with new data...")
                item_dicts = [item.to_dict() for item in items]
                self.db.bulk_insert(item_dicts)
                
                # Save current data for next comparison
                self.extractor.extracted_data = items
                self.extractor.save_to_json('gst_data.json')
                self.extractor.save_to_csv('gst_data.csv')
                
                # Generate and send change report
                report = self.change_detector.generate_change_report(changes)
                logger.info("\n" + report)
                
                # Send notifications
                if change_summary['rate_changes'] > 0 or change_summary['new_items'] > 0:
                    self.send_change_notification(report, change_summary)
            else:
                logger.info("No changes detected. Database not updated.")
            
            logger.info("Daily extraction job completed successfully")
            
        except Exception as e:
            logger.error(f"Daily extraction job failed: {str(e)}", exc_info=True)
            self.send_alert("GST Daily Update Failed", f"Error: {str(e)}")

    def weekly_comprehensive_update(self):
        """
        Weekly comprehensive update including data validation and cleanup
        """
        logger.info("=" * 80)
        logger.info("STARTING WEEKLY COMPREHENSIVE UPDATE")
        logger.info("=" * 80)
        
        try:
            # Run daily extraction
            self.daily_extraction_job()
            
            # Additional weekly tasks
            logger.info("Running data validation...")
            validation_results = self.validate_data()
            
            logger.info("Generating weekly statistics...")
            stats = self.generate_weekly_stats()
            
            # Send weekly report
            self.send_weekly_report(validation_results, stats)
            
            logger.info("Weekly comprehensive update completed")
            
        except Exception as e:
            logger.error(f"Weekly update failed: {str(e)}", exc_info=True)
            self.send_alert("GST Weekly Update Failed", f"Error: {str(e)}")

    def health_check_job(self):
        """
        Hourly health check for database and API
        """
        try:
            # Check database connectivity
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM gst_items")
            item_count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"Health check passed. Database contains {item_count} items.")
            
            # Check if data is stale (older than 7 days)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(last_updated) FROM gst_items")
            last_update = cursor.fetchone()[0]
            
            if last_update:
                last_update_date = datetime.fromisoformat(last_update)
                days_old = (datetime.now() - last_update_date).days
                
                if days_old > 7:
                    logger.warning(f"Data is {days_old} days old. Consider updating.")
                    self.send_alert("GST Data Stale", f"Data is {days_old} days old.")
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            self.send_alert("GST Health Check Failed", f"Error: {str(e)}")

    def backup_job(self):
        """
        Daily backup of database and data files
        """
        logger.info("Starting backup job...")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup database
            db_backup_path = self.backup_dir / f"gst_data_{timestamp}.db"
            import shutil
            shutil.copy2(self.db.db_path, db_backup_path)
            logger.info(f"Database backed up to {db_backup_path}")
            
            # Backup JSON data
            json_backup_path = self.backup_dir / f"gst_data_{timestamp}.json"
            if Path('gst_data.json').exists():
                shutil.copy2('gst_data.json', json_backup_path)
                logger.info(f"JSON data backed up to {json_backup_path}")
            
            # Backup CSV data
            csv_backup_path = self.backup_dir / f"gst_data_{timestamp}.csv"
            if Path('gst_data.csv').exists():
                shutil.copy2('gst_data.csv', csv_backup_path)
                logger.info(f"CSV data backed up to {csv_backup_path}")
            
            # Cleanup old backups (keep last 30 days)
            self.cleanup_old_backups(30)
            
            logger.info("Backup job completed successfully")
            
        except Exception as e:
            logger.error(f"Backup job failed: {str(e)}", exc_info=True)
            self.send_alert("GST Backup Failed", f"Error: {str(e)}")

    def cleanup_job(self):
        """
        Weekly cleanup job
        """
        logger.info("Starting cleanup job...")
        
        try:
            # Clean up old log files
            self.cleanup_old_logs(30)
            
            # Clean up old backups
            self.cleanup_old_backups(30)
            
            logger.info("Cleanup job completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup job failed: {str(e)}", exc_info=True)

    # ==================== HELPER METHODS ====================

    def validate_data(self) -> Dict:
        """
        Validate database data integrity
        """
        logger.info("Validating data integrity...")
        
        validation_results = {
            'total_items': 0,
            'missing_hsn': 0,
            'invalid_rates': 0,
            'missing_categories': 0,
            'duplicates': 0
        }
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Total items
        cursor.execute("SELECT COUNT(*) FROM gst_items")
        validation_results['total_items'] = cursor.fetchone()[0]
        
        # Missing HSN codes
        cursor.execute("SELECT COUNT(*) FROM gst_items WHERE hsn_code IS NULL OR hsn_code = ''")
        validation_results['missing_hsn'] = cursor.fetchone()[0]
        
        # Invalid rates (outside 0-40 range)
        cursor.execute("SELECT COUNT(*) FROM gst_items WHERE gst_rate < 0 OR gst_rate > 40")
        validation_results['invalid_rates'] = cursor.fetchone()[0]
        
        # Missing categories
        cursor.execute("SELECT COUNT(*) FROM gst_items WHERE item_category IS NULL OR item_category = ''")
        validation_results['missing_categories'] = cursor.fetchone()[0]
        
        # Duplicates
        cursor.execute("""
            SELECT hsn_code, COUNT(*) as count 
            FROM gst_items 
            WHERE hsn_code IS NOT NULL 
            GROUP BY hsn_code 
            HAVING count > 1
        """)
        validation_results['duplicates'] = len(cursor.fetchall())
        
        conn.close()
        
        logger.info(f"Validation results: {validation_results}")
        return validation_results

    def generate_weekly_stats(self) -> Dict:
        """
        Generate weekly statistics
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Items by rate
        cursor.execute("""
            SELECT gst_rate, COUNT(*) as count 
            FROM gst_items 
            GROUP BY gst_rate 
            ORDER BY gst_rate
        """)
        stats['items_by_rate'] = {f"{row[0]}%": row[1] for row in cursor.fetchall()}
        
        # Top 10 categories
        cursor.execute("""
            SELECT item_category, COUNT(*) as count 
            FROM gst_items 
            WHERE item_category IS NOT NULL
            GROUP BY item_category 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['top_categories'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent rate changes (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM rate_history 
            WHERE change_date >= date('now', '-7 days')
        """)
        stats['recent_changes'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats

    def cleanup_old_backups(self, days: int = 30):
        """
        Remove backups older than specified days
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for file in self.backup_dir.glob('gst_data_*.db'):
            if file.stat().st_mtime < cutoff_date.timestamp():
                file.unlink()
                logger.info(f"Removed old backup: {file}")

    def cleanup_old_logs(self, days: int = 30):
        """
        Remove log files older than specified days
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for file in Path('.').glob('*.log'):
            if file.stat().st_mtime < cutoff_date.timestamp():
                file.unlink()
                logger.info(f"Removed old log: {file}")

    # ==================== NOTIFICATION METHODS ====================

    def send_change_notification(self, report: str, summary: Dict):
        """
        Send notification when changes are detected
        """
        subject = f"GST Rate Changes Detected - {datetime.now().strftime('%Y-%m-%d')}"
        message = f"""
GST Data Update Report
{'-' * 80}

Summary:
- New Items: {summary['new_items']}
- Rate Changes: {summary['rate_changes']}
- Removed Items: {summary['removed_items']}
- Modified Items: {summary['modified_items']}
- Total Items: {summary['total_items']}

Detailed Report:
{report}

---
This is an automated notification from GST Data Management System.
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        if self.email_enabled:
            self.send_email(subject, message)
        
        if self.webhook_enabled:
            self.send_webhook_notification({
                'type': 'gst_change_detected',
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            })

    def send_weekly_report(self, validation: Dict, stats: Dict):
        """
        Send weekly summary report
        """
        subject = f"GST Weekly Report - {datetime.now().strftime('%Y-%m-%d')}"
        message = f"""
GST Data Weekly Report
{'-' * 80}

Data Validation:
- Total Items: {validation['total_items']}
- Missing HSN Codes: {validation['missing_hsn']}
- Invalid Rates: {validation['invalid_rates']}
- Missing Categories: {validation['missing_categories']}
- Duplicate Entries: {validation['duplicates']}

Statistics:
Items by Rate:
{json.dumps(stats.get('items_by_rate', {}), indent=2)}

Top Categories:
{json.dumps(stats.get('top_categories', {}), indent=2)}

Recent Changes (Last 7 Days): {stats.get('recent_changes', 0)}

---
This is an automated weekly report from GST Data Management System.
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        if self.email_enabled:
            self.send_email(subject, message)

    def send_alert(self, subject: str, message: str):
        """
        Send alert notification
        """
        full_message = f"""
ALERT: {subject}
{'-' * 80}

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: GST Data Management System

This is an automated alert. Please investigate.
        """
        
        logger.warning(f"ALERT: {subject} - {message}")
        
        if self.email_enabled:
            self.send_email(f"[ALERT] {subject}", full_message)
        
        if self.webhook_enabled:
            self.send_webhook_notification({
                'type': 'alert',
                'subject': subject,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })

    def send_email(self, subject: str, body: str):
        """
        Send email notification
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('from')
            msg['To'] = ', '.join(self.smtp_config.get('to', []))
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_config.get('host'), self.smtp_config.get('port', 587)) as server:
                server.starttls()
                if self.smtp_config.get('username') and self.smtp_config.get('password'):
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

    def send_webhook_notification(self, data: Dict):
        """
        Send webhook notification
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook notification sent: {data['type']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")


# ==================== CONFIGURATION ====================

def load_config(config_file: str = 'scheduler_config.json') -> Dict:
    """
    Load configuration from file
    """
    default_config = {
        'db_path': 'gst_data.db',
        'previous_data_file': 'gst_data.json',
        'backup_enabled': True,
        'backup_dir': './backups',
        'email_enabled': False,
        'smtp': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'from': 'your-email@gmail.com',
            'to': ['recipient@example.com'],
            'username': 'your-email@gmail.com',
            'password': 'your-password'
        },
        'webhook_enabled': False,
        'webhook_url': 'https://your-webhook-url.com/gst-updates'
    }
    
    if Path(config_file).exists():
        with open(config_file, 'r') as f:
            user_config = json.load(f)
            default_config.update(user_config)
    else:
        # Save default config
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Created default config file: {config_file}")
    
    return default_config


# ==================== MAIN ====================

if __name__ == '__main__':
    import signal
    
    # Load configuration
    config = load_config()
    
    # Initialize scheduler
    scheduler = GSTUpdateScheduler(config)
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received...")
        scheduler.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start scheduler
    scheduler.start()
    
    logger.info("GST Update Scheduler is running. Press Ctrl+C to exit.")
    
    # Keep the script running
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received...")
        scheduler.stop()
