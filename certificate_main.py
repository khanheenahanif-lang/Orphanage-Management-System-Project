# certificate_app_live_update.py
from flask import Flask, render_template_string, request, jsonify, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from io import BytesIO
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# --- font registration helpers for ReportLab ---
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def try_register_segoeui():
    candidates = {
        'segoeui': [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\SegoeUI.ttf",
        ],
        'segoeui_bold': [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\SegoeUI-Bold.ttf",
        ],
        'segoeui_alt': [
            "/usr/share/fonts/truetype/msttcorefonts/Segoe_UI.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/segoeui.ttf",
            "/usr/share/fonts/truetype/segoeui/segoeui.ttf",
            "/usr/local/share/fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/segoeui.ttf",
            "/Library/Fonts/Segoe UI.ttf",
        ],
        'segoeui_bold_alt': [
            "/usr/share/fonts/truetype/msttcorefonts/Segoe_UI_Bold.ttf",
            "/usr/share/fonts/truetype/segoeui/segoeui_bold.ttf",
            "/Library/Fonts/Segoe UI Bold.ttf",
        ]
    }

    found = {}
    for path in candidates['segoeui'] + candidates.get('segoeui_alt', []):
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('SegoeUI', path))
                found['regular'] = 'SegoeUI'
                break
            except Exception:
                pass

    for path in candidates['segoeui_bold'] + candidates.get('segoeui_bold_alt', []):
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('SegoeUI-Bold', path))
                found['bold'] = 'SegoeUI-Bold'
                break
            except Exception:
                pass

    if 'regular' in found and 'bold' not in found:
        try:
            pdfmetrics.registerFont(TTFont('SegoeUI-Bold', path))
            found['bold'] = 'SegoeUI-Bold'
        except Exception:
            pass

    return found

REGISTERED_FONTS = try_register_segoeui()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Use absolute DB path to avoid different working-dir issues
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'certificate_records.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'assets')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(basedir, 'static'), exist_ok=True)

db = SQLAlchemy(app)

class CertificateRecord(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certType = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200))
    recipient = db.Column(db.String(200))
    childName = db.Column(db.String(100))
    childDOB = db.Column(db.String(20))
    parentName = db.Column(db.String(200))
    reason = db.Column(db.String(300))
    duration = db.Column(db.String(100))
    placeOfBirth = db.Column(db.String(200))
    medicalStatement = db.Column(db.String(300))
    purpose = db.Column(db.String(200))
    courseName = db.Column(db.String(200))
    courseDuration = db.Column(db.String(100))
    startDate = db.Column(db.String(20))
    endDate = db.Column(db.String(20))
    certNo = db.Column(db.String(100))
    issuedDate = db.Column(db.String(20))
    issuer = db.Column(db.String(200))
    logoFile = db.Column(db.String(500))
    signatureFile = db.Column(db.String(500))
    pdfFile = db.Column(db.String(500))
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/assets/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

