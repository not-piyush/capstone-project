import io
import csv
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import database
import data_collection
import analytics 
import threading
import notifier

app = Flask(__name__)
app.secret_key = 'capstone_tracker_super_secret'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    u = database.get_user_by_id(user_id)
    if u:
        return User(u[0], u[1])
    return None

# Ensure DB is initialized to prevent file-not-found issues on cold start
database.init_db()

# Start the background notification thread
notifier_thread = threading.Thread(target=notifier.run_notifier_loop, daemon=True)
notifier_thread.start()

@app.route('/')
@login_required
def index():
    user_data = database.get_user_by_id(current_user.id)
    webhook = user_data[3] if user_data and len(user_data) > 3 else ""
    return render_template('index.html', webhook=webhook)

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    """Return all products and their overarching statistics."""
    products = database.get_all_products(user_id=current_user.id)
    res = []
    for p in products:
        stats = analytics.get_stats(p[0])
        res.append({
            "id": p[0],
            "name": p[1],
            "category": p[2],
            "tracking_url": p[3],
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
@login_required
def add_price():
    """Add a new price via UI form."""
    data = request.json
    try:
        data_collection.add_manual_entry(
            data['product_name'], 
            data['vendor_name'], 
            float(data['price']), 
            data.get('category', ''), 
            data.get('location', ''),
            user_id=current_user.id,
            tracking_url=data.get('tracking_url', None)
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/force_sync', methods=['POST'])
@login_required
def force_sync():
    products = database.get_all_products(user_id=current_user.id)
    success_count = 0
    vid = database.add_vendor('Web Scraper', 'Online')
    for p in products:
        pid, name, category, tracking_url = p
        if tracking_url:
            price = data_collection.scrape_url(tracking_url)
            if price is not None:
                database.add_price(pid, vid, price)
                success_count += 1
    return jsonify({"success": True, "synced": success_count})

@app.route('/api/add_alert', methods=['POST'])
@login_required
def add_alert():
    """Set an alert via UI form."""
    data = request.json
    try:
        pid = int(data['product_id'])
        target = float(data['target_price'])
        database.add_alert(pid, target, user_id=current_user.id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/update_webhook', methods=['POST'])
@login_required
def update_webhook():
    data = request.json
    webhook = data.get('webhook_url', '')
    database.update_webhook(current_user.id, webhook)
    return jsonify({"success": True})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        u = database.get_user_by_username(username)
        if u and check_password_hash(u[2], password):
            user_obj = User(u[0], u[1])
            login_user(user_obj)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if database.get_user_by_username(username):
            flash('Username already exists.')
        else:
            hashed_pw = generate_password_hash(password)
            database.add_user(username, hashed_pw)
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("[STARTUP] Launching Local Price Tracker Web App!")
    print("[READY] Visit http://127.0.0.1:5001 in your browser.")
    app.run(debug=True, port=5001)
