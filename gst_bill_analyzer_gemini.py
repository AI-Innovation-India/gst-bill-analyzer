"""
GST Bill Analyzer with Google Gemini Integration
Version: 2.0
Purpose: Analyze restaurant bills, extract items, and calculate accurate GST/CGST
Uses: Google Gemini for intelligent item extraction and categorization
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3
from pathlib import Path

# Google Gemini integration
import google.generativeai as genai

# PDF/Image processing
try:
    import pdfplumber
    from PIL import Image
    import pytesseract
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Note: pdfplumber, PIL, and pytesseract not installed. Install for PDF/image support:")
    print("pip install pdfplumber Pillow pytesseract")

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
class BillAnalysisResult:
    """Complete analysis result"""
    bill_number: Optional[str]
    restaurant_name: Optional[str]
    date: Optional[str]
    items: List[BillLineItem]
    subtotal: float
    total_gst_charged: float
    total_cgst_charged: float
    total_sgst_charged: float
    grand_total: float

    # Calculated correct values
    calculated_total_gst: float = 0.0
    calculated_cgst: float = 0.0
    calculated_sgst: float = 0.0
    calculated_grand_total: float = 0.0

    # Discrepancy detection
    has_discrepancy: bool = False
    discrepancy_amount: float = 0.0
    discrepancy_details: List[str] = None

    # Accuracy and validation
    confidence_score: float = 1.0
    warnings: List[str] = None
    gross_amount: float = 0.0
    discount: float = 0.0
    gstin: Optional[str] = None

    def to_dict(self):
        result = {
            'bill_number': self.bill_number,
            'restaurant_name': self.restaurant_name,
            'date': self.date,
            'gstin': self.gstin,
            'items': [item.to_dict() for item in self.items],
            'gross_amount': self.gross_amount,
            'discount': self.discount,
            'subtotal': self.subtotal,
            'bill_charges': {
                'total_gst': self.total_gst_charged,
                'cgst': self.total_cgst_charged,
                'sgst': self.total_sgst_charged,
                'grand_total': self.grand_total
            },
            'correct_calculation': {
                'total_gst': self.calculated_total_gst,
                'cgst': self.calculated_cgst,
                'sgst': self.calculated_sgst,
                'grand_total': self.calculated_grand_total
            },
            'discrepancy': {
                'found': self.has_discrepancy,
                'amount': self.discrepancy_amount,
                'details': self.discrepancy_details or []
            },
            'confidence_score': self.confidence_score,
            'warnings': self.warnings or []
        }
        return result


class GeminiGSTAnalyzer:
    """
    Analyze bills using Google Gemini API and calculate accurate GST
    """

    def __init__(self, api_key: str = None, db_path: str = 'gst_data.db'):
        """
        Initialize the analyzer

        Args:
            api_key: Google Gemini API key (or set GOOGLE_API_KEY env variable)
            db_path: Path to GST database
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Google API key required! "
                "Pass as api_key parameter or set GOOGLE_API_KEY environment variable. "
                "Get your key from: https://aistudio.google.com"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        # Use gemini-2.5-flash - latest stable flash model
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        self.db_path = db_path
        logger.info("Gemini GST Analyzer initialized")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file using Gemini Vision for scanned PDFs"""
        if not PDF_AVAILABLE:
            raise ImportError("PDF support not available. Install: pip install pdfplumber")

        # Try extracting text first
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        # If no text found, it's a scanned PDF - use Gemini Vision
        if not text.strip():
            logger.info("No text layer found in PDF, using Gemini Vision for scanned document")
            return self.extract_text_from_pdf_with_vision(pdf_path)

        return text

    def extract_text_from_pdf_with_vision(self, pdf_path: str) -> str:
        """Extract text from scanned PDF using Gemini Vision API"""
        import google.generativeai as genai
        from PIL import Image
        import io

        # Convert first page of PDF to image
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            # Convert page to image
            img = first_page.to_image(resolution=150)
            pil_image = img.original

        # Use Gemini Vision to extract text from image
        prompt = """Extract ALL text from this bill/invoice image EXACTLY as shown.
        Include:
        - Store/restaurant name
        - Bill number and date
        - ALL items with quantities and prices
        - Subtotal, taxes, discounts, total

        Return the complete text exactly as it appears in the image."""

        response = self.model.generate_content([prompt, pil_image])
        return response.text

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        if not PDF_AVAILABLE:
            raise ImportError("Image support not available. Install: pip install Pillow pytesseract")

        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text

    def analyze_bill_with_gemini(self, bill_text: str) -> Dict:
        """
        Use Gemini to extract structured data from bill text - ANY type of bill
        """
        prompt = f"""
