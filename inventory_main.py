from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database and upload configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/assets'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

db = SQLAlchemy(app)


# Inventory Item Model
class InventoryItem(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    itemName = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer)
    unit = db.Column(db.String(20))
    purchaseDate = db.Column(db.String(20), nullable=False)
    expiryDate = db.Column(db.String(20), nullable=False)
    supplier = db.Column(db.String(100))
    storageArea = db.Column(db.String(100))
    condition = db.Column(db.String(20), default='New')
    minimumStockLevel = db.Column(db.Integer)
    itemPhoto = db.Column(db.String(500))  # Filename only
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create database tables
with app.app_context():
    db.create_all()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Serve uploaded images
@app.route('/assets/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Inventory Management System</title>
    <style>
        :root {
            --bg-primary: #ffffff; --bg-secondary: #f8f9fa; --text-primary: #212529;
            --text-secondary: #6c757d; --primary-color: #007bff; --success-color: #28a745;
            --danger-color: #dc3545; --border-color: #dee2e6; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
            --warning-color: #ffc107;
        }
        [data-theme="dark"] {
            --bg-primary: #1a1a1a; --bg-secondary: #2d2d2d; --text-primary: #ffffff;
            --text-secondary: #adb5bd; --primary-color: #4dabf7; --success-color: #51cf66;
            --danger-color: #ff6b6b; --border-color: #444444; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.5);
            --warning-color: #ffed4a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; transition: all 0.3s ease; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding: 20px; background: var(--bg-secondary); border-radius: 15px; box-shadow: var(--shadow); }
        .logo { font-size: 2rem; font-weight: bold; background: linear-gradient(45deg, var(--primary-color), #6610f2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .theme-toggle { background: none; border: 2px solid var(--primary-color); width: 50px; height: 50px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; transition: all 0.3s ease; }
        .theme-toggle:hover { transform: scale(1.1); box-shadow: 0 0 20px var(--primary-color); }
        .btn { padding: 12px 24px; border: none; border-radius: 25px; cursor: pointer; font-size: 1rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: all 0.3s ease; box-shadow: var(--shadow); }
        .btn-primary { background: var(--primary-color); color: white; } .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,123,255,0.4); }
        .btn-success { background: var(--success-color); color: white; } .btn-danger { background: var(--danger-color); color: white; }
        .btn-secondary { background: var(--text-secondary); color: white; } .btn-info { background: #17a2b8; color: white; }
        .btn-warning { background: var(--warning-color); color: #212529; }
        .page { display: none; animation: fadeIn 0.5s ease-in; } .page.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .search-panel { background: var(--bg-secondary); padding: 20px; border-radius: 15px; margin-bottom: 30px; box-shadow: var(--shadow); display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .search-input { flex: 1; max-width: 400px; padding: 12px 20px; border: 2px solid var(--border-color); border-radius: 25px; font-size: 1rem; transition: all 0.3s ease; }
        .search-input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(0,123,255,0.1); }
        .records-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .record-card { background: var(--bg-secondary); padding: 25px; border-radius: 20px; box-shadow: var(--shadow); transition: all 0.3s ease; border-left: 5px solid var(--primary-color); position: relative; }
        .record-card:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.2); }
        .record-name { font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; color: var(--primary-color); }
        .record-detail { margin: 8px 0; }
        .low-stock { color: var(--warning-color); font-weight: bold; }
        .expired { color: var(--danger-color); font-weight: bold; }
        .form-container { background: var(--bg-secondary); padding: 40px; border-radius: 25px; box-shadow: var(--shadow); max-width: 1000px; margin: 0 auto; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .form-group { margin-bottom: 25px; } .form-group.full-width { grid-column: 1 / -1; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary); }
        .required { color: var(--danger-color); }
        input, select, textarea { width: 100%; padding: 15px; border: 2px solid var(--border-color); border-radius: 12px; font-size: 1rem; transition: all 0.3s ease; background: var(--bg-primary); color: var(--text-primary); }
        input:focus, select:focus, textarea:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(0,123,255,0.1); }
        textarea { resize: vertical; min-height: 100px; }
        .file-upload { position: relative; overflow: hidden; display: inline-block; }
        .file-upload input[type=file] { position: absolute; left: -9999px; }
        .photo-preview { width: 100px; height: 100px; border-radius: 12px; object-fit: cover; border: 3px solid var(--primary-color); margin-top: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, var(--primary-color), #0056b3); color: white; padding: 25px; border-radius: 20px; text-align: center; box-shadow: var(--shadow); }
        .stat-number { font-size: 2.5rem; font-weight: bold; }
        .btn-group { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
        @media (max-width: 768px) { 
            .form-grid, .records-grid { grid-template-columns: 1fr; } 
            .header { flex-direction: column; gap: 20px; text-align: center; } 
            .container { padding: 10px; } 
            .search-panel { flex-direction: column; align-items: stretch; } 
            .search-input { max-width: none; } 
        }
        .empty-state { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📦 Inventory</div>
            <div><button class="theme-toggle" id="themeToggle">☀️</button></div>
        </div>

        <div id="recordsPage" class="page active">
            <div class="stats">
                <div class="stat-card"><div class="stat-number" id="totalRecords">0</div><div>Total Items</div></div>
                <div class="stat-card"><div class="stat-number" id="lowStockCount">0</div><div>Low Stock</div></div>
                <div class="stat-card"><div class="stat-number" id="expiringSoon">0</div><div>Expiring Soon</div></div>
            </div>
            <div class="search-panel">
                <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search by item name, supplier, or storage...">
                <button class="btn btn-primary" onclick="performSearch()">🔍 Search</button>
                <button class="btn btn-secondary" onclick="resetSearch()">📄 All Records</button>
            </div>
            <div style="display: flex; gap: 15px; margin-bottom: 30px;">
                <a href="#formPage" class="btn btn-primary" onclick="showPage('formPage'); resetForm();">➕ Add New Item</a>
                <button class="btn btn-secondary" onclick="exportData()">📥 Export Data</button>
            </div>
            <div class="records-grid" id="recordsGrid">
                <div class="empty-state" id="emptyState"><div style="font-size: 4rem;">📦</div><h2>No inventory items yet</h2><p>Click "Add New Item" to get started</p></div>
            </div>
        </div>

        <div id="formPage" class="page">
            <a href="#recordsPage" class="btn btn-secondary" onclick="showPage('recordsPage')" style="margin-bottom: 30px; display: inline-flex;">← Back to Inventory</a>
            <div class="form-container">
                <h1 style="text-align: center; margin-bottom: 40px; color: var(--primary-color);"><span id="formTitle">Add New Inventory Item</span></h1>
                <form id="inventoryForm">
                    <input type="hidden" id="recordId">
                    <input type="hidden" id="existingPhoto">
                    <div class="form-grid">
                        <div>
                            <div class="form-group"><label>Item Name <span class="required">*</span></label><input type="text" id="itemName" required></div>
                            <div class="form-group"><label>Quantity</label><input type="number" id="quantity" min="0"></div>
                            <div class="form-group"><label>Unit</label><input type="text" id="unit" placeholder="e.g., kg, pcs, liters"></div>
                            <div class="form-group"><label>Purchase Date <span class="required">*</span></label><input type="date" id="purchaseDate" required></div>
                        </div>
                        <div>
                            <div class="form-group">
                                <label>Item Photo</label>
                                <div class="file-upload"><input type="file" id="itemPhoto" accept="image/*"><label for="itemPhoto" class="btn btn-primary">📷 Upload Photo</label></div>
                                <img id="photoPreview" class="photo-preview" style="display: none;">
                            </div>
                            <div class="form-group"><label>Expiry Date <span class="required">*</span></label><input type="date" id="expiryDate" required></div>
                            <div class="form-group"><label>Condition</label><select id="condition"><option value="New">New</option><option value="Used">Used</option><option value="Damaged">Damaged</option></select></div>
                        </div>
                        <h3 style="grid-column: 1 / -1; text-align: center; margin: 30px 0 20px 0; color: var(--primary-color);">📍 Supplier & Storage</h3>
                        <div>
                            <div class="form-group"><label>Supplier</label><input type="text" id="supplier" placeholder="Supplier name/company"></div>
                            <div class="form-group"><label>Storage Area</label><input type="text" id="storageArea" placeholder="e.g., Shelf A1, Warehouse B"></div>
                        </div>
                        <div>
                            <div class="form-group"><label>Minimum Stock Level</label><input type="number" id="minimumStockLevel" min="0" placeholder="Alert when stock falls below this"></div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <button type="submit" class="btn btn-success" style="font-size: 1.2rem; padding: 18px 50px;">💾 Save Inventory Item</button>
                        <button type="button" id="cancelEditBtn" class="btn btn-secondary" style="font-size: 1.2rem; padding: 18px 50px; display:none; margin-left: 10px;">❌ Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

<script>
let records = {{ records|tojson|safe }};
let filteredRecords = [...records];
let editingRecordId = null;

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
const currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);
themeToggle.textContent = currentTheme === 'light' ? '🌙' : '☀️';
themeToggle.addEventListener('click', () => {
    const newTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeToggle.textContent = newTheme === 'light' ? '🌙' : '☀️';
});

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    if (pageId === 'recordsPage') renderRecords();
}

function performSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    filteredRecords = records.filter(record =>
        (record.itemName && record.itemName.toLowerCase().includes(query)) ||
        (record.supplier && record.supplier.toLowerCase().includes(query)) ||
        (record.storageArea && record.storageArea.toLowerCase().includes(query))
    );
    renderRecords();
}

function renderRecords() {
    const grid = document.getElementById('recordsGrid');
    const emptyState = document.getElementById('emptyState');
    if (filteredRecords.length === 0) {
        grid.innerHTML = emptyState.outerHTML;
        updateStats(0, 0, 0);
        return;
    }
    grid.innerHTML = filteredRecords.map(record => {
        const qtyClass = record.quantity <= (record.minimumStockLevel || 0) ? 'low-stock' : '';
        const expiry = record.expiryDate ? new Date(record.expiryDate) : null;
        const isExpiring = expiry && expiry < new Date(Date.now() + 30*24*60*60*1000);
        const expiryClass = isExpiring ? 'expired' : '';

        return `
        <div class="record-card">
            <div class="record-name">${record.itemName}</div>
            ${record.itemPhoto ? `<img src="/assets/${record.itemPhoto}" style="width:60px;height:60px;border-radius:10px;object-fit:cover;float:right;" onerror="this.style.display='none'">` : ''}
            <div class="record-detail"><strong>Qty:</strong> <span class="${qtyClass}">${record.quantity || 0} ${record.unit || ''}</span></div>
            <div class="record-detail"><strong>Condition:</strong> ${record.condition || 'N/A'}</div>
            <div class="record-detail"><strong>Purchase:</strong> ${record.purchaseDate ? new Date(record.purchaseDate).toLocaleDateString() : 'N/A'}</div>
            <div class="record-detail"><strong>Expiry:</strong> <span class="${expiryClass}">${record.expiryDate ? new Date(record.expiryDate).toLocaleDateString() : 'N/A'}</span></div>
            <div class="record-detail"><strong>Supplier:</strong> ${record.supplier || 'N/A'}</div>
            <div class="record-detail"><strong>Storage:</strong> ${record.storageArea || 'N/A'}</div>
            <div class="btn-group">
                <button class="btn btn-info" onclick="viewRecord('${record.id}')">👁️ View</button>
                <button class="btn btn-primary" onclick="editRecord('${record.id}')">✏️ Edit</button>
                <button class="btn btn-danger" onclick="deleteRecord('${record.id}')">🗑️ Delete</button>
            </div>
        </div>
        `;
    }).join('');
    updateStats(filteredRecords.length, 
                filteredRecords.filter(r => (r.quantity || 0) <= (r.minimumStockLevel || 0)).length,
                filteredRecords.filter(r => {
                    const expiry = r.expiryDate ? new Date(r.expiryDate) : null;
                    return expiry && expiry < new Date(Date.now() + 30*24*60*60*1000);
                }).length);
}

function updateStats(total, lowStock, expiring) {
    document.getElementById('totalRecords').textContent = total;
    document.getElementById('lowStockCount').textContent = lowStock;
    document.getElementById('expiringSoon').textContent = expiring;
}

document.getElementById('searchInput').addEventListener('keypress', (e) => { if (e.key === 'Enter') performSearch(); });
function resetSearch() { document.getElementById('searchInput').value = ''; filteredRecords = [...records]; renderRecords(); }

function resetForm() {
    editingRecordId = null;
    document.getElementById('formTitle').textContent = 'Add New Inventory Item';
    document.getElementById('recordId').value = '';
    document.getElementById('existingPhoto').value = '';
    document.getElementById('inventoryForm').reset();
    document.getElementById('photoPreview').style.display = 'none';
    document.getElementById('cancelEditBtn').style.display = 'none';
    document.querySelector("#inventoryForm button[type='submit']").style.display = 'inline-block';
}

function populateForm(record, readOnly = false) {
    document.getElementById('recordId').value = record.id;
    document.getElementById('existingPhoto').value = record.itemPhoto || '';
    document.getElementById('itemName').value = record.itemName || '';
    document.getElementById('quantity').value = record.quantity || '';
    document.getElementById('unit').value = record.unit || '';
    document.getElementById('purchaseDate').value = record.purchaseDate || '';
    document.getElementById('expiryDate').value = record.expiryDate || '';
    document.getElementById('supplier').value = record.supplier || '';
    document.getElementById('storageArea').value = record.storageArea || '';
    document.getElementById('condition').value = record.condition || '';
    document.getElementById('minimumStockLevel').value = record.minimumStockLevel || '';

    if (record.itemPhoto) {
        document.getElementById('photoPreview').src = `/assets/${record.itemPhoto}`;
        document.getElementById('photoPreview').style.display = 'block';
    }

    const inputs = Array.from(document.querySelectorAll("#inventoryForm input:not([type=hidden]), #inventoryForm select"));
    inputs.forEach(input => input.disabled = readOnly);

    document.getElementById('cancelEditBtn').style.display = 'inline-block';
    if (readOnly) {
        document.getElementById('formTitle').textContent = 'View Inventory Item';
        document.querySelector("#inventoryForm button[type='submit']").style.display = 'none';
    } else {
        document.getElementById('formTitle').textContent = 'Edit Inventory Item';
        document.querySelector("#inventoryForm button[type='submit']").style.display = 'inline-block';
    }
}

function viewRecord(id) { 
    const record = records.find(r => r.id === id); 
    if (!record) return alert("Item not found"); 
    editingRecordId = id; 
    populateForm(record, true); 
    showPage('formPage'); 
}
function editRecord(id) { 
    const record = records.find(r => r.id === id); 
    if (!record) return alert("Item not found"); 
    editingRecordId = id; 
    populateForm(record, false); 
    showPage('formPage'); 
}

document.getElementById('cancelEditBtn').addEventListener('click', () => { resetForm(); showPage('recordsPage'); });

// Photo preview
document.getElementById('itemPhoto').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('photoPreview').src = e.target.result;
            document.getElementById('photoPreview').style.display = 'block';
            document.getElementById('existingPhoto').value = '';
        };
        reader.readAsDataURL(file);
    }
});

