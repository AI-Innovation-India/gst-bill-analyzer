"""
Quick test script for Gemini GST Bill Analyzer
"""
import os
from gst_bill_analyzer_gemini import GeminiGSTAnalyzer

# Sample restaurant bill (your use case: Dosa vs Parotta GST)
sample_bill = """
SARAVANA BHAVAN
Chennai, Tamil Nadu
Bill No: SB-12345
Date: 16-Nov-2025

Items:
Masala Dosa x2      ₹120.00
Idli (4 pcs)        ₹50.00
Parotta x3          ₹60.00

Subtotal:           ₹230.00
CGST (2.5%):        ₹5.75
SGST (2.5%):        ₹5.75
Total GST:          ₹11.50
------------------
Grand Total:        ₹241.50

Thank you! Visit again!
"""

print("="*60)
print("TESTING GEMINI GST BILL ANALYZER")
print("="*60)

# Get API key from environment or prompt user
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print("\nWARNING: GOOGLE_API_KEY not found in environment.")
    api_key = input("Please enter your Gemini API key: ").strip()

    if not api_key:
        print("\nERROR: No API key provided. Exiting.")
        print("\nGet your free API key from: https://aistudio.google.com")
        exit(1)

try:
    print("\n[OK] Initializing Gemini analyzer...")
    analyzer = GeminiGSTAnalyzer(api_key=api_key)

    print("[OK] Analyzing bill...")
    result = analyzer.analyze_bill(bill_text=sample_bill)

    print("\n")
    analyzer.print_analysis(result)

    if result.has_discrepancy:
        print("\n[ALERT] THIS IS YOUR USE CASE!")
        print("   Restaurant charged wrong GST on Parotta")
        print("   Parotta should be 0% GST, but they charged 5%")

    print("\n[OK] Test complete!")
    print("\nFull results saved to: bill_analysis_result.json")

except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\nTroubleshooting:")
    print("1. Check your API key is correct")
    print("2. Make sure you have internet connection")
    print("3. Verify the API key has Gemini API enabled")
    import traceback
    traceback.print_exc()
