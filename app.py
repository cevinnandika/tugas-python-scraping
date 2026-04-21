"""
MONOLITH DEMO - GABUNGAN SEMUA FITUR
1. Web Server Socket (tanpa framework)
2. Flask Dasar
3. CRUD App
4. WebSocket + Web Scraping
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_socketio import SocketIO, emit
import requests
from bs4 import BeautifulSoup
import pandas as pd
import threading
import socket
import os
from urllib.parse import urlparse, parse_qs

# ============================================================
# INISIALISASI FLASK + WEBSOCKET
# ============================================================
app = Flask(__name__)
app.secret_key = 'rahasia_crud_123'
socketio = SocketIO(app)

# ============================================================
# DATABASE MAHASISWA (dari CRUD)
# ============================================================
daftar_mahasiswa = [
    {"id": 1, "nama": "Andi Wijaya", "nim": "20230001", "jurusan": "Teknik Informatika", "angkatan": 2023},
    {"id": 2, "nama": "Budi Santoso", "nim": "20230002", "jurusan": "Sistem Informasi", "angkatan": 2023},
    {"id": 3, "nama": "Citra Dewi", "nim": "20230003", "jurusan": "Teknik Komputer", "angkatan": 2023},
]

def get_next_id():
    if not daftar_mahasiswa:
        return 1
    return max(m["id"] for m in daftar_mahasiswa) + 1

def find_mahasiswa_by_id(mahasiswa_id):
    for m in daftar_mahasiswa:
        if m["id"] == mahasiswa_id:
            return m
    return None

# ============================================================
# CRUD ROUTES (dari 03_crud_app)
# ============================================================

@app.route('/')
def index():
    return render_template('index.html', mahasiswa=daftar_mahasiswa)

@app.route('/tambah', methods=['GET', 'POST'])
def tambah():
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        nim = request.form.get('nim', '').strip()
        jurusan = request.form.get('jurusan', '').strip()
        angkatan = request.form.get('angkatan', '').strip()
        
        if not nama or not nim or not jurusan or not angkatan:
            flash('Semua field harus diisi!', 'error')
            return redirect(url_for('tambah'))
        
        for m in daftar_mahasiswa:
            if m['nim'] == nim:
                flash(f'NIM {nim} sudah terdaftar!', 'error')
                return redirect(url_for('tambah'))
        
        data_baru = {
            "id": get_next_id(),
            "nama": nama,
            "nim": nim,
            "jurusan": jurusan,
            "angkatan": int(angkatan) if angkatan.isdigit() else 2023
        }
        daftar_mahasiswa.append(data_baru)
        flash(f'Data mahasiswa {nama} berhasil ditambahkan!', 'success')
        return redirect(url_for('index'))
    
    return render_template('create.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    mahasiswa = find_mahasiswa_by_id(id)
    if not mahasiswa:
        flash('Data mahasiswa tidak ditemukan!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        nim = request.form.get('nim', '').strip()
        jurusan = request.form.get('jurusan', '').strip()
        angkatan = request.form.get('angkatan', '').strip()
        
        if not nama or not nim or not jurusan or not angkatan:
            flash('Semua field harus diisi!', 'error')
            return redirect(url_for('edit', id=id))
        
        for m in daftar_mahasiswa:
            if m['nim'] == nim and m['id'] != id:
                flash(f'NIM {nim} sudah digunakan oleh mahasiswa lain!', 'error')
                return redirect(url_for('edit', id=id))
        
        mahasiswa['nama'] = nama
        mahasiswa['nim'] = nim
        mahasiswa['jurusan'] = jurusan
        mahasiswa['angkatan'] = int(angkatan) if angkatan.isdigit() else 2023
        flash(f'Data mahasiswa {nama} berhasil diupdate!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit.html', mhs=mahasiswa)

@app.route('/hapus/<int:id>')
def hapus(id):
    mahasiswa = find_mahasiswa_by_id(id)
    if mahasiswa:
        nama = mahasiswa['nama']
        daftar_mahasiswa.remove(mahasiswa)
        flash(f'Data mahasiswa {nama} berhasil dihapus!', 'success')
    else:
        flash('Data tidak ditemukan!', 'error')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return redirect(url_for('index'))
    results = []
    for m in daftar_mahasiswa:
        if keyword.lower() in m['nama'].lower() or keyword in m['nim']:
            results.append(m)
    return render_template('index.html', mahasiswa=results, search_keyword=keyword)

# ============================================================
# FITUR FLASK DASAR (dari 02_flask_dasar)
# ============================================================

@app.route('/hello/<name>')
def say_hello(name):
    return f"""
    <h1>Hello {name}!</h1>
    <p>Flask otomatis menangkap parameter <code>name</code> dari URL.</p>
    <a href="/">Kembali ke Home</a>
    """

@app.route('/user/<int:user_id>')
def get_user(user_id):
    users = {
        1: {"name": "Alice", "email": "alice@example.com"},
        2: {"name": "Bob", "email": "bob@example.com"},
        3: {"name": "Charlie", "email": "charlie@example.com"}
    }
    user = users.get(user_id)
    if user:
        return f"""
        <h1>User Profile</h1>
        <p>ID: {user_id}</p>
        <p>Name: {user['name']}</p>
        <p>Email: {user['email']}</p>
        <a href="/">Back</a>
        """
    return f"<h1>User {user_id} not found</h1>", 404

@app.route('/query')
def handle_query():
    nama = request.args.get('nama', 'Guest')
    umur = request.args.get('umur', '?')
    all_params = dict(request.args)
    return f"""
    <h1>Query Parameters</h1>
    <p>Nama: {nama}</p>
    <p>Umur: {umur}</p>
    <p>Semua parameter: {all_params}</p>
    <a href="/">Back</a>
    """

@app.route('/form', methods=['GET', 'POST'])
def handle_form():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        return f"""
        <h1>Form Submitted!</h1>
        <p>Name: {name}</p>
        <p>Email: {email}</p>
        <p>Message: {message}</p>
        <a href="/form">Back to Form</a>
        """
    return """
    <h1>Contact Form</h1>
    <form method="POST">
        <p>Name: <input type="text" name="name" required></p>
        <p>Email: <input type="email" name="email" required></p>
        <p>Message: <textarea name="message" rows="4" cols="30"></textarea></p>
        <p><input type="submit" value="Send"></p>
    </form>
    <a href="/">Home</a>
    """

@app.route('/api/data')
def api_data():
    return jsonify({
        "status": "success",
        "message": "Ini adalah response JSON dari Flask",
        "data": {
            "framework": "Flask",
            "version": "2.3.x",
            "features": ["Routing", "Templating", "Request Parsing"]
        }
    })

# ============================================================
# SCRAPING KE UMSIDA (dari app.py scraping punya lu)
# ============================================================

def scraping_data():
    url = "https://admisi.umsida.ac.id/fortama/"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except:
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    if table is None:
        return []
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [c.text.strip() for c in cols]
        if cols:
            data.append(cols)
    # simpan ke file
    os.makedirs('data', exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv('data/hasil.csv', index=False)
    df.to_json('data/hasil.json', orient='records', indent=4)
    return data

@app.route("/scraping-umsida")
def scraping_umsida():
    data = scraping_data()
    return render_template("scrape_result.html", data=data)

# ============================================================
# WEBSOCKET + WEB SCRAPING (REAL-TIME)
# ============================================================

def scrape_websocket(url, sid):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else 'Tidak ada title'
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3'])[:5]:
            headings.append(h.get_text(strip=True))
        socketio.emit('scrape_result', {
            'status': 'success',
            'url': url,
            'title': title,
            'headings': headings
        }, room=sid)
    except Exception as e:
        socketio.emit('scrape_result', {
            'status': 'error',
            'url': url,
            'message': str(e)
        }, room=sid)

@socketio.on('start_scraping')
def handle_start_scraping(data):
    url = data.get('url')
    sid = request.sid
    emit('scraping_started', {'message': f'Memulai scraping untuk: {url}'})
    thread = threading.Thread(target=scrape_websocket, args=(url, sid))
    thread.daemon = True
    thread.start()

@app.route("/scrape-websocket")
def scrape_websocket_page():
    return render_template("scrape.html")

# ============================================================
# DEMO WEB SERVER SOCKET (Simulasi)
# ============================================================

@app.route("/socket-demo")
def socket_demo():
    """Menampilkan info tentang web server socket yang dibuat sebelumnya"""
    return """
    <h1>Web Server Socket Demo</h1>
    <p>Sebelumnya kita membuat web server manual dengan socket di port 8080 dan 8081.</p>
    <p>Kelebihan Flask dibanding socket manual:</p>
    <ul>
        <li>✅ Routing otomatis</li>
        <li>✅ Parsing parameter</li>
        <li>✅ Debug mode</li>
        <li>✅ WebSocket support</li>
    </ul>
    <p>Web server socket manual bisa dijalankan terpisah dengan:</p>
    <pre>
cd 01_web_server_so...
python simple_server.py  # atau advanced_server.py
    </pre>
    <a href="/">Kembali ke Home</a>
    """

# ============================================================
# ERROR HANDLING
# ============================================================

@app.errorhandler(404)
def page_not_found(error):
    return """
    <h1>404 - Halaman Tidak Ditemukan</h1>
    <p>URL yang Anda cari tidak tersedia.</p>
    <a href="/">Kembali ke Home</a>
    """, 404

# ============================================================
# MENJALANKAN SERVER
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("📦 MONOLITH DEMO - SEMUA FITUR DALAM SATU APLIKASI")
    print("=" * 60)
    print("✅ CRUD Mahasiswa      : http://localhost:5000/")
    print("✅ Flask Dasar         : http://localhost:5000/hello/Andi")
    print("✅ WebSocket Scraper   : http://localhost:5000/scrape-websocket")
    print("✅ Scraping UMSIDA     : http://localhost:5000/scraping-umsida")
    print("✅ Socket Demo         : http://localhost:5000/socket-demo")
    print("=" * 60)
    socketio.run(app, debug=True, host='localhost', port=5000)