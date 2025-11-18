"""
GST Data Extraction & Management System - Core Scraper Module
Version: 1.0
Purpose: Extract, parse, and structure GST rate data from ClearTax and government sources
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gst_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GSTSlab(Enum):
    """GST rate slabs as per 2025 reforms (effective Sept 22, 2025)"""
    NIL = 0.0
    GOLD = 3.0  # Special rate for gold/silver
    MERIT = 5.0  # Essential goods
    STANDARD = 18.0  # Most goods/services
    DEMERIT = 40.0  # Luxury/sin goods
    COMP_1_5 = 1.5  # Composition scheme
    COMP_5 = 5.0  # Composition scheme
    COMP_6 = 6.0  # Composition scheme


@dataclass
class GSTItem:
    """Structured GST item data model"""
    hsn_code: str
    sac_code: Optional[str]
    item_name: str
    item_category: str
    description: str
    gst_rate: float
    cgst_rate: float
    sgst_rate: float
    igst_rate: float
    previous_rate: Optional[float]
    effective_date: str
    chapter: Optional[str]
    exemptions: Optional[str]
    conditions: Optional[str]
    last_updated: str
    data_hash: str  # For change detection

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def calculate_component_rates(total_gst: float) -> Tuple[float, float, float]:
        """Calculate CGST, SGST, IGST from total GST rate"""
        cgst = sgst = total_gst / 2
        igst = total_gst
        return cgst, sgst, igst


class GSTDataExtractor:
    """
    Primary scraper class for extracting GST data from multiple sources
    """

    def __init__(self, user_agent: str = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.base_urls = {
            'cleartax_main': 'https://cleartax.in/s/gst-rates',
            'cleartax_changes': 'https://cleartax.in/s/gst-rate-revamp-list-of-cheaper-and-costlier-items',
            'gst_portal': 'https://www.gst.gov.in',
            'cbic_notifications': 'https://www.cbic.gov.in/resources//htdocs-cbec/gst/Notification-09-2025-CT-Rate.pdf'
        }
        self.extracted_data: List[GSTItem] = []

    def fetch_page(self, url: str, retry: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch webpage with retry logic and error handling
        """
        for attempt in range(retry):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                logger.info(f"Successfully fetched: {url}")
                return BeautifulSoup(response.content, 'lxml')
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == retry - 1:
                    logger.error(f"Failed to fetch {url} after {retry} attempts")
                    return None
        return None

    def extract_cleartax_main_page(self) -> List[GSTItem]:
        """
        Extract GST rates from ClearTax main rates page
        Handles tables, nested structures, and dynamic content (Next.js)
        """
        soup = self.fetch_page(self.base_urls['cleartax_main'])
        if not soup:
            return []

        items = []

        # Strategy 0: Extract from Next.js __NEXT_DATA__ (for client-side rendered content)
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if next_data_script:
            try:
                next_data = json.loads(next_data_script.string)
                html_content = next_data.get('props', {}).get('pageProps', {}).get('postData', {}).get('data', {}).get('content', '')
                if html_content:
                    content_soup = BeautifulSoup(html_content, 'lxml')
                    tables = content_soup.find_all('table')
                    logger.info(f"Found {len(tables)} tables in Next.js content")
                    for table in tables:
                        items.extend(self._parse_table(table))
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                logger.warning(f"Failed to parse Next.js data: {str(e)}")

        # Strategy 1: Extract from structured tables (fallback for static content)
        if not items:
            tables = soup.find_all('table')
            for table in tables:
                items.extend(self._parse_table(table))

        # Strategy 2: Extract from HSN code sections
        hsn_sections = soup.find_all(['div', 'section'], class_=re.compile(r'hsn|rate|gst', re.I))
        for section in hsn_sections:
            items.extend(self._parse_hsn_section(section))

        # Strategy 3: Extract from JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            items.extend(self._parse_json_ld(script.string))

        logger.info(f"Extracted {len(items)} items from ClearTax main page")
        return items

    def _parse_table(self, table) -> List[GSTItem]:
        """
        Parse HTML table into GSTItem objects
        """
        items = []

        # Try to get headers from <th> tags first
        headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]

        # If no <th> tags, use first row as headers (common in some tables)
        all_rows = table.find_all('tr')
        if not headers and all_rows:
            first_row_cells = all_rows[0].find_all(['td', 'th'])
            # Check if first row looks like headers (contains keywords like 'category', 'items', etc.)
            first_row_text = [cell.get_text(strip=True).lower() for cell in first_row_cells]
            if any(keyword in ' '.join(first_row_text) for keyword in ['category', 'items', 'rate', 'hsn', 'from', 'to']):
                headers = first_row_text
                rows = all_rows[1:]  # Skip first row since it's the header
            else:
                return items  # No valid headers found
        else:
            rows = all_rows[1:] if headers else all_rows

        if not headers:
            return items

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            row_data = {}

            # Handle tables with inconsistent column counts
            # Some rows may have fewer columns (e.g., category + rates without separate items column)
            if len(cells) < len(headers):
                # Map cells to headers intelligently
                cell_values = [cell.get_text(strip=True) for cell in cells]

                # Common pattern: [Category/Item, From (%), To (%)] when expecting [Category, Items, From (%), To (%)]
                if len(cells) == 3 and len(headers) == 4:
                    # First cell is both category and item
                    row_data[headers[0]] = cell_values[0]  # category
                    row_data[headers[1]] = cell_values[0]  # items (same as category)
                    row_data[headers[2]] = cell_values[1]  # from (%)
                    row_data[headers[3]] = cell_values[2]  # to (%)
                else:
                    # Default mapping
                    for idx, cell in enumerate(cells):
                        if idx < len(headers):
                            row_data[headers[idx]] = cell.get_text(strip=True)
            else:
                # Normal mapping when cell count matches header count
                for idx, cell in enumerate(cells):
                    if idx < len(headers):
                        row_data[headers[idx]] = cell.get_text(strip=True)

            # Map to GSTItem structure
            item = self._map_to_gst_item(row_data)
            if item:
                items.append(item)

        return items

    def _map_to_gst_item(self, data: Dict) -> Optional[GSTItem]:
        """
        Map scraped data dictionary to GSTItem object
        """
        try:
            # Extract HSN/SAC code
            hsn_code = self._extract_code(data, ['hsn', 'hsn code', 'code', 'chapter'])
            sac_code = self._extract_code(data, ['sac', 'sac code', 'service code'])

            # Extract item details
            item_name = self._extract_field(data, ['items', 'item', 'product', 'goods', 'service', 'description'])
            category = self._extract_field(data, ['category', 'type', 'group'])

            # Extract rates - support both 'to (%)' and 'rate' formats
            gst_rate = self._extract_rate(data, ['to (%)', 'gst rate', 'rate', 'tax rate', 'new rate', 'current rate', 'to'])
            previous_rate = self._extract_rate(data, ['from (%)', 'old rate', 'previous rate', 'earlier rate', 'from'])

            # Allow items without HSN/SAC codes if they have item names and rates
            if not item_name:
                return None
            if gst_rate is None:
                return None

            cgst, sgst, igst = GSTItem.calculate_component_rates(gst_rate)

            # Generate data hash for change detection
            data_string = f"{hsn_code}{item_name}{gst_rate}{datetime.now().date()}"
            data_hash = hashlib.md5(data_string.encode()).hexdigest()

            return GSTItem(
                hsn_code=hsn_code or '',
                sac_code=sac_code,
                item_name=item_name,
                item_category=category,
                description=self._extract_field(data, ['description', 'details']),
                gst_rate=gst_rate,
                cgst_rate=cgst,
                sgst_rate=sgst,
                igst_rate=igst,
                previous_rate=previous_rate,
                effective_date='2025-09-22',  # GST 2.0 effective date
                chapter=hsn_code[:2] if hsn_code else None,
                exemptions=self._extract_field(data, ['exemption', 'exemptions']),
                conditions=self._extract_field(data, ['conditions', 'notes']),
                last_updated=datetime.now().isoformat(),
                data_hash=data_hash
            )

        except Exception as e:
            logger.error(f"Error mapping data to GSTItem: {str(e)}")
            return None

    def _extract_code(self, data: Dict, possible_keys: List[str]) -> Optional[str]:
        """Extract HSN/SAC code from various possible field names"""
        for key in possible_keys:
            for data_key, value in data.items():
                if key in data_key.lower() and value:
                    # Clean and validate code
                    code = re.sub(r'[^\d]', '', value)
                    if code:
                        return code
        return None

    def _extract_field(self, data: Dict, possible_keys: List[str]) -> str:
        """Extract field value from various possible keys"""
        for key in possible_keys:
            for data_key, value in data.items():
                if key in data_key.lower() and value:
                    return value.strip()
        return ''

    def _extract_rate(self, data: Dict, possible_keys: List[str]) -> Optional[float]:
        """Extract and clean GST rate from text"""
        for key in possible_keys:
            for data_key, value in data.items():
                if key in data_key.lower() and value:
                    # Extract numeric rate
                    match = re.search(r'(\d+\.?\d*)\s*%?', value)
                    if match:
                        return float(match.group(1))
        return None

    def _parse_hsn_section(self, section) -> List[GSTItem]:
        """Parse HSN code sections from page content"""
        items = []
        # Implementation depends on actual HTML structure
        # This is a placeholder for the pattern
        return items

    def _parse_json_ld(self, json_string: str) -> List[GSTItem]:
        """Parse JSON-LD structured data if present"""
        items = []
        try:
            data = json.loads(json_string)
            # Extract relevant GST data from JSON structure
            # Implementation depends on actual JSON structure
        except json.JSONDecodeError:
            pass
        return items

    def extract_government_notification(self, notification_url: str = None) -> List[GSTItem]:
        """
        Extract data from official CBIC notification PDF/webpage
        This requires PDF parsing (PyPDF2 or pdfplumber)
        """
        # This would use pdfplumber or PyPDF2 to extract tables from official PDFs
        # Placeholder for now
        logger.info("Government notification extraction not yet implemented")
        return []

    def enrich_with_categories(self, items: List[GSTItem]) -> List[GSTItem]:
        """
        Enrich items with category information based on HSN chapter
        """
        # HSN Chapter to Category mapping
        chapter_mapping = {
            '01-05': 'Live Animals & Animal Products',
            '06-14': 'Vegetable Products',
            '15': 'Animal/Vegetable Fats & Oils',
            '16-24': 'Prepared Foodstuffs',
            '25-27': 'Mineral Products',
            '28-38': 'Chemicals & Allied Industries',
            '39-40': 'Plastics & Rubber',
            '41-43': 'Raw Hides, Skins & Leather',
            '44-46': 'Wood & Articles',
            '47-49': 'Paper & Paperboard',
            '50-63': 'Textiles',
            '64-67': 'Footwear, Headgear',
            '68-70': 'Stone, Cement, Ceramics, Glass',
            '71': 'Precious Stones & Metals',
            '72-83': 'Base Metals',
            '84-85': 'Machinery & Electrical Equipment',
            '86-89': 'Vehicles, Aircraft, Vessels',
            '90-92': 'Optical, Medical Instruments',
            '93': 'Arms & Ammunition',
            '94-96': 'Miscellaneous Manufactured Articles',
            '97': 'Works of Art'
        }

        for item in items:
            if item.hsn_code:
                chapter_num = int(item.hsn_code[:2])
                for range_key, category in chapter_mapping.items():
                    if '-' in range_key:
                        start, end = map(int, range_key.split('-'))
                        if start <= chapter_num <= end:
                            item.item_category = category
                            break
                    elif int(range_key) == chapter_num:
                        item.item_category = category
                        break

        return items

    def save_to_json(self, filename: str = 'gst_data.json'):
        """Save extracted data to JSON file"""
        data = [item.to_dict() for item in self.extracted_data]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(data)} items to {filename}")

    def save_to_csv(self, filename: str = 'gst_data.csv'):
        """Save extracted data to CSV file"""
        if not self.extracted_data:
            logger.warning("No data to save")
            return
        
        df = pd.DataFrame([item.to_dict() for item in self.extracted_data])
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(df)} items to {filename}")

    def run_full_extraction(self) -> List[GSTItem]:
        """
        Execute complete extraction workflow
        """
        logger.info("Starting GST data extraction...")
        
        # Extract from ClearTax
        cleartax_items = self.extract_cleartax_main_page()
        
        # Extract from government sources (if accessible)
        # gov_items = self.extract_government_notification()
        
        # Combine and deduplicate
        all_items = cleartax_items  # + gov_items
        
        # Enrich with categories
        all_items = self.enrich_with_categories(all_items)
        
        # Remove duplicates based on HSN code or item name
        unique_items = {}
        for item in all_items:
            # Use HSN/SAC code as primary key, fallback to item_name + category
            key = item.hsn_code or item.sac_code
            if not key and item.item_name:
                # Create a unique key from item name and category for items without codes
                key = f"{item.item_category}:{item.item_name}".lower().strip()

            if key and key not in unique_items:
                unique_items[key] = item

        self.extracted_data = list(unique_items.values())
        
        logger.info(f"Extraction complete. Total unique items: {len(self.extracted_data)}")
        return self.extracted_data


