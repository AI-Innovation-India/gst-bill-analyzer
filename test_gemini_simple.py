"""
Simple Gemini test that avoids encoding issues
"""
import os
import json
from gst_bill_analyzer_gemini import GeminiGSTAnalyzer

# Sample bill
sample_bill = """
SARAVANA BHAVAN
Chennai, Tamil Nadu
Bill No: SB-12345
Date: 16-Nov-2025

Items:
Masala Dosa x2      Rs.120.00
Idli (4 pcs)        Rs.50.00
Parotta x3          Rs.60.00

Subtotal:           Rs.230.00
CGST (2.5%):        Rs.5.75
SGST (2.5%):        Rs.5.75
Total GST:          Rs.11.50
------------------
Grand Total:        Rs.241.50
"""

print("="*60)
print("GEMINI GST BILL ANALYZER - SIMPLE TEST")
print("="*60)

api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyBK43ALMA_VriahnZ0hJdnl2-J6zXxBqhE')

try:
    print("\n[1/3] Initializing analyzer...")
    analyzer = GeminiGSTAnalyzer(api_key=api_key)

    print("[2/3] Analyzing bill with Gemini AI...")
    result = analyzer.analyze_bill(bill_text=sample_bill)

    print("[3/3] Saving results...")

    # Save to JSON
    with open('bill_analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    # Print key results
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    print(f"\nRestaurant: {result.restaurant_name}")
    print(f"Bill Number: {result.bill_number}")
    print(f"Date: {result.date}")
    print(f"\nItems analyzed: {len(result.items)}")
    print(f"Subtotal: Rs.{result.subtotal:.2f}")
    print(f"\nGST charged on bill: Rs.{result.total_gst_charged:.2f}")
    print(f"Correct GST should be: Rs.{result.calculated_total_gst:.2f}")

    if result.has_discrepancy:
        print(f"\n*** DISCREPANCY FOUND ***")
        print(f"Difference: Rs.{abs(result.discrepancy_amount):.2f}")
        if result.discrepancy_amount > 0:
            print("You were OVERCHARGED!")
        else:
            print("You were UNDERCHARGED")
        print(f"\nDetails:")
        for detail in result.discrepancy_details:
            print(f"  - {detail}")
    else:
        print(f"\nNo discrepancy found - bill GST is correct!")

    print(f"\nFull results saved to: bill_analysis_result.json")
    print("="*60)
    print("\n*** SUCCESS! Gemini integration working perfectly! ***\n")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
