"""
Populate GST Database with HSN/SAC Codes for Indian Items
Based on official GST classification (2025)
"""

import sqlite3
from datetime import datetime

def populate_hsn_codes():
    """Add HSN/SAC codes to existing items and add new items with codes"""

    conn = sqlite3.connect('gst_data.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist (for Render deployment)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gst_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hsn_code TEXT,
            sac_code TEXT,
            item_name TEXT NOT NULL,
            item_category TEXT,
            gst_rate REAL NOT NULL,
            cgst_rate REAL,
            sgst_rate REAL,
            igst_rate REAL,
            cess_rate REAL DEFAULT 0,
            effective_from TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hsn_code, sac_code, item_name)
        )
    """)
    conn.commit()

    # Common Indian items with proper HSN/SAC codes
    items_with_codes = [
        # Food items (5% GST)
        {
            'hsn_code': '0801',
            'item_name': 'Cashews, almonds, walnuts (Dry fruits)',
            'item_category': 'Dry fruits and nuts',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0802',
            'item_name': 'Dates, figs, pineapples, avocados, guavas',
            'item_category': 'Dry fruits',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0713',
            'item_name': 'Pulses (Dal - Dried leguminous vegetables)',
            'item_category': 'Food grains',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0401',
            'item_name': 'Milk and cream (not concentrated)',
            'item_category': 'Dairy products',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0402',
            'item_name': 'Milk powder, condensed milk',
            'item_category': 'Dairy products',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0405',
            'item_name': 'Butter and dairy spreads',
            'item_category': 'Dairy products',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0406',
            'item_name': 'Cheese and curd',
            'item_category': 'Dairy products',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },

        # Edible oils (5% GST)
        {
            'hsn_code': '1507',
            'item_name': 'Soya bean oil',
            'item_category': 'Edible oils',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '1508',
            'item_name': 'Groundnut oil',
            'item_category': 'Edible oils',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '1511',
            'item_name': 'Palm oil',
            'item_category': 'Edible oils',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '1512',
            'item_name': 'Sunflower oil, safflower oil',
            'item_category': 'Edible oils',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '1514',
            'item_name': 'Mustard oil, rapeseed oil',
            'item_category': 'Edible oils',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },

        # Spices (5% GST)
        {
            'hsn_code': '0904',
            'item_name': 'Pepper (Black/White)',
            'item_category': 'Spices',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0906',
            'item_name': 'Cinnamon and cinnamon-tree flowers',
            'item_category': 'Spices',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0907',
            'item_name': 'Cloves',
            'item_category': 'Spices',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0909',
            'item_name': 'Seeds of anise, coriander, cumin, fennel',
            'item_category': 'Spices',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '0910',
            'item_name': 'Ginger, saffron, turmeric, bay leaves',
            'item_category': 'Spices',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },

        # Personal care (18% GST)
        {
            'hsn_code': '3305',
            'item_name': 'Shampoo, hair oil',
            'item_category': 'Hair care products',
            'gst_rate': 18.0,
            'cgst_rate': 9.0,
            'sgst_rate': 9.0,
            'igst_rate': 18.0,
        },
        {
            'hsn_code': '3306',
            'item_name': 'Toothpaste, tooth powder',
            'item_category': 'Oral care',
            'gst_rate': 18.0,
            'cgst_rate': 9.0,
            'sgst_rate': 9.0,
            'igst_rate': 18.0,
        },
        {
            'hsn_code': '3401',
            'item_name': 'Toilet soap, washing soap',
            'item_category': 'Soaps',
            'gst_rate': 18.0,
            'cgst_rate': 9.0,
            'sgst_rate': 9.0,
            'igst_rate': 18.0,
        },

        # Packaged food (12% GST)
        {
            'hsn_code': '1905',
            'item_name': 'Bread, biscuits, cakes, pastries',
            'item_category': 'Bakery products',
            'gst_rate': 12.0,
            'cgst_rate': 6.0,
            'sgst_rate': 6.0,
            'igst_rate': 12.0,
        },
        {
            'hsn_code': '2106',
            'item_name': 'Namkeens, bhujia, mixture (pre-packaged)',
            'item_category': 'Snacks',
            'gst_rate': 12.0,
            'cgst_rate': 6.0,
            'sgst_rate': 6.0,
            'igst_rate': 12.0,
        },

        # Beverages
        {
            'hsn_code': '2202',
            'item_name': 'Fruit juice, vegetable juice',
            'item_category': 'Beverages',
            'gst_rate': 12.0,
            'cgst_rate': 6.0,
            'sgst_rate': 6.0,
            'igst_rate': 12.0,
        },
        {
            'hsn_code': '2201',
            'item_name': 'Packaged drinking water',
            'item_category': 'Beverages',
            'gst_rate': 18.0,
            'cgst_rate': 9.0,
            'sgst_rate': 9.0,
            'igst_rate': 18.0,
        },

        # Restaurant services (SAC codes)
        {
            'sac_code': '996331',
            'item_name': 'Restaurant service (AC)',
            'item_category': 'Restaurant services',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'sac_code': '996332',
            'item_name': 'Restaurant service (Non-AC)',
            'item_category': 'Restaurant services',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },

        # Common prepared foods (Restaurant context)
        {
            'hsn_code': '1006',
            'item_name': 'Rice dishes (Biryani, Pulao, etc.)',
            'item_category': 'Restaurant food',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },
        {
            'hsn_code': '1101',
            'item_name': 'Wheat flour products (Roti, Parotta, Chapati)',
            'item_category': 'Restaurant food',
            'gst_rate': 5.0,
            'cgst_rate': 2.5,
            'sgst_rate': 2.5,
            'igst_rate': 5.0,
        },

        # Electronics (18% GST)
        {
            'hsn_code': '8517',
            'item_name': 'Mobile phones, smartphones',
            'item_category': 'Electronics',
            'gst_rate': 18.0,
            'cgst_rate': 9.0,
            'sgst_rate': 9.0,
            'igst_rate': 18.0,
        },
        {
            'hsn_code': '8471',
            'item_name': 'Computers, laptops',
            'item_category': 'Electronics',
            'gst_rate': 18.0,
            'cgst_rate': 9.0,
            'sgst_rate': 9.0,
            'igst_rate': 18.0,
        },

        # Household items (18% GST)
        {
            'hsn_code': '7323',
            'item_name': 'Stainless steel utensils',
            'item_category': 'Utensils',
            'gst_rate': 18.0,
            'cgst_rate': 9.0,
            'sgst_rate': 9.0,
            'igst_rate': 18.0,
        },
    ]

    now = datetime.now().isoformat()

    print("Populating HSN/SAC codes...")
    count = 0

    for item in items_with_codes:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO gst_items
                (hsn_code, sac_code, item_name, item_category,
                 gst_rate, cgst_rate, sgst_rate, igst_rate, cess_rate,
                 effective_from, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('hsn_code'),
                item.get('sac_code'),
                item['item_name'],
                item.get('item_category', ''),
                item['gst_rate'],
                item.get('cgst_rate', item['gst_rate'] / 2),
                item.get('sgst_rate', item['gst_rate'] / 2),
                item.get('igst_rate', item['gst_rate']),
                item.get('cess_rate', 0),
                '2025-01-01',
                item.get('remarks', '')
            ))
            count += 1
            print(f"[OK] Added: {item['item_name']} (HSN: {item.get('hsn_code', 'N/A')}, SAC: {item.get('sac_code', 'N/A')})")
        except Exception as e:
            print(f"[ERR] Error adding {item['item_name']}: {e}")

    conn.commit()
    conn.close()

    print(f"\n[OK] Successfully added {count} items with HSN/SAC codes!")
    print(f"Database: gst_data.db")

if __name__ == '__main__':
    populate_hsn_codes()
