import database
import data_collection
import analytics
import os

def main_menu():
    while True:
        print("\n" + "="*30)
        print("Local Price Tracker CLI")
        print("="*30)
        print("1. View Current Products")
        print("2. Add Manual Price Entry (Local Shop)")
        print("3. Fetch Mock Online Price (Amazon)")
        print("4. View Analytics & Trends (Generate Charts)")
        print("5. Set Price Alert for Product")
        print("6. Exit")
        
        choice = input("Enter choice (1-6): ").strip()
        
        if choice == '1':
            view_products()
        elif choice == '2':
            add_manual_price_menu()
        elif choice == '3':
            fetch_online_price_menu()
        elif choice == '4':
            analytics_menu()
        elif choice == '5':
            set_alert_menu()
        elif choice == '6':
            print("Exiting Tracker. Have a great day!")
            break
        else:
            print("[ERROR] Invalid choice. Please select 1-6.")

def view_products():
    products = database.get_all_products()
    if not products:
        print("\nNo products found in database yet. Add some!")
        return
    print("\n--- Product List ---")
    for p in products:
        print(f"ID: [{p[0]}] | Name: {p[1]} | Category: {p[2]}")

def add_manual_price_menu():
    print("\n--- Add Manual Price ---")
    product_name = input("Product Name (e.g., iPhone 13): ").strip()
    if not product_name: 
        print("Name cannot be empty.")
        return
    category = input("Category (optional): ").strip()
    vendor_name = input("Vendor Name (e.g., Local Electronics Store): ").strip()
    location = input("Vendor Location (optional): ").strip()
    try:
        price = float(input("Price recorded (Rs.): ").strip())
        data_collection.add_manual_entry(product_name, vendor_name, price, category, location)
        print("[SUCCESS] Price entry successful!")
    except ValueError:
        print("[ERROR] Invalid price format. Must be a number.")

def fetch_online_price_menu():
    print("\n--- Fetch Mock Online Price ---")
    product_name = input("Enter product name to track on mock Amazon: ").strip()
    if product_name:
        price = data_collection.scrape_mock_amazon(product_name)
        print(f"[SUCCESS] Fetched mock price for '{product_name}' from Amazon: Rs.{price}")
    else:
        print("Name cannot be empty.")

def analytics_menu():
    print("\n--- Analytics & Trends ---")
    view_products()
    try:
        pid = int(input("\nEnter Product ID to analyze: ").strip())
        products = database.get_all_products()
        p_name = next((p[1] for p in products if p[0] == pid), None)
        
        if not p_name:
            print("[ERROR] Product ID not found.")
            return

        stats = analytics.get_stats(pid)
        if stats:
            print(f"\n[STATS] {p_name}:")
            print(f" Min Price: Rs.{stats['min']}\n Max Price: Rs.{stats['max']}\n Average Price: Rs.{stats['avg']}\n Total Records: {stats['count']}")
        else:
            print("No historic data available.")
            return
            
        print("\nGenerating visual charts...")
        analytics.plot_trend(pid, p_name)
        analytics.plot_vendor_comparison(pid, p_name)
    except ValueError:
        print("[ERROR] Invalid ID format.")

def set_alert_menu():
    print("\n--- Set Price Alert ---")
    view_products()
    try:
        pid = int(input("\nEnter Product ID to watch: ").strip())
        target = float(input("Enter Target Price to be alerted below (Rs.): ").strip())
        database.add_alert(pid, target)
        print(f"[SUCCESS] Alert set! You will be notified when price drops below Rs.{target}.")
    except ValueError:
        print("[ERROR] Invalid input format.")
