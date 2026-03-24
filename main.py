import database
import ui

def check_alerts():
    """Check if any recent price drops below user-defined threshold."""
    alerts = database.get_active_alerts()
    triggered = False
    
    if alerts:
        print("Checking active alerts...")
    for alert in alerts:
        aid, pid, p_name, target = alert
        history = database.get_price_history(pid)
        if history:
            latest_price = history[-1][1]
            if latest_price <= target:
                print(f"\n[ALERT - NOTICE] Price Drop Detected! '{p_name}' is currently at Rs.{latest_price} (Target: Rs.{target})")
                triggered = True
                
    if alerts and not triggered:
        print("No alerts triggered based on latest prices.")

def main():
    print("Initializing Database...")
    database.init_db()
    
    check_alerts()
    ui.main_menu()

if __name__ == "__main__":
    main()
