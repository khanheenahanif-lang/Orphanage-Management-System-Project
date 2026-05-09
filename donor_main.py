from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database and upload configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///donor_records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/assets'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

db = SQLAlchemy(app)


# Donor Model
class Donor(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    address = db.Column(db.Text)
    contact_number = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100))
    donation_amount = db.Column(db.Float)
    donated_thing = db.Column(db.String(200))
    date_of_donation = db.Column(db.String(20), nullable=False)
    organization_name = db.Column(db.String(150))
    donor_type = db.Column(db.String(20))  # Individual or Organization
    donor_photo = db.Column(db.String(500))  # Filename only
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Donor Management System</title>
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
        .theme-toggle { background: none; border: 2px solid var(--primary-color); width: 50px; height: 50px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; transition: all 0.3s ease; }
        .theme-toggle:hover { transform: scale(1.1); box-shadow: 0 0 20px var(--primary-color); }
        .btn { padding: 12px 24px; border: none; border-radius: 25px; cursor: pointer; font-size: 1rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: all 0.3s ease; box-shadow: var(--shadow); }
        .btn-primary { background: var(--primary-color); color: white; } .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,123,255,0.4); }
        .btn-success { background: var(--success-color); color: white; } .btn-danger { background: var(--danger-color); color: white; }
        .btn-secondary { background: var(--text-secondary); color: white; } .btn-info { background: #17a2b8; color: white; }
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
        .btn-group { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
        @media (max-width: 768px) { .form-grid, .records-grid { grid-template-columns: 1fr; } .header { flex-direction: column; gap: 20px; text-align: center; } .container { padding: 10px; } .search-panel { flex-direction: column; align-items: stretch; } .search-input { max-width: none; } }
        .empty-state { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎁 Donor </div>
            <div><button class="theme-toggle" id="themeToggle">☀️</button></div>
        </div>

        <div id="recordsPage" class="page active">
            <div class="search-panel">
                <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search by name, donated thing, or donor type...">
                <button class="btn btn-primary" onclick="performSearch()">🔍 Search</button>
                <button class="btn btn-secondary" onclick="resetSearch()">📄 All Records</button>
            </div>
            <div style="display: flex; gap: 15px; margin-bottom: 30px;">
                <a href="#formPage" class="btn btn-primary" onclick="showPage('formPage'); resetForm();">➕ Add New Donor</a>
            </div>
            <div class="records-grid" id="recordsGrid">
                <div class="empty-state" id="emptyState"><div style="font-size: 4rem;">🎁</div><h2>No records yet</h2><p>Click "Add New Donor" to get started</p></div>
            </div>
        </div>

        <div id="formPage" class="page">
            <a href="#recordsPage" class="btn btn-secondary" onclick="showPage('recordsPage')" style="margin-bottom: 30px; display: inline-flex;">← Back to Records</a>
            <div class="form-container">
                <h1 style="text-align: center; margin-bottom: 40px; color: var(--primary-color);"><span id="formTitle">Add New Donor</span></h1>
                <form id="donorForm" novalidate>
                    <input type="hidden" id="recordId">
                    <input type="hidden" id="existingPhoto">
                    <div class="form-grid">
                        <div>
                            <div class="form-group">
                                <label>Name <span class="required">*</span></label>
                                <input type="text" id="name" required />
                                <small id="nameError" style="color: var(--danger-color); display:none;">Name is required</small>
                            </div>
                            <div class="form-group">
                                <label>Age</label>
                                <input type="number" id="age" min="0" max="120" />
                            </div>
                            <div class="form-group">
                                <label>Gender</label>
                                <select id="gender">
                                    <option value="">Select Gender</option>
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Address</label>
                                <textarea id="address" placeholder="Enter address..."></textarea>
                            </div>
                            <div class="form-group">
                                <label>Contact Number <span class="required">*</span></label>
                                <input type="tel" id="contact_number" pattern="\\d{10}" maxlength="10" />
                                <small id="contactError" style="color: var(--danger-color); display:none;">Must be 10 digits</small>
                            </div>
                            <div class="form-group">
                                <label>Email</label>
                                <input type="email" id="email" />
                            </div>
                        </div>
                        <div>
                            <div class="form-group">
                                <label>Donation Amount</label>
                                <input type="number" id="donation_amount" min="0" step="0.01" />
                            </div>
                            <div class="form-group">
                                <label>Donated Thing</label>
                                <input type="text" id="donated_thing" />
                            </div>
                            <div class="form-group">
                                <label>Date of Donation <span class="required">*</span></label>
                                <input type="date" id="date_of_donation" required />
                                <small id="dateError" style="color: var(--danger-color); display:none;">Date of donation is required</small>
                            </div>
                            <div class="form-group">
                                <label>Organization Name</label>
                                <input type="text" id="organization_name" />
                            </div>
                            <div class="form-group">
                                <label>Donor Type</label>
                                <select id="donor_type">
                                    <option value="">Select Type</option>
                                    <option value="Individual">Individual</option>
                                    <option value="Organization">Organization</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Donor Photo</label>
                                <div class="file-upload">
                                    <input type="file" id="donorPhoto" accept="image/*" />
                                    <label for="donorPhoto" class="btn btn-primary">📷 Upload Photo</label>
                                </div>
                                <img id="photoPreview" class="photo-preview" style="display: none;" alt="Donor photo preview" />
                            </div>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <button type="submit" class="btn btn-success" style="font-size: 1.2rem; padding: 18px 50px;">💾 Save Donor</button>
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
        (record.name && record.name.toLowerCase().includes(query)) ||
        (record.donated_thing && record.donated_thing.toLowerCase().includes(query)) ||
        (record.donor_type && record.donor_type.toLowerCase().includes(query))
    );
    renderRecords();
}

function renderRecords() {
    const grid = document.getElementById('recordsGrid');
    const emptyState = document.getElementById('emptyState');
    if (filteredRecords.length === 0) {
        grid.innerHTML = emptyState.outerHTML;
        return;
    }
    grid.innerHTML = filteredRecords.map(record => `
        <div class="record-card">
            <div class="record-name">${record.name}</div>
            ${record.donor_photo ? `<img src="/assets/${record.donor_photo}" style="width:60px;height:60px;border-radius:10px;object-fit:cover;float:right;" onerror="this.style.display='none'">` : ''}
            <div class="record-detail"><strong>Age:</strong> ${record.age ?? 'N/A'}</div>
            <div class="record-detail"><strong>Gender:</strong> ${record.gender || 'N/A'}</div>
            <div class="record-detail"><strong>Contact:</strong> ${record.contact_number}</div>
            <div class="record-detail"><strong>Email:</strong> ${record.email || 'N/A'}</div>
            <div class="record-detail"><strong>Donation Amount:</strong> ${record.donation_amount != null ? '$' + record.donation_amount.toFixed(2) : 'N/A'}</div>
            <div class="record-detail"><strong>Donated Thing:</strong> ${record.donated_thing || 'N/A'}</div>
            <div class="record-detail"><strong>Date of Donation:</strong> ${record.date_of_donation ? new Date(record.date_of_donation).toLocaleDateString() : 'N/A'}</div>
            <div class="record-detail"><strong>Organization:</strong> ${record.organization_name || 'N/A'}</div>
            <div class="record-detail"><strong>Donor Type:</strong> ${record.donor_type || 'N/A'}</div>
            <div class="btn-group">
                <button class="btn btn-info" onclick="viewRecord('${record.id}')">👁️ View</button>
                <button class="btn btn-primary" onclick="editRecord('${record.id}')">✏️ Edit</button>
                <button class="btn btn-danger" onclick="deleteRecord('${record.id}')">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

document.getElementById('searchInput').addEventListener('keypress', (e) => { if (e.key === 'Enter') performSearch(); });
function resetSearch() {
    document.getElementById('searchInput').value = '';
    filteredRecords = [...records];
    renderRecords();
}

function resetForm() {
    editingRecordId = null;
    document.getElementById('formTitle').textContent = 'Add New Donor';
    document.getElementById('recordId').value = '';
    document.getElementById('existingPhoto').value = '';
    document.getElementById('donorForm').reset();
    document.getElementById('photoPreview').style.display = 'none';
    document.getElementById('cancelEditBtn').style.display = 'none';
    hideErrors();
    showSubmitButton(true);
}

function populateForm(record, readOnly = false) {
    document.getElementById('recordId').value = record.id;
    document.getElementById('existingPhoto').value = record.donor_photo || '';
    document.getElementById('name').value = record.name || '';
    document.getElementById('age').value = record.age ?? '';
    document.getElementById('gender').value = record.gender || '';
    document.getElementById('address').value = record.address || '';
    document.getElementById('contact_number').value = record.contact_number || '';
    document.getElementById('email').value = record.email || '';
    document.getElementById('donation_amount').value = record.donation_amount ?? '';
    document.getElementById('donated_thing').value = record.donated_thing || '';
    document.getElementById('date_of_donation').value = record.date_of_donation || '';
    document.getElementById('organization_name').value = record.organization_name || '';
    document.getElementById('donor_type').value = record.donor_type || '';

    if (record.donor_photo) {
        document.getElementById('photoPreview').src = `/assets/${record.donor_photo}`;
        document.getElementById('photoPreview').style.display = 'block';
    }

    const inputs = Array.from(document.querySelectorAll("#donorForm input:not([type=hidden]), #donorForm select, #donorForm textarea"));
    inputs.forEach(input => input.disabled = readOnly);

    document.getElementById('cancelEditBtn').style.display = 'inline-block';
    if (readOnly) {
        document.getElementById('formTitle').textContent = 'View Donor';
        showSubmitButton(false);
    } else {
        document.getElementById('formTitle').textContent = 'Edit Donor';
        showSubmitButton(true);
    }
}

function showSubmitButton(show) {
    const btn = document.querySelector("#donorForm button[type='submit']");
    if (btn) btn.style.display = show ? 'inline-block' : 'none';
}

function hideErrors() {
    document.getElementById('nameError').style.display = 'none';
    document.getElementById('contactError').style.display = 'none';
    document.getElementById('dateError').style.display = 'none';
}

function validateForm() {
    hideErrors();
    let valid = true;
    const name = document.getElementById('name').value.trim();
    const contact = document.getElementById('contact_number').value.trim();
    const dateDonation = document.getElementById('date_of_donation').value.trim();

    if (!name) {
        document.getElementById('nameError').style.display = 'block';
        valid = false;
    }
    if (!/^\d{10}$/.test(contact)) {
        document.getElementById('contactError').style.display = 'block';
        valid = false;
    }
    if (!dateDonation) {
        document.getElementById('dateError').style.display = 'block';
        valid = false;
    }
    return valid;
}

function viewRecord(id) { 
    const record = records.find(r => r.id === id); 
    if (!record) return alert("Record not found"); 
    editingRecordId = id; 
    populateForm(record, true); 
    showPage('formPage'); 
}
function editRecord(id) { 
    const record = records.find(r => r.id === id); 
    if (!record) return alert("Record not found"); 
    editingRecordId = id; 
    populateForm(record, false); 
    showPage('formPage'); 
}

document.getElementById('cancelEditBtn').addEventListener('click', () => { resetForm(); showPage('recordsPage'); });

// Photo preview
document.getElementById('donorPhoto').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('photoPreview').src = e.target.result;
            document.getElementById('photoPreview').style.display = 'block';
            document.getElementById('existingPhoto').value = ''; // Clear existing photo when new is uploaded
        };
        reader.readAsDataURL(file);
    }
});

// Form submission with validation and photo upload
document.getElementById('donorForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    const recordId = document.getElementById('recordId').value;
    const existingPhoto = document.getElementById('existingPhoto').value;
    const photoFile = document.getElementById('donorPhoto').files[0];

    const formData = new FormData();
    formData.append('recordId', recordId);
    formData.append('existingPhoto', existingPhoto);
    formData.append('name', document.getElementById('name').value);
    formData.append('age', document.getElementById('age').value);
    formData.append('gender', document.getElementById('gender').value);
    formData.append('address', document.getElementById('address').value);
    formData.append('contact_number', document.getElementById('contact_number').value);
    formData.append('email', document.getElementById('email').value);
    formData.append('donation_amount', document.getElementById('donation_amount').value);
    formData.append('donated_thing', document.getElementById('donated_thing').value);
    formData.append('date_of_donation', document.getElementById('date_of_donation').value);
    formData.append('organization_name', document.getElementById('organization_name').value);
    formData.append('donor_type', document.getElementById('donor_type').value);

    if (photoFile) {
        formData.append('donorPhoto', photoFile);
    }

    const method = recordId ? 'PUT' : 'POST';
    const url = recordId ? `/api/records/${recordId}` : '/api/records';

    try {
        const response = await fetch(url, {
            method: method,
            body: formData
        });

       if (response.ok) {
    alert(recordId ? "✅ Donor record updated successfully!" : "✅ Donor record saved successfully!");
    resetForm();
    location.reload();
}
 // Reload to fetch fresh data
         else {
            alert('❌ Error saving record. Please try again.');
        }
    } catch (error) {
        alert('❌ Network error. Please check your connection.');
    }
});

async function deleteRecord(id) {
    if (confirm('Are you sure you want to delete this donor record?')) {
        await fetch(`/api/records/${id}`, { method: 'DELETE' });
        location.reload();
    }
}

renderRecords();
</script>
</body>
</html>
"""


@app.route('/')
def index():
    records = Donor.query.order_by(Donor.created_at.desc()).all()
    records_json = []
    for record in records:
        record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}
        records_json.append(record_dict)
    return render_template_string(HTML_TEMPLATE, records=records_json)


@app.route('/api/records', methods=['POST'])
def create_record():
    # Photo upload
    filename = None
    if 'donorPhoto' in request.files and request.files['donorPhoto'].filename:
        file = request.files['donorPhoto']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

    # Validate mandatory fields on server side too
    name = request.form.get('name', '').strip()
    contact = request.form.get('contact_number', '').strip()
    date_of_donation = request.form.get('date_of_donation', '').strip()

    if not name or not contact or not date_of_donation:
        return jsonify({'error': 'Mandatory fields missing'}), 400

    if not re.fullmatch(r'\d{10}', contact):
        return jsonify({'error': 'Contact number must be 10 digits'}), 400

    record = Donor(
        name=name,
        contact_number=contact,
        date_of_donation=date_of_donation,
        donor_photo=filename
    )
    # Optional fields
    for attr in ['age', 'gender', 'address', 'email', 'donation_amount', 'donated_thing', 'organization_name', 'donor_type']:
        value = request.form.get(attr)
        if value:
            if attr == 'age':
                try:
                    record.age = int(value)
                except:
                    pass
            elif attr == 'donation_amount':
                try:
                    record.donation_amount = float(value)
                except:
                    pass
            else:
                setattr(record, attr, value)

    db.session.add(record)
    db.session.commit()
    return jsonify({'message': 'Donor created', 'id': record.id}), 201


@app.route('/api/records/<record_id>', methods=['GET', 'PUT', 'DELETE'])
def record_detail(record_id):
    record = Donor.query.get(record_id)
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    if request.method == 'GET':
        return jsonify({c.name: getattr(record, c.name) for c in record.__table__.columns})

    elif request.method == 'PUT':
        # Handle photo update
        if 'donorPhoto' in request.files and request.files['donorPhoto'].filename:
            file = request.files['donorPhoto']
            if file and allowed_file(file.filename):
                # Delete old photo if exists
                if record.donor_photo:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], record.donor_photo)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                record.donor_photo = filename

        # Update other fields
        name = request.form.get('name', '').strip()
        contact = request.form.get('contact_number', '').strip()
        date_of_donation = request.form.get('date_of_donation', '').strip()

        if not name or not contact or not date_of_donation:
            return jsonify({'error': 'Mandatory fields missing'}), 400

        if not re.fullmatch(r'\d{10}', contact):
            return jsonify({'error': 'Contact number must be 10 digits'}), 400

        record.name = name
        record.contact_number = contact
        record.date_of_donation = date_of_donation

        # Optional fields
        for attr in ['age', 'gender', 'address', 'email', 'donation_amount', 'donated_thing', 'organization_name', 'donor_type']:
            value = request.form.get(attr)
            if value:
                if attr == 'age':
                    try:
                        setattr(record, attr, int(value))
                    except:
                        pass
                elif attr == 'donation_amount':
                    try:
                        setattr(record, attr, float(value))
                    except:
                        pass
                else:
                    setattr(record, attr, value)
            else:
                setattr(record, attr, None)

        db.session.commit()
        return jsonify({'message': 'Donor updated'})

    elif request.method == 'DELETE':
        if record.donor_photo:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], record.donor_photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Donor deleted'})


if __name__ == '__main__':
    print("🚀 Donor Management System started successfully")
    app.run(debug=True, port=5003)