// Form submission
document.getElementById('inventoryForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const recordId = document.getElementById('recordId').value;
    const existingPhoto = document.getElementById('existingPhoto').value;
    const photoFile = document.getElementById('itemPhoto').files[0];

    const formData = new FormData();
    formData.append('recordId', recordId);
    formData.append('existingPhoto', existingPhoto);
    formData.append('itemName', document.getElementById('itemName').value);
    formData.append('quantity', document.getElementById('quantity').value);
    formData.append('unit', document.getElementById('unit').value);
    formData.append('purchaseDate', document.getElementById('purchaseDate').value);
    formData.append('expiryDate', document.getElementById('expiryDate').value);
    formData.append('supplier', document.getElementById('supplier').value);
    formData.append('storageArea', document.getElementById('storageArea').value);
    formData.append('condition', document.getElementById('condition').value);
    formData.append('minimumStockLevel', document.getElementById('minimumStockLevel').value);

    if (photoFile) {
        formData.append('itemPhoto', photoFile);
    }

    const method = recordId ? 'PUT' : 'POST';
    const url = recordId ? `/api/inventory/${recordId}` : '/api/inventory';

    try {
        const response = await fetch(url, {
            method: method,
            body: formData
        });

        if (response.ok) {
    alert("Saved successfully");
    resetForm();
    location.reload();

        } else {
            alert('❌ Error saving item. Please try again.');
        }
    } catch (error) {
        alert('❌ Network error. Please check your connection.');
    }
});

