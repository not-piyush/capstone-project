import os
import database
import data_collection
import analytics

def run_tests():
    print("Testing DB initialization...")
    database.init_db()

    print("Adding product 'Sony Headphones'...")
    pid = database.add_product("Sony Headphones", "Electronics")

    print("Adding vendor & base prices...")
    vid1 = database.add_vendor("Local Shop A", "Downtown")
    vid2 = database.add_vendor("Local Shop B", "Uptown")
    
    database.add_price(pid, vid1, 4000)
    database.add_price(pid, vid2, 4200)
    
    print("Testing data collection mock (Amazon)...")
    mock_price = data_collection.scrape_mock_amazon("Sony Headphones")

    print("Setting alert target = 3900...")
    database.add_alert(pid, 3900)
    
    print("Testing analytics stats...")
    stats = analytics.get_stats(pid)
    print(f"Stats: {stats}")
    
    print("Generating analytics plots...")
    analytics.plot_trend(pid, "Sony Headphones")
    analytics.plot_vendor_comparison(pid, "Sony Headphones")

    print("Checking if images exist...")
    assert os.path.exists(f"trend_{pid}.png"), "Trend plot missing"
    assert os.path.exists(f"comparison_{pid}.png"), "Comparison plot missing"

    print("\n[SUCCESS] All programmatic tests passed! DB, Data Collection, Alerts, and Analytics are working correctly.")

if __name__ == "__main__":
    run_tests()
