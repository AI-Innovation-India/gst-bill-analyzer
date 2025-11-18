"""
GST Data Validation & Quality Control Utility
Version: 1.0
Purpose: Validate data integrity, check for anomalies, and generate quality reports
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GSTDataValidator:
    """
    Comprehensive validation suite for GST data
    """

    def __init__(self, db_path: str = 'gst_data.db'):
        self.db_path = db_path
        self.validation_results = {}

    def run_all_validations(self) -> Dict:
        """
        Run complete validation suite
        """
        logger.info("Starting comprehensive data validation...")
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'database': self.db_path,
            'checks': {}
        }

        # Run all validation checks
        self.check_database_connectivity()
        self.check_data_completeness()
        self.check_hsn_code_validity()
        self.check_rate_validity()
        self.check_duplicates()
        self.check_category_consistency()
        self.check_data_freshness()
        self.check_mathematical_consistency()
        self.generate_statistics()

        # Calculate overall health score
        self.calculate_health_score()

        logger.info("Validation complete!")
        return self.validation_results

    def check_database_connectivity(self):
        """Verify database is accessible"""
        check_name = "database_connectivity"
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM gst_items")
            count = cursor.fetchone()[0]
            conn.close()

            self.validation_results['checks'][check_name] = {
                'status': 'PASS',
                'total_items': count,
                'message': f"Database accessible with {count} items"
            }
        except Exception as e:
            self.validation_results['checks'][check_name] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def check_data_completeness(self):
        """Check for missing required fields"""
        check_name = "data_completeness"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        issues = []

        # Check missing HSN codes
        cursor.execute("SELECT COUNT(*) FROM gst_items WHERE hsn_code IS NULL OR hsn_code = ''")
        missing_hsn = cursor.fetchone()[0]
        if missing_hsn > 0:
            issues.append(f"{missing_hsn} items missing HSN code")

        # Check missing item names
        cursor.execute("SELECT COUNT(*) FROM gst_items WHERE item_name IS NULL OR item_name = ''")
        missing_names = cursor.fetchone()[0]
        if missing_names > 0:
            issues.append(f"{missing_names} items missing item name")

        # Check missing rates
        cursor.execute("SELECT COUNT(*) FROM gst_items WHERE gst_rate IS NULL")
        missing_rates = cursor.fetchone()[0]
        if missing_rates > 0:
            issues.append(f"{missing_rates} items missing GST rate")

        conn.close()

        self.validation_results['checks'][check_name] = {
            'status': 'PASS' if not issues else 'WARN',
            'issues': issues,
            'missing_hsn': missing_hsn,
            'missing_names': missing_names,
            'missing_rates': missing_rates
        }

    def check_hsn_code_validity(self):
        """Validate HSN code format"""
        check_name = "hsn_code_validity"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # HSN codes should be 2, 4, 6, or 8 digits
        cursor.execute("""
            SELECT hsn_code, COUNT(*) 
            FROM gst_items 
            WHERE hsn_code IS NOT NULL 
            GROUP BY hsn_code
        """)

        invalid_hsn = []
        for hsn_code, count in cursor.fetchall():
            if not hsn_code.isdigit():
                invalid_hsn.append((hsn_code, "non-numeric"))
            elif len(hsn_code) not in [2, 4, 6, 8]:
                invalid_hsn.append((hsn_code, "invalid length"))

        conn.close()

        self.validation_results['checks'][check_name] = {
            'status': 'PASS' if not invalid_hsn else 'FAIL',
            'invalid_count': len(invalid_hsn),
            'samples': invalid_hsn[:10]  # First 10 samples
        }

    def check_rate_validity(self):
        """Validate GST rates are within expected range"""
        check_name = "rate_validity"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Valid rates: 0, 3, 5, 18, 40, plus some special rates
        valid_rates = {0, 0.25, 3, 5, 12, 18, 28, 40}  # Including deprecated rates

        cursor.execute("SELECT DISTINCT gst_rate FROM gst_items WHERE gst_rate IS NOT NULL")
        rates = [row[0] for row in cursor.fetchall()]

        invalid_rates = [r for r in rates if r not in valid_rates and r < 0 or r > 40]

        # Count items with each rate
        cursor.execute("""
            SELECT gst_rate, COUNT(*) 
            FROM gst_items 
            WHERE gst_rate IS NOT NULL 
            GROUP BY gst_rate 
            ORDER BY gst_rate
        """)
        rate_distribution = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        self.validation_results['checks'][check_name] = {
            'status': 'PASS' if not invalid_rates else 'WARN',
            'invalid_rates': invalid_rates,
            'rate_distribution': rate_distribution,
            'unique_rates': len(rates)
        }

    def check_duplicates(self):
        """Check for duplicate HSN codes"""
        check_name = "duplicates"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT hsn_code, COUNT(*) as count 
            FROM gst_items 
            WHERE hsn_code IS NOT NULL 
            GROUP BY hsn_code 
            HAVING count > 1
        """)

        duplicates = cursor.fetchall()
        conn.close()

        self.validation_results['checks'][check_name] = {
            'status': 'PASS' if not duplicates else 'WARN',
            'duplicate_count': len(duplicates),
            'samples': duplicates[:10]
        }

    def check_category_consistency(self):
        """Check category assignments"""
        check_name = "category_consistency"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count items by category
        cursor.execute("""
            SELECT item_category, COUNT(*) 
            FROM gst_items 
            WHERE item_category IS NOT NULL 
            GROUP BY item_category 
            ORDER BY COUNT(*) DESC
        """)
        categories = cursor.fetchall()

        # Items without category
        cursor.execute("SELECT COUNT(*) FROM gst_items WHERE item_category IS NULL OR item_category = ''")
        uncategorized = cursor.fetchone()[0]

        conn.close()

        self.validation_results['checks'][check_name] = {
            'status': 'PASS' if uncategorized < 100 else 'WARN',
            'total_categories': len(categories),
            'uncategorized_items': uncategorized,
            'top_categories': dict(categories[:10])
        }

    def check_data_freshness(self):
        """Check how recent the data is"""
        check_name = "data_freshness"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(last_updated) FROM gst_items")
        last_update = cursor.fetchone()[0]

        conn.close()

        if last_update:
            last_update_date = datetime.fromisoformat(last_update)
            days_old = (datetime.now() - last_update_date).days

            status = 'PASS' if days_old <= 7 else ('WARN' if days_old <= 30 else 'FAIL')
        else:
            days_old = None
            status = 'FAIL'

        self.validation_results['checks'][check_name] = {
            'status': status,
            'last_update': last_update,
            'days_old': days_old,
            'message': f"Data is {days_old} days old" if days_old else "No update timestamp"
        }

    def check_mathematical_consistency(self):
        """Verify CGST + SGST = IGST"""
        check_name = "mathematical_consistency"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT hsn_code, gst_rate, cgst_rate, sgst_rate, igst_rate 
            FROM gst_items 
            WHERE gst_rate IS NOT NULL
        """)

        inconsistencies = []
        for row in cursor.fetchall():
            hsn, gst, cgst, sgst, igst = row
            
            # CGST + SGST should equal GST
            if cgst and sgst and abs((cgst + sgst) - gst) > 0.01:
                inconsistencies.append((hsn, "CGST+SGST != GST"))
            
            # IGST should equal GST
            if igst and abs(igst - gst) > 0.01:
                inconsistencies.append((hsn, "IGST != GST"))
            
            # CGST should equal SGST
            if cgst and sgst and abs(cgst - sgst) > 0.01:
                inconsistencies.append((hsn, "CGST != SGST"))

        conn.close()

        self.validation_results['checks'][check_name] = {
            'status': 'PASS' if not inconsistencies else 'FAIL',
            'inconsistencies_count': len(inconsistencies),
            'samples': inconsistencies[:10]
        }

    def generate_statistics(self):
        """Generate comprehensive statistics"""
        conn = sqlite3.connect(self.db_path)
        
        # Load data into pandas for analysis
        df = pd.read_sql_query("SELECT * FROM gst_items", conn)
        conn.close()

        stats = {
            'total_items': len(df),
            'unique_hsn_codes': df['hsn_code'].nunique(),
            'rate_statistics': {
                'mean': float(df['gst_rate'].mean()),
                'median': float(df['gst_rate'].median()),
                'min': float(df['gst_rate'].min()),
                'max': float(df['gst_rate'].max())
            },
            'category_count': df['item_category'].nunique(),
            'has_previous_rate': int((df['previous_rate'].notna()).sum())
        }

        self.validation_results['statistics'] = stats

    def calculate_health_score(self):
        """Calculate overall data health score (0-100)"""
        checks = self.validation_results['checks']
        
        total_checks = len(checks)
        passed = sum(1 for c in checks.values() if c['status'] == 'PASS')
        warned = sum(1 for c in checks.values() if c['status'] == 'WARN')

        # Scoring: PASS=100%, WARN=50%, FAIL=0%
        score = ((passed * 100) + (warned * 50)) / (total_checks * 100) * 100

        self.validation_results['health_score'] = round(score, 2)
        self.validation_results['summary'] = {
            'passed': passed,
            'warned': warned,
            'failed': total_checks - passed - warned,
            'total': total_checks
        }

    def generate_report(self, output_file: str = 'validation_report.txt'):
        """Generate human-readable validation report"""
        lines = []
        lines.append("=" * 80)
        lines.append("GST DATA VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.validation_results['timestamp']}")
        lines.append(f"Database: {self.validation_results['database']}")
        lines.append(f"Health Score: {self.validation_results.get('health_score', 0)}/100")
        lines.append("")

        # Summary
        summary = self.validation_results.get('summary', {})
        lines.append(f"Summary: {summary.get('passed', 0)} PASSED, "
                    f"{summary.get('warned', 0)} WARNED, "
                    f"{summary.get('failed', 0)} FAILED")
        lines.append("")

        # Statistics
        stats = self.validation_results.get('statistics', {})
        lines.append("Statistics:")
        lines.append(f"  Total Items: {stats.get('total_items', 0)}")
        lines.append(f"  Unique HSN Codes: {stats.get('unique_hsn_codes', 0)}")
        lines.append(f"  Categories: {stats.get('category_count', 0)}")
        lines.append("")

        # Detailed checks
        lines.append("Detailed Checks:")
        lines.append("-" * 80)
        for check_name, check_result in self.validation_results['checks'].items():
            status = check_result.get('status', 'UNKNOWN')
            status_symbol = "✓" if status == 'PASS' else ("⚠" if status == 'WARN' else "✗")
            lines.append(f"{status_symbol} {check_name.replace('_', ' ').title()}: {status}")
            
            if 'message' in check_result:
                lines.append(f"    {check_result['message']}")
            if 'issues' in check_result and check_result['issues']:
                for issue in check_result['issues']:
                    lines.append(f"    - {issue}")
            lines.append("")

        report_text = "\n".join(lines)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        logger.info(f"Validation report saved to {output_file}")
        return report_text

    def export_to_json(self, output_file: str = 'validation_results.json'):
        """Export validation results to JSON"""
        with open(output_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        logger.info(f"Validation results exported to {output_file}")


class DataCleaner:
    """
    Automated data cleaning and correction
    """

    def __init__(self, db_path: str = 'gst_data.db'):
        self.db_path = db_path

    def clean_all(self):
        """Run all cleaning operations"""
        logger.info("Starting data cleaning...")
        
        self.remove_duplicates()
        self.fix_rate_components()
        self.normalize_categories()
        self.fix_hsn_codes()

        logger.info("Data cleaning complete!")

    def remove_duplicates(self):
        """Remove duplicate HSN entries, keeping most recent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM gst_items 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM gst_items 
                GROUP BY hsn_code
            )
        """)

        removed = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Removed {removed} duplicate entries")

    def fix_rate_components(self):
        """Recalculate CGST, SGST, IGST from GST rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, gst_rate FROM gst_items WHERE gst_rate IS NOT NULL")
        items = cursor.fetchall()

        for item_id, gst_rate in items:
            cgst = sgst = gst_rate / 2
            igst = gst_rate

            cursor.execute("""
                UPDATE gst_items 
                SET cgst_rate = ?, sgst_rate = ?, igst_rate = ? 
                WHERE id = ?
            """, (cgst, sgst, igst, item_id))

        conn.commit()
        conn.close()

        logger.info(f"Fixed rate components for {len(items)} items")

    def normalize_categories(self):
        """Normalize category names"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Add normalization rules as needed
        normalizations = {
            'food products': 'Prepared Foodstuffs',
            'electronics': 'Machinery & Electrical Equipment',
            # Add more as needed
        }

        for old, new in normalizations.items():
            cursor.execute("""
                UPDATE gst_items 
                SET item_category = ? 
                WHERE LOWER(item_category) = ?
            """, (new, old.lower()))

        conn.commit()
        conn.close()

        logger.info("Category normalization complete")

    def fix_hsn_codes(self):
        """Pad HSN codes to standard length"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, hsn_code FROM gst_items WHERE hsn_code IS NOT NULL")
        items = cursor.fetchall()

        for item_id, hsn_code in items:
            # Pad to 6 or 8 digits if shorter
            if len(hsn_code) < 6:
                padded = hsn_code.ljust(6, '0')
                cursor.execute("UPDATE gst_items SET hsn_code = ? WHERE id = ?", (padded, item_id))

        conn.commit()
        conn.close()

        logger.info("HSN code normalization complete")


if __name__ == '__main__':
    # Run validation
    validator = GSTDataValidator()
    results = validator.run_all_validations()
    
    # Generate reports
    report = validator.generate_report()
    print(report)
    validator.export_to_json()

    # Run cleaning if needed
    health_score = results.get('health_score', 0)
    if health_score < 80:
        logger.warning(f"Health score {health_score} is below threshold. Running data cleaning...")
        cleaner = DataCleaner()
        cleaner.clean_all()
        
        # Re-validate after cleaning
        validator = GSTDataValidator()
        results = validator.run_all_validations()
        validator.generate_report('validation_report_after_cleaning.txt')