You are an expert Indian tax accountant analyzing bills/invoices for GST compliance.

**CRITICAL ACCURACY REQUIREMENTS:**
1. Extract EXACT numbers from the bill - DO NOT calculate or guess
2. If there are discounts, extract them separately
3. Read ALL line items carefully
4. Preserve exact item names and amounts

**Bill Text:**
{bill_text}

**Extract and return ONLY a valid JSON object with:**
{{
  "store_name": "exact business name from bill",
  "bill_number": "exact bill/invoice number",
  "date": "date in DD/MM/YY or DD-MM-YYYY format",
  "gstin": "GSTIN if shown, else null",
  "items": [
    {{
      "original_name": "EXACT item name from bill",
      "item_name": "cleaned/standardized name",
      "quantity": number (exact quantity shown),
      "unit_price": number (price per unit),
      "total_price": number (quantity × unit_price OR amount shown for this item)
    }}
  ],
  "gross_amount": number (EXACT total of all items BEFORE any discounts),
  "discount": number (EXACT discount amount if shown, else 0),
  "subtotal": number (EXACT subtotal/goods value/taxable amount AFTER discount - READ THIS NUMBER DIRECTLY FROM BILL, do NOT calculate),
  "cgst_charged": number (EXACT CGST from bill, or total_gst/2 if not split),
  "sgst_charged": number (EXACT SGST from bill, or total_gst/2 if not split),
  "igst_charged": number (EXACT IGST if shown, else 0),
  "total_gst_charged": number (EXACT total tax from bill),
  "grand_total": number (EXACT final amount from bill)
}}

