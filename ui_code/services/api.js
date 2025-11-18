/**
 * API service for GST Bill Analyzer
 * Connects React frontend to FastAPI backend
 */

const API_BASE_URL = 'http://127.0.0.1:8001';

/**
 * Analyze a bill using Gemini AI
 * @param {string} billText - The text content of the bill
 * @returns {Promise<Object>} Analysis result with GST calculations
 */
export const analyzeBill = async (billText) => {
  try {
    const response = await fetch(`${API_BASE_URL}/gst/analyze-bill`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
      body: JSON.stringify({
        bill_text: billText
      })
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error analyzing bill:', error);
    throw new Error(
      error.message ||
      'Failed to analyze bill. Make sure the FastAPI server is running on port 8001.'
    );
  }
};

/**
 * Search for GST items by query
 * @param {string} query - Search term (item name, HSN code, category)
 * @returns {Promise<Array>} List of matching GST items
 */
export const searchGST = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}/gst/search/${encodeURIComponent(query)}`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      }
    });

    if (!response.ok) {
      throw new Error(`Search failed with status ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error searching GST:', error);
    throw new Error('Search failed. Please try again.');
  }
};

/**
 * Get all GST items from database
 * @returns {Promise<Array>} List of all GST items
 */
export const getAllGSTItems = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/gst/items`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch items with status ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching all items:', error);
    throw new Error('Failed to load GST items.');
  }
};

/**
 * Get a single GST item by HSN code
 * @param {string} hsnCode - The HSN code to lookup
 * @returns {Promise<Object>} GST item details
 */
export const getGSTByHSN = async (hsnCode) => {
  try {
    const response = await fetch(`${API_BASE_URL}/gst/${encodeURIComponent(hsnCode)}`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`HSN code ${hsnCode} not found`);
      }
      throw new Error(`Failed to fetch item with status ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching GST item:', error);
    throw error;
  }
};

/**
 * Upload and analyze a bill file (PDF or image)
 * @param {File} file - The file to upload
 * @returns {Promise<Object>} Analysis result
 */
export const analyzeBillFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/gst/analyze-bill-file`, {
      method: 'POST',
      headers: {
        'ngrok-skip-browser-warning': 'true',
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`File upload failed with status ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw new Error(
      error.message || 'File upload failed. Please try again.'
    );
  }
};

// Health check endpoint
export const checkAPIHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      headers: {
        'ngrok-skip-browser-warning': 'true',
      }
    });
    return response.ok;
  } catch (error) {
    return false;
  }
};
