
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'adopter-info-app-secret-key-2025'

# === CONFIGURATION ===
# Use an absolute upload folder to avoid path issues
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'assets')

DB_PATH = os.path.join(BASE_DIR, 'adopter_records.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)


# === DATABASE MODEL ===
class AdopterRecord(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    childName = db.Column(db.String(100), nullable=False)
    contactNumber = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text, nullable=False)
    occupation = db.Column(db.String(100))
    adharCardNumber = db.Column(db.String(12))
    panCardNumber = db.Column(db.String(10))
    qualification = db.Column(db.String(100))
    income = db.Column(db.Float)
    maritalStatus = db.Column(db.String(20))
    dateOfAdoption = db.Column(db.String(20), nullable=False)
    adoptionStatus = db.Column(db.String(20), default='Applied')
    photo = db.Column(db.String(500))
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables
with app.app_context():
    db.create_all()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/assets/<filename>')
def uploaded_file(filename):
    # Serve files from absolute upload folder
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# === HTML TEMPLATE ===
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Adopter Management System</title>
    <style>
        :root {
            --bg-primary: #ffffff; --bg-secondary: #f8f9fa; --text-primary: #212529;
            --text-secondary: #6c757d; --primary-color: #007bff; --success-color: #28a745;
            --danger-color: #dc3545; --border-color: #dee2e6; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
        }
        [data-theme="dark"] {
            --bg-primary: #1a1a1a; --bg-secondary: #2d2d2d; --text-primary: #ffffff;
            --text-secondary: #adb5bd; --primary-color: #4dabf7; --success-color: #51cf66;
            --danger-color: #ff6b6b; --border-color: #444444; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.5);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; transition: all 0.3s ease; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding: 20px; background: var(--bg-secondary); border-radius: 15px; box-shadow: var(--shadow); }
        .logo { font-size: 2rem; font-weight: bold; background: linear-gradient(45deg, var(--primary-color), #6610f2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .theme-toggle { background: none; border: 2px solid var(--primary-color); width: 50px; height: 50px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; transition: all 0.3s ease; }
        .theme-toggle:hover { transform: scale(1.1); box-shadow: 0 0 20px var(--primary-color); }
        .btn { padding: 12px 24px; border: none; border-radius: 25px; cursor: pointer; font-size: 1rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: all 0.3s ease; box-shadow: var(--shadow); margin: 5px; }
        .btn-primary { background: var(--primary-color); color: white; } .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,123,255,0.4); }
        .btn-success { background: var(--success-color); color: white; } .btn-danger { background: var(--danger-color); color: white; }
        .btn-secondary { background: var(--text-secondary); color: white; } .btn-info { background: #17a2b8; color: white; }
        .page { display: none; animation: fadeIn 0.5s ease-in; } .page.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .search-panel { background: var(--bg-secondary); padding: 20px; border-radius: 15px; margin-bottom: 30px; box-shadow: var(--shadow); display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .search-input { flex: 1; max-width: 400px; padding: 12px 20px; border: 2px solid var(--border-color); border-radius: 25px; font-size: 1rem; transition: all 0.3s ease; background: var(--bg-primary); color: var(--text-primary); }
        .search-input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(0,123,255,0.1); }
        .records-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .record-card { background: var(--bg-secondary); padding: 25px; border-radius: 20px; box-shadow: var(--shadow); transition: all 0.3s ease; border-left: 5px solid var(--primary-color); }
        .record-card:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.2); }
        .record-name { font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; color: var(--primary-color); word-break: break-word; }
        .record-detail { margin: 8px 0; word-break: break-word; }
        .form-container { background: var(--bg-secondary); padding: 40px; border-radius: 25px; box-shadow: var(--shadow); max-width: 1000px; margin: 0 auto; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .form-group { margin-bottom: 25px; } .form-group.full-width { grid-column: 1 / -1; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary); }
        .required { color: var(--danger-color); }
        input, select, textarea { width: 100%; padding: 15px; border: 2px solid var(--border-color); border-radius: 12px; font-size: 1rem; transition: all 0.3s ease; background: var(--bg-primary); color: var(--text-primary); }
        input:focus, select:focus, textarea:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(0,123,255,0.1); }
        textarea { resize: vertical; min-height: 100px; }
        .file-upload { position: relative; overflow: hidden; display: inline-block; width: 100%; }
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
        .alert { padding: 15px; margin: 20px 0; border-radius: 10px; font-weight: 500; }
        .alert-success { background: rgba(40, 167, 69, 0.1); color: #28a745; border: 1px solid #28a745; }
        .alert-error { background: rgba(220, 53, 69, 0.1); color: #dc3545; border: 1px solid #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">👤 AdopterInfo </div>
            <div><button class="theme-toggle" id="themeToggle" title="Toggle Dark/Light">☀️</button></div>
        </div>

        <!-- Records Page -->
        <div id="recordsPage" class="page active">
            <div class="stats">
                <div class="stat-card"><div class="stat-number" id="totalRecords">0</div><div>Total Records</div></div>
                <div class="stat-card"><div class="stat-number" id="completedCount">0</div><div>Completed</div></div>
                <div class="stat-card"><div class="stat-number" id="appliedCount">0</div><div>Applied</div></div>
                <div class="stat-card"><div class="stat-number" id="approvedCount">0</div><div>Approved</div></div>
            </div>
            <div class="search-panel">
                <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search by name, child name, contact or email...">
                <button class="btn btn-primary" onclick="performSearch()">Search</button>
                <button class="btn btn-secondary" onclick="resetSearch()">All Records</button>
            </div>
            <div style="display: flex; gap: 15px; margin-bottom: 30px; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="showPage('formPage'); resetForm()">➕ Add New</button>
                <button class="btn btn-secondary" onclick="exportData()">📥 Export JSON</button>
            </div>
            <div class="records-grid" id="recordsGrid">
                <div class="empty-state" id="emptyState">
                    <div style="font-size: 4rem;">👤</div>
                    <h2>No records yet</h2>
                    <p>Click "Add New" to get started</p>
                </div>
            </div>
        </div>

        <!-- Form Page -->
        <div id="formPage" class="page">
            <button class="btn btn-secondary" onclick="showPage('recordsPage')" style="margin-bottom: 30px;">← Back</button>
            <div class="form-container">
                <h1 style="text-align: center; margin-bottom: 40px; color: var(--primary-color);"><span id="formTitle">Add New Record</span></h1>
                <form id="adopterForm" enctype="multipart/form-data">
                    <input type="hidden" id="recordId" name="recordId">
                    <input type="hidden" id="existingPhoto" name="existingPhoto">
                    <div class="form-grid">
                        <div>
                            <div class="form-group"><label>Name <span class="required">*</span></label><input type="text" id="name" name="name" required></div>
                            <div class="form-group"><label>Child Name <span class="required">*</span></label><input type="text" id="childName" name="childName" required></div>
                            <div class="form-group"><label>Contact <span class="required">*</span></label><input type="tel" id="contactNumber" name="contactNumber" pattern="[0-9]{10,15}" required></div>
                            <div class="form-group"><label>Address <span class="required">*</span></label><textarea id="address" name="address" required></textarea></div>
                            <div class="form-group"><label>Occupation</label><input type="text" id="occupation" name="occupation"></div>
                            <div class="form-group"><label>Aadhar</label><input type="text" id="adharCardNumber" name="adharCardNumber" pattern="\\d{12}"></div>
                            <div class="form-group"><label>Qualification</label><input type="text" id="qualification" name="qualification"></div>
                        </div>
                        <div>
                            <div class="form-group">
                                <label>Photo</label>
                                <div class="file-upload"><input type="file" id="photo" name="photo" accept="image/*"><label for="photo" class="btn btn-primary">📷 Choose Photo</label></div>
                                <img id="photoPreview" class="photo-preview" style="display: none;">
                            </div>
                            <div class="form-group"><label>Email</label><input type="email" id="email" name="email"></div>
                            <div class="form-group"><label>Marital Status</label><select id="maritalStatus" name="maritalStatus"><option value="">Select</option><option value="Single">Single</option><option value="Married">Married</option><option value="Divorced">Divorced</option></select></div>
                            <div class="form-group"><label>Date <span class="required">*</span></label><input type="date" id="dateOfAdoption" name="dateOfAdoption" required></div>
                            <div class="form-group"><label>PAN</label><input type="text" id="panCardNumber" name="panCardNumber" pattern="[A-Z]{5}[0-9]{4}[A-Z]{1}"></div>
                            <div class="form-group"><label>Income</label><input type="number" id="income" name="income" min="0" step="0.01"></div>
                        </div>
                        <div class="form-group full-width">
                            <label>Status <span class="required">*</span></label>
                            <select id="adoptionStatus" name="adoptionStatus" required>
                                <option value="">Select</option><option value="Applied">Applied</option><option value="Approved">Approved</option><option value="Completed">Completed</option>
                            </select>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <!-- Save button: visibility controlled via JS when editing/viewing -->
                        <button type="submit" class="btn btn-success" id="saveBtn" style="font-size: 1.2rem; padding: 18px 50px;">💾 Save Record</button>
                        <button type="button" id="cancelBtn" class="btn btn-secondary" style="font-size: 1.2rem; padding: 18px 50px; display:none; margin-left: 10px;">❌ Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

<script>
/* Records injected from Flask */
let records = {{ records|tojson|safe }};
let filteredRecords = [...records];
let editingId = null;

document.addEventListener('DOMContentLoaded', function() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    document.getElementById('themeToggle').textContent = currentTheme === 'light' ? '🌙' : '☀️';

    document.getElementById('themeToggle').addEventListener('click', function() {
        const newTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.textContent = newTheme === 'light' ? '🌙' : '☀️';
    });

    renderRecords();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    document.getElementById('photo').addEventListener('change', (e) => {
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

    document.getElementById('adopterForm').addEventListener('submit', handleFormSubmit);
    document.getElementById('cancelBtn').addEventListener('click', () => {
        resetForm(); showPage('recordsPage');
    });
}

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    if (pageId === 'recordsPage') renderRecords();
}

function performSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase().trim();
    if (!query) return resetSearch();
    filteredRecords = records.filter(r =>
        (r.name || '').toLowerCase().includes(query) ||
        (r.childName || '').toLowerCase().includes(query) ||
        (r.contactNumber || '').includes(query) ||
        (r.email || '').toLowerCase().includes(query)
    );
    renderRecords();
}

function resetSearch() {
    document.getElementById('searchInput').value = '';
    filteredRecords = [...records];
    renderRecords();
}

function updateStats() {
    const total = filteredRecords.length;
    const stats = {
        completed: filteredRecords.filter(r => r.adoptionStatus === 'Completed').length,
        applied: filteredRecords.filter(r => r.adoptionStatus === 'Applied').length,
        approved: filteredRecords.filter(r => r.adoptionStatus === 'Approved').length
    };
    document.getElementById('totalRecords').textContent = total;
    document.getElementById('completedCount').textContent = stats.completed;
    document.getElementById('appliedCount').textContent = stats.applied;
    document.getElementById('approvedCount').textContent = stats.approved;
}

function renderRecords() {
    const grid = document.getElementById('recordsGrid');
    const emptyState = document.getElementById('emptyState');
    if (filteredRecords.length === 0) {
        grid.innerHTML = emptyState.outerHTML;
        updateStats();
        return;
    }
    grid.innerHTML = filteredRecords.map(r => `
        <div class="record-card">
            <div class="record-name">${r.name}</div>
            ${r.photo ? `<img src="/assets/${r.photo}" style="width:60px;height:60px;border-radius:10px;object-fit:cover;float:right;margin-left:10px;" onerror="this.style.display='none'">` : ''}
            <div class="record-detail"><strong>Child: </strong> ${r.childName}</div>
            <div class="record-detail"><strong>Mobile: </strong> ${r.contactNumber}</div>
            <div class="record-detail"><strong>Email:</strong> ${r.email || 'N/A'}</div>
            <div class="record-detail"><strong>Address:</strong> ${r.address && r.address.length > 50 ? r.address.substring(0, 50) + '...' : (r.address || '')}</div>
            <div class="record-detail"><strong>Occupation:</strong> ${r.occupation || 'N/A'}</div>
            <div class="record-detail"><strong>Status:</strong>
                <span style="color: ${r.adoptionStatus === 'Completed' ? '#28a745' : r.adoptionStatus === 'Approved' ? '#17a2b8' : '#ffc107'}; font-weight: bold;">
                    ${r.adoptionStatus}
                </span>
            </div>
            <div class="btn-group">
                <button class="btn btn-info" onclick="viewRecord('${r.id}')">👁️ View</button>
                <button class="btn btn-primary" onclick="editRecord('${r.id}')">✏️ Edit</button>
                <button class="btn btn-danger" onclick="deleteRecord('${r.id}')">🗑️ Delete</button>
            </div>
            <div style="clear: both;"></div>
        </div>
    `).join('');
    updateStats();
}

function resetForm() {
    editingId = null;
    document.getElementById('formTitle').textContent = 'Add New Record';
    document.getElementById('recordId').value = '';
    document.getElementById('existingPhoto').value = '';
    document.getElementById('adopterForm').reset();
    document.getElementById('photoPreview').style.display = 'none';
    document.getElementById('cancelBtn').style.display = 'none';
    // ensure save button visible for new record
    document.getElementById('saveBtn').style.display = 'inline-block';
    Array.from(document.querySelectorAll('#adopterForm input, #adopterForm select, #adopterForm textarea')).forEach(el => el.disabled = false);
}

function populateForm(record, readonly = false) {
    editingId = record.id;
    document.getElementById('recordId').value = record.id;
    document.getElementById('existingPhoto').value = record.photo || '';
    document.getElementById('name').value = record.name || '';
    document.getElementById('childName').value = record.childName || '';
    document.getElementById('contactNumber').value = record.contactNumber || '';
    document.getElementById('email').value = record.email || '';
    document.getElementById('address').value = record.address || '';
    document.getElementById('occupation').value = record.occupation || '';
    document.getElementById('maritalStatus').value = record.maritalStatus || '';
    document.getElementById('dateOfAdoption').value = record.dateOfAdoption || '';
    document.getElementById('adharCardNumber').value = record.adharCardNumber || '';
    document.getElementById('panCardNumber').value = record.panCardNumber || '';
    document.getElementById('qualification').value = record.qualification || '';
    document.getElementById('income').value = record.income || '';
    document.getElementById('adoptionStatus').value = record.adoptionStatus || '';

    if (record.photo) {
        document.getElementById('photoPreview').src = `/assets/${record.photo}`;
        document.getElementById('photoPreview').style.display = 'block';
    } else {
        document.getElementById('photoPreview').style.display = 'none';
    }

    const inputs = document.querySelectorAll('#adopterForm input:not([type=hidden]), #adopterForm select, #adopterForm textarea');
    inputs.forEach(input => input.disabled = readonly);

    // Show cancel button whenever we are on a record form (view or edit)
    document.getElementById('cancelBtn').style.display = 'inline-block';

    // Ensure Save button visibility is explicitly controlled:
    // - hide when readonly (view mode)
    // - show when editing (readonly === false)
    document.getElementById('saveBtn').style.display = readonly ? 'none' : 'inline-block';

    document.getElementById('formTitle').textContent = readonly ? 'View Record' : 'Edit Record';
}

/* Improved handleFormSubmit:
   - POST to /api/records (no trailing slash)
   - PUT to /api/records/<id>
*/
async function handleFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const recordId = (document.getElementById('recordId').value || '').trim();

    // Build the correct URL: POST -> /api/records, PUT -> /api/records/<id>
    const url = recordId ? `/api/records/${recordId}` : '/api/records';
    const method = recordId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            body: formData
        });

        if (response.ok) {
            alert('✅ Record saved successfully!');
            resetForm();
            showPage('recordsPage');
            // reload to refresh server-sourced records
            location.reload();
        } else {
            const error = await response.json().catch(() => ({}));
            alert('❌ Error: ' + (error.message || 'Failed to save record'));
        }
    } catch (error) {
        alert('❌ Network error. Please try again.');
    }
}