**IMPORTANT:**
- Use EXACT numbers from the bill - do NOT recalculate
- If discount exists, include it
- Return ONLY valid JSON, no markdown, no explanations
- All monetary values must match the bill EXACTLY
"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text

            # Remove markdown code blocks if present
            result_text = re.sub(r'```json\s*', '', result_text)
            result_text = re.sub(r'```\s*', '', result_text)

            # Extract JSON from response (Gemini might add markdown formatting)
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                json_text = json_match.group()

                # Sometimes Gemini adds random non-JSON text in the middle of values
                # Look for pattern: "value": number RandomText,
                # Replace with: "value": number,
                json_text = re.sub(r'(\d+\.\d+)\s+[A-Za-z]+\s*}', r'\1}', json_text)
                json_text = re.sub(r'(\d+\.\d+)\s+[A-Za-z]+\s*,', r'\1,', json_text)

                result_json = json.loads(json_text)
                return result_json
            else:
                # Try parsing the whole response
                return json.loads(result_text)

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.error(f"Response was: {response.text if 'response' in locals() else 'No response'}")
            raise

    def get_correct_gst_rate(self, item_name: str) -> Tuple[float, Optional[str], Optional[str]]:
        """
        Look up correct GST rate from database
        Returns: (gst_rate, hsn_code, category)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Search for item in database
            cursor.execute("""
                SELECT gst_rate, hsn_code, item_category
                FROM gst_items
                WHERE LOWER(item_name) LIKE ? OR LOWER(item_category) LIKE ?
                LIMIT 1
            """, (f'%{item_name.lower()}%', f'%{item_name.lower()}%'))

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0], result[1], result[2]

            # Expanded category keywords for better detection
            item_lower = item_name.lower()

            # Dry fruits and nuts (5% or 12% GST depending on packaging)
            dry_fruits_keywords = ['cashew', 'almond', 'walnut', 'dates', 'raisin', 'pistachio',
                                   'badam', 'kaju', 'pista', 'kishmish', 'anjeer', 'fig',
                                   'mixed nuts', 'mixed bites', 'dry fruit']
            for keyword in dry_fruits_keywords:
                if keyword in item_lower:
                    return 5.0, '08013200', "Dry fruits and nuts"

            # Electronics (18% or 28% GST)
            electronics_keywords = ['mobile', 'phone', 'laptop', 'computer', 'charger', 'earphone',
                                   'headphone', 'tv', 'television', 'ac', 'refrigerator', 'washing machine']
            for keyword in electronics_keywords:
                if keyword in item_lower:
                    return 18.0, None, "Electronics"

            # Medical items (5% or 12% GST, some exempt)
            medical_keywords = ['medicine', 'tablet', 'syrup', 'injection', 'capsule',
                               'test', 'pathology', 'xray', 'scan']
            for keyword in medical_keywords:
                if keyword in item_lower:
                    return 12.0, None, "Medical supplies"

            # Fresh food items (0% GST)
            food_items_0_percent = ['parotta', 'chapati', 'roti', 'bread', 'milk', 'curd',
                                   'vegetables', 'fruits', 'eggs']
            for item in food_items_0_percent:
                if item in item_lower:
                    return 0.0, None, "Food items (fresh)"

            # Restaurant services (5% GST)
            food_items_5_percent = ['dosa', 'idli', 'vada', 'rice', 'dal', 'sambar',
                                   'biryani', 'curry', 'meal', 'coffee', 'tea']
            for item in food_items_5_percent:
                if item in item_lower:
                    return 5.0, None, "Restaurant services"

            # Default for unknown items - use 5% as safest assumption
            logger.warning(f"Unknown item category for '{item_name}', defaulting to 5% GST")
            return 5.0, None, "Unknown (default 5%)"

        except Exception as e:
            logger.error(f"Error looking up GST rate: {e}")
            # Default fallback
            return 5.0, None, "Unknown"

    def validate_extraction(self, gemini_result: Dict, items: List[BillLineItem]) -> Tuple[float, List[str]]:
        """
        Validate extracted data and calculate confidence score
        Returns: (confidence_score, warnings_list)
        """
        warnings = []
        confidence = 1.0

        # Extract values
        gross_amount = float(gemini_result.get('gross_amount', 0))
        discount = float(gemini_result.get('discount', 0))
        subtotal = float(gemini_result.get('subtotal', 0))
        total_gst = float(gemini_result.get('total_gst_charged', 0))
        grand_total = float(gemini_result.get('grand_total', 0))

        # Check 1: Do items sum to gross amount?
        items_total = sum(item.total_price for item in items)
        if abs(items_total - gross_amount) > 1:
            warnings.append(f"⚠️ Items sum (₹{items_total:.2f}) ≠ Gross amount (₹{gross_amount:.2f})")
            confidence -= 0.15

        # Check 2: Does discount math make sense?
        expected_subtotal = gross_amount - discount
        # Allow up to Rs 30 difference for rounding on large discounts
        tolerance = 30.0 if discount > 100 else 1.0
        if abs(expected_subtotal - subtotal) > tolerance:
            warnings.append(f"⚠️ Gross (₹{gross_amount:.2f}) - Discount (₹{discount:.2f}) ≠ Subtotal (₹{subtotal:.2f})")
            confidence -= 0.15
        elif abs(expected_subtotal - subtotal) > 1.0:
            # Minor rounding difference - just note it, don't penalize heavily
            warnings.append(f"ℹ️ Minor rounding difference: Gross - Discount = ₹{expected_subtotal:.2f}, Bill shows ₹{subtotal:.2f}")
            confidence -= 0.05

        # Check 3: Does final math add up?
        calculated_total = subtotal + total_gst
        if abs(calculated_total - grand_total) > 1:
            warnings.append(f"⚠️ Subtotal + GST (₹{calculated_total:.2f}) ≠ Grand Total (₹{grand_total:.2f})")
            confidence -= 0.20

        # Check 4: Is GST percentage reasonable?
        if subtotal > 0:
            gst_percent = (total_gst / subtotal) * 100
            valid_gst_rates = [0, 5, 12, 18, 28]
            # Allow 0.5% tolerance for rounding
            if not any(abs(gst_percent - rate) < 0.5 for rate in valid_gst_rates):
                warnings.append(f"⚠️ Unusual GST rate: {gst_percent:.1f}% (expected: 0%, 5%, 12%, 18%, or 28%)")
                confidence -= 0.10

        # Check 5: Are there any missing critical fields?
        if not gemini_result.get('store_name'):
            warnings.append("⚠️ Store name not found")
            confidence -= 0.05
        if not gemini_result.get('bill_number'):
            warnings.append("⚠️ Bill number not found")
            confidence -= 0.05

        # Ensure confidence is between 0 and 1
        confidence = max(0.0, min(1.0, confidence))

        return confidence, warnings

    def calculate_correct_gst(self, items: List[BillLineItem], subtotal_after_discount: float) -> Tuple[float, float, float]:
        """
        Calculate what the GST SHOULD be for all items
        IMPORTANT: GST in India is calculated on the amount AFTER discount

        Args:
            items: List of bill items with GST rates
            subtotal_after_discount: Total amount after applying discounts

        Returns: (total_gst, cgst, sgst)
        """
        # Calculate weighted average GST rate based on items
        total_item_amount = sum(item.total_price for item in items)

        if total_item_amount == 0:
            return 0.0, 0.0, 0.0

        # Calculate weighted GST rate
        weighted_gst_rate = 0.0
        for item in items:
            if item.gst_rate is not None:
                weight = item.total_price / total_item_amount
                weighted_gst_rate += item.gst_rate * weight

        # Apply GST to the discounted amount
        total_gst = (subtotal_after_discount * weighted_gst_rate) / 100

        # For intrastate transactions, GST is split equally into CGST and SGST
        cgst = total_gst / 2
        sgst = total_gst / 2

        return round(total_gst, 2), round(cgst, 2), round(sgst, 2)

    def analyze_bill(
        self,
        bill_text: str = None,
        pdf_path: str = None,
        image_path: str = None
    ) -> BillAnalysisResult:
        """
        Complete bill analysis workflow

        Args:
            bill_text: Raw text of bill (if you already have it)
            pdf_path: Path to PDF file
            image_path: Path to image file (jpg, png, etc.)

        Returns:
            BillAnalysisResult with complete analysis
        """
        # Step 1: Get bill text
        if bill_text is None:
            if pdf_path:
                logger.info(f"Extracting text from PDF: {pdf_path}")
                bill_text = self.extract_text_from_pdf(pdf_path)
            elif image_path:
                logger.info(f"Extracting text from image: {image_path}")
                bill_text = self.extract_text_from_image(image_path)
            else:
                raise ValueError("Provide bill_text, pdf_path, or image_path")

        logger.info("Analyzing bill with Gemini...")

        # Step 2: Use Gemini to extract structured data
        gemini_result = self.analyze_bill_with_gemini(bill_text)

        # Step 3: Extract discount and amounts
        gross_amount = float(gemini_result.get('gross_amount', 0))
        discount = float(gemini_result.get('discount', 0))
        subtotal = float(gemini_result.get('subtotal', 0))
        gstin = gemini_result.get('gstin')

        # Step 4: Look up correct GST rates for each item
        items = []
        for item_data in gemini_result.get('items', []):
            item_name = item_data.get('item_name', '')
            gst_rate, hsn_code, category = self.get_correct_gst_rate(item_name)

            total_price = float(item_data.get('total_price', 0))

            # Calculate what GST would be for this item at its price
            # (Note: actual GST calculation happens on discounted total)
            item_gst = (total_price * gst_rate) / 100

            item = BillLineItem(
                item_name=item_name,
                original_name=item_data.get('original_name', item_name),
                quantity=float(item_data.get('quantity', 1)),
                unit_price=float(item_data.get('unit_price', 0)),
                total_price=total_price,
                hsn_code=hsn_code,
                gst_rate=gst_rate,
                cgst=round(item_gst / 2, 2),
                sgst=round(item_gst / 2, 2),
                category=category
            )
            items.append(item)

        # Step 5: Validate extraction and calculate confidence
        confidence_score, validation_warnings = self.validate_extraction(gemini_result, items)

        # Step 6: Calculate correct GST on discounted amount
        # CRITICAL: GST in India is calculated AFTER applying discount
        calculated_gst, calculated_cgst, calculated_sgst = self.calculate_correct_gst(items, subtotal)
        calculated_total = round(subtotal + calculated_gst, 2)

        # Step 7: Compare with bill's charges
        bill_gst = float(gemini_result.get('total_gst_charged', 0))
        bill_total = float(gemini_result.get('grand_total', 0))

        discrepancy_amount = round(bill_gst - calculated_gst, 2)
        has_discrepancy = abs(discrepancy_amount) > 0.01  # Allow 1 paisa tolerance

        discrepancy_details = []
        if has_discrepancy:
            discrepancy_details.append(
                f"Bill charged ₹{bill_gst} GST, but should be ₹{calculated_gst}"
            )
            discrepancy_details.append(
                f"Overcharged by ₹{abs(discrepancy_amount)}" if discrepancy_amount > 0
                else f"Undercharged by ₹{abs(discrepancy_amount)}"
            )

            # Find which items have wrong GST
            for item in items:
                if item.gst_rate == 0 and bill_gst > 0:
                    discrepancy_details.append(
                        f"'{item.item_name}' should have 0% GST (charged on bill)"
                    )

        # Add discount information to discrepancy details if significant
        if discount > 0:
            discrepancy_details.insert(0, f"Discount applied: ₹{discount:.2f} ({(discount/gross_amount*100):.1f}%)")

        # Step 8: Create result with validation data
        result = BillAnalysisResult(
            bill_number=gemini_result.get('bill_number'),
            restaurant_name=gemini_result.get('store_name'),  # Fixed: use 'store_name' from prompt
            date=gemini_result.get('date'),
            gstin=gstin,
            items=items,
            gross_amount=gross_amount,
            discount=discount,
            subtotal=subtotal,
            total_gst_charged=bill_gst,
            total_cgst_charged=float(gemini_result.get('cgst_charged', bill_gst/2)),
            total_sgst_charged=float(gemini_result.get('sgst_charged', bill_gst/2)),
            grand_total=bill_total,
            calculated_total_gst=calculated_gst,
            calculated_cgst=calculated_cgst,
            calculated_sgst=calculated_sgst,
            calculated_grand_total=calculated_total,
            has_discrepancy=has_discrepancy,
            discrepancy_amount=discrepancy_amount,
            discrepancy_details=discrepancy_details,
            confidence_score=confidence_score,
            warnings=validation_warnings
        )

        logger.info(f"Analysis complete. Discrepancy: {has_discrepancy}")
        return result

    def print_analysis(self, result: BillAnalysisResult):
        """Print analysis in readable format"""
        print("\n" + "="*70)
        print("GST BILL ANALYSIS REPORT")
        print("="*70)

        if result.restaurant_name:
            print(f"\nBusiness: {result.restaurant_name}")
        if result.gstin:
            print(f"GSTIN: {result.gstin}")
        if result.bill_number:
            print(f"Bill Number: {result.bill_number}")
        if result.date:
            print(f"Date: {result.date}")

        # Confidence score
        confidence_pct = result.confidence_score * 100
        confidence_emoji = "🟢" if confidence_pct >= 90 else "🟡" if confidence_pct >= 70 else "🔴"
        print(f"\nConfidence Score: {confidence_emoji} {confidence_pct:.1f}%")

        # Warnings
        if result.warnings:
            print(f"\n⚠️  VALIDATION WARNINGS:")
            for warning in result.warnings:
                print(f"   {warning}")

        print(f"\n{'Item':<30} {'Qty':<8} {'Price':<10} {'Category':<20} {'GST%':<8}")
        print("-" * 80)

        for item in result.items:
            print(f"{item.item_name:<30} {item.quantity:<8.0f} ₹{item.total_price:<9.2f} "
                  f"{(item.category or 'Unknown'):<20} {item.gst_rate or 0:<7.1f}%")

        print("-" * 80)
        print(f"{'Gross Amount:':<48} ₹{result.gross_amount:.2f}")
        if result.discount > 0:
            discount_pct = (result.discount / result.gross_amount * 100) if result.gross_amount > 0 else 0
            print(f"{'Discount:':<48} -₹{result.discount:.2f} ({discount_pct:.1f}%)")
        print(f"{'Subtotal (after discount):':<48} ₹{result.subtotal:.2f}")
        print(f"{'GST (Bill charged):':<48} ₹{result.total_gst_charged:.2f}")
        print(f"{'GST (Correct calculation):':<48} ₹{result.calculated_total_gst:.2f}")
        print(f"{'Grand Total (Bill):':<48} ₹{result.grand_total:.2f}")

        if result.has_discrepancy:
            print(f"\n⚠️  DISCREPANCY DETECTED:")
            print(f"   Difference: ₹{abs(result.discrepancy_amount):.2f}")
            for detail in result.discrepancy_details:
                print(f"   - {detail}")
        else:
            print(f"\n✓ Bill GST is correct!")

        # Legal readiness warning
        if confidence_pct < 90:
            print(f"\n⚠️  WARNING: Confidence below 90% - NOT recommended for legal disputes")
            print(f"   Please verify the extracted data manually before taking action")

        print("\n" + "="*70)


# Example usage
if __name__ == '__main__':
    # Example 1: Analyze text bill
    sample_bill = """
    SARAVANA BHAVAN
    Bill No: 12345
    Date: 16-Nov-2025

    Masala Dosa x2    ₹120
    Idli (4 pcs)      ₹50
    Parotta x3        ₹60

    Subtotal:         ₹230
    GST (5%):         ₹11.50
    Total:            ₹241.50
    """

    # Set your API key (or use environment variable GOOGLE_API_KEY)
    api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key:
        print("\n⚠️  Please set your Google API key:")
        print("   export GOOGLE_API_KEY='your-key-here'")
        print("\n   Or pass it to the analyzer:")
        print("   analyzer = GeminiGSTAnalyzer(api_key='your-key')")
        print("\n   Get your key from: https://aistudio.google.com")
    else:
        try:
            analyzer = GeminiGSTAnalyzer(api_key=api_key)
            result = analyzer.analyze_bill(bill_text=sample_bill)
            analyzer.print_analysis(result)

            # Also save as JSON
            with open('bill_analysis_result.json', 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            print("\n✓ Detailed results saved to: bill_analysis_result.json")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Analysis failed: {e}", exc_info=True)
