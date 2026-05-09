from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ---------------- CONFIG ----------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'child_records.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/assets'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

db = SQLAlchemy(app)

# ---------------- MODEL ----------------
class ChildRecord(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    childName = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    dob = db.Column(db.String(20))
    admissionDate = db.Column(db.String(20))
    adoptionStatus = db.Column(db.String(20), default='Not Adopted')
    adopterName = db.Column(db.String(100))
    dateOfAdoption = db.Column(db.String(20))
    bloodGroup = db.Column(db.String(10))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    vaccination = db.Column(db.Text)
    medicalHistory = db.Column(db.Text)
    disability = db.Column(db.String(20))
    schoolName = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50))
    activities = db.Column(db.Text)
    childPhoto = db.Column(db.String(500))
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

with app.app_context():
    db.create_all()

# ---------------- HELPERS ----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ---------------- ROUTES ----------------
@app.route('/assets/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------------- HTML ----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Child Information Management System</title>
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
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, var(--primary-color), #0056b3); color: white; padding: 25px; border-radius: 20px; text-align: center; box-shadow: var(--shadow); }
        .stat-number { font-size: 2.5rem; font-weight: bold; }
        .btn-group { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
        @media (max-width: 768px) { .form-grid, .records-grid { grid-template-columns: 1fr; } .header { flex-direction: column; gap: 20px; text-align: center; } .container { padding: 10px; } .search-panel { flex-direction: column; align-items: stretch; } .search-input { max-width: none; } }
        .empty-state { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">👶 ChildInfo </div>
            <div><button class="theme-toggle" id="themeToggle">☀️</button></div>
        </div>

        <div id="recordsPage" class="page active">
            <div class="stats">
                <div class="stat-card"><div class="stat-number" id="totalRecords">0</div><div>Total Records</div></div>
                <div class="stat-card"><div class="stat-number" id="adoptedCount">0</div><div>Adopted Children</div></div>
            </div>
            <div class="search-panel">
                <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search by name, school, or grade...">
                <button class="btn btn-primary" onclick="performSearch()">🔍 Search</button>
                <button class="btn btn-secondary" onclick="resetSearch()">📄 All Records</button>
            </div>
            <div style="display: flex; gap: 15px; margin-bottom: 30px;">
                <a href="#formPage" class="btn btn-primary" onclick="showPage('formPage'); resetForm();">➕ Add New Child</a>
                <button class="btn btn-secondary" onclick="exportData()">📥 Export Data</button>
            </div>
            <div class="records-grid" id="recordsGrid">
                <div class="empty-state" id="emptyState"><div style="font-size: 4rem;">👶</div><h2>No records yet</h2><p>Click "Add New Child" to get started</p></div>
            </div>
        </div>

        <div id="formPage" class="page">
            <a href="#recordsPage" class="btn btn-secondary" onclick="showPage('recordsPage')" style="margin-bottom: 30px; display: inline-flex;">← Back to Records</a>
            <div class="form-container">
                <h1 style="text-align: center; margin-bottom: 40px; color: var(--primary-color);"><span id="formTitle">Add New Child Record</span></h1>
                <form id="childForm">
                    <input type="hidden" id="recordId">
                    <input type="hidden" id="existingPhoto">
                    <div class="form-grid">
                        <div>
                            <div class="form-group"><label>Child Name <span class="required">*</span></label><input type="text" id="childName" required></div>
                            <div class="form-group"><label>Age <span class="required">*</span></label><input type="number" id="age" min="0" max="18" required></div>
                            <div class="form-group"><label>Gender <span class="required">*</span></label><select id="gender" required><option value="">Select Gender</option><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option></select></div>
                            <div class="form-group"><label>Date of Birth <span class="required">*</span></label><input type="date" id="dob" required></div>
                        </div>
                        <div>
                            <div class="form-group">
                                <label>Child Photo</label>
                                <div class="file-upload"><input type="file" id="childPhoto" accept="image/*"><label for="childPhoto" class="btn btn-primary">📷 Upload Photo</label></div>
                                <img id="photoPreview" class="photo-preview" style="display: none;">
                            </div>
                            <div class="form-group"><label>Date of Admission <span class="required">*</span></label><input type="date" id="admissionDate" required></div>
                            <div class="form-group"><label>Adoption Status <span class="required">*</span></label><select id="adoptionStatus" required><option value="">Select Status</option><option value="Adopted">Adopted</option><option value="Not Adopted">Not Adopted</option></select></div>
                            <div class="form-group"><label>Adopter Name</label><input type="text" id="adopterName"></div>
                            <div class="form-group"><label>Date of Adoption</label><input type="date" id="dateOfAdoption"></div>
                        </div>
                        <h3 style="grid-column: 1 / -1; text-align: center; margin: 30px 0 20px 0; color: var(--primary-color);">🏥 Health Information</h3>
                        <div>
                            <div class="form-group"><label>Blood Group</label><select id="bloodGroup"><option value="">Select Blood Group</option><option value="A+">A+</option><option value="A-">A-</option><option value="B+">B+</option><option value="B-">B-</option><option value="AB+">AB+</option><option value="AB-">AB-</option><option value="O+">O+</option><option value="O-">O-</option></select></div>
                            <div class="form-group"><label>Height (cm) <span class="required">*</span> </label><input type="number" id="height"  step="0.1" required></div>
                            <div class="form-group"><label>Weight (kg) <span class="required">*</span> </label><input type="number" id="weight" min="1" max="100" step="0.1" required></div>
                        </div>
                        <div>
                            <div class="form-group"><label>Disability</label><select id="disability"><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select></div>
                            <div class="form-group full-width"><label>Vaccination Details</label><textarea id="vaccination" placeholder="List all vaccinations..."></textarea></div>
                            <div class="form-group full-width"><label>Medical History</label><textarea id="medicalHistory" placeholder="Any medical conditions or history..."></textarea></div>
                        </div>
                        <h3 style="grid-column: 1 / -1; text-align: center; margin: 30px 0 20px 0; color: var(--primary-color);">🎓 Educational Information</h3>
                        <div class="form-group"><label>School Name <span class="required">*</span></label><input type="text" id="schoolName" required></div>
                        <div class="form-group"><label>Grade</label><input type="text" id="grade" placeholder="e.g., Grade 5, KG2, etc."></div>
                        <div class="form-group full-width"><label>Extracurricular Activities</label><textarea id="activities" placeholder="Sports, music, dance, etc..."></textarea></div>
                    </div>
                    <div style="text-align: center; margin-top: 40px;">
                        <button type="submit" class="btn btn-success" style="font-size: 1.2rem; padding: 18px 50px;">💾 Save Child Record</button>
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
        (record.childName && record.childName.toLowerCase().includes(query)) ||
        (record.schoolName && record.schoolName.toLowerCase().includes(query)) ||
        (record.grade && record.grade.toLowerCase().includes(query))
    );
    renderRecords();
}

function renderRecords() {
    const grid = document.getElementById('recordsGrid');
    const emptyState = document.getElementById('emptyState');
    if (filteredRecords.length === 0) {
        grid.innerHTML = emptyState.outerHTML;
        updateStats(0, 0);
        return;
    }
    grid.innerHTML = filteredRecords.map(record => `
        <div class="record-card">
            <div class="record-name">${record.childName}</div>
            ${record.childPhoto ? `<img src="/assets/${record.childPhoto}" style="width:60px;height:60px;border-radius:10px;object-fit:cover;float:right;" onerror="this.style.display='none'">` : ''}
            <div class="record-detail"><strong>Age:</strong> ${record.age || 'N/A'} years</div>
            <div class="record-detail"><strong>Gender:</strong> ${record.gender || 'N/A'}</div>
            <div class="record-detail"><strong>DOB:</strong> ${record.dob ? new Date(record.dob).toLocaleDateString() : 'N/A'}</div>
            <div class="record-detail"><strong>Status:</strong> <span style="color: ${record.adoptionStatus === 'Adopted' ? '#28a745' : '#ffc107'}">${record.adoptionStatus}</span></div>
            <div class="record-detail"><strong>School:</strong> ${record.schoolName || 'N/A'}</div>
            <div class="record-detail"><strong>Grade:</strong> ${record.grade || 'N/A'}</div>
            <div class="btn-group">
                <button class="btn btn-info" onclick="viewRecord('${record.id}')">👁️ View</button>
                <button class="btn btn-primary" onclick="editRecord('${record.id}')">✏️ Edit</button>
                <button class="btn btn-danger" onclick="deleteRecord('${record.id}')">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
    updateStats(filteredRecords.length, filteredRecords.filter(r => r.adoptionStatus === 'Adopted').length);
}

function updateStats(total, adopted) {
    document.getElementById('totalRecords').textContent = total;
    document.getElementById('adoptedCount').textContent = adopted;
}

document.getElementById('searchInput').addEventListener('keypress', (e) => { if (e.key === 'Enter') performSearch(); });
function resetSearch() { document.getElementById('searchInput').value = ''; filteredRecords = [...records]; renderRecords(); }

function resetForm() {
    editingRecordId = null;
    document.getElementById('formTitle').textContent = 'Add New Child Record';
    document.getElementById('recordId').value = '';
    document.getElementById('existingPhoto').value = '';
    document.getElementById('childForm').reset();
    document.getElementById('photoPreview').style.display = 'none';
    document.getElementById('cancelEditBtn').style.display = 'none';
    document.querySelector("#childForm button[type='submit']").style.display = 'inline-block';
}

function populateForm(record, readOnly = false) {
    document.getElementById('recordId').value = record.id;
    document.getElementById('existingPhoto').value = record.childPhoto || '';
    document.getElementById('childName').value = record.childName || '';
    document.getElementById('age').value = record.age || '';
    document.getElementById('gender').value = record.gender || '';
    document.getElementById('dob').value = record.dob || '';
    document.getElementById('admissionDate').value = record.admissionDate || '';
    document.getElementById('adoptionStatus').value = record.adoptionStatus || '';
    document.getElementById('adopterName').value = record.adopterName || '';
    document.getElementById('dateOfAdoption').value = record.dateOfAdoption || '';
    document.getElementById('bloodGroup').value = record.bloodGroup || '';
    document.getElementById('height').value = record.height || '';
    document.getElementById('weight').value = record.weight || '';
    document.getElementById('vaccination').value = record.vaccination || '';
    document.getElementById('medicalHistory').value = record.medicalHistory || '';
    document.getElementById('disability').value = record.disability || '';
    document.getElementById('schoolName').value = record.schoolName || '';
    document.getElementById('grade').value = record.grade || '';
    document.getElementById('activities').value = record.activities || '';

    if (record.childPhoto) {
        document.getElementById('photoPreview').src = `/assets/${record.childPhoto}`;
        document.getElementById('photoPreview').style.display = 'block';
    }

    const inputs = Array.from(document.querySelectorAll("#childForm input:not([type=hidden]), #childForm select, #childForm textarea"));
    inputs.forEach(input => input.disabled = readOnly);

    document.getElementById('cancelEditBtn').style.display = 'inline-block';
    if (readOnly) {
        document.getElementById('formTitle').textContent = 'View Child Record';
        document.querySelector("#childForm button[type='submit']").style.display = 'none';
    } else {
        document.getElementById('formTitle').textContent = 'Edit Child Record';
        document.querySelector("#childForm button[type='submit']").style.display = 'inline-block';
    }
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
document.getElementById('childPhoto').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('photoPreview').src = e.target.result;
            document.getElementById('photoPreview').style.display = 'block';
            document.getElementById('existingPhoto').value = ''; // Clear existing photo when new uploaded
        };
        reader.readAsDataURL(file);
    }
});

// Form submission with proper photo upload
document.getElementById('childForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const recordId = document.getElementById('recordId').value;
    const existingPhoto = document.getElementById('existingPhoto').value;
    const photoFile = document.getElementById('childPhoto').files[0];

    const formData = new FormData();
    formData.append('recordId', recordId);
    formData.append('existingPhoto', existingPhoto);
    formData.append('childName', document.getElementById('childName').value);
    formData.append('age', document.getElementById('age').value);
    formData.append('gender', document.getElementById('gender').value);
    formData.append('dob', document.getElementById('dob').value);
    formData.append('admissionDate', document.getElementById('admissionDate').value);
    formData.append('adoptionStatus', document.getElementById('adoptionStatus').value);
    formData.append('adopterName', document.getElementById('adopterName').value);
    formData.append('dateOfAdoption', document.getElementById('dateOfAdoption').value);
    formData.append('bloodGroup', document.getElementById('bloodGroup').value);
    formData.append('height', document.getElementById('height').value);
    formData.append('weight', document.getElementById('weight').value);
    formData.append('vaccination', document.getElementById('vaccination').value);
    formData.append('medicalHistory', document.getElementById('medicalHistory').value);
    formData.append('disability', document.getElementById('disability').value);
    formData.append('schoolName', document.getElementById('schoolName').value);
    formData.append('grade', document.getElementById('grade').value);
    formData.append('activities', document.getElementById('activities').value);

    if (photoFile) {
        formData.append('childPhoto', photoFile);
    }

    const method = recordId ? 'PUT' : 'POST';
    const url = recordId ? `/api/records/${recordId}` : '/api/records';

    try {
        const response = await fetch(url, {
            method: method,
            body: formData
        });

        if (response.ok) {
            alert(recordId
                ? "✅ Child record updated successfully!"
                : "✅ Child record saved successfully!"
            );
            resetForm();
            location.reload();
        } else {
            alert('❌ Error saving record. Please try again.');
        }
    } catch (error) {
        alert('❌ Network error. Please check your connection.');
    }
});

async function deleteRecord(id) {
    if (confirm('Are you sure you want to delete this record?')) {
        await fetch(`/api/records/${id}`, { method: 'DELETE' });
        location.reload();
    }
}

function exportData() {
    const dataStr = JSON.stringify(records, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'child_records.json';
    link.click();
}

renderRecords();
</script>
</body>
</html>
"""

# ---------------- PAGES ----------------
@app.route('/')
def index():
    records = ChildRecord.query.all()
    records_json = [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]
    return render_template_string(HTML_TEMPLATE, records=records_json)

# ---------------- API ----------------
@app.route('/api/records', methods=['POST'])
def create_record():
    record = ChildRecord()

    # PHOTO UPLOAD
    if 'childPhoto' in request.files and request.files['childPhoto'].filename:
        file = request.files['childPhoto']
        if allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            record.childPhoto = filename

    # FORM DATA
    for key, value in request.form.items():
        if hasattr(record, key) and key not in ['id', 'childPhoto', 'existingPhoto']:
            setattr(record, key, value)

    db.session.add(record)
    db.session.commit()
    return jsonify({'message': 'Record created', 'id': record.id}), 201

@app.route('/api/records/<record_id>', methods=['GET', 'PUT', 'DELETE'])
def record_detail(record_id):
    record = ChildRecord.query.get_or_404(record_id)

    if request.method == 'GET':
        return jsonify({c.name: getattr(record, c.name) for c in record.__table__.columns})

    if request.method == 'PUT':

        # NEW PHOTO
        if 'childPhoto' in request.files and request.files['childPhoto'].filename:
            file = request.files['childPhoto']
            if allowed_file(file.filename):

                if record.childPhoto:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], record.childPhoto)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                record.childPhoto = filename

        # UPDATE FIELDS
        for key, value in request.form.items():
            if hasattr(record, key) and key not in ['id', 'childPhoto', 'existingPhoto']:
                setattr(record, key, value)

        db.session.commit()
        return jsonify({'message': 'Record updated'})

    if request.method == 'DELETE':
        if record.childPhoto:
            path = os.path.join(app.config['UPLOAD_FOLDER'], record.childPhoto)
            if os.path.exists(path):
                os.remove(path)

        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Record deleted'})

# ---------------- RUN ----------------
if __name__ == '__main__':
    print("🚀 Child Module started successfully")
    app.run(debug=True, port=5001)