function viewRecord(id) {
    const record = records.find(r => r.id === id);
    if (record) {
        populateForm(record, true);
        showPage('formPage');
    }
}

function editRecord(id) {
    const record = records.find(r => r.id === id);
    if (record) {
        populateForm(record, false);
        showPage('formPage');
    }
}

async function deleteRecord(id) {
    if (confirm('Are you sure you want to delete this record?')) {
        try {
            const response = await fetch(`/api/records/${id}`, { method: 'DELETE' });
            if (response.ok) {
                alert('✅ Record deleted successfully!');
                location.reload();
            } else {
                alert('❌ Delete failed');
            }
        } catch (error) {
            alert('❌ Delete failed');
        }
    }
}

function exportData() {
    const dataStr = JSON.stringify(records, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `adopter_records_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
}
</script>
</body>
</html>
"""


# === ROUTES ===
@app.route('/')
def index():
    records = AdopterRecord.query.order_by(AdopterRecord.createdAt.desc()).all()
    records_list = []
    for r in records:
        # Prepare simple serializable dict (all values as simple primitives / strings)
        record_dict = {}
        for c in r.__table__.columns:
            val = getattr(r, c.name)
            # convert datetimes / floats / None to JSON-friendly values
            if isinstance(val, datetime):
                record_dict[c.name] = val.isoformat()
            elif val is None:
                record_dict[c.name] = ''
            else:
                record_dict[c.name] = val
        records_list.append(record_dict)
    return render_template_string(HTML_TEMPLATE, records=records_list)


# Accept both /api/records and /api/records/ for safety
@app.route('/api/records', methods=['POST'])
@app.route('/api/records/', methods=['POST'])
def create_record():
    try:
        photo_filename = None
        if 'photo' in request.files and request.files['photo'].filename:
            file = request.files['photo']
            if allowed_file(file.filename):
                # build a secure filename
                original_name = secure_filename(file.filename)
                photo_filename = f"{uuid.uuid4().hex}_{original_name}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                file.save(filepath)

        # required fields
        name = request.form.get('name', '').strip()
        child_name = request.form.get('childName', '').strip()
        contact = request.form.get('contactNumber', '').strip()
        address = request.form.get('address', '').strip()
        date_of_adoption = request.form.get('dateOfAdoption', '').strip()
        if not name or not child_name or not contact or not address or not date_of_adoption:
            return jsonify({'error': 'Missing required fields (name, childName, contactNumber, address, dateOfAdoption)'}), 400

        income_val = None
        if request.form.get('income'):
            try:
                income_val = float(request.form.get('income'))
            except ValueError:
                income_val = None

        record = AdopterRecord(
            name=name,
            childName=child_name,
            contactNumber=contact,
            address=address,
            dateOfAdoption=date_of_adoption,
            adoptionStatus=request.form.get('adoptionStatus', 'Applied'),
            photo=photo_filename,
            email=request.form.get('email') or '',
            occupation=request.form.get('occupation') or '',
            adharCardNumber=request.form.get('adharCardNumber') or '',
            panCardNumber=request.form.get('panCardNumber') or '',
            qualification=request.form.get('qualification') or '',
            income=income_val,
            maritalStatus=request.form.get('maritalStatus') or ''
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'message': 'Created', 'id': record.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/records/<record_id>', methods=['GET', 'PUT', 'DELETE'])
def record_ops(record_id):
    record = AdopterRecord.query.get(record_id)
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    if request.method == 'GET':
        result = {}
        for c in record.__table__.columns:
            val = getattr(record, c.name)
            if isinstance(val, datetime):
                result[c.name] = val.isoformat()
            elif val is None:
                result[c.name] = ''
            else:
                result[c.name] = val
        return jsonify(result)

    elif request.method == 'PUT':
        try:
            # Handle photo update
            if 'photo' in request.files and request.files['photo'].filename:
                file = request.files['photo']
                if allowed_file(file.filename):
                    # Delete old photo
                    if record.photo:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], record.photo)
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                            except Exception:
                                pass
                    # Save new photo
                    original_name = secure_filename(file.filename)
                    photo_filename = f"{uuid.uuid4().hex}_{original_name}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                    file.save(filepath)
                    record.photo = photo_filename

            # Update simple fields from form; ignore id
            for key, value in request.form.items():
                if hasattr(record, key) and key != 'id':
                    # convert income to float where appropriate
                    if key == 'income':
                        try:
                            setattr(record, key, float(value) if value != '' else None)
                        except ValueError:
                            setattr(record, key, None)
                    else:
                        setattr(record, key, value)

            db.session.commit()
            return jsonify({'message': 'Updated'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    elif request.method == 'DELETE':
        try:
            if record.photo:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], record.photo)
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                    except Exception:
                        pass
            db.session.delete(record)
            db.session.commit()
            return jsonify({'message': 'Deleted'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    print("🚀 Adopter Management System started successfully")
    app.run(debug=True, port=5002)


