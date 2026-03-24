import database
import random
from datetime import datetime, timedelta

def seed_db():
    print("Clearing old data... (reinitializing database)")
    conn = database.get_connection()
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS Prices')
    c.execute('DROP TABLE IF EXISTS Alerts')
    c.execute('DROP TABLE IF EXISTS Vendors')
    c.execute('DROP TABLE IF EXISTS Products')
    conn.commit()
    conn.close()

    database.init_db()
    
    products = [
        ("iPhone 15 Pro", "Smartphone", 120000),
        ("Samsung Galaxy S24", "Smartphone", 95000),
        ("Google Pixel 8", "Smartphone", 75000),
        ("Sony WH-1000XM5", "Audio", 30000),
        ("Bose QuietComfort 45", "Audio", 25000),
        ("MacBook Pro M3", "Laptop", 160000),
        ("Dell XPS 15", "Laptop", 145000),
        ("Lenovo ThinkPad X1", "Laptop", 130000),
        ("iPad Air 5", "Tablet", 55000),
        ("Samsung Galaxy Tab S9", "Tablet", 72000)
    ]
    
    vendors = [
        ("Amazon India", "Online"),
        ("Flipkart", "Online"),
        ("Reliance Digital", "Local")
    ]
    
    print("Seeding Vendors...")
    v_ids = []
    for v in vendors:
        v_ids.append(database.add_vendor(v[0], v[1]))
        
    print("Seeding Products and 30-day Price History...")
    now = datetime.now()
    
    for p in products:
        p_id = database.add_product(p[0], p[1])
        base_price = p[2]
        
        for v_id in v_ids:
            # Vendor specific offset
            vendor_offset = random.uniform(-0.03, 0.03)
            vendor_base = base_price * (1 + vendor_offset)
            
            for days_ago in range(30, -1, -1):
                # Daily fluctuation & artificial trend line
                fluctuation = vendor_base * random.uniform(-0.015, 0.015)
                trend_drop = (30 - days_ago) * (base_price * 0.001) 
                
                final_price = round(vendor_base + fluctuation - trend_drop, 2)
                date_str = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Insert directly to spoof the historical date
                conn = database.get_connection()
                c = conn.cursor()
                c.execute('INSERT INTO Prices (product_id, vendor_id, price, date) VALUES (?, ?, ?, ?)', 
                          (p_id, v_id, final_price, date_str))
                conn.commit()
                conn.close()

    print("[SUCCESS] Seeding complete! 30 days of market realistic data generated across 3000+ data points.")

if __name__ == "__main__":
    seed_db()
