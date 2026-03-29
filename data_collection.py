import requests
from bs4 import BeautifulSoup
import database

def add_manual_entry(product_name, vendor_name, price, category="", location="", user_id=None, tracking_url=None):
    """Manually add a price for a product from a vendor."""
    product_id = database.add_product(product_name, category, user_id=user_id, tracking_url=tracking_url)
    vendor_id = database.add_vendor(vendor_name, location)
    database.add_price(product_id, vendor_id, price)
    return True

def scrape_mock_amazon(product_name):
    """
    Simulated scraper that returns a slightly varying price.
    In a real scenario, we would use an API or headless browser to bypass bot protections.
    """
    import random
    
    # Simulated base prices for mock demo
    base_prices = {
        "samsung galaxy m14": 12500,
        "iphone 13": 55000,
        "sony headphones": 4000
    }
    
    key = product_name.lower().strip()
    base_price = base_prices.get(key, random.randint(1000, 20000))
    fluctuation = base_price * random.uniform(-0.05, 0.05)
    mock_price = round(base_price + fluctuation, 2)
    
    add_manual_entry(product_name, "Amazon", mock_price, "Online", "Web")
    return mock_price

import re

def scrape_url(url):
    """
    Real scraper using BeautifulSoup to extract price. Includes fail-safes.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for common price classes/ids
            price_elem = soup.find(class_=re.compile(r'price|a-price-whole', re.I)) or soup.find(id=re.compile(r'price', re.I))
            if price_elem:
                match = re.search(r'[\d,]+\.?\d*', price_elem.text)
                if match:
                    return float(match.group().replace(',', ''))
            
            # Fallback: scan entire document text for random money patterns like Rs.1999 or $1999
            text_match = re.search(r'(?:Rs\.?|₹|\$)\s?([\d,]+\.?\d*)', soup.text)
            if text_match:
                return float(text_match.group(1).replace(',', ''))
                
        return None
    except Exception as e:
        print(f"Scrape error: {e}")
        return None
