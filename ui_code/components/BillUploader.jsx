import React, { useState } from 'react';
import { analyzeBill, analyzeBillFile } from '../services/api';

// Format API response to display in textarea
const formatApiResponse = (apiResponse) => {
  if (!apiResponse) return '';

  const {
    restaurant_name,
    bill_number,
    date,
    gstin,
    items,
    gross_amount,
    discount,
    subtotal,
    bill_charges
  } = apiResponse;

  let bill = `${restaurant_name || 'BILL'}\n`;
  if (gstin) {
    bill += `GSTIN: ${gstin}\n`;
  }
  if (bill_number) {
    bill += `Bill No: ${bill_number}\n`;
  }
  if (date) {
    bill += `Date: ${date}\n\n`;
  }

  bill += 'Items:\n';

  if (items && items.length > 0) {
    items.forEach(item => {
      const qty = item.quantity || 1;
      const price = item.total_price || 0;
      const itemName = item.item_name || item.original_name || 'Unknown';
      bill += `${itemName} x${qty.toFixed(2)}      ₹${price.toFixed(2)}\n`;
    });
  }

  bill += '\n';
  if (gross_amount) {
    bill += `Gross Amount:       ₹${gross_amount.toFixed(2)}\n`;
  }
  if (discount > 0) {
    bill += `Discount:           -₹${discount.toFixed(2)}\n`;
  }
  bill += `Subtotal:           ₹${(subtotal || 0).toFixed(2)}\n`;

  if (bill_charges) {
    bill += `CGST:               ₹${(bill_charges.cgst || 0).toFixed(2)}\n`;
    bill += `SGST:               ₹${(bill_charges.sgst || 0).toFixed(2)}\n`;
    bill += `Total GST:          ₹${(bill_charges.total_gst || 0).toFixed(2)}\n`;
    bill += '------------------\n';
    bill += `Grand Total:        ₹${(bill_charges.grand_total || 0).toFixed(2)}\n`;
  }

  return bill;
};

function BillUploader({ onAnalysisComplete }) {
  const [billText, setBillText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const sampleBill = `SARAVANA BHAVAN
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

Thank you! Visit again!`;

  const handleAnalyze = async () => {
    if (!billText.trim()) {
      setError('Please enter bill text or upload a file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await analyzeBill(billText);
      onAnalysisComplete(result);
    } catch (err) {
      setError(err.message || 'Failed to analyze bill. Make sure the API is running on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['.pdf', '.jpg', '.jpeg', '.png'];
    const fileName = file.name.toLowerCase();
    const isValid = validTypes.some(type => fileName.endsWith(type));

    if (!isValid) {
      setError('Please upload a PDF, JPG, JPEG, or PNG file.');
      return;
    }

    setSelectedFile(file);
    setError('📝 File upload is temporarily unavailable in production.\n\nPlease use:\n• "Sample Bill" button to test the analyzer\n• Or manually type/paste your bill text\n\nFile upload will be enabled soon!');

    // Clear file selection
    event.target.value = '';
    setSelectedFile(null);
  };

  const useSampleBill = () => {
    setBillText(sampleBill);
  };

  return (
    <div className="bill-uploader">
      <h2>Upload Your Bill</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Paste your restaurant bill text below or upload a PDF/image
      </p>

      <div className="upload-options">
        <button
          onClick={useSampleBill}
          style={{
            background: '#28a745',
            marginRight: '10px',
            marginTop: 0
          }}
        >
          Use Sample Bill
        </button>

        <label className="file-upload-button" style={{ display: 'inline-block' }}>
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            type="button"
            style={{ background: '#17a2b8', marginTop: 0 }}
            onClick={() => document.querySelector('input[type="file"]').click()}
          >
            Upload PDF/Image
          </button>
        </label>
      </div>

      {selectedFile && (
        <div style={{ marginTop: '10px', color: '#666' }}>
          Selected: {selectedFile.name}
        </div>
      )}

      <textarea
        value={billText}
        onChange={(e) => setBillText(e.target.value)}
        placeholder="Paste your restaurant bill here...

Example:
RESTAURANT NAME
Bill No: 12345

Masala Dosa x2    ₹120
Idli x4           ₹50
Parotta x3        ₹60

Subtotal:         ₹230
GST (5%):         ₹11.50
Total:            ₹241.50"
        rows={15}
      />

      <button
        onClick={handleAnalyze}
        disabled={loading || !billText.trim()}
      >
        {loading ? (
          <>
            <span className="loading"></span>
            {' Analyzing...'}
          </>
        ) : (
          'Analyze Bill'
        )}
      </button>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div style={{ marginTop: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '8px' }}>
        <h4 style={{ marginBottom: '10px' }}>How it works:</h4>
        <ol style={{ paddingLeft: '20px', color: '#666' }}>
          <li>Paste your bill text or click "Use Sample Bill"</li>
          <li>Click "Analyze Bill" to check for GST errors</li>
          <li>View detailed analysis below with discrepancies highlighted</li>
        </ol>
      </div>
    </div>
  );
}

export default BillUploader;
