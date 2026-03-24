import matplotlib.pyplot as plt
import pandas as pd
import database
import os

def get_stats(product_id):
    """Fetch minimum, maximum, average price statistics."""
    history = database.get_price_history(product_id)
    if not history:
        return None
        
    prices = [row[1] for row in history]
    return {
        "min": min(prices),
        "max": max(prices),
        "avg": round(sum(prices) / len(prices), 2),
        "count": len(prices)
    }

def plot_trend(product_id, product_name):
    """Plot line chart for historical prices over time for a product."""
    history = database.get_price_history(product_id)
    if not history:
        print("No data available to plot.")
        return

    df = pd.DataFrame(history, columns=["Vendor", "Price", "Date"])
    df['Date'] = pd.to_datetime(df['Date'])
    
    plt.figure(figsize=(10, 5))
    for vendor in df['Vendor'].unique():
        vendor_data = df[df['Vendor'] == vendor].sort_values(by="Date")
        plt.plot(vendor_data['Date'], vendor_data['Price'], marker='o', linestyle='-', label=vendor)

    plt.title(f"Price Trend: {product_name}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    filename = f"trend_{product_id}.png"
    plt.savefig(filename)
    plt.close()
    print(f"[SUCCESS] Trend chart saved as {filename}")

def plot_vendor_comparison(product_id, product_name):
    """Plot bar chart comparing latest prices across vendors."""
    history = database.get_price_history(product_id)
    if not history:
        print("No data available to plot.")
        return

    df = pd.DataFrame(history, columns=["Vendor", "Price", "Date"])
    df['Date'] = pd.to_datetime(df['Date'])
    latest_prices = df.sort_values('Date').groupby('Vendor').last().reset_index()

    plt.figure(figsize=(8, 5))
    plt.bar(latest_prices['Vendor'], latest_prices['Price'], color='skyblue')
    plt.title(f"Latest Price Comparison: {product_name}")
    plt.xlabel("Vendor")
    plt.ylabel("Price")
    plt.tight_layout()
    
    for _, row in latest_prices.iterrows():
        plt.text(row['Vendor'], row['Price'] + (max(latest_prices['Price']) * 0.01), f"Rs.{row['Price']:.2f}", ha='center')

    filename = f"comparison_{product_id}.png"
    plt.savefig(filename)
    plt.close()
    print(f"[SUCCESS] Vendor Comparison chart saved as {filename}")
