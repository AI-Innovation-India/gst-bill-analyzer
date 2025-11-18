"""
GST Bill Analyzer with LLM Integration
Version: 1.0
Purpose: Analyze restaurant bills, extract items, and calculate accurate GST/CGST
Uses: OpenAI GPT-4 for intelligent item extraction and categorization
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
from pathlib import Path

# OpenAI integration
import openai
from openai import OpenAI

# PDF/Image processing
import pdfplumber
from PIL import Image
import pytesseract

# Our GST database
from gst_api_service import GSTDatabase

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BillLineItem:
    """Individual item from a bill"""
    item_name: str
    original_name: str  # As written on bill
    quantity: float
    unit_price: float
    total_price: float
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = None
    cgst: Optional[float] = None
    sgst: Optional[float] = None
    category: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class BillAnalysis:
    """Complete bill analysis result"""
    bill_number: str
    vendor_name: str
    bill_date: str
    items: List[BillLineItem]
    subtotal: float
    total_gst_claimed: float
    total_cgst_claimed: float
    total_sgst_claimed: float
    total_amount: float
    
    # Calculated values
    calculated_gst: float
    calculated_cgst: float
    calculated_sgst: float
    discrepancy: float
    
    # Breakdown by rate
    gst_breakdown: Dict[str, Dict]
    
    def to_dict(self):
        return {
            **asdict(self),
            'items': [item.to_dict() for item in self.items]
        }


class LLMBillAnalyzer:
    """
    Intelligent bill analyzer using LLM for item extraction and GST calculation
    """
    
    def __init__(self, openai_api_key: str = None, db_path: str = 'gst_data.db'):
        # Initialize OpenAI
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize GST database
        self.gst_db = GSTDatabase(db_path)
        
        # Food category HSN mappings (common restaurant items)
        self.food_hsn_mapping = {
            'rice_based': '1006',      # Rice preparations
            'wheat_based': '1101',     # Wheat preparations  
            'bread': '1905',           # Bread, pastry
            'snacks': '2106',          # Food preparations
            'beverages': '2202',       # Non-alcoholic beverages
            'sweets': '1704',          # Sugar confectionery
            'dairy': '0402',           # Milk products
        }

    def analyze_bill(self, 
                    bill_path: str = None, 
                    bill_text: str = None,
                    bill_image: str = None) -> BillAnalysis:
        """
        Analyze a bill from file path, text, or image
        
        Args:
            bill_path: Path to PDF/image bill
            bill_text: Raw text of bill
            bill_image: Path to image file
            
        Returns:
            BillAnalysis object with complete breakdown
        """
        
        # Step 1: Extract text from bill
        if bill_text:
            extracted_text = bill_text
        elif bill_path:
            extracted_text = self._extract_text_from_file(bill_path)
        elif bill_image:
            extracted_text = self._extract_text_from_image(bill_image)
        else:
            raise ValueError("Provide bill_path, bill_text, or bill_image")
        
        logger.info("Extracted bill text successfully")
        
        # Step 2: Use LLM to parse bill structure
        parsed_bill = self._parse_bill_with_llm(extracted_text)
        
        # Step 3: Classify items and get GST rates
        classified_items = self._classify_items_with_llm(parsed_bill['items'])
        
        # Step 4: Calculate accurate GST
        analysis = self._calculate_gst_breakdown(
            parsed_bill, 
            classified_items
        )
        
        return analysis

    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or image"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            return self._extract_text_from_image(file_path)
        else:
            # Try reading as text file
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

    def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text

    def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR (Tesseract)"""
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text

    def _parse_bill_with_llm(self, bill_text: str) -> Dict:
        """
        Use GPT-4 to intelligently parse bill structure
        """
        
        prompt = f"""You are an expert at analyzing restaurant bills from India. 
Extract the following information from this bill in JSON format:

1. bill_number: The invoice/bill number
2. vendor_name: Restaurant/vendor name
3. bill_date: Date of bill (ISO format YYYY-MM-DD)
4. items: List of items with:
   - item_name: Name of the dish/item
   - quantity: Quantity ordered
   - unit_price: Price per unit
   - total_price: Total for this line item
5. subtotal: Subtotal before tax
6. gst_amount: Total GST charged (if mentioned)
7. cgst_amount: CGST charged (if mentioned)
8. sgst_amount: SGST charged (if mentioned)
9. total_amount: Final total amount

Bill Text:
{bill_text}

Return ONLY valid JSON, no other text.
"""

        response = self.client.chat.completions.create(
            model="gpt-4o",  # or "gpt-4-turbo" or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a precise bill parsing assistant. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Parsed bill: {result.get('vendor_name')} - {len(result.get('items', []))} items")
        
        return result

    def _classify_items_with_llm(self, items: List[Dict]) -> List[BillLineItem]:
        """
        Use LLM to classify food items and determine GST rates
        """
        
        # Create classification prompt
        item_names = [item['item_name'] for item in items]
        
        prompt = f"""You are a GST expert for Indian restaurant items. Classify these food items according to Indian GST rules.

For each item, determine:
1. category: One of [rice_based, wheat_based, bread, snacks, beverages, sweets, dairy, other]
2. is_prepared: Is it a prepared/cooked food item? (true/false)
3. standard_gst_rate: Applicable GST rate (0, 5, 12, 18, 28)

GST Rules for Reference:
- Plain roti/chapati, plain dosa, plain idli = 5% (basic prepared food)
- Parotta/paratha (with oil/ghee) = 0% (considered unprepared)
- Rice preparations = 5%
- Snacks, fried items = 5%
- Beverages (tea, coffee, juice) = 5%
- Packaged items = Usually 12% or 18%
- Restaurant service charge = 18%

Items to classify:
{json.dumps(item_names, indent=2)}

Return ONLY valid JSON array with classification for each item.
Format: [{{"item_name": "...", "category": "...", "is_prepared": true/false, "standard_gst_rate": 5}}]
"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a GST classification expert. Always return valid JSON array."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result_json = json.loads(response.choices[0].message.content)
        
        # Handle if wrapped in object
        if 'items' in result_json:
            classifications = result_json['items']
        elif 'classifications' in result_json:
            classifications = result_json['classifications']
        else:
            # Assume it's the array directly
            classifications = result_json if isinstance(result_json, list) else []
        
        # Match classifications to original items
        classified_items = []
        for i, item in enumerate(items):
            classification = classifications[i] if i < len(classifications) else {}
            
            # Get HSN code based on category
            category = classification.get('category', 'other')
            hsn_code = self.food_hsn_mapping.get(category, '2106')
            
            # Create BillLineItem
            bill_item = BillLineItem(
                item_name=classification.get('item_name', item['item_name']),
                original_name=item['item_name'],
                quantity=float(item.get('quantity', 1)),
                unit_price=float(item.get('unit_price', 0)),
                total_price=float(item.get('total_price', 0)),
                hsn_code=hsn_code,
                gst_rate=float(classification.get('standard_gst_rate', 5)),
                category=category
            )
            
            # Calculate GST for this item
            gst_amount = (bill_item.total_price * bill_item.gst_rate) / 100
            bill_item.cgst = gst_amount / 2
            bill_item.sgst = gst_amount / 2
            
            classified_items.append(bill_item)
            
            logger.info(f"Classified: {bill_item.item_name} -> {bill_item.gst_rate}% GST")
        
        return classified_items

    def _calculate_gst_breakdown(self, 
                                 parsed_bill: Dict, 
                                 items: List[BillLineItem]) -> BillAnalysis:
        """
        Calculate accurate GST breakdown and compare with bill
        """
        
        # Calculate totals
        subtotal = sum(item.total_price for item in items)
        calculated_cgst = sum(item.cgst or 0 for item in items)
        calculated_sgst = sum(item.sgst or 0 for item in items)
        calculated_gst = calculated_cgst + calculated_sgst
        
        # Get claimed amounts from bill
        total_gst_claimed = float(parsed_bill.get('gst_amount', 0))
        total_cgst_claimed = float(parsed_bill.get('cgst_amount', 0))
        total_sgst_claimed = float(parsed_bill.get('sgst_amount', 0))
        
        # If only total GST given, split it
        if total_gst_claimed > 0 and total_cgst_claimed == 0:
            total_cgst_claimed = total_gst_claimed / 2
            total_sgst_claimed = total_gst_claimed / 2
        
        # Calculate discrepancy
        discrepancy = calculated_gst - total_gst_claimed
        
        # Create breakdown by rate
        gst_breakdown = {}
        for item in items:
            rate_key = f"{item.gst_rate}%"
            if rate_key not in gst_breakdown:
                gst_breakdown[rate_key] = {
                    'rate': item.gst_rate,
                    'items': [],
                    'subtotal': 0,
                    'cgst': 0,
                    'sgst': 0,
                    'total_gst': 0
                }
            
            gst_breakdown[rate_key]['items'].append(item.item_name)
            gst_breakdown[rate_key]['subtotal'] += item.total_price
            gst_breakdown[rate_key]['cgst'] += item.cgst or 0
            gst_breakdown[rate_key]['sgst'] += item.sgst or 0
            gst_breakdown[rate_key]['total_gst'] += (item.cgst or 0) + (item.sgst or 0)
        
        return BillAnalysis(
            bill_number=parsed_bill.get('bill_number', 'N/A'),
            vendor_name=parsed_bill.get('vendor_name', 'Unknown'),
            bill_date=parsed_bill.get('bill_date', datetime.now().date().isoformat()),
            items=items,
            subtotal=subtotal,
            total_gst_claimed=total_gst_claimed,
            total_cgst_claimed=total_cgst_claimed,
            total_sgst_claimed=total_sgst_claimed,
            total_amount=float(parsed_bill.get('total_amount', subtotal + total_gst_claimed)),
            calculated_gst=calculated_gst,
            calculated_cgst=calculated_cgst,
            calculated_sgst=calculated_sgst,
            discrepancy=discrepancy,
            gst_breakdown=gst_breakdown
        )

    def generate_report(self, analysis: BillAnalysis, output_format: str = 'text') -> str:
        """
        Generate detailed GST analysis report
        """
        
        if output_format == 'json':
            return json.dumps(analysis.to_dict(), indent=2)
        
        # Text report
        report = []
        report.append("=" * 80)
        report.append("GST BILL ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Vendor: {analysis.vendor_name}")
        report.append(f"Bill Number: {analysis.bill_number}")
        report.append(f"Date: {analysis.bill_date}")
        report.append("")
        
        # Items table
        report.append("LINE ITEMS:")
        report.append("-" * 80)
        report.append(f"{'Item':<30} {'Qty':<8} {'Price':<10} {'GST%':<8} {'CGST':<10} {'SGST':<10}")
        report.append("-" * 80)
        
        for item in analysis.items:
            report.append(
                f"{item.item_name[:30]:<30} "
                f"{item.quantity:<8.2f} "
                f"₹{item.total_price:<9.2f} "
                f"{item.gst_rate:<8.1f} "
                f"₹{item.cgst or 0:<9.2f} "
                f"₹{item.sgst or 0:<9.2f}"
            )
        
        report.append("-" * 80)
        report.append("")
        
        # GST Breakdown by Rate
        report.append("GST BREAKDOWN BY RATE:")
        report.append("-" * 80)
        
        for rate_key, data in sorted(analysis.gst_breakdown.items()):
            report.append(f"\n{rate_key} GST Items:")
            report.append(f"  Items: {', '.join(data['items'])}")
            report.append(f"  Subtotal: ₹{data['subtotal']:.2f}")
            report.append(f"  CGST: ₹{data['cgst']:.2f}")
            report.append(f"  SGST: ₹{data['sgst']:.2f}")
            report.append(f"  Total GST: ₹{data['total_gst']:.2f}")
        
        report.append("")
        report.append("=" * 80)
        report.append("SUMMARY:")
        report.append("-" * 80)
        report.append(f"Subtotal (before GST):        ₹{analysis.subtotal:.2f}")
        report.append(f"")
        report.append(f"GST Claimed on Bill:")
        report.append(f"  CGST:                       ₹{analysis.total_cgst_claimed:.2f}")
        report.append(f"  SGST:                       ₹{analysis.total_sgst_claimed:.2f}")
        report.append(f"  Total GST:                  ₹{analysis.total_gst_claimed:.2f}")
        report.append(f"")
        report.append(f"GST Calculated (Item-wise):")
        report.append(f"  CGST:                       ₹{analysis.calculated_cgst:.2f}")
        report.append(f"  SGST:                       ₹{analysis.calculated_sgst:.2f}")
        report.append(f"  Total GST:                  ₹{analysis.calculated_gst:.2f}")
        report.append(f"")
        
        # Discrepancy
        if abs(analysis.discrepancy) > 0.01:
            report.append(f"⚠️  DISCREPANCY FOUND:          ₹{analysis.discrepancy:.2f}")
            if analysis.discrepancy > 0:
                report.append(f"   (Bill undercharged GST)")
            else:
                report.append(f"   (Bill overcharged GST)")
        else:
            report.append(f"✅ No discrepancy - GST correctly calculated")
        
        report.append(f"")
        report.append(f"Total Amount:                 ₹{analysis.total_amount:.2f}")
        report.append("=" * 80)
        
        return "\n".join(report)


# ============================================================================
# Example Usage & Testing
# ============================================================================

def example_usage():
    """
    Example: Analyze a restaurant bill
    """
    
    # Initialize analyzer
    analyzer = LLMBillAnalyzer(
        openai_api_key="your-openai-api-key",  # or set OPENAI_API_KEY env var
        db_path="gst_data.db"
    )
    
    # Example bill text
    sample_bill = """
    SARAVANA BHAVAN
    Invoice #: SB-2025-1234
    Date: 2025-11-15
    
    Items:
    1. Plain Dosa          x2    ₹60  = ₹120
    2. Idli (4pcs)         x1    ₹50  = ₹50
    3. Parotta             x3    ₹20  = ₹60
    4. Coffee              x2    ₹30  = ₹60
    
    Subtotal:                      ₹290
    CGST @5%:                      ₹11.50
    SGST @5%:                      ₹11.50
    Total:                         ₹313
    """
    
    # Analyze bill
    analysis = analyzer.analyze_bill(bill_text=sample_bill)
    
    # Generate report
    report = analyzer.generate_report(analysis)
    print(report)
    
    # Save as JSON
    with open('bill_analysis.json', 'w') as f:
        f.write(analyzer.generate_report(analysis, output_format='json'))
    
    print("\n✅ Analysis saved to bill_analysis.json")


if __name__ == '__main__':
    # Set your OpenAI API key
    os.environ['OPENAI_API_KEY'] = 'your-api-key-here'
    
    example_usage()
