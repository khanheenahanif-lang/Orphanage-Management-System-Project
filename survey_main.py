# survey_app.py
from flask import Flask, render_template_string, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# FIXED: Database config with absolute path
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'survey_records.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# COMPLETE Survey Record Model
class SurveyRecord(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    survey_date = db.Column(db.String(20), default=datetime.utcnow().strftime('%Y-%m-%d'))
    respondent_type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    cleanliness_rooms = db.Column(db.Integer)
    cleanliness_toilets = db.Column(db.Integer)
    food_quality = db.Column(db.Integer)
    medical_support = db.Column(db.Integer)
    study_environment = db.Column(db.Integer)
    play_facilities = db.Column(db.Integer)
    clothes_availability = db.Column(db.Integer)
    safety_security = db.Column(db.Integer)
    staff_friendliness = db.Column(db.Integer)
    staff_supportiveness = db.Column(db.Integer)
    staff_professionalism = db.Column(db.Integer)
    responsiveness = db.Column(db.Integer)
    adoption_ease = db.Column(db.Integer)
    adoption_transparency = db.Column(db.Integer)
    adoption_communication = db.Column(db.Integer)
    legal_support = db.Column(db.Integer)
    adoption_satisfaction = db.Column(db.Integer)
    donation_convenience = db.Column(db.Integer)
    donation_transparency = db.Column(db.Integer)
    donation_updates = db.Column(db.Integer)
    donor_staff_behaviour = db.Column(db.Integer)
    donor_satisfaction = db.Column(db.Integer)
    donate_again = db.Column(db.String(10))
    suggestions = db.Column(db.Text)
    problems = db.Column(db.Text)
    happy_about = db.Column(db.Text)
    comments = db.Column(db.Text)
    feel_safe = db.Column(db.String(10))
    feel_happy = db.Column(db.String(10))
    has_friends = db.Column(db.String(10))
    overall_rating = db.Column(db.Integer)
    recommend = db.Column(db.String(10))
    review_status = db.Column(db.String(20), default='Pending')
    staff_reviewer = db.Column(db.String(100))
    follow_up_required = db.Column(db.String(10), default='No')
    follow_up_notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables BEFORE first request
def init_db():
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")


init_db()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Smart Survey Management Pro</title>
    <style>
        /* Original polished theme variables & layout retained */
        :root {
            --bg-primary: #ffffff; --bg-secondary: #f8f9fa; --text-primary: #212529;
            --text-secondary: #6c757d; --primary-color: #007bff; --success-color: #28a745;
            --danger-color: #dc3545; --border-color: #dee2e6; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
            --card-radius: 15px;
            --control-radius: 12px;
            --font-sans: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            
        }
        [data-theme="dark"] {
            --bg-primary: #1a1a1a; --bg-secondary: #2d2d2d; --text-primary: #ffffff;
            --text-secondary: #adb5bd; --primary-color: #4dabf7; --success-color: #51cf66;
            --danger-color: #ff6b6b; --border-color: #444444; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.5);
            
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html,body { height: 100%; }
        body { font-family: var(--font-sans); background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; transition: all 0.3s ease; -webkit-font-smoothing:antialiased; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding: 20px; background: var(--bg-secondary); border-radius: var(--card-radius); box-shadow: var(--shadow); }
        .logo { font-size: 2rem; font-weight: bold; background: linear-gradient(45deg, var(--primary-color), #6610f2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .theme-toggle { background: none; border: 2px solid var(--primary-color); width: 50px; height: 50px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; transition: all 0.3s ease; }
        .theme-toggle:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(0,123,255,0.12); }
        .btn { padding: 12px 24px; border: none; border-radius: 25px; cursor: pointer; font-size: 1rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: all 0.25s ease; box-shadow: var(--shadow); margin: 5px; background: var(--primary-color); /* primary blue */
         color: #fff; }
        .btn-primary { background: var(--primary-color); color: white; } .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,123,255,0.18); }
        .btn-success { background: var(--success-color); color: white; } .btn-danger { background: var(--danger-color); color: white; }
        .btn-secondary { background: var(--text-secondary); color: white; } .btn-info { background: #17a2b8; color: white; }
        .btn.active-tab { background: var(--success-color) !important; box-shadow: none; }
        .page { display: none; animation: fadeIn 0.45s ease-in; } .page.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .search-panel { background: var(--bg-secondary); padding: 18px; border-radius: var(--card-radius); margin-bottom: 24px; box-shadow: var(--shadow); display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .search-input { flex: 1; max-width: 420px; padding: 12px 20px; border: 2px solid var(--border-color); border-radius: 25px; font-size: 1rem; transition: all 0.25s ease; background: var(--bg-primary); color: var(--text-primary); }
        .search-input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 4px rgba(0,123,255,0.06); }
        .records-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .record-card { background: var(--bg-secondary); padding: 22px; border-radius: 20px; box-shadow: var(--shadow); transition: all 0.25s ease; border-left: 5px solid var(--primary-color); }
        .record-card:hover { transform: translateY(-6px); box-shadow: 0 18px 45px rgba(0,0,0,0.14); }
        .record-name { font-size: 1.25rem; font-weight: 700; margin-bottom: 8px; color: var(--primary-color); }
        .record-detail { margin: 6px 0; font-size: 0.95rem; color: var(--text-primary); }
        .tab-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 26px; background: var(--bg-secondary); padding: 18px; border-radius: var(--card-radius); box-shadow: var(--shadow); }
        .form-container { background: var(--bg-secondary); padding: 36px; border-radius: 25px; box-shadow: var(--shadow); max-width: 1400px; margin: 0 auto; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
        .form-section { display: none; margin-bottom: 20px; padding: 18px; background: rgba(255,255,255,0.03); border-radius: 15px; border-left: 5px solid var(--primary-color); }
        .form-section.active { display: block; }
        .form-group { margin-bottom: 20px; } .form-group.full-width { grid-column: 1 / -1; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-primary); }
        .required { color: var(--danger-color); }
        input, select, textarea { width: 100%; padding: 14px; border: 2px solid var(--border-color); border-radius: var(--control-radius); font-size: 1rem; transition: all 0.25s ease; background: var(--bg-primary); color: var(--text-primary); }
        input:focus, select:focus, textarea:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 6px rgba(0,123,255,0.04); }
        textarea { resize: vertical; min-height: 120px; }
        .rating-group { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
        .rating-stars { display: flex; gap: 8px; align-items: center; user-select: none; }
        .star { font-size: 1.5rem; cursor: pointer; color: #ddd; transition: color 0.15s ease; }
        .star.active { color: #ffd700; }
        .star.preview { color: #ffd980; }
        .section-title { grid-column: 1 / -1; text-align: center; margin: 36px 0 18px 0; color: var(--primary-color); font-size: 1.6rem; }
        .btn-group { margin-top: 12px; display:flex; gap:10px; flex-wrap:wrap; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, var(--primary-color), #0056b3); color: white; padding: 24px; border-radius: 20px; text-align: center; box-shadow: var(--shadow); }
        .stat-number { font-size: 2.5rem; font-weight: 700; }
        @media (max-width: 768px) {
            .form-grid, .records-grid { grid-template-columns: 1fr; }
            .header { flex-direction: column; gap: 18px; align-items: stretch; }
            .container { padding: 12px; }
            .tab-buttons { flex-direction: column; }
        }
        .empty-state { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
        .muted { color: var(--text-secondary); font-size: .95rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">📊  Survey  </div>
            <div><button class="theme-toggle" id="themeToggle">☀️</button></div>
        </div>

        <div id="recordsPage" class="page active">
            <div class="stats">
                <div class="stat-card"><div class="stat-number" id="totalRecords">0</div><div>Total Surveys</div></div>
                <div class="stat-card"><div class="stat-number" id="completedCount">0</div><div>Completed</div></div>
            </div>
            <div class="search-panel">
                <input type="text" class="search-input" id="searchInput" placeholder="🔍 Search by name, respondent type...">
                <button class="btn btn-primary" onclick="performSearch()">🔍 Search</button>
                <button class="btn btn-secondary" onclick="resetSearch()">📄 All Records</button>
            </div>
            <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="showPage('formPage'); resetForm();">➕ Add New Survey</button>
            </div>

            <div class="tab-buttons">
                <button class="btn btn-primary active-tab" data-tab="all">📋 All Surveys</button>
                <button class="btn btn-info" data-tab="Child">👶 Child</button>
                <button class="btn btn-info" data-tab="Staff">👨‍💼 Staff</button>
                <button class="btn btn-info" data-tab="Donor">💰 Donor</button>
                <button class="btn btn-info" data-tab="Adopter">🏠 Adopter</button>
            </div>

            <div class="records-grid" id="recordsGrid">
                <div class="empty-state" id="emptyState">
                    <div style="font-size: 4rem;">📊</div>
                    <h2>No survey records yet</h2>
                    <p class="muted">Click "Add New Survey" to get started</p>
                </div>
            </div>
        </div>

        <div id="formPage" class="page">
            <button class="btn btn-secondary" onclick="showPage('recordsPage')" style="margin-bottom: 30px;">← Back to Records</button>
            <div class="form-container">
                <h1 style="text-align: center; margin-bottom: 28px; color: var(--primary-color);" id="formTitle">Add New Survey Record</h1>
                <form id="surveyForm">
                    <input type="hidden" id="recordId">

                    <div class="form-grid">
                        <div class="section-title">1. Basic Information</div>
                        <div class="form-group">
                            <label>Survey Date</label>
                            <input type="date" id="survey_date">
                        </div>
                        <div class="form-group">
                            <label>Respondent Type <span class="required">*</span></label>
                            <select id="respondent_type" required onchange="showRelevantSections(this.value)">
                                <option value="">Select Type</option>
                                <option value="Child">Child</option>
                                <option value="Staff">Staff</option>
                                <option value="Donor">Donor</option>
                                <option value="Adopter">Adopter</option>
                            </select>
                        </div>
                        <div class="form-group"><label>Name</label><input type="text" id="name"></div>
                        <div class="form-group"><label>Age</label><input type="number" id="age" min="0" max="100"></div>
                        <div class="form-group">
                            <label>Gender</label>
                            <select id="gender">
                                <option value="">Select</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>

                        <!-- LIVING/FACILITY SECTION - Child & Staff -->
                        <div id="livingSection" class="form-section">
                            <h3>🏠 Living/Facility Feedback</h3>
                            <div class="form-group"><label>Cleanliness of Rooms (1-5)</label><div class="rating-group"><div class="rating-stars" data-field="cleanliness_rooms"></div><input type="hidden" id="cleanliness_rooms"></div></div>
                            <div class="form-group"><label>Quality of Food (1-5)</label><div class="rating-group"><div class="rating-stars" data-field="food_quality"></div><input type="hidden" id="food_quality"></div></div>
                            <div class="form-group"><label>Medical Support (1-5)</label><div class="rating-group"><div class="rating-stars" data-field="medical_support"></div><input type="hidden" id="medical_support"></div></div>
                        </div>

                        <!-- STAFF BEHAVIOUR SECTION - Child/Adopter -->
                        <div id="staffSection" class="form-section">
                            <h3>👨‍💼 Staff Behaviour</h3>
                            <div class="form-group"><label>Friendliness (1-5)</label><div class="rating-group"><div class="rating-stars" data-field="staff_friendliness"></div><input type="hidden" id="staff_friendliness"></div></div>
                        </div>

                        <!-- ADOPTER SECTION -->
                        <div id="adopterSection" class="form-section">
                            <h3>🏠 Adoption Process</h3>
                            <div class="form-group"><label>Adoption Ease (1-5)</label><div class="rating-group"><div class="rating-stars" data-field="adoption_ease"></div><input type="hidden" id="adoption_ease"></div></div>
                        </div>

                        <!-- DONOR SECTION -->
                        <div id="donorSection" class="form-section">
                            <h3>💰 Donor Feedback</h3>
                            <div class="form-group"><label>Donation Convenience (1-5)</label><div class="rating-group"><div class="rating-stars" data-field="donation_convenience"></div><input type="hidden" id="donation_convenience"></div></div>
                            <div class="form-group"><label>Donate Again?</label><select id="donate_again"><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select></div>
                        </div>

                        <!-- CHILD EMOTIONAL SECTION -->
                        <div id="childSection" class="form-section">
                            <h3>❤️ Child Emotions</h3>
                            <div class="form-group"><label>Feel Safe?</label><select id="feel_safe"><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select></div>
                            <div class="form-group"><label>Feel Happy?</label><select id="feel_happy"><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select></div>
                        </div>

                        <div class="section-title">Summary</div>
                        <div class="form-group full-width">
                            <label>Overall Rating <span class="required">*</span> (1-5)</label>
                            <div class="rating-group"><div class="rating-stars" data-field="overall_rating"></div><input type="hidden" id="overall_rating" required></div>
                        </div>
                        <div class="form-group full-width">
                            <label>Recommend? <span class="required">*</span></label>
                            <select id="recommend" required>
                                <option value="">Select</option>
                                <option value="Yes">Yes</option>
                                <option value="No">No</option>
                            </select>
                        </div>
                        <div class="form-group full-width">
                            <label>Suggestions/Comments</label>
                            <textarea id="comments" placeholder="Your feedback..."></textarea>
                        </div>

                        <div class="section-title">Admin</div>
                        <div class="form-group"><label>Review Status</label>
                            <select id="review_status">
                                <option value="Pending">Pending</option>
                                <option value="Completed">Completed</option>
                            </select>
                        </div>
                        <div class="form-group"><label>Follow-up Required</label>
                            <select id="follow_up_required">
                                <option value="No">No</option>
                                <option value="Yes">Yes</option>
                            </select>
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 36px;">
                        <button type="submit" class="btn btn-success" style="font-size: 1.2rem; padding: 18px 50px;">💾 Save Survey</button>
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
let currentTab = 'all';

// Theme toggle (persist)
const themeToggle = document.getElementById('themeToggle');
const currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);
themeToggle.textContent = currentTheme === 'light' ? '🌙' : '☀️';
themeToggle.onclick = () => {
    const newTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeToggle.textContent = newTheme === 'light' ? '🌙' : '☀️';
};

function showRelevantSections(type) {
    // Hide all sections
    document.querySelectorAll('.form-section').forEach(section => section.classList.remove('active'));

    if (type === 'Child') {
        document.getElementById('livingSection').classList.add('active');
        document.getElementById('staffSection').classList.add('active');
        document.getElementById('childSection').classList.add('active');
    } else if (type === 'Staff') {
        document.getElementById('livingSection').classList.add('active');
    } else if (type === 'Adopter') {
        document.getElementById('staffSection').classList.add('active');
        document.getElementById('adopterSection').classList.add('active');
    } else if (type === 'Donor') {
        document.getElementById('donorSection').classList.add('active');
    }
}

// Tab functionality
document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.onclick = () => {
        document.querySelectorAll('[data-tab]').forEach(b => b.classList.remove('active-tab'));
        btn.classList.add('active-tab');
        currentTab = btn.dataset.tab;
        performSearch();
    };
});

function filterByTab() {
    let tempRecords = records;
    if (currentTab !== 'all') {
        tempRecords = records.filter(r => (r.respondent_type || '').toLowerCase() === currentTab.toLowerCase());
    }
    const searchQuery = (document.getElementById('searchInput').value || '').toLowerCase().trim();
    if (searchQuery) {
        filteredRecords = tempRecords.filter(record =>
            (record.name || '').toLowerCase().includes(searchQuery) ||
            (record.respondent_type || '').toLowerCase().includes(searchQuery)
        );
    } else {
        filteredRecords = tempRecords;
    }
}

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    if (pageId === 'recordsPage') renderRecords();
}

function performSearch() {
    filterByTab();
    renderRecords();
}

function renderRecords() {
    const grid = document.getElementById('recordsGrid');
    const emptyState = document.getElementById('emptyState');
    if (!filteredRecords || filteredRecords.length === 0) {
        // If no records at all show the "no records" empty state.
        // If there are records globally but the filter produced none, show a blank grid (per your request).
        if (!records || records.length === 0) {
            grid.innerHTML = emptyState.outerHTML;
        } else {
            grid.innerHTML = '';
        }
        updateStats(records.length, records.filter(r => r.review_status === 'Completed').length);
        return;
    }
    grid.innerHTML = filteredRecords.map(record => `
        <div class="record-card">
            <div class="record-name">${record.respondent_type || 'Unknown'} Survey</div>
            <div class="record-detail"><strong>Name:</strong> ${record.name || 'Anonymous'}</div>
            <div class="record-detail"><strong>Date:</strong> ${record.survey_date || 'N/A'}</div>
            <div class="record-detail"><strong>Status:</strong> <span style="color: ${record.review_status === 'Completed' ? '#28a745' : '#ffc107'}">${record.review_status}</span></div>
            <div class="record-detail"><strong>Overall:</strong> ${record.overall_rating || 'N/A'}/5</div>
            <div class="btn-group">
                <button class="btn btn-info" onclick="viewRecord('${record.id}')">👁️ View</button>
                <button class="btn btn-primary" onclick="editRecord('${record.id}')">✏️ Edit</button>
                <button class="btn btn-danger" onclick="deleteRecord('${record.id}')">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
    updateStats(records.length, records.filter(r => r.review_status === 'Completed').length);
}

function updateStats(total, completed) {
    document.getElementById('totalRecords').textContent = total;
    document.getElementById('completedCount').textContent = completed;
}

// Star rating: create stars using character that respects CSS color (★). Add preview on hover and set on click.
function makeStarsInteractive(container) {
    const stars = Array.from(container.children);
    stars.forEach((star, idx) => {
        star.onmouseenter = () => {
            stars.forEach((s,i) => s.classList.toggle('preview', i <= idx));
        };
        star.onmouseleave = () => {
            stars.forEach(s => s.classList.remove('preview'));
        };
        star.onclick = () => {
            const rating = idx + 1;
            stars.forEach((s,i) => s.classList.toggle('active', i < rating));
            const field = container.dataset.field;
            const hidden = document.getElementById(field);
            if (hidden) hidden.value = rating;
        };
    });
}

// Initialize ratings and UI
document.addEventListener('DOMContentLoaded', () => {
    // Build stars in every rating container
    document.querySelectorAll('.rating-stars').forEach(stars => {
        stars.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            const s = document.createElement('span');
            s.className = 'star';
            s.textContent = '★'; // character respects CSS color
            stars.appendChild(s);
        }
        makeStarsInteractive(stars);
    });

    if (!document.getElementById('survey_date').value) {
        document.getElementById('survey_date').value = new Date().toISOString().split('T')[0];
    }
    renderRecords();
});

// Form handling & populate/reset/edit/view/delete
function resetForm() {
    editingRecordId = null;
    document.getElementById('formTitle').textContent = 'Add New Survey Record';
    document.getElementById('recordId').value = '';
    document.getElementById('surveyForm').reset();
    document.getElementById('cancelEditBtn').style.display = 'none';
    document.querySelectorAll('.rating-stars').forEach(container => {
        Array.from(container.children).forEach(star => star.classList.remove('active','preview'));
        const hidden = document.getElementById(container.dataset.field);
        if (hidden) hidden.value = '';
    });
    document.querySelectorAll('.form-section').forEach(section => section.classList.remove('active'));
    document.querySelectorAll('#surveyForm input, #surveyForm select, #surveyForm textarea').forEach(el => el.removeAttribute('disabled'));
}

function populateForm(record, readOnly = false) {
    editingRecordId = record.id;
    document.getElementById('formTitle').textContent = readOnly ? 'View Survey' : 'Edit Survey Record';
    document.getElementById('recordId').value = record.id;

    const simpleFields = ['survey_date','respondent_type','name','age','gender','donate_again','recommend','comments','review_status','follow_up_required'];
    simpleFields.forEach(f => {
        const el = document.getElementById(f);
        if (!el) return;
        el.value = record[f] !== null && record[f] !== undefined ? record[f] : '';
        if (readOnly) el.setAttribute('disabled','disabled'); else el.removeAttribute('disabled');
    });

    const ratingFields = [
        'cleanliness_rooms','food_quality','medical_support',
        'staff_friendliness','adoption_ease','donation_convenience',
        'overall_rating'
    ];
    ['cleanliness_toilets','study_environment','play_facilities','clothes_availability','safety_security',
     'staff_supportiveness','staff_professionalism','responsiveness','adoption_transparency','adoption_communication',
     'legal_support','adoption_satisfaction','donation_transparency','donation_updates','donor_staff_behaviour',
     'donor_satisfaction'].forEach(x => ratingFields.push(x));

    ratingFields.forEach(f => {
        const val = record[f] !== null && record[f] !== undefined ? record[f] : '';
        const hidden = document.getElementById(f);
        if (hidden) hidden.value = val;
        const container = document.querySelector('.rating-stars[data-field="'+f+'"]');
        if (container) {
            Array.from(container.children).forEach((star, i) => {
                star.classList.toggle('active', val !== '' && i < Number(val));
                star.classList.toggle('preview', false);
                star.style.pointerEvents = readOnly ? 'none' : 'auto';
            });
        }
    });

    ['feel_safe','feel_happy','has_friends'].forEach(f => {
        const el = document.getElementById(f);
        if (el) {
            el.value = record[f] !== null && record[f] !== undefined ? record[f] : '';
            if (readOnly) el.setAttribute('disabled','disabled'); else el.removeAttribute('disabled');
        }
    });

    showRelevantSections(record.respondent_type || '');
    document.querySelectorAll('.rating-stars').forEach(container => {
        if (readOnly) container.style.pointerEvents = 'none'; else container.style.pointerEvents = 'auto';
    });

    document.getElementById('cancelEditBtn').style.display = readOnly ? 'none' : 'inline-block';
    if (readOnly) {
        document.querySelectorAll('#surveyForm input, #surveyForm select, #surveyForm textarea, #surveyForm button[type="submit"]').forEach(el => {
            el.setAttribute('disabled','disabled');
        });
    } else {
        document.querySelectorAll('#surveyForm input, #surveyForm select, #surveyForm textarea').forEach(el => el.removeAttribute('disabled'));
        document.querySelector('#surveyForm button[type="submit"]').removeAttribute('disabled');
    }
}

function viewRecord(id) {
    const record = records.find(r => r.id === id);
    if (!record) return alert("Record not found");
    populateForm(record, true);
    showPage('formPage');
}

function editRecord(id) {
    const record = records.find(r => r.id === id);
    if (!record) return alert("Record not found");
    populateForm(record, false);
    showPage('formPage');
}

document.getElementById('cancelEditBtn').onclick = () => {
    resetForm();
    showPage('recordsPage');
};

document.getElementById('searchInput').onkeypress = (e) => {
    if (e.key === 'Enter') performSearch();
};

function resetSearch() {
    document.getElementById('searchInput').value = '';
    document.querySelector('[data-tab="all"]').click();
}

// Form submission (creates or updates via existing endpoints)
document.getElementById('surveyForm').onsubmit = async (e) => {
    e.preventDefault();
    const recordId = document.getElementById('recordId').value;
    const formData = new FormData();
    const allInputs = document.querySelectorAll('#surveyForm input, #surveyForm select, #surveyForm textarea');
    allInputs.forEach(input => {
        if (input.disabled) return;
        formData.append(input.id, input.value);
    });

    const url = recordId ? `/api/surveys/${recordId}` : '/api/surveys';
    const method = recordId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, { method, body: formData });
        if (response.ok) {
            alert(recordId ? "✅ Survey updated successfully!" : "✅ Survey saved successfully!");
location.reload();

        } else {
            const error = await response.json();
            alert('❌ Error: ' + (error.error || 'Please try again'));
        }
    } catch (error) {
        alert('❌ Network error. Please check your connection.');
    }
};

async function deleteRecord(id) {
    if (confirm('Are you sure?')) {
        try {
            const res = await fetch(`/api/surveys/${id}`, { method: 'DELETE' });
            if (res.ok) location.reload();
            else alert('Delete failed');
        } catch (error) {
            alert('Delete failed');
        }
    }
}
</script>
</body>
</html>
"""


@app.route('/')
def index():
    records = SurveyRecord.query.order_by(SurveyRecord.createdAt.desc()).all()
    records_json = []
    for record in records:
        record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}
        # convert datetimes to strings for the page
        for k, v in record_dict.items():
            if isinstance(v, datetime):
                record_dict[k] = v.strftime('%Y-%m-%d %H:%M:%S')
        records_json.append(record_dict)
    return render_template_string(HTML_TEMPLATE, records=records_json)


# helper to parse int fields safely
INT_FIELDS = {
    'age', 'cleanliness_rooms', 'cleanliness_toilets', 'food_quality', 'medical_support',
    'study_environment', 'play_facilities', 'clothes_availability', 'safety_security',
    'staff_friendliness', 'staff_supportiveness', 'staff_professionalism', 'responsiveness',
    'adoption_ease', 'adoption_transparency', 'adoption_communication', 'legal_support',
    'adoption_satisfaction', 'donation_convenience', 'donation_transparency', 'donation_updates',
    'donor_staff_behaviour', 'donor_satisfaction', 'overall_rating'
}


@app.route('/api/surveys', methods=['POST'])
def create_survey():
    try:
        record = SurveyRecord()
        for key, value in request.form.items():
            if not hasattr(record, key) or key == 'id':
                continue
            if key in INT_FIELDS:
                try:
                    setattr(record, key, int(value) if value != '' else None)
                except:
                    setattr(record, key, None)
            else:
                setattr(record, key, value if value != '' else None)
        # ensure respondent_type - required
        if not record.respondent_type:
            return jsonify({'error': 'respondent_type is required'}), 400
        db.session.add(record)
        db.session.commit()
        return jsonify({'message': 'Survey created', 'id': record.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys/<record_id>', methods=['GET', 'PUT', 'DELETE'])
def survey_detail(record_id):
    record = SurveyRecord.query.get(record_id)
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    if request.method == 'GET':
        data = {}
        for c in record.__table__.columns:
            v = getattr(record, c.name)
            if isinstance(v, datetime):
                data[c.name] = v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                data[c.name] = v
        return jsonify(data)

    elif request.method == 'PUT':
        try:
            for key, value in request.form.items():
                if not hasattr(record, key) or key == 'id':
                    continue
                if key in INT_FIELDS:
                    try:
                        setattr(record, key, int(value) if value != '' else None)
                    except:

                        setattr(record, key, None)
                else:
                    setattr(record, key, value if value != '' else None)
            db.session.commit()
            return jsonify({'message': 'Survey updated'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(record)
            db.session.commit()
            return jsonify({'message': 'Survey deleted'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 Survey app started successfully")
    app.run(debug=True, port=5007)







