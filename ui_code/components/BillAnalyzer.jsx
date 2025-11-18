import React from 'react';

function BillAnalyzer({ result }) {
  if (!result) return null;

  const {
    restaurant_name,
    bill_number,
    date,
    gstin,
    items = [],
    gross_amount,
    discount,
    subtotal,
    bill_charges,
    correct_calculation,
    discrepancy,
    confidence_score,
    warnings = []
  } = result;

  // Calculate confidence percentage and color
  const confidencePct = (confidence_score || 0) * 100;
  const confidenceColor = confidencePct >= 90 ? '#28a745' : confidencePct >= 70 ? '#ffc107' : '#dc3545';
  const confidenceLabel = confidencePct >= 90 ? 'HIGH' : confidencePct >= 70 ? 'MEDIUM' : 'LOW';

  return (
    <div className="bill-analyzer">
      <h2>Bill Analysis Results</h2>

      {/* Confidence Score Banner */}
      <div style={{
        padding: '15px 20px',
        background: confidenceColor,
        color: 'white',
        borderRadius: '10px',
        marginBottom: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.2rem' }}>
            Confidence Score: {confidencePct.toFixed(1)}% ({confidenceLabel})
          </h3>
          {confidencePct < 90 && (
            <p style={{ margin: '5px 0 0 0', fontSize: '0.9rem' }}>
              ⚠️ Below 90% - Manual verification recommended for legal use
            </p>
          )}
        </div>
        <div style={{ fontSize: '2rem' }}>
          {confidencePct >= 90 ? '🟢' : confidencePct >= 70 ? '🟡' : '🔴'}
        </div>
      </div>

      {/* Validation Warnings */}
      {warnings && warnings.length > 0 && (
        <div style={{
          padding: '15px 20px',
          background: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '10px',
          marginBottom: '20px'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#856404' }}>
            ⚠️ Validation Warnings:
          </h4>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#856404' }}>
            {warnings.map((warning, index) => (
              <li key={index} style={{ marginBottom: '5px' }}>
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Bill Header */}
      <div style={{
        background: '#f8f9fa',
        padding: '20px',
        borderRadius: '10px',
        marginBottom: '20px'
      }}>
        {restaurant_name && (
          <h3 style={{ margin: '0 0 10px 0', color: '#667eea' }}>
            {restaurant_name}
          </h3>
        )}
        <div style={{ display: 'flex', gap: '20px', color: '#666', flexWrap: 'wrap' }}>
          {bill_number && <span><strong>Bill No:</strong> {bill_number}</span>}
          {date && <span><strong>Date:</strong> {date}</span>}
          {gstin && <span><strong>GSTIN:</strong> {gstin}</span>}
        </div>
      </div>

      {/* Items Table */}
      <h3 style={{ marginBottom: '15px' }}>Items Breakdown</h3>
      <table className="item-table">
        <thead>
          <tr>
            <th>Item Name</th>
            <th>Qty</th>
            <th>Price</th>
            <th>GST Rate</th>
            <th>CGST</th>
            <th>SGST</th>
            <th>Total GST</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => {
            const itemGST = (item.cgst || 0) + (item.sgst || 0);
            return (
              <tr key={index}>
                <td>
                  <strong>{item.item_name}</strong>
                  {item.category && (
                    <div style={{ fontSize: '0.85rem', color: '#666' }}>
                      {item.category}
                    </div>
                  )}
                </td>
                <td>{item.quantity}</td>
                <td>₹{item.total_price.toFixed(2)}</td>
                <td>
                  <span style={{
                    padding: '3px 8px',
                    background: item.gst_rate === 0 ? '#efe' : '#f0f8ff',
                    borderRadius: '5px',
                    fontWeight: '600'
                  }}>
                    {item.gst_rate}%
                  </span>
                </td>
                <td>₹{(item.cgst || 0).toFixed(2)}</td>
                <td>₹{(item.sgst || 0).toFixed(2)}</td>
                <td>₹{itemGST.toFixed(2)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Totals Comparison */}
      <div style={{
        marginTop: '30px',
        padding: '20px',
        background: '#f8f9fa',
        borderRadius: '10px'
      }}>
        <h3 style={{ marginBottom: '15px' }}>GST Calculation Comparison</h3>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ textAlign: 'left', padding: '10px' }}>Item</th>
              <th style={{ textAlign: 'right', padding: '10px' }}>Bill Charged</th>
              <th style={{ textAlign: 'right', padding: '10px' }}>Correct Amount</th>
              <th style={{ textAlign: 'right', padding: '10px' }}>Difference</th>
            </tr>
          </thead>
          <tbody>
            {gross_amount > 0 && (
              <tr>
                <td style={{ padding: '10px' }}>Gross Amount</td>
                <td style={{ textAlign: 'right', padding: '10px' }}>
                  ₹{gross_amount.toFixed(2)}
                </td>
                <td style={{ textAlign: 'right', padding: '10px' }}>
                  ₹{gross_amount.toFixed(2)}
                </td>
                <td style={{ textAlign: 'right', padding: '10px' }}>-</td>
              </tr>
            )}
            {discount > 0 && (
              <tr style={{ background: '#e7f5ff' }}>
                <td style={{ padding: '10px' }}>
                  <strong>Discount</strong>
                  <span style={{ fontSize: '0.85rem', color: '#666', marginLeft: '10px' }}>
                    ({((discount / gross_amount) * 100).toFixed(1)}% off)
                  </span>
                </td>
                <td style={{ textAlign: 'right', padding: '10px', color: '#28a745' }}>
                  -₹{discount.toFixed(2)}
                </td>
                <td style={{ textAlign: 'right', padding: '10px', color: '#28a745' }}>
                  -₹{discount.toFixed(2)}
                </td>
                <td style={{ textAlign: 'right', padding: '10px' }}>-</td>
              </tr>
            )}
            <tr style={{ fontWeight: '600' }}>
              <td style={{ padding: '10px' }}>
                Subtotal {discount > 0 && <span style={{ fontSize: '0.85rem', fontWeight: 'normal' }}>(after discount)</span>}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{subtotal?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{subtotal?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>-</td>
            </tr>
            <tr>
              <td style={{ padding: '10px' }}>CGST</td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{bill_charges?.cgst?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{correct_calculation?.cgst?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{((bill_charges?.cgst || 0) - (correct_calculation?.cgst || 0)).toFixed(2)}
              </td>
            </tr>
            <tr>
              <td style={{ padding: '10px' }}>SGST</td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{bill_charges?.sgst?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{correct_calculation?.sgst?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{((bill_charges?.sgst || 0) - (correct_calculation?.sgst || 0)).toFixed(2)}
              </td>
            </tr>
            <tr style={{
              fontWeight: '600',
              background: discrepancy?.found ? '#fee' : '#efe',
              borderTop: '2px solid #ddd'
            }}>
              <td style={{ padding: '10px' }}>Total GST</td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{bill_charges?.total_gst?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{correct_calculation?.total_gst?.toFixed(2) || '0.00'}
              </td>
              <td style={{
                textAlign: 'right',
                padding: '10px',
                color: discrepancy?.found ? '#c33' : '#3c3'
              }}>
                ₹{discrepancy?.amount?.toFixed(2) || '0.00'}
              </td>
            </tr>
            <tr style={{ fontWeight: '600', fontSize: '1.1rem' }}>
              <td style={{ padding: '10px' }}>Grand Total</td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{bill_charges?.grand_total?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>
                ₹{correct_calculation?.grand_total?.toFixed(2) || '0.00'}
              </td>
              <td style={{ textAlign: 'right', padding: '10px' }}>-</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Discrepancy Alert */}
      {discrepancy?.found ? (
        <div style={{
          marginTop: '20px',
          padding: '20px',
          background: '#fee',
          border: '2px solid #c33',
          borderRadius: '10px'
        }}>
          <h3 style={{ color: '#c33', marginBottom: '15px' }}>
            ⚠️ GST Discrepancy Detected!
          </h3>
          <div style={{ color: '#333' }}>
            <p style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '10px' }}>
              Amount: ₹{Math.abs(discrepancy.amount).toFixed(2)}
              {discrepancy.amount > 0 ? ' OVERCHARGED' : ' UNDERCHARGED'}
            </p>
            {discrepancy.details && discrepancy.details.length > 0 && (
              <ul style={{ paddingLeft: '20px', marginTop: '10px' }}>
                {discrepancy.details.map((detail, index) => (
                  <li key={index} style={{ marginBottom: '5px' }}>
                    {detail}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : (
        <div style={{
          marginTop: '20px',
          padding: '20px',
          background: '#efe',
          border: '2px solid #3c3',
          borderRadius: '10px'
        }}>
          <h3 style={{ color: '#3c3', marginBottom: '10px' }}>
            ✓ Bill GST is Correct!
          </h3>
          <p style={{ color: '#333' }}>
            All GST calculations match the correct rates. No discrepancies found.
          </p>
        </div>
      )}

      {/* Download/Print Options */}
      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <button
          onClick={() => window.print()}
          style={{ background: '#6c757d' }}
        >
          Print Report
        </button>
        <button
          onClick={() => {
            const dataStr = JSON.stringify(result, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `bill_analysis_${bill_number || 'report'}.json`;
            link.click();
          }}
          style={{ background: '#28a745' }}
        >
          Download JSON
        </button>
      </div>
    </div>
  );
}

export default BillAnalyzer;
