import React, { useState, useEffect } from 'react';
import { searchGST, getAllGSTItems } from '../services/api';

function GSTLookup() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [allItems, setAllItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load all items on mount
    loadAllItems();
  }, []);

  const loadAllItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await getAllGSTItems();
      setAllItems(items);
      setSearchResults(items);
    } catch (err) {
      setError('Failed to load GST items. Make sure the API is running on port 8001.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!searchQuery.trim()) {
      setSearchResults(allItems);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const results = await searchGST(searchQuery);
      setSearchResults(results);
    } catch (err) {
      setError('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSearchQuery('');
    setSearchResults(allItems);
  };

  return (
    <div className="gst-lookup">
      <h2>GST Database Lookup</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Search for items to find their GST rates, HSN codes, and categories
      </p>

      {/* Search Box */}
      <form onSubmit={handleSearch} className="search-box">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by item name, HSN code, or category... (e.g., Dosa, Parotta, 1905)"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
        {searchQuery && (
          <button
            type="button"
            onClick={handleClear}
            style={{ background: '#6c757d' }}
          >
            Clear
          </button>
        )}
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results Count */}
      {searchResults.length > 0 && (
        <div style={{
          marginTop: '20px',
          padding: '10px',
          background: '#f8f9fa',
          borderRadius: '5px',
          color: '#666'
        }}>
          Found {searchResults.length} item{searchResults.length !== 1 ? 's' : ''}
          {searchQuery && ` matching "${searchQuery}"`}
        </div>
      )}

      {/* Results Table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <span className="loading" style={{ display: 'inline-block' }}></span>
          <p style={{ marginTop: '10px', color: '#666' }}>Loading...</p>
        </div>
      ) : searchResults.length > 0 ? (
        <div style={{ marginTop: '20px', overflowX: 'auto' }}>
          <table className="item-table">
            <thead>
              <tr>
                <th>Item Name</th>
                <th>HSN/SAC Code</th>
                <th>Category</th>
                <th>GST Rate</th>
                <th>CGST</th>
                <th>SGST</th>
                <th>IGST</th>
              </tr>
            </thead>
            <tbody>
              {searchResults.map((item, index) => (
                <tr key={index}>
                  <td>
                    <strong>{item.item_name || 'N/A'}</strong>
                    {item.description && (
                      <div style={{
                        fontSize: '0.85rem',
                        color: '#666',
                        marginTop: '5px'
                      }}>
                        {item.description}
                      </div>
                    )}
                  </td>
                  <td>
                    {item.hsn_code && (
                      <span style={{
                        padding: '3px 8px',
                        background: '#e3f2fd',
                        borderRadius: '5px',
                        fontFamily: 'monospace'
                      }}>
                        {item.hsn_code}
                      </span>
                    )}
                    {item.sac_code && (
                      <span style={{
                        padding: '3px 8px',
                        background: '#f3e5f5',
                        borderRadius: '5px',
                        fontFamily: 'monospace',
                        marginLeft: '5px'
                      }}>
                        {item.sac_code}
                      </span>
                    )}
                    {!item.hsn_code && !item.sac_code && '-'}
                  </td>
                  <td>{item.item_category || '-'}</td>
                  <td>
                    <span style={{
                      padding: '5px 12px',
                      background: item.gst_rate === 0 ? '#c8e6c9' :
                                 item.gst_rate <= 5 ? '#fff9c4' :
                                 item.gst_rate <= 12 ? '#ffe0b2' : '#ffccbc',
                      borderRadius: '5px',
                      fontWeight: '600'
                    }}>
                      {item.gst_rate}%
                    </span>
                  </td>
                  <td>{item.cgst_rate !== null ? `${item.cgst_rate}%` : '-'}</td>
                  <td>{item.sgst_rate !== null ? `${item.sgst_rate}%` : '-'}</td>
                  <td>{item.igst_rate !== null ? `${item.igst_rate}%` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#666'
        }}>
          <p>No items found.</p>
          {searchQuery && (
            <p style={{ marginTop: '10px' }}>
              Try searching for different keywords or{' '}
              <button
                onClick={handleClear}
                style={{
                  background: 'none',
                  color: '#667eea',
                  textDecoration: 'underline',
                  padding: 0,
                  margin: 0
                }}
              >
                view all items
              </button>
            </p>
          )}
        </div>
      )}

      {/* Info Box */}
      <div style={{
        marginTop: '30px',
        padding: '20px',
        background: '#f8f9fa',
        borderRadius: '10px'
      }}>
        <h4 style={{ marginBottom: '10px' }}>Understanding GST Rates:</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginTop: '15px' }}>
          <div style={{ padding: '10px', background: '#c8e6c9', borderRadius: '5px' }}>
            <strong>0%</strong> - Essential items (Parotta, Bread)
          </div>
          <div style={{ padding: '10px', background: '#fff9c4', borderRadius: '5px' }}>
            <strong>5%</strong> - Restaurant food (Dosa, Idli)
          </div>
          <div style={{ padding: '10px', background: '#ffe0b2', borderRadius: '5px' }}>
            <strong>12%</strong> - Standard goods
          </div>
          <div style={{ padding: '10px', background: '#ffccbc', borderRadius: '5px' }}>
            <strong>18%+</strong> - Luxury items
          </div>
        </div>

        <div style={{ marginTop: '20px', color: '#666' }}>
          <p><strong>HSN Code:</strong> Harmonized System of Nomenclature (for goods)</p>
          <p><strong>SAC Code:</strong> Services Accounting Code (for services)</p>
          <p><strong>CGST:</strong> Central GST (charged by central government)</p>
          <p><strong>SGST:</strong> State GST (charged by state government)</p>
          <p><strong>IGST:</strong> Integrated GST (for inter-state transactions)</p>
        </div>
      </div>
    </div>
  );
}

export default GSTLookup;
