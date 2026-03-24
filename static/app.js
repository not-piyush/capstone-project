// State
let products = [];
let currentChart = null;
let currentProductId = null;

// DOM Elements
const productList = document.getElementById('productList');
const alertProductSelect = document.getElementById('alertProductSelect');
const chartTitle = document.getElementById('chartTitle');
const chartStats = document.getElementById('chartStats');

// Utilities
const showToast = (msg) => {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
};

window.showSection = (id, event) => {
    document.querySelectorAll('.view-section').forEach(s => s.style.display = 'none');
    document.getElementById(id).style.display = 'block';
    
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    if(event) event.currentTarget.classList.add('active');
};

// Advanced Feature: Fuzzy Search Filter
window.filterProducts = () => {
    const query = document.getElementById('searchInput').value.toLowerCase();
    document.querySelectorAll('.product-card').forEach(card => {
        const title = card.querySelector('.product-title').innerText.toLowerCase();
        const category = card.querySelector('.product-meta span:first-child').innerText.toLowerCase();
        
        if(title.includes(query) || category.includes(query)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
};

// Advanced Feature: Export CSV
window.exportCSV = () => {
    if (!currentProductId) {
        showToast("Please select a product first!");
        return;
    }
    // Triggers browser download natively
    window.open(`/api/export/${currentProductId}`, '_blank');
};

// Advanced Feature: Recommendation Engine UI
const loadRecommendations = async (pid) => {
    const box = document.getElementById('recommendationBox');
    const list = document.getElementById('recList');
    
    try {
        const res = await fetch(`/api/recommend/${pid}`);
        const recs = await res.json();
        
        if (recs && recs.length > 0) {
            box.style.display = 'block';
            list.innerHTML = recs.map(r => `
                <div class="rec-item" onclick="switchProduct(${r.id})">
                    <b>${r.name}</b> <br> Avg: Rs. ${r.avg_price} <br>
                    <span>Save Rs. ${r.savings}</span>
                </div>
            `).join('');
        } else {
            box.style.display = 'none';
            list.innerHTML = '';
        }
    } catch(e) { 
        console.error("Recommendations API failed", e); 
        box.style.display = 'none';
    }
};

window.switchProduct = (id) => {
    const target = products.find(p => p.id === id);
    if(target) loadChart(target);
};

// Data Fetching
const loadProducts = async () => {
    try {
        const res = await fetch('/api/products');
        products = await res.json();
        renderProducts();
        populateSelects();
        
        // Auto-load chart for first product
        if (products.length > 0) {
            loadChart(products[0]);
        }
    } catch (e) {
        console.error("Failed to load products", e);
    }
};

const renderProducts = () => {
    productList.innerHTML = '';
    if(products.length === 0) {
        productList.innerHTML = '<div style="color:var(--text-muted);text-align:center;">No inventory available. Run the seeder or add manual entries!</div>';
        return;
    }
    
    products.forEach(p => {
        const div = document.createElement('div');
        div.className = 'product-card';
        div.id = `prod-card-${p.id}`;
        
        div.onclick = () => loadChart(p);
        
        let statsHtml = p.stats ? `<span>Avg: Rs. ${p.stats.avg}</span>` : `<span>No data</span>`;
        
        div.innerHTML = `
            <div class="product-title">${p.name}</div>
            <div class="product-meta">
                <span>${p.category || 'General'}</span>
                ${statsHtml}
            </div>
        `;
        productList.appendChild(div);
    });
};

const populateSelects = () => {
    alertProductSelect.innerHTML = '<option value="" disabled selected>Choose a tracked product...</option>';
    products.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.name;
        alertProductSelect.appendChild(opt);
    });
};

const loadChart = async (product) => {
    currentProductId = product.id;
    
    // UI active state handling
    document.querySelectorAll('.product-card').forEach(c => c.classList.remove('active'));
    const activeCard = document.getElementById(`prod-card-${product.id}`);
    if (activeCard) activeCard.classList.add('active');

    chartTitle.innerHTML = `${product.name} <span class="badge">All Data</span>`;
    
    if (product.stats) {
        chartStats.innerHTML = `
            <div>Min: <span>Rs. ${product.stats.min}</span></div>
            <div>Max: <span>Rs. ${product.stats.max}</span></div>
            <div>Entries: <span>${product.stats.count}</span></div>
        `;
    } else {
        chartStats.innerHTML = '';
    }

    try {
        const res = await fetch(`/api/history/${product.id}`);
        const history = await res.json();
        renderChart(history);
        
        // Load AI recommendations
        loadRecommendations(product.id);
    } catch (e) {
        console.error("Chart load failed", e);
    }
};

const renderChart = (data) => {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (currentChart) {
        currentChart.destroy();
    }

    // Group by vendor for datasets
    const vendors = [...new Set(data.map(d => d.vendor))];
    const colors = ['#38bdf8', '#818cf8', '#34d399', '#f472b6'];
    
    // Sort all dates to create unified X axis
    const dates = [...new Set(data.map(d => {
        return d.date.split(' ')[0]; // Just the YYYY-MM-DD
    }))].sort((a,b) => new Date(a) - new Date(b));

    const datasets = vendors.map((v, i) => {
        const vData = data.filter(d => d.vendor === v);
        // Map data to the unified dates array 
        const mappedData = dates.map(dt => {
            const point = vData.find(d => d.date.startsWith(dt));
            return point ? point.price : null;
        });

        const c = colors[i % colors.length];
        return {
            label: v,
            data: mappedData,
            borderColor: c,
            backgroundColor: c + '33',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#0f172a',
            pointBorderColor: c,
            pointBorderWidth: 2,
            pointRadius: 4,
            spanGaps: true
        };
    });

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Outfit';

    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end', labels: { boxWidth: 15, usePointStyle: true } },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#38bdf8',
                    padding: 12,
                    borderColor: 'rgba(56, 189, 248, 0.2)',
                    borderWidth: 1,
                    displayColors: false
                }
            },
            scales: {
                y: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, beginAtZero: false },
                x: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, ticks: { maxTicksLimit: 10 } }
            },
            interaction: {
                mode: 'nearest',
                intersect: false,
            }
        }
    });
};

// Form Handlers
document.getElementById('priceForm').onsubmit = async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    
    const payload = {
        product_name: document.getElementById('prodName').value,
        category: document.getElementById('prodCat').value,
        vendor_name: document.getElementById('vendName').value,
        price: document.getElementById('prodPrice').value
    };

    try {
        const res = await fetch('/api/add_price', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            showToast('Price Entry Recorded Successfully!');
            e.target.reset();
            loadProducts(); // refresh UI automatically
        }
    } catch (err) {
        showToast('Error recording entry');
    }
    btn.innerHTML = 'Record Transaction <i class="fa-solid fa-arrow-right"></i>';
};

document.getElementById('alertForm').onsubmit = async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Configuring...';

    const payload = {
        product_id: document.getElementById('alertProductSelect').value,
        target_price: document.getElementById('alertPrice').value
    };

    try {
        const res = await fetch('/api/add_alert', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            showToast('Alert Threshold Set & Active!');
            e.target.reset();
        }
    } catch (err) {
        showToast('Error setting alert');
    }
    btn.innerHTML = 'Initialize Watcher <i class="fa-solid fa-shield-alt"></i>';
};

// Initialization triggers
window.onload = loadProducts;