class GSTChangeDetector:
    """
    Detect changes in GST rates by comparing current vs. previous data
    """

    def __init__(self, previous_data_file: str = 'gst_data.json'):
        self.previous_data_file = previous_data_file
        self.previous_data: Dict[str, GSTItem] = {}

    def load_previous_data(self):
        """Load previously scraped data"""
        try:
            with open(self.previous_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item_dict in data:
                    item = GSTItem(**item_dict)
                    key = item.hsn_code or item.sac_code
                    if key:
                        self.previous_data[key] = item
            logger.info(f"Loaded {len(self.previous_data)} previous items")
        except FileNotFoundError:
            logger.warning("No previous data file found")

    def detect_changes(self, current_items: List[GSTItem]) -> Dict[str, List[GSTItem]]:
        """
        Compare current vs previous data and categorize changes
        """
        changes = {
            'new_items': [],
            'rate_changes': [],
            'removed_items': [],
            'modified_items': []
        }

        current_keys = set()

        for item in current_items:
            key = item.hsn_code or item.sac_code
            if not key:
                continue
            
            current_keys.add(key)

            if key not in self.previous_data:
                changes['new_items'].append(item)
            else:
                prev_item = self.previous_data[key]
                if item.gst_rate != prev_item.gst_rate:
                    changes['rate_changes'].append(item)
                elif item.data_hash != prev_item.data_hash:
                    changes['modified_items'].append(item)

        # Find removed items
        for key, prev_item in self.previous_data.items():
            if key not in current_keys:
                changes['removed_items'].append(prev_item)

        logger.info(f"Changes detected - New: {len(changes['new_items'])}, "
                   f"Rate changes: {len(changes['rate_changes'])}, "
                   f"Removed: {len(changes['removed_items'])}, "
                   f"Modified: {len(changes['modified_items'])}")

        return changes

    def generate_change_report(self, changes: Dict) -> str:
        """Generate human-readable change report"""
        report = []
        report.append("=" * 80)
        report.append("GST DATA CHANGE REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")

        for change_type, items in changes.items():
            if items:
                report.append(f"\n{change_type.upper().replace('_', ' ')} ({len(items)} items):")
                report.append("-" * 80)
                for item in items[:10]:  # Show first 10
                    report.append(f"  HSN: {item.hsn_code} | {item.item_name} | Rate: {item.gst_rate}%")
                if len(items) > 10:
                    report.append(f"  ... and {len(items) - 10} more")

        return "\n".join(report)


if __name__ == '__main__':
    # Example usage
    extractor = GSTDataExtractor()
    
    # Run extraction
    items = extractor.run_full_extraction()
    
    # Save results
    extractor.save_to_json('gst_data_2025.json')
    extractor.save_to_csv('gst_data_2025.csv')
    
    # Detect changes (if previous data exists)
    detector = GSTChangeDetector('gst_data_2025.json')
    detector.load_previous_data()
    changes = detector.detect_changes(items)
    
    # Print report
    print(detector.generate_change_report(changes))
