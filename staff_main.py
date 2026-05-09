from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///staff_records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class StaffRecord(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.Text, nullable=False)
    dob = db.Column(db.String(20))
    doj = db.Column(db.String(20), nullable=False)  # Date of joining
    salary = db.Column(db.Float)
    post = db.Column(db.String(100))
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

with app.app_context():
    db.create_all()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Staff Information Management System</title>
<style>
    :root {
        --bg-primary: #fff; --bg-secondary: #f8f9fa; --text-primary: #212529;
        --text-secondary: #6c757d; --primary-color: #007bff; --success-color: #28a745;
        --danger-color: #dc3545; --border-color: #dee2e6; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
    }
    [data-theme="dark"] {
        --bg-primary: #1a1a1a; --bg-secondary: #2d2d2d; --text-primary: #fff;
        --text-secondary: #adb5bd; --primary-color: #4dabf7; --success-color: #51cf66;
        --danger-color: #ff6b6b; --border-color: #444; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.5);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;background: var(--bg-primary);color: var(--text-primary); line-height: 1.6;transition: all 0.3s ease;}
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .header {display: flex; justify-content: space-between;align-items: center;margin-bottom: 30px;padding: 20px;background: var(--bg-secondary);border-radius: 15px; box-shadow: var(--shadow);}
    .logo {font-size: 2rem;font-weight: bold;background: linear-gradient(45deg, var(--primary-color), #6610f2); -webkit-background-clip: text;-webkit-text-fill-color: transparent;background-clip: text; }
    .theme-toggle {background: none;border: 2px solid var(--primary-color); width: 50px;height: 50px;border-radius: 50%;cursor: pointer;display: flex;align-items: center;justify-content: center;font-size: 1.5rem; transition: all 0.3s ease;}
    .theme-toggle:hover {transform: scale(1.1);box-shadow: 0 0 20px var(--primary-color); }
    .btn {padding: 12px 24px; border: none;border-radius: 25px;cursor: pointer;font-size: 1rem;font-weight: 600; text-decoration: none; display: inline-flex; align-items: center;gap: 8px;transition: all 0.3s ease;box-shadow: var(--shadow);}
    .btn-primary { background: var(--primary-color); color: white; }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,123,255,0.4); }
    .btn-success { background: var(--success-color); color: white; }
    .btn-danger { background: var(--danger-color); color: white; }
    .btn-secondary { background: var(--text-secondary); color: white; }
    .btn-info { background: #17a2b8; color: white; }
    .page { display: none; animation: fadeIn 0.5s ease-in; }
    .page.active { display: block; }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .search-panel { background: var(--bg-secondary);padding: 20px;border-radius: 15px; margin-bottom: 30px; box-shadow: var(--shadow);display: flex;gap: 15px;align-items: center;flex-wrap: wrap;}
    .search-input {flex: 1;max-width: 400px;padding: 12px 20px; border: 2px solid var(--border-color);border-radius: 25px;font-size: 1rem;transition: all 0.3s ease;}
    .search-input:focus {outline: none; border-color: var(--primary-color);box-shadow: 0 0 0 3px rgba(0,123,255,0.1);}
    .records-grid {display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));gap: 20px; margin-bottom: 30px;}
    .record-card {background: var(--bg-secondary); padding: 25px;border-radius: 20px;box-shadow: var(--shadow); transition: all 0.3s ease;border-left: 5px solid var(--primary-color);position: relative; }
    .record-card:hover {transform: translateY(-5px);box-shadow: 0 15px 40px rgba(0,0,0,0.2); }
    .record-name { font-size: 1.5rem; font-weight: bold;margin-bottom: 10px; color: var(--primary-color);}
    .record-detail { margin: 8px 0; }
    .form-container { background: var(--bg-secondary); padding: 40px;border-radius: 25px;box-shadow: var(--shadow);max-width: 1000px; margin: 0 auto;}
    .form-grid { display: grid;grid-template-columns: 1fr 1fr;gap: 30px; }
    .form-group {margin-bottom: 25px;}
    .form-group.full-width { grid-column: 1 / -1; }
    label {display: block; margin-bottom: 8px;font-weight: 600;color: var(--text-primary); }
    .required { color: var(--danger-color); }
    input, select, textarea { width: 100%;padding: 15px; border: 2px solid var(--border-color); border-radius: 12px;font-size: 1rem; transition: all 0.3s ease;background: var(--bg-primary);color: var(--text-primary);}
    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
    }
    textarea { resize: vertical; min-height: 100px; }
    .btn-group { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
    @media (max-width: 768px) {
        .form-grid, .records-grid {
            grid-template-columns: 1fr;
        }
        .header {
            flex-direction: column;
            gap: 20px;
            text-align: center;
        }
        .container { padding: 10px; }
        .search-panel { flex-direction: column; align-items: stretch; }
        .search-input { max-width: none; }
    }
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: var(--text-secondary);
    }
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo">👔 StaffInfo</div>
        <div><button class="theme-toggle" id="themeToggle">☀️</button></div>
    </div>

    <div id="recordsPage" class="page active">
        <div class="search-panel">
            <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search by name, mobile, email, post...">
            <button class="btn btn-primary" onclick="performSearch()">🔍 Search</button>
            <button class="btn btn-secondary" onclick="resetSearch()">📄 All Records</button>
        </div>
        <div style="display: flex; gap: 15px; margin-bottom: 30px;">
            <button class="btn btn-primary" onclick="showPage('formPage'); resetForm();">➕ Add New Staff</button>
        </div>
        <div class="records-grid" id="recordsGrid">
            <div class="empty-state" id="emptyState"><div style="font-size: 4rem;">👔</div><h2>No records yet</h2><p>Click "Add New Staff" to get started</p></div>
        </div>
    </div>

    <div id="formPage" class="page">
        <button class="btn btn-secondary" onclick="showPage('recordsPage')" style="margin-bottom: 30px;">← Back to Records</button>
        <div class="form-container">
            <h1 style="text-align: center; margin-bottom: 40px; color: var(--primary-color);" id="formTitle">Add New Staff Record</h1>
            <form id="staffForm" novalidate>
                <input type="hidden" id="recordId" />
                <div class="form-grid">
                    <div>
                        <div class="form-group">
                            <label>Name <span class="required">*</span></label>
                            <input type="text" id="name" required />
                        </div>
                        <div class="form-group">
                            <label>Age</label>
                            <input type="number" id="age" min="18" max="100" />
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
                            <label>Mobile Number <span class="required">*</span></label>
                            <input type="tel" id="mobile" required pattern="\\d{7,15}" placeholder="Digits only" />
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="email" placeholder="example@domain.com"/>
                        </div>
                        <div class="form-group">
                            <label>Address <span class="required">*</span></label>
                            <textarea id="address" required></textarea>
                        </div>
                    </div>
                    <div>
                        <div class="form-group">
                            <label>Date of Birth</label>
                            <input type="date" id="dob" max="{{today}}" />
                        </div>
                        <div class="form-group">
                            <label>Date of Joining <span class="required">*</span></label>
                            <input type="date" id="doj" required max="{{today}}" />
                        </div>
                        <div class="form-group">
                            <label>Salary</label>
                            <input type="number" id="salary" min="0" step="0.01" />
                        </div>
                        <div class="form-group">
                            <label>Post</label>
                            <input type="text" id="post" />
                        </div>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 40px;">
                    <button type="submit" class="btn btn-success" style="font-size: 1.2rem; padding: 18px 50px;">💾 Save Staff Record</button>
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
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    if (pageId === 'recordsPage') renderRecords();
}

