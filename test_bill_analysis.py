"""
Test script for analyzing Bill.pdf with updated analyzer
"""
import os
import json
from gst_bill_analyzer_gemini import GeminiGSTAnalyzer

def main():
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set")
        return

    print("="*70)
    print("Testing Updated GST Bill Analyzer")
    print("="*70)

    analyzer = GeminiGSTAnalyzer(api_key=api_key)

    # Test with Bill.pdf
    print("\nAnalyzing Bill.pdf (Jazz Dates and Nuts)...")
    result = analyzer.analyze_bill(pdf_path='Bill.pdf')

    # Print results without emojis for Windows console
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
    confidence_label = "HIGH" if confidence_pct >= 90 else "MEDIUM" if confidence_pct >= 70 else "LOW"
    print(f"\nConfidence Score: [{confidence_label}] {confidence_pct:.1f}%")

    # Warnings
    if result.warnings:
        print(f"\nVALIDATION WARNINGS:")
        for warning in result.warnings:
            # Remove emojis/Unicode for Windows console
            warning_clean = warning.replace('⚠️', '!').replace('ℹ️', 'i').replace('₹', 'Rs ').replace('≠', '!=')
            print(f"   {warning_clean}")

    print(f"\n{'Item':<30} {'Qty':<8} {'Price':<10} {'Category':<20} {'GST%':<8}")
    print("-" * 80)

    for item in result.items:
        print(f"{item.item_name:<30} {item.quantity:<8.0f} Rs {item.total_price:<9.2f} "
              f"{(item.category or 'Unknown'):<20} {item.gst_rate or 0:<7.1f}%")

    print("-" * 80)
    print(f"{'Gross Amount:':<48} Rs {result.gross_amount:.2f}")
    if result.discount > 0:
        discount_pct = (result.discount / result.gross_amount * 100) if result.gross_amount > 0 else 0
        print(f"{'Discount:':<48} -Rs {result.discount:.2f} ({discount_pct:.1f}%)")
    print(f"{'Subtotal (after discount):':<48} Rs {result.subtotal:.2f}")
    print(f"{'GST (Bill charged):':<48} Rs {result.total_gst_charged:.2f}")
    print(f"{'GST (Correct calculation):':<48} Rs {result.calculated_total_gst:.2f}")
    print(f"{'Grand Total (Bill):':<48} Rs {result.grand_total:.2f}")

    if result.has_discrepancy:
        print(f"\nDISCREPANCY DETECTED:")
        print(f"   Difference: Rs {abs(result.discrepancy_amount):.2f}")
        for detail in result.discrepancy_details:
            # Remove Unicode symbols for Windows console
            detail_clean = detail.replace('₹', 'Rs ').replace('⚠️', '!')
            print(f"   - {detail_clean}")
    else:
        print(f"\nBill GST is correct!")

    # Legal readiness warning
    if confidence_pct < 90:
        print(f"\nWARNING: Confidence below 90% - NOT recommended for legal disputes")
        print(f"Please verify the extracted data manually before taking action")

    print("\n" + "="*70)

    # Save detailed JSON
    with open('bill_analysis_result_updated.json', 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    print("\nDetailed results saved to: bill_analysis_result_updated.json")

if __name__ == '__main__':
    main()