CERT_TEMPLATES = {
    "adoption": {
        "label": "Certificate of Adoption",
        "subtitle": "Official Adoption Certificate",
        "declaration": ("This is to certify that {childName}, born on {childDOB}, has been officially adopted by "
                        "{parentName} on {issuedDate}. Adoption ID: {certNo}."),
        "fields": ["childName", "childDOB", "parentName"]
    },
    "appreciation": {
        "label": "Certificate of Appreciation",
        "subtitle": "Acknowledgement of Outstanding Service",
        "declaration": ("Presented to {recipient} for {reason}. In recognition of {duration} of dedicated service to {issuer}."),
        "fields": ["recipient", "reason", "duration"]
    },
    "birth": {
        "label": "Birth Certificate",
        "subtitle": "Official Record of Birth",
        "declaration": ("This certifies that {childName} was born on {childDOB} to {parentName}. Place of Birth: {placeOfBirth}. "
                        "Registration ID: {certNo}."),
        "fields": ["childName", "childDOB", "parentName", "placeOfBirth"]
    },
    "medical": {
        "label": "Medical Certificate",
        "subtitle": "Medical Certificate",
        "declaration": ("This is to certify that {recipient} was examined on {issuedDate} and found {medicalStatement}. "
                        "This certificate is issued for {purpose}."),
        "fields": ["recipient", "medicalStatement", "purpose"]
    },
    "training": {
        "label": "Certificate of Completion",
        "subtitle": "Training Completion Certificate",
        "declaration": ("This certifies that {recipient} has successfully completed the training on {courseName} "
                        "({courseDuration}) held from {startDate} to {endDate}."),
        "fields": ["recipient", "courseName", "courseDuration", "startDate", "endDate"]
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Certificate Management System</title>
  <style>
  a {
  text-decoration: none !important;
  color: inherit;
}

    :root { --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    [data-theme="dark"]{ --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    :root {
      --bg-primary:#ffffff;--bg-secondary:#f8f9fa;--text-primary:#212529;
      --text-secondary:#6c757d;--primary-color:#007bff;--success-color:#28a745;
      --danger-color:#dc3545;--border-color:#dee2e6;--shadow:0 0.5rem 1rem rgba(0,0,0,0.15);
    }
    [data-theme="dark"]{
      --bg-primary:#1a1a1a;--bg-secondary:#2d2d2d;--text-primary:#fff;
      --text-secondary:#adb5bd;--primary-color:#4dabf7;--success-color:#51cf66;
      --danger-color:#ff6b6b;--border-color:#444444;--shadow:0 0.5rem 1rem rgba(0,0,0,0.5);
    }
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:var(--font-family);font-size:16px;background:var(--bg-primary);color:var(--text-primary);line-height:1.6;transition: all 0.3s ease; -webkit-font-smoothing:antialiased;}
    .container{max-width:1200px;margin:0 auto;padding:20px}
    .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;padding:20px;background:var(--bg-secondary);border-radius:15px;box-shadow:var(--shadow)}
    .logo{font-size:2rem;font-weight:700;background:linear-gradient(45deg,var(--primary-color),#6610f2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
    .theme-toggle{background:none;border:2px solid var(--primary-color);width:50px;height:50px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.5rem;transition: all 0.3s ease;}
    .theme-toggle:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(0,123,255,0.12); }
    .btn{padding:12px 24px;border:none;border-radius:25px;cursor:pointer;font-size:1rem;font-weight:600;display:inline-flex;align-items:center;gap:8px;inline-flex; align-items: center; gap: 8px; transition: all 0.25s ease; box-shadow: var(--shadow); margin: 5px; }
    .btn-primary{background:var(--primary-color);color:#fff}
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,123,255,0.18); }
    .btn-secondary{background:var(--text-secondary);color:#fff}
    .btn-success{background:var(--success-color);color:#fff}


.filter-btn {background: var(--primary-color);color: #fff;border-radius: 20px;padding: 8px 14px;font-weight: 600;border: none;display: flex;align-items: center;gap: 6px;transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease;box-shadow: 0 6px 18px rgba(0, 123, 255, 0.15);}
.filter-btn:hover {transform: translateY(-3px);box-shadow: 0 12px 30px rgba(0, 123, 255, 0.25);opacity: 0.97;cursor: pointer;}
.filter-btn {background: var(--primary-color);color: #fff !important;        border-radius: 20px;padding: 8px 14px;font-weight: 600;border: none;display: inline-flex;align-items: center;gap: 6px;transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease;box-shadow: 0 6px 18px rgba(0, 123, 255, 0.15);}
.filter-btn {background: var(--primary-color);border: none;border-radius: 20px;padding: 8px 14px;font-weight: 600;display: inline-flex;align-items: center;gap: 6px;transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease;box-shadow: 0 6px 18px rgba(0, 123, 255, 0.15);}

html[data-theme="light"] .filter-btn {
  color: #000 !important;
}
html[data-theme="light"] .filter-btn * {
  color: #000 !important;
}

html[data-theme="dark"] .filter-btn {
  color: #fff !important;
}
html[data-theme="dark"] .filter-btn * {
  color: #fff !important;
}

.filter-btn:hover {cursor: pointer;transform: translateY(-3px);box-shadow: 0 12px 30px rgba(0, 123, 255, 0.25);opacity: 0.95;}
.filter-btn.active {font-weight: 700;transform: translateY(-3px);background: var(--primary-color);box-shadow: 0 14px 34px rgba(0, 123, 255, 0.32);}
.filter-btn:active {transform: translateY(0);opacity: 0.92;}
.btn-danger {background: var(--danger-color);color: #fff;}
.btn-danger:hover {transform: translateY(-2px); box-shadow: 0 8px 25px rgba(220,53,69,0.18);}
.btn-group { margin-top: 12px; display:flex; gap:10px; flex-wrap:wrap; }
.tab-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 26px; background: var(--bg-secondary); padding: 18px; border-radius: var(--card-radius); box-shadow: var(--shadow); }
.page{display:none;animation: fadeIn 0.45s ease-in;}
.page.active{display:block;}
 @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .search-panel{background:var(--bg-secondary);padding:20px;border-radius:15px;margin-bottom:12px;display:flex;gap:15px;align-items:center;flex-wrap:wrap;box-shadow: var(--shadow);}
    .search-input{flex:1;max-width:400px;padding:12px 20px;border:2px solid var(--border-color);border-radius:25px;transition: all 0.25s ease;background: var(--bg-primary); color: var(--text-primary);}
    .search-input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 4px rgba(0,123,255,0.06); }
    .cert-filter-bar{display:flex;gap:10px;margin-bottom:20px;padding:10px;border-radius:12px;background:var(--bg-secondary);align-items:center;flex-wrap:wrap}
    .filter-btn{padding:8px 12px;border-radius:12px;border:none;background:transparent;cursor:pointer;font-weight:700;display:inline-flex;align-items:center;gap:8px}
    .filter-btn.active{background:var(--primary-color);color:#fff}
    .records-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:20px;margin-bottom:30px}
    .record-card{background:var(--bg-secondary);padding:25px;border-radius:20px;box-shadow:var(--shadow);border-left:5px solid var(--primary-color); transition: all 0.25s ease; }
    .record-card:hover { transform: translateY(-6px); box-shadow: 0 18px 45px rgba(0,0,0,0.14); }
    .record-name{font-size:1.25rem;font-weight:700;margin-bottom:8px;color:var(--primary-color)}
    .record-detail { margin: 6px 0; font-size: 0.95rem; color: var(--text-primary); }
    .tab-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 26px; background: var(--bg-secondary); padding: 18px; border-radius: var(--card-radius); box-shadow: var(--shadow); }
    .form-container{background:var(--bg-secondary);padding:36px;border-radius:25px;box-shadow:var(--shadow); max-width: 1400px; margin: 0 auto;}
    .form-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
    .form-section { display: none; margin-bottom: 20px; padding: 18px; background: rgba(255,255,255,0.03); border-radius: 15px; border-left: 5px solid var(--primary-color); }
    .form-section.active { display: block; }
    .form-group { margin-bottom: 20px; } .form-group.full-width { grid-column: 1 / -1; }
    label{display:block;margin-bottom:8px;font-weight:600}
    # input,select,textarea{width:100%;padding:12px;border:2px solid var(--border-color);border-radius:10px;background:var(--bg-primary);font-family:var(--font-family)}
    input,
select,
textarea {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid var(--border-color);
  border-radius: 18px;        /* 🔵 softer corners */
  background: var(--bg-primary);
  font-family: var(--font-family);
  font-size: 1rem;
  transition: all 0.25s ease;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
}

 textarea{min-height:100px}
    # input, select, textarea { width: 100%; padding: 14px; border: 2px solid var(--border-color); border-radius: var(--control-radius); font-size: 1rem; transition: all 0.25s ease; background: var(--bg-primary); color: var(--text-primary); }
    input,
select,
textarea {width: 100%;padding: 14px 18px;border: 2px solid var(--border-color);border-radius: 18px;background: var(--bg-primary);font-family: var(--font-family);font-size: 1rem;transition: all 0.25s ease; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);color: var(--text-primary);}
::placeholder {color: var(--text-secondary);opacity: 1}


    input:focus, select:focus, textarea:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 6px rgba(0,123,255,0.04); }

    textarea { resize: vertical; min-height: 120px; }
    .photo-preview{width:100px;height:100px;border-radius:12px;object-fit:cover;border:3px solid var(--primary-color);margin-top:10px}
    .muted{color:var(--text-secondary)}
    @media(max-width:768px){.form-grid{grid-template-columns:1fr} .cert-filter-bar { justify-content: center; } }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">📜 Certificate</div>
      <div><button id="themeToggle" class="theme-toggle">☀️</button></div>
    </div>

    <div id="recordsPage" class="page active">
      <div style="display:flex;gap:15px;margin-bottom:20px;">
        <a href="#formPage" class="btn btn-primary" id="addBtn">➕ Add Certificate</a>
        <button class="btn btn-secondary" id="exportBtn">📥 Export</button>
      </div>

      <div class="search-panel">
        <input id="searchInput" class="search-input" placeholder="🔍 Search by recipient, type or cert no...">
        <button class="btn btn-primary" id="searchBtn">🔍 Search</button>
        <button class="btn btn-secondary" id="allBtn">📄 All Records</button>
      </div>

      <!-- NEW: certificate type filter buttons -->

      <div class="tab-buttons" id="certFilterBar" aria-label="Certificate type filters">

        <button class="filter-btn active" data-filter="all" onclick="setCertFilter('all')">📋 All <span id="count_all" style="margin-left:8px;font-weight:600;color:var(--text-secondary)"></span></button>
        <button class="filter-btn" data-filter="adoption" onclick="setCertFilter('adoption')">👶 {{ templates['adoption'].label }}</button>
        <button class="filter-btn" data-filter="appreciation" onclick="setCertFilter('appreciation')">👏 {{ templates['appreciation'].label }}</button>
        <button class="filter-btn" data-filter="birth" onclick="setCertFilter('birth')">🍼 {{ templates['birth'].label }}</button>
        <button class="filter-btn" data-filter="medical" onclick="setCertFilter('medical')">🩺 {{ templates['medical'].label }}</button>
        <button class="filter-btn" data-filter="training" onclick="setCertFilter('training')">🎓 {{ templates['training'].label }}</button>

    </div>

      <div class="records-grid" id="recordsGrid"></div>
    </div>

    <div id="formPage" class="page">
      <a href="#recordsPage" class="btn btn-secondary" id="backBtn" style="margin-bottom:20px">Back to record </a>
      <div class="form-container">
        <h2 id="formTitle" style="color:var(--primary-color)">Add New Certificate</h2>
        <form id="certForm" enctype="multipart/form-data">
          <input type="hidden" id="recordId">
          <input type="hidden" id="existingLogo">
          <input type="hidden" id="existingSignature">
          <div class="form-grid">
            <div>
              <div style="margin-bottom:12px">
                <label>Certificate Type</label>
                <select id="certType" required>
                  {% for k,v in templates.items() %}
                  <option value="{{k}}">{{ v.label }}</option>
                  {% endfor %}
                </select>
              </div>

              <div style="margin-bottom:12px">
                <label>Title</label>
                <input id="title" value="Certificate">
              </div>

              <div style="margin-bottom:12px">
                <label>Subtitle</label>
                <input id="subtitle">
              </div>

              <div style="margin-bottom:12px">
                <label>Certificate No (optional)</label>
                <input id="certNo" placeholder="Auto-generated if left blank">
              </div>

              <div style="margin-bottom:12px">
                <label>Issued Date</label>
                <input id="issuedDate" type="date" value="{{ today }}">
              </div>

              <div style="margin-bottom:12px">
                <label>Issuer</label>
                <input id="issuer" value="Hope Orphanage Trust">
              </div>
            </div>

            <div>
              <div style="margin-bottom:12px">
                <label>Logo (optional)</label>
                <input type="file" id="logoFile" accept="image/*">
                <img id="logoPreview" class="photo-preview" style="display:none">
              </div>

              <div style="margin-bottom:12px">
                <label>Signature (optional)</label>
                <input type="file" id="signatureFile" accept="image/*">
                <img id="sigPreview" class="photo-preview" style="display:none">
              </div>

              <div style="margin-bottom:12px">
                <label>PDF File (will be generated)</label>
                <div class="muted">PDF will be created and saved when you click Generate PDF</div>
              </div>
            </div>

            <div id="dynamicFields" style="grid-column:1 / -1"></div>
          </div>

          <div style="margin-top:18px;text-align:center">
            <button class="btn btn-success" id="saveBtn" type="submit">💾 Save & Generate PDF</button>
            <button class="btn btn-secondary" id="cancelBtn" type="button" style="display:none;margin-left:10px">Cancel</button>
          </div>
        </form>
      </div>
    </div>

  </div>

<script>
document.addEventListener('DOMContentLoaded', () => {
  let records = {{ records|tojson|safe }};
  if (!Array.isArray(records)) records = [];
  let filtered = [...records];
  let editingId = null;
  const TEMPLATES = {{ templates_json|safe }};
  const emptyHTML = `<div id="emptyState" style="text-align:center;padding:40px;color:var(--text-secondary)"><div style="font-size:3rem">📜</div><h3>No certificates yet</h3><p class="muted">Click Add Certificate to create one</p></div>`;

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

  // current certificate-type filter (keys from CERT_TEMPLATES, or 'all')
  let currentCertFilter = 'all';

  function showPage(id){
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
    if (id === 'recordsPage') renderRecords();
  }

  function escapeHtml(s = '') {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Update counts for each type and show count on All button as well
  function updateTypeCounts(){
    const counts = { all: (records || []).length };
    for (const k in TEMPLATES) counts[k] = (records || []).filter(r => (r.certType || '').toLowerCase() === k.toLowerCase()).length;
    document.getElementById('count_all').textContent = counts.all ? '(' + counts.all + ')' : '';
  }

  // Set active state on filter buttons
  window.setCertFilter = function(filterKey){
    currentCertFilter = filterKey || 'all';
    document.querySelectorAll('.filter-btn').forEach(btn => {
      const key = btn.getAttribute('data-filter') || 'all';
      btn.classList.toggle('active', key === currentCertFilter);
    });
    applyFiltersAndRender();
  };

  function applyFiltersAndRender(){
    const q = (document.getElementById('searchInput').value || '').toLowerCase().trim();
    filtered = (records || []).filter(r => {
      // type filter
      if (currentCertFilter !== 'all'){
        if (!r.certType || r.certType.toLowerCase() !== currentCertFilter.toLowerCase()) return false;
      }
      // search filter
      if (!q) return true;
      const recipient = (r.recipient || r.childName || '').toString().toLowerCase();
      const certType = (r.certType || '').toString().toLowerCase();
      const certNo = (r.certNo || '').toString().toLowerCase();
      return (recipient.includes(q) || certType.includes(q) || certNo.includes(q));
    });
    renderRecords();
  }

  function renderRecords(){
    updateTypeCounts();
    const grid = document.getElementById('recordsGrid');
    if (!Array.isArray(filtered) || filtered.length === 0) { grid.innerHTML = emptyHTML; return; }
    grid.innerHTML = filtered.map(r => {
      const recipientText = (r.recipient && r.recipient.trim()) || (r.childName && r.childName.trim()) || 'N/A';
      const issued = r.issuedDate || 'N/A';
      const certno = r.certNo || 'N/A';
      const logoImg = r.logoFile ? `<img src="/assets/${r.logoFile}" style="width:60px;height:60px;border-radius:10px;float:right;object-fit:cover" onerror="this.style.display='none'">` : '';
      return `
      <div class="record-card">
        <div class="record-name">${escapeHtml(r.title || '')} — ${escapeHtml(r.certType || '')}</div>
        ${logoImg}
        <div><strong>Recipient:</strong> ${escapeHtml(recipientText)}</div>
        <div><strong>Issued:</strong> ${escapeHtml(issued)}</div>
        <div><strong>Cert No:</strong> ${escapeHtml(certno)}</div>
        <div class="btn-group" div style="margin-top:10px">
          <button class="btn btn-primary" onclick="downloadPdf('${r.id}')">📄 Download PDF</button>
          <button class="btn btn-secondary" onclick="viewRecord('${r.id}')">👁️ View</button>
          <button class="btn btn-danger" onclick="deleteRecord('${r.id}')">🗑️ Delete</button>
        </div>
      </div>
    `;
    }).join('');
  }

  function performSearch(){
    applyFiltersAndRender();
  }

  function resetSearch(){
    document.getElementById('searchInput').value = '';
    // clear type filter and set All active
    setCertFilter('all');
    filtered = [...records];
    renderRecords();
  }

  function resetForm(){
    editingId = null;
    document.getElementById('recordId').value = '';
    document.getElementById('existingLogo').value = '';
    document.getElementById('existingSignature').value = '';
    document.getElementById('certForm').reset();
    document.getElementById('logoPreview').style.display = 'none';
    document.getElementById('sigPreview').style.display = 'none';
    document.getElementById('cancelBtn').style.display = 'none';
    document.getElementById('formTitle').innerText = 'Add New Certificate';
    renderDynamicFields(document.getElementById('certType').value);
    document.getElementById('saveBtn').style.display = 'inline-block';
  }

  function renderDynamicFields(typeKey){
    const container = document.getElementById('dynamicFields');
    container.innerHTML = '';
    const tmpl = TEMPLATES[typeKey] || {fields: [], subtitle: ''};
    document.getElementById('subtitle').value = tmpl.subtitle || '';
    tmpl.fields.forEach(f => {
      const el = document.createElement('div');
      el.style.marginBottom='12px';
      let label = prettify(f);
      let inputType = 'text';
      if (f.toLowerCase().includes('date') || f.toLowerCase().includes('dob') || f.toLowerCase().includes('start') || f.toLowerCase().includes('end')) inputType='date';
      if (f.toLowerCase().includes('reason') || f.toLowerCase().includes('statement') || f.toLowerCase().includes('place')) {
        el.innerHTML = `<label>${label}</label><textarea id="${f}"></textarea>`;
      } else {
        el.innerHTML = `<label>${label}</label><input id="${f}" type="${inputType}">`;
      }
      container.appendChild(el);
    });

    const generic = document.createElement('div');
    generic.innerHTML = `<div style="margin-bottom:12px"><label>Recipient (if not using childName)</label><input id="recipient"></div>`;
    container.appendChild(generic);
  }

  function prettify(s){ return s.split(/(?=[A-Z])|_/).join(' ').replace(/\b\w/g, l => l.toUpperCase()) }

  document.getElementById('logoFile').addEventListener('change', (e)=>{
    const f = e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = (ev)=> {
      const img = document.getElementById('logoPreview');
      img.src = ev.target.result;
      img.style.display='block';
      document.getElementById('existingLogo').value = '';
    };
    r.readAsDataURL(f);
  });
  document.getElementById('signatureFile').addEventListener('change', (e)=>{
    const f = e.target.files[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = (ev)=> {
      const img = document.getElementById('sigPreview');
      img.src = ev.target.result;
      img.style.display='block';
      document.getElementById('existingSignature').value = '';
    };
    r.readAsDataURL(f);
  });

  // UPDATED submit handler: updates records in-memory and re-renders without reload
  document.getElementById('certForm').addEventListener('submit', async (e)=>{
    e.preventDefault();
    const id = document.getElementById('recordId').value;
    const formData = new FormData();
    const type = document.getElementById('certType').value;
    formData.append('certType', type);
    formData.append('title', document.getElementById('title').value || '');
    formData.append('subtitle', document.getElementById('subtitle').value || '');
    formData.append('certNo', document.getElementById('certNo').value || '');
    formData.append('issuedDate', document.getElementById('issuedDate').value || '');
    formData.append('issuer', document.getElementById('issuer').value || '');

    const fields = (TEMPLATES[type] && TEMPLATES[type].fields) || [];
    fields.forEach(f => {
      const el = document.getElementById(f);
      if (el) formData.append(f, el.value || '');
    });
    formData.append('recipient', (document.getElementById('recipient') ? document.getElementById('recipient').value : '') || '');

    const logo = document.getElementById('logoFile').files[0];
    const sig = document.getElementById('signatureFile').files[0];
    const existingLogo = document.getElementById('existingLogo').value;
    const existingSignature = document.getElementById('existingSignature').value;
    if (logo) formData.append('logoFile', logo);
    if (sig) formData.append('signatureFile', sig);
    formData.append('existingLogo', existingLogo);
    formData.append('existingSignature', existingSignature);

    const url = id ? `/api/records/${id}` : '/api/records';
    const method = id ? 'PUT' : 'POST';
    try {
      const res = await fetch(url, { method, body: formData });
      if (!res.ok) {
        const txt = await res.text().catch(()=>null);
        alert('Error saving record: ' + (txt || res.statusText));
        return;
      }
      const data = await res.json().catch(()=>null);
      const newId = data && data.id ? data.id : id;

      if (newId) {
        const rres = await fetch(`/api/records/${newId}`);
        if (rres.ok) {
          const rec = await rres.json();
          const idx = records.findIndex(x => x.id === rec.id);
          if (idx >= 0) {
            records[idx] = rec;
          } else {
            records.unshift(rec);
          }
          // apply filters to show updated state
          applyFiltersAndRender();
          resetForm();
          showPage('recordsPage');
          alert("✅ Certificate saved successfully!");

          return;
        } else {
          location.reload();
          return;
        }
      } else {
        location.reload();
      }
    } catch (err) {
      console.error('Save error', err);
      alert('Network error');
    }
  });

  window.viewRecord = function(id){
    const r = (records || []).find(x=>x.id===id);
    if (!r) return alert('Not found');
    populateForm(r, true);
    showPage('formPage');
  };
  window.editRecord = function(id){
    const r = (records || []).find(x=>x.id===id);
    if (!r) return alert('Not found');
    populateForm(r, false);
    showPage('formPage');
  };

  function populateForm(r, readOnly=false){
    document.getElementById('recordId').value = r.id;
    document.getElementById('existingLogo').value = r.logoFile || '';
    document.getElementById('existingSignature').value = r.signatureFile || '';
    // ensure certType select is set to the saved key
    document.getElementById('certType').value = r.certType || '';
    // render fields for this cert type
    renderDynamicFields(r.certType || Object.keys(TEMPLATES)[0] || 'adoption');

    // --- Robust fill: wait until dynamic fields exist, then fill them ---
    // Choose a field to test existence; prefer the first declared template field,
    // otherwise fallback to 'recipient'
    const firstField = (TEMPLATES[r.certType] && TEMPLATES[r.certType].fields && TEMPLATES[r.certType].fields[0]) || 'recipient';
    let attempts = 0;
    function tryFill() {
      attempts++;
      // If first field exists OR we've tried enough times, proceed to fill whatever exists
      if (document.getElementById(firstField) || attempts > 20) {
        // fill all matching inputs/selects/textareas present in the form
        for (const k in r) {
          const el = document.getElementById(k);
          if (el) {
            try { el.value = r[k] !== null && r[k] !== undefined ? r[k] : ''; } catch(e) {}
          }
        }
        // show previews if files exist
        if (r.logoFile) {
          const lp = document.getElementById('logoPreview'); lp.src = `/assets/${r.logoFile}`; lp.style.display='block';
        }
        if (r.signatureFile) {
          const sp = document.getElementById('sigPreview'); sp.src = `/assets/${r.signatureFile}`; sp.style.display='block';
        }
      } else {
        // retry shortly
        setTimeout(tryFill, 35);
      }
    }
    tryFill();
    // --- end robust fill ---

    document.getElementById('cancelBtn').style.display='inline-block';
    document.getElementById('formTitle').innerText = readOnly ? 'View Certificate' : 'Edit Certificate';
    const inputs = Array.from(document.querySelectorAll('#certForm input, #certForm select, #certForm textarea'));
    inputs.forEach(i => {
      i.disabled = readOnly && !['recordId','existingLogo','existingSignature'].includes(i.id);
    });
    document.getElementById('saveBtn').style.display = readOnly ? 'none' : 'inline-block';
  }

  window.deleteRecord = async function(id){
    if (!confirm('Delete this certificate?')) return;
    await fetch(`/api/records/${id}`, { method:'DELETE' });
    // remove from in-memory list to avoid reload
    records = (records || []).filter(r => r.id !== id);
    // re-apply current filters
    applyFiltersAndRender();
  };

  window.downloadPdf = function(id){
    window.open(`/download/${id}`, '_blank');
  };

  document.getElementById('addBtn').addEventListener('click', (ev) => {
    ev.preventDefault();
    resetForm();
    showPage('formPage');
  });
  document.getElementById('backBtn').addEventListener('click', (ev) => { ev.preventDefault(); showPage('recordsPage'); });
  document.getElementById('exportBtn').addEventListener('click', exportData);
  document.getElementById('searchBtn').addEventListener('click', performSearch);
  document.getElementById('allBtn').addEventListener('click', resetSearch);
  document.getElementById('cancelBtn').addEventListener('click', () => { resetForm(); showPage('recordsPage'); });

  document.getElementById('searchInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); performSearch(); }
  });

  document.getElementById('certType').addEventListener('change', (e) => renderDynamicFields(e.target.value));

  function exportData(){
    const blob = new Blob([JSON.stringify(records, null, 2)], { type:'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'certificates.json'; a.click();
  }

  // initialize
  filtered = [...records];
  // set counts and ensure All filter active
  updateTypeCounts();
  setCertFilter('all');
  renderDynamicFields(document.getElementById('certType').value);
  renderRecords();
});
</script>

</body>
</html>
"""

@app.route('/')
def index():
    records = CertificateRecord.query.order_by(CertificateRecord.createdAt.desc()).all()
    records_json = []
    for r in records:
        record_dict = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        if record_dict.get('createdAt'):
            record_dict['createdAt'] = record_dict['createdAt'].isoformat()
        records_json.append(record_dict)
    return render_template_string(HTML_TEMPLATE,
                                  records=records_json,
                                  templates=CERT_TEMPLATES,
                                  templates_json={k: {"label": v["label"], "subtitle": v["subtitle"], "declaration": v["declaration"], "fields": v["fields"]} for k,v in CERT_TEMPLATES.items()},
                                  today=datetime.utcnow().strftime('%Y-%m-%d'))

@app.route('/api/records', methods=['POST'])
def create_record():
    logo_filename = None
    sig_filename = None
    if 'logoFile' in request.files and request.files['logoFile'].filename:
        f = request.files['logoFile']
        if f and allowed_file(f.filename):
            logo_filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
    elif request.form.get('existingLogo'):
        logo_filename = request.form.get('existingLogo')

    if 'signatureFile' in request.files and request.files['signatureFile'].filename:
        f = request.files['signatureFile']
        if f and allowed_file(f.filename):
            sig_filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], sig_filename))
    elif request.form.get('existingSignature'):
        sig_filename = request.form.get('existingSignature')

    rec = CertificateRecord()
    fields = ['certType','title','subtitle','recipient','childName','childDOB','parentName','reason','duration','placeOfBirth',
              'medicalStatement','purpose','courseName','courseDuration','startDate','endDate','certNo','issuedDate','issuer']
    for f in fields:
        val = request.form.get(f)
        if val is not None:
            setattr(rec, f, val)
    rec.logoFile = logo_filename
    rec.signatureFile = sig_filename

    try:
        if not rec.certNo or (isinstance(rec.certNo, str) and rec.certNo.strip()==''):
            rec.certNo = f"CERT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        if not rec.issuedDate or (isinstance(rec.issuedDate, str) and rec.issuedDate.strip()==''):
            rec.issuedDate = datetime.utcnow().strftime('%Y-%m-%d')

        db.session.add(rec)
        db.session.commit()

        pdf_buf = create_certificate_pdf_bytes(
            title=rec.title or CERT_TEMPLATES.get(rec.certType, {}).get('label','Certificate'),
            subtitle=rec.subtitle or CERT_TEMPLATES.get(rec.certType, {}).get('subtitle',''),
            recipient=rec.recipient or rec.childName or '',
            declaration=render_declaration(rec),
            cert_no=rec.certNo,
            issued_date=rec.issuedDate,
            issuer=rec.issuer or 'Organization',
            logo_filename=rec.logoFile,
            signature_filename=rec.signatureFile,
            verification_url=(request.url_root.rstrip('/') + url_for('verify_certificate', cert_id=rec.certNo))
        )
        pdf_filename = secure_filename(f"{rec.id}.pdf")
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_buf.getbuffer())
        rec.pdfFile = pdf_filename
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("PDF generation or DB error:", e)

    return jsonify({'message':'Record created','id':rec.id}), 201

@app.route('/api/records/<record_id>', methods=['GET','PUT','DELETE'])
def record_detail(record_id):
    rec = CertificateRecord.query.get(record_id)
    if not rec:
        return jsonify({'error':'Record not found'}), 404

    if request.method == 'GET':
        return jsonify({c.name: getattr(rec, c.name) for c in rec.__table__.columns})

    if request.method == 'PUT':
        if 'logoFile' in request.files and request.files['logoFile'].filename:
            f = request.files['logoFile']
            if f and allowed_file(f.filename):
                if rec.logoFile:
                    old = os.path.join(app.config['UPLOAD_FOLDER'], rec.logoFile)
                    if os.path.exists(old): os.remove(old)
                logo_filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
                rec.logoFile = logo_filename
        elif request.form.get('existingLogo'):
            rec.logoFile = request.form.get('existingLogo')

        if 'signatureFile' in request.files and request.files['signatureFile'].filename:
            f = request.files['signatureFile']
            if f and allowed_file(f.filename):
                if rec.signatureFile:
                    old = os.path.join(app.config['UPLOAD_FOLDER'], rec.signatureFile)
                    if os.path.exists(old): os.remove(old)
                sig_filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], sig_filename))
                rec.signatureFile = sig_filename
        elif request.form.get('existingSignature'):
            rec.signatureFile = request.form.get('existingSignature')

        fields = ['certType','title','subtitle','recipient','childName','childDOB','parentName','reason','duration','placeOfBirth',
                  'medicalStatement','purpose','courseName','courseDuration','startDate','endDate','certNo','issuedDate','issuer']
        for f in fields:
            val = request.form.get(f)
            if val is not None:
                setattr(rec, f, val)

        try:
            pdf_buf = create_certificate_pdf_bytes(
                title=rec.title or CERT_TEMPLATES.get(rec.certType, {}).get('label','Certificate'),
                subtitle=rec.subtitle or CERT_TEMPLATES.get(rec.certType, {}).get('subtitle',''),
                recipient=rec.recipient or rec.childName or '',
                declaration=render_declaration(rec),
                cert_no=rec.certNo or f"CERT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                issued_date=rec.issuedDate or datetime.utcnow().strftime('%Y-%m-%d'),
                issuer=rec.issuer or 'Organization',
                logo_filename=rec.logoFile,
                signature_filename=rec.signatureFile,
                verification_url=(request.url_root.rstrip('/') + url_for('verify_certificate', cert_id=rec.certNo or ''))
            )
            pdf_filename = secure_filename(f"{rec.id}.pdf")
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_buf.getbuffer())
            rec.pdfFile = pdf_filename
        except Exception as e:
            print("PDF regen error:", e)

        db.session.commit()
        return jsonify({'message':'Record updated'})

    if request.method == 'DELETE':
        if rec.logoFile:
            p = os.path.join(app.config['UPLOAD_FOLDER'], rec.logoFile)
            if os.path.exists(p): os.remove(p)
        if rec.signatureFile:
            p = os.path.join(app.config['UPLOAD_FOLDER'], rec.signatureFile)
            if os.path.exists(p): os.remove(p)
        if rec.pdfFile:
            p = os.path.join(app.config['UPLOAD_FOLDER'], rec.pdfFile)
            if os.path.exists(p): os.remove(p)
        db.session.delete(rec)
        db.session.commit()
        return jsonify({'message':'Record deleted'})

@app.route('/download/<record_id>')
def download(record_id):
    rec = CertificateRecord.query.get(record_id)
    if not rec or not rec.pdfFile:
        return "PDF not found", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], rec.pdfFile)

@app.route('/verify/<cert_id>')
def verify_certificate(cert_id):
    rec = CertificateRecord.query.filter_by(certNo=cert_id).first()
    if not rec:
        return f"<h3>Certificate ID {cert_id} not found</h3>", 404
    return f"<h3>Certificate {rec.certNo} — {rec.title}</h3><p>Issued: {rec.issuedDate} • Issuer: {rec.issuer}</p>"

def render_declaration(rec):
    tpl = CERT_TEMPLATES.get(rec.certType, {}).get('declaration', '')
    mapping = {
        "childName": rec.childName or "",
        "childDOB": rec.childDOB or "",
        "parentName": rec.parentName or "",
        "recipient": rec.recipient or "",
        "reason": rec.reason or "",
        "duration": rec.duration or "",
        "placeOfBirth": rec.placeOfBirth or "",
        "medicalStatement": rec.medicalStatement or "",
        "purpose": rec.purpose or "",
        "courseName": rec.courseName or "",
        "courseDuration": rec.courseDuration or "",
        "startDate": rec.startDate or "",
        "endDate": rec.endDate or "",
        "certNo": rec.certNo or "",
        "issuedDate": rec.issuedDate or "",
        "issuer": rec.issuer or ""
    }
    s = tpl
    for k,v in mapping.items():
        s = s.replace("{" + k + "}", v)
    import re
    s = re.sub(r'\{[^}]+\}', '', s)
    return s

def create_certificate_pdf_bytes(title, subtitle, recipient, declaration, cert_no, issued_date, issuer, logo_filename=None, signature_filename=None, verification_url=None):
    buffer = BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(width, height))
    margin_x = 20 * mm
    margin_y = 20 * mm

    c.setLineWidth(1.5)
    c.rect(margin_x/2, margin_y/2, width - margin_x, height - margin_y)

    normal_font = REGISTERED_FONTS.get('regular', 'Helvetica')
    bold_font = REGISTERED_FONTS.get('bold', 'Helvetica-Bold')

    try:
        if logo_filename:
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path).convert("RGB")
                max_logo_w = 60 * mm
                max_logo_h = 30 * mm
                logo_img.thumbnail((max_logo_w, max_logo_h))
                c.drawImage(ImageReader(logo_img), margin_x + 10, height - margin_y - max_logo_h - 5, width=logo_img.width, height=logo_img.height, mask='auto')
    except Exception:
        pass

    c.setFont(bold_font, 34)
    c.drawCentredString(width/2, height - margin_y - 20, title)
    c.setFont(normal_font, 14)
    c.drawCentredString(width/2, height - margin_y - 48, subtitle or "")

    c.setFont(normal_font, 9)
    c.drawRightString(width - margin_x - 10, height - margin_y - 12, f"Certificate No: {cert_no}")
    c.drawRightString(width - margin_x - 10, height - margin_y - 26, f"Issued: {issued_date}")

    c.setFont(bold_font, 26)
    c.drawCentredString(width/2, height/2 + 22*mm, recipient)

    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    styles = getSampleStyleSheet()
    styleN = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=normal_font,
        fontSize=12,
        leading=15
    )
    para = Paragraph(declaration, styleN)
    text_x = margin_x + 30
    text_w = width - 2*(margin_x + 30)
    w,h = para.wrap(text_w, 120*mm)
    para.drawOn(c, text_x, height/2 - 6*mm - h)

    try:
        if signature_filename:
            sig_path = os.path.join(app.config['UPLOAD_FOLDER'], signature_filename)
            if os.path.exists(sig_path):
                sig = Image.open(sig_path).convert("RGB")
                sig_max_w = 50 * mm
                sig_max_h = 20 * mm
                sig.thumbnail((sig_max_w, sig_max_h))
                sig_x = margin_x + 20
                sig_y = margin_y + 30
                c.drawImage(ImageReader(sig), sig_x, sig_y, width=sig.width, height=sig.height, mask='auto')
                c.setFont(bold_font, 11)
                c.drawString(sig_x, sig_y - 12, issuer)
                c.setFont(normal_font, 9)
                c.drawString(sig_x, sig_y - 24, "Authorized Signatory")
    except Exception:
        pass

    try:
        if verification_url:
            qr_img = qrcode.make(verification_url)
            qr_sz = 80
            qr_img = qr_img.resize((qr_sz, qr_sz))
            qr_reader = ImageReader(qr_img)
            qr_x = width - margin_x - qr_sz - 10
            qr_y = margin_y + 10
            c.drawImage(qr_reader, qr_x, qr_y, width=qr_sz, height=qr_sz)
            c.setFont(normal_font, 8)
            c.drawCentredString(qr_x + qr_sz/2, qr_y - 10, "Scan to verify")
    except Exception:
        pass

    c.setFont(normal_font, 9)
    footer_text = f"Issued by {issuer} • Issued: {issued_date} • Certificate: {cert_no}"
    c.drawCentredString(width/2, margin_y/2 + 4, footer_text)

    try:
        c.saveState()
        c.translate(width/2, height/2)
        c.rotate(30)
        c.setFont(bold_font, 72)
        c.setFillGray(0.9, 0.5)
        c.drawCentredString(0, 0, issuer)
        c.restoreState()
    except Exception:
        pass

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

if __name__ == '__main__':
    print("🚀 Certificate Management System started successfully")
    app.run(debug=True, port=5006)





