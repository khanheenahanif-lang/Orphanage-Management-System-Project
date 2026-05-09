from flask import Flask, render_template_string, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = 'hope-orphanage-secret-key-2025'

USER_CREDENTIALS = {'heena':'heena19'}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hope Orphanage</title>
<style>
:root {
    --bg-primary:#ffffff; --bg-secondary:#f8f9fa; --text-primary:#212529;
    --text-secondary:#6c757d; --primary-color:#007bff; --success-color:#28a745;
    --danger-color:#dc3545; --border-color:#dee2e6; --shadow:0 0.5rem 1rem rgba(0,0,0,0.15);
}
[data-theme="dark"] {
    --bg-primary:#1a1a1a; --bg-secondary:#2d2d2d; --text-primary:#ffffff;
    --text-secondary:#adb5bd; --primary-color:#4dabf7; --success-color:#51cf66;
    --danger-color:#ff6b6b; --border-color:#444; --shadow:0 0.5rem 1rem rgba(0,0,0,0.5);
}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif;}
body{height:100vh;display:flex;justify-content:center;align-items:center;background:var(--bg-primary);transition:all 0.3s;}
.container{position:relative;width:100%;max-width:450px;text-align:center;}
.splash-logo{width:150px;opacity:0;transform:scale(0.5);animation:logoAnim 1s forwards;}
@keyframes logoAnim{to{opacity:1;transform:scale(1);}}
.splash-text{font-size:2.5rem;font-weight:700;color:var(--primary-color);margin-top:15px;opacity:0;animation:textAnim 1s 0.5s forwards;}
.tagline{font-size:1rem;color:var(--text-secondary);margin-top:10px;opacity:0;animation:textAnim 1s 1s forwards;}
@keyframes textAnim{to{opacity:1;}}
.login-box{display:none;background:var(--bg-secondary);padding:40px 30px;border-radius:20px;box-shadow:var(--shadow);animation:fadeIn 0.5s ease-in;}
.login-box.active{display:block;}
h2{margin-bottom:25px;color:var(--primary-color);}
input{width:100%;padding:14px 18px;margin:10px 0;border:1px solid var(--border-color);border-radius:12px;font-size:1rem;transition:0.3s;background:var(--bg-primary);color:var(--text-primary);}
input:focus{outline:none;border-color:var(--primary-color);box-shadow:0 0 0 3px rgba(0,123,255,0.2);}
.password-wrapper{position:relative;}
.toggle-password{position:absolute;right:15px;top:50%;transform:translateY(-50%);cursor:pointer;font-size:1.2rem;color:var(--text-secondary);}
button{width:100%;padding:14px;border:none;border-radius:25px;background:var(--primary-color);color:#fff;font-size:1rem;font-weight:600;cursor:pointer;transition:all 0.3s;margin-top:15px;}
button:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(0,123,255,0.4);}
.alert{padding:12px;margin:10px 0;border-radius:10px;font-weight:500;color:#fff;display:none;opacity:0;transition:0.5s;}
.alert-danger{background:var(--danger-color);}
.alert-success{background:var(--success-color);}
.checkbox-wrapper{display:flex;align-items:center;margin-top:10px;font-size:0.9rem;color:var(--text-primary);cursor:pointer;user-select:none;}
.checkbox-wrapper input{margin-right:8px;width:auto;}
.theme-toggle { position: fixed; top: 20px;right: 20px; width: 50px;height: 50px; border-radius: 50%; background: var(--bg-primary); border: 2px solid var(--primary-color);font-size: 1.5rem;display: flex;align-items: center;justify-content: center; cursor: pointer;transition: all 0.3s ease; z-index: 1000;}
.theme-toggle:hover{transform: scale(1.1); box-shadow: 0 0 15px var(--primary-color);}
@keyframes fadeIn{from{opacity:0;transform:translateY(20px);}to{opacity:1;transform:translateY(0);}}
</style>
</head>
<body>
<div class="container">
    <button class="theme-toggle" id="themeToggle">🌙</button>
    <div id="splashScreen">
        <img src="{{ url_for('static', filename='orphanage logo.jpg') }}" class="splash-logo" alt="Logo">
        <div class="splash-text">Hope Orphanage</div>
        <div class="tagline">Empowering lives, one child at a time...</div>
    </div>
    <div id="loginBox" class="login-box">
        <h2>Login</h2>
        <div class="alert alert-danger" id="alertBox"></div>
        <div class="alert alert-success" id="successBox"></div>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <div class="password-wrapper">
                <input type="password" name="password" id="password" placeholder="Password" required>
                <span class="toggle-password" onclick="togglePassword()">👁️</span>
            </div>
            <label class="checkbox-wrapper">
                <input type="checkbox" name="remember"> Remember Me
            </label>
            <button type="submit">Login</button>
        </form>
    </div>
</div>

<script>
// Splash -> Login
setTimeout(()=>{
    document.getElementById('splashScreen').style.opacity = '0';
    setTimeout(()=>{
        document.getElementById('splashScreen').style.display='none';
        document.getElementById('loginBox').classList.add('active');
    },500);
},3500);

// Toggle password eye
function togglePassword(){
    const pw=document.getElementById('password');
    const toggle=document.querySelector('.toggle-password');
    if(pw.type==='password'){pw.type='text';toggle.innerText='🙈';}
    else{pw.type='password';toggle.innerText='👁️';}
}

// Theme toggle
const themeBtn = document.getElementById('themeToggle');
const currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);
themeBtn.textContent = currentTheme==='light'?'🌙':'☀️';
themeBtn.addEventListener('click',()=>{
    const newTheme = document.documentElement.getAttribute('data-theme')==='light'?'dark':'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeBtn.textContent = newTheme==='light'?'🌙':'☀️';
});

// Show messages if any
{% if error %}
const alertBox=document.getElementById('alertBox');
alertBox.innerText="{{ error }}";
alertBox.style.display='block';
{% endif %}
{% if success %}
const successBox=document.getElementById('successBox');
successBox.innerText="{{ success }}";
successBox.style.display='block';

// Redirect to dashboard after 2 seconds
setTimeout(()=>{ window.location.href="{{ url_for('dashboard') }}"; }, 2000);
{% endif %}
</script>
</body>
</html>
"""

@app.route('/', methods=['GET','POST'])
def login():
    error=None
    success=None
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        remember=request.form.get('remember')
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username]==password:
            session['user']=username
            if remember: session.permanent=True
            success = "✅ Successfully Logged In!"
            return render_template_string(HTML_TEMPLATE, success=success)
        else: error='❌ Invalid credentials!'
    return render_template_string(HTML_TEMPLATE,error=error)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    # Redirect to your existing dashboard template
    return redirect("http://127.0.0.1:5000/")  # Opens the main dashboard

if __name__=="__main__":
    print("🚀 Hope Orphanage Splash+Login started")
    app.run(debug=True, port=5008)










