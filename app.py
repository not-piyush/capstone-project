import io
import csv
from flask import Flask, render_template, request, jsonify, Response
import database
import data_collection
import analytics 

app = Flask(__name__)

# Ensure DB is initialized to prevent file-not-found issues on cold start
database.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    """Return all products and their overarching statistics."""
    products = database.get_all_products()
    res = []
    for p in products:
        stats = analytics.get_stats(p[0])
        res.append({
            "id": p[0],
            "name": p[1],
            "category": p[2],
            "stats": stats
        })
    return jsonify(res)

@app.route('/api/history/<int:product_id>', methods=['GET'])
def get_history(product_id):
    """Return normalized price history for a specific product."""
    history = database.get_price_history(product_id)
    # Database shape: list of (vendor_name, price, date)
    data = [{"vendor": row[0], "price": row[1], "date": row[2]} for row in history]
    return jsonify(data)

@app.route('/api/export/<int:product_id>', methods=['GET'])
def export_csv(product_id):
    """Advanced Feature: Download history as format CSV"""
    history = database.get_price_history(product_id)
    products = database.get_all_products()
    p_name = next((p[1] for p in products if p[0] == product_id), "product")
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Vendor', 'Price (Rs)', 'Date'])
    for row in history:
        cw.writerow([row[0], row[1], row[2]])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={p_name.replace(' ', '_')}_history.csv"}
    )

@app.route('/api/recommend/<int:product_id>', methods=['GET'])
def recommend_cheaper(product_id):
    """Advanced Feature: Content-based recommendation Engine"""
    products = database.get_all_products()
    target_p = next((p for p in products if p[0] == product_id), None)
    if not target_p:
        return jsonify([])
        
    category = target_p[2]
    target_stats = analytics.get_stats(product_id)
    if not target_stats:
        return jsonify([])
        
    target_avg = target_stats['avg']
    
    recommendations = []
    for p in products:
        if p[2] == category and p[0] != product_id:
            stats = analytics.get_stats(p[0])
            if stats and stats['avg'] < target_avg:
                recommendations.append({
                    "id": p[0],
                    "name": p[1],
                    "avg_price": stats['avg'],
                    "savings": round(target_avg - stats['avg'], 2)
                })
                
    recommendations.sort(key=lambda x: x['savings'], reverse=True)
    return jsonify(recommendations[:3])

@app.route('/api/add_price', methods=['POST'])
def add_price():
    """Add a new price via UI form."""
    data = request.json
    try:
        data_collection.add_manual_entry(
            data['product_name'], 
            data['vendor_name'], 
            float(data['price']), 
            data.get('category', ''), 
            data.get('location', '')
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/add_alert', methods=['POST'])
def add_alert():
    """Set an alert via UI form."""
    data = request.json
    try:
        pid = int(data['product_id'])
        target = float(data['target_price'])
        database.add_alert(pid, target)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    print("[STARTUP] Launching Local Price Tracker Web App!")
    print("[READY] Visit http://127.0.0.1:5000 in your browser.")
    app.run(debug=True, port=5000)