function performSearch() {
    const q = document.getElementById('searchInput').value.trim().toLowerCase();
    filteredRecords = records.filter(rec =>
        (rec.name && rec.name.toLowerCase().includes(q)) ||
        (rec.mobile && rec.mobile.toLowerCase().includes(q)) ||
        (rec.email && rec.email.toLowerCase().includes(q)) ||
        (rec.post && rec.post.toLowerCase().includes(q))
    );
    renderRecords();
}

function resetSearch() {
    document.getElementById('searchInput').value = '';
    filteredRecords = [...records];
    renderRecords();
}

function renderRecords() {
    const grid = document.getElementById('recordsGrid');
    const emptyState = document.getElementById('emptyState');
    if (filteredRecords.length === 0) {
        grid.innerHTML = emptyState.outerHTML;
        return;
    }
    grid.innerHTML = filteredRecords.map(r => `
        <div class="record-card">
            <div class="record-name">${r.name}</div>
            <div class="record-detail"><strong>Mobile:</strong> ${r.mobile}</div>
            <div class="record-detail"><strong>Email:</strong> ${r.email || 'N/A'}</div>
            <div class="record-detail"><strong>Post:</strong> ${r.post || 'N/A'}</div>
            <div class="record-detail"><strong>DOJ:</strong> ${r.doj ? new Date(r.doj).toLocaleDateString() : 'N/A'}</div>
            <div class="btn-group">
                <button class="btn btn-info" onclick="viewRecord('${r.id}')">👁️ View</button>
                <button class="btn btn-primary" onclick="editRecord('${r.id}')">✏️ Edit</button>
                <button class="btn btn-danger" onclick="deleteRecord('${r.id}')">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

function resetForm() {
    editingRecordId = null;
    document.getElementById('formTitle').textContent = 'Add New Staff Record';
    document.getElementById('recordId').value = '';
    document.getElementById('staffForm').reset();
    document.getElementById('cancelEditBtn').style.display = 'none';
}

function populateForm(record, readOnly = false) {
    editingRecordId = record.id;
    document.getElementById('recordId').value = record.id;
    document.getElementById('name').value = record.name || '';
    document.getElementById('age').value = record.age || '';
    document.getElementById('gender').value = record.gender || '';
    document.getElementById('mobile').value = record.mobile || '';
    document.getElementById('email').value = record.email || '';
    document.getElementById('address').value = record.address || '';
    document.getElementById('dob').value = record.dob || '';
    document.getElementById('doj').value = record.doj || '';
    document.getElementById('salary').value = record.salary || '';
    document.getElementById('post').value = record.post || '';

    const inputs = Array.from(document.querySelectorAll("#staffForm input, #staffForm select, #staffForm textarea"));
    inputs.forEach(i => i.disabled = readOnly);

    document.getElementById('cancelEditBtn').style.display = readOnly ? 'inline-block' : 'inline-block';
    if (readOnly) {
        document.getElementById('formTitle').textContent = 'View Staff Record';
        document.querySelector("#staffForm button[type='submit']").style.display = 'none';
    } else {
        document.getElementById('formTitle').textContent = 'Edit Staff Record';
        document.querySelector("#staffForm button[type='submit']").style.display = 'inline-block';
    }
}

function viewRecord(id) {
    const rec = records.find(r => r.id === id);
    if (!rec) return alert("Record not found");
    populateForm(rec, true);
    showPage('formPage');
}
function editRecord(id) {
    const rec = records.find(r => r.id === id);
    if (!rec) return alert("Record not found");
    populateForm(rec, false);
    showPage('formPage');
}

document.getElementById('cancelEditBtn').addEventListener('click', () => {
    resetForm();
    showPage('recordsPage');
});

document.getElementById('staffForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Validation manual for required fields and email "@" presence
    const name = document.getElementById('name').value.trim();
    const mobile = document.getElementById('mobile').value.trim();
    const address = document.getElementById('address').value.trim();
    const doj = document.getElementById('doj').value.trim();
    const email = document.getElementById('email').value.trim();
    if(!name) return alert("Name is mandatory");
    if(!mobile) return alert("Mobile number is mandatory");
    if(!address) return alert("Address is mandatory");
    if(!doj) return alert("Date of Joining is mandatory");
    if(email && !email.includes('@')) return alert("Please enter a valid email including '@'");

    const recordId = document.getElementById('recordId').value;

    const payload = {
        name,
        age: document.getElementById('age').value || null,
        gender: document.getElementById('gender').value || null,
        mobile,
        email: email || null,
        address,
        dob: document.getElementById('dob').value || null,
        doj,
        salary: document.getElementById('salary').value || null,
        post: document.getElementById('post').value || null,
    };

    const method = recordId ? 'PUT' : 'POST';
    const url = recordId ? `/api/staff/${recordId}` : '/api/staff';

    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
           alert(recordId ? "✅ Staff record updated successfully!" : "✅ Staff record saved successfully!");

            resetForm();
            location.reload();
        } else {
            const data = await res.json();
            alert('❌ ' + (data.error || 'Failed to save record'));
        }
    } catch {
        alert('❌ Network error');
    }
});

async function deleteRecord(id) {
    if (confirm('Are you sure to delete this record?')) {
        const res = await fetch(`/api/staff/${id}`, { method: 'DELETE' });
        if (res.ok) location.reload();
        else alert('❌ Failed to delete record');
    }
}

renderRecords();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    records = StaffRecord.query.order_by(StaffRecord.createdAt.desc()).all()
    records_json = [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]
    return render_template_string(HTML_TEMPLATE, records=records_json, today=datetime.today().strftime('%Y-%m-%d'))

@app.route('/api/staff', methods=['POST'])
def create_staff():
    data = request.get_json(force=True)
    if not data.get('name') or not data.get('mobile') or not data.get('address') or not data.get('doj'):
        return jsonify({"error": "Missing mandatory fields"}), 400
    if data.get('email') and '@' not in data['email']:
        return jsonify({"error": "Email must contain '@'"}), 400

    record = StaffRecord(
        name=data['name'],
        age=int(data['age']) if data.get('age') else None,
        gender=data.get('gender'),
        mobile=data['mobile'],
        email=data.get('email'),
        address=data['address'],
        dob=data.get('dob'),
        doj=data['doj'],
        salary=float(data['salary']) if data.get('salary') else None,
        post=data.get('post')
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "Staff record created", "id": record.id}), 201

@app.route('/api/staff/<record_id>', methods=['GET', 'PUT', 'DELETE'])
def staff_detail(record_id):
    record = StaffRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    if request.method == 'GET':
        return jsonify({c.name: getattr(record, c.name) for c in record.__table__.columns})

    if request.method == 'PUT':
        data = request.get_json(force=True)
        if not data.get('name') or not data.get('mobile') or not data.get('address') or not data.get('doj'):
            return jsonify({"error": "Missing mandatory fields"}), 400
        if data.get('email') and '@' not in data['email']:
            return jsonify({"error": "Email must contain '@'"}), 400

        record.name = data['name']
        record.age = int(data['age']) if data.get('age') else None
        record.gender = data.get('gender')
        record.mobile = data['mobile']
        record.email = data.get('email')
        record.address = data['address']
        record.dob = data.get('dob')
        record.doj = data['doj']
        record.salary = float(data['salary']) if data.get('salary') else None
        record.post = data.get('post')
        db.session.commit()
        return jsonify({"message": "Record updated"})

    if request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        return jsonify({"message": "Record deleted"})

if __name__ == '__main__':
    print("🚀 Staff Information Management System started successfully")
    app.run(debug=True, host='127.0.0.1', port=5004)

