from flask import Flask, render_template_string

app = Flask(__name__)

# ---------------- MODULE ROUTES ----------------
MODULE_ROUTES = {
    'child': 'http://127.0.0.1:5001/',
    'adopter': 'http://127.0.0.1:5002/',
    'donor': 'http://127.0.0.1:5003/',
    'staff': 'http://127.0.0.1:5004/',
    'inventory': 'http://127.0.0.1:5005/',
    'certificate': 'http://127.0.0.1:5006/',
    'survey': 'http://127.0.0.1:5007/'
}

# ---------------- MODULE METADATA ----------------
MODULES = {
    'child': {'icon': '👶', 'title': 'Child Records', 'desc': 'Photo upload, search, CRUD', 'color': '#ff6b6b,#f06595'},
    'adopter': {'icon': '👨‍👩‍👧', 'title': 'Adopter Management', 'desc': 'Adoption forms & matching', 'color': '#339af0,#22b8cf'},
    'donor': {'icon': '💰', 'title': 'Donor Management', 'desc': 'Donation tracking & receipts', 'color': '#51cf66,#94d82d'},
    'staff': {'icon': '👥', 'title': 'Staff Management', 'desc': 'Employee scheduling & payroll', 'color': '#845ef7,#5c7cfa'},
    'inventory': {'icon': '📦', 'title': 'Inventory', 'desc': 'Supplies & low stock alerts', 'color': '#ff922b,#fd7e14'},
    'certificate': {'icon': '📜', 'title': 'Certificates', 'desc': 'PDF generation & printing', 'color': '#20c997,#12b886'},
    'survey': {'icon': '📊', 'title': 'Surveys', 'desc': 'Feedback collection & reports', 'color': '#e64980,#f03e3e'}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Orphanage Management System</title>
<style>
    :root {
        --bg-primary: #fff; --bg-secondary: #f8f9fa; --text-primary: #212529;
        --text-secondary: #6c757d; --primary-color: #007bff; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
    }
    [data-theme="dark"] {
        --bg-primary: #1a1a1a; --bg-secondary: #2d2d2d; --text-primary: #fff;
        --text-secondary: #adb5bd; --primary-color: #4dabf7; --shadow: 0 0.5rem 1rem rgba(0,0,0,0.5);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
        line-height: 1.6;
        transition: all 0.3s ease;
        padding: 20px;
    }
    .container { max-width: 1400px; margin: auto; }
    .header {display: flex;justify-content: center;align-items: center;margin-bottom: 40px;position: relative;}
    .header h1 { font-size: 2.5rem;background: linear-gradient(45deg, var(--primary-color), #6610f2);-webkit-background-clip: text;-webkit-text-fill-color: transparent;background-clip: text;}
    .theme-toggle {background: none;border: 2px solid var(--primary-color);width: 50px;height: 50px;border-radius: 50%;cursor: pointer;font-size: 1.5rem;display: flex;align-items: center;justify-content: center;transition: all 0.3s ease;position: absolute;right: 0;}
    .theme-toggle:hover {transform: scale(1.1);box-shadow: 0 0 20px var(--primary-color);}
    .modules-grid {display: grid;grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;}
    .module-card {background: var(--bg-secondary);padding: 30px;border-radius: 20px;box-shadow: var(--shadow);cursor: pointer;transition: all 0.3s ease;text-decoration: none;display: flex;flex-direction: column;align-items: center;justify-content: space-between;border-left: 8px solid;animation: gradient-border 3s linear infinite;}
    .module-card:hover {transform: translateY(-10px);box-shadow: 0 15px 40px rgba(0,0,0,0.2);}
    .module-icon { font-size: 4rem; margin-bottom: 20px; }
    .module-title { font-size: 1.8rem; margin-bottom: 15px; color: var(--primary-color); text-align: center; }
    .module-desc { color: var(--text-secondary); text-align: center; font-size: 1.1rem; margin-bottom: 25px; }
    .launch-text { color: var(--primary-color); font-weight: bold; font-size: 1.2rem; }

    @keyframes gradient-border {
        0% { border-color: currentColor; }
        0%, 100% { border-image-slice: 1; }
    }

    @media (max-width: 768px) {
        .modules-grid { grid-template-columns: 1fr; }
        .header { flex-direction: column; gap: 15px; }
    }
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🏠 Orphanage Management System</h1>
        <button class="theme-toggle" id="themeToggle">🌙</button>
    </div>
    <div class="modules-grid">
        {% for key, module in modules.items() %}
        <a href="{{ routes[key] }}" target="_blank" class="module-card"
           style="border-image: linear-gradient(45deg, {{ module.color }}) 1; border-image-slice: 1;">
            <div class="module-icon">{{ module.icon }}</div>
            <h2 class="module-title">{{ module.title }}</h2>
            <p class="module-desc">{{ module.desc }}</p>
            <div class="launch-text">👆 Click to Launch</div>
        </a>
        {% endfor %}
    </div>
</div>

<script>
const themeToggle = document.getElementById('themeToggle');
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);
themeToggle.textContent = savedTheme === 'light' ? '🌙' : '☀️';

themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeToggle.textContent = newTheme === 'light' ? '🌙' : '☀️';
});
</script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE, modules=MODULES, routes=MODULE_ROUTES)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)