async function deleteRecord(id) {
    if (confirm('Are you sure you want to delete this inventory item?')) {
        await fetch(`/api/inventory/${id}`, { method: 'DELETE' });
        location.reload();
    }
}

function exportData() {
    const dataStr = JSON.stringify(records, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'inventory.json';
    link.click();
}

renderRecords();
</script>
</body>
</html>
"""


@app.route('/')
def index():
    records = InventoryItem.query.all()
    records_json = []
    for record in records:
        record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}
        records_json.append(record_dict)
    return render_template_string(HTML_TEMPLATE, records=records_json)


@app.route('/api/inventory', methods=['POST'])
def create_record():
    if 'itemPhoto' in request.files and request.files['itemPhoto'].filename:
        file = request.files['itemPhoto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            request.form['itemPhoto'] = filename

    record = InventoryItem()
    for key, value in request.form.items():
        if hasattr(record, key) and key != 'id':
            setattr(record, key, value)

    db.session.add(record)
    db.session.commit()
    return jsonify({'message': 'Record created', 'id': record.id}), 201


@app.route('/api/inventory/<record_id>', methods=['GET', 'PUT', 'DELETE'])
def record_detail(record_id):
    record = InventoryItem.query.get(record_id)
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    if request.method == 'GET':
        return jsonify({c.name: getattr(record, c.name) for c in record.__table__.columns})

    elif request.method == 'PUT':
        if 'itemPhoto' in request.files and request.files['itemPhoto'].filename:
            file = request.files['itemPhoto']
            if file and allowed_file(file.filename):
                if record.itemPhoto:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], record.itemPhoto)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                record.itemPhoto = filename

        for key, value in request.form.items():
            if hasattr(record, key) and key != 'id':
                setattr(record, key, value)

        db.session.commit()
        return jsonify({'message': 'Record updated'})

    elif request.method == 'DELETE':
        if record.itemPhoto:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], record.itemPhoto)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Record deleted'})


if __name__ == '__main__':
    print("🚀 Starting Inventory Management System...")
    app.run(debug=True, port=5005)
