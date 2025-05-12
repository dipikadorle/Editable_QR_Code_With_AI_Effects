from flask import Flask, render_template, request, redirect, url_for, session, flash
import qrcode
import os
import uuid
from database.db import get_db_connection, hash_password, verify_password
from PIL import Image
from gtts import gTTS

# ✅ Correct Flask Initialization
app = Flask(__name__)
app.secret_key = 'dipika123'

# ✅ Directories
QR_FOLDER = "static/qrcodes/"
AUDIO_FOLDER = "static/audio/"
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = hash_password(password)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.fetchall()
        cursor.close()
        conn.close()

        if user and verify_password(password, user['password']):
            session['user_id'] = user['id']
            flash("Login Successful", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Email or Password 🚫", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM qr_codes WHERE user_id = %s", (session['user_id'],))
    qr_codes = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', qr_codes=qr_codes)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    url = request.form['url']
    short_url = str(uuid.uuid4())[:8]

    fill_color = request.form.get('fill_color') or 'black'
    back_color = request.form.get('back_color') or 'white'
    logo_file = request.files.get('logo')

    # ✅ Save to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO qr_codes (user_id, short_url, target_url) VALUES (%s, %s, %s)", (session['user_id'], short_url, url))
    conn.commit()

    # ✅ Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGB')

    # ✅ Add logo if uploaded
    if logo_file and logo_file.filename != '':
        logo = Image.open(logo_file)
        logo = logo.resize((50, 50))
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        img.paste(logo, pos)

    # ✅ Save QR Code
    qr_path = os.path.join(QR_FOLDER, f"{short_url}.png")
    img.save(qr_path)

    # ✅ Generate Audio Description
    tts = gTTS(f"This QR code redirects you to {url}", lang='en')
    audio_path = os.path.join(AUDIO_FOLDER, f"{short_url}.mp3")
    tts.save(audio_path)

    cursor.close()
    conn.close()

    flash("QR Code Generated Successfully ✅", "success")
    return redirect('/dashboard')

@app.route('/qr/<short_url>')
def redirect_qr(short_url):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT target_url FROM qr_codes WHERE short_url = %s", (short_url,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return redirect(result['target_url'])
    else:
        return "Invalid QR Code"

@app.route('/update_qr', methods=['POST'])
def update_qr():
    short_url = request.form['short_url']
    new_url = request.form['new_url']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE qr_codes SET target_url = %s WHERE short_url = %s", (new_url, short_url))
    conn.commit()

    # ✅ Update Audio Description also
    tts = gTTS(f"This QR code now redirects you to {new_url}", lang='en')
    audio_path = os.path.join(AUDIO_FOLDER, f"{short_url}.mp3")
    tts.save(audio_path)

    cursor.close()
    conn.close()

    flash("QR Code Link Updated Successfully 🔥", "success")
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
