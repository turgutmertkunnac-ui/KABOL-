from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexus_secret_key_123!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/nexus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Veritabanı Modelleri
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=False)

with app.app_context():
    db.create_all()

# ----------------- KÖK DİZİN (Test İçin) -----------------
@app.route('/')
def home():
    return "Nexus SMP Server Active!"

# ----------------- API ENDPOINT'LERİ -----------------
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Eksik bilgi!'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'status': 'error', 'message': 'Bu kullanıcı adı zaten alınmış!'}), 400

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Kayıt başarılı!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            return jsonify({'status': 'success', 'message': 'Giriş başarılı!', 'username': user.username})
        else:
            return jsonify({'status': 'error', 'message': 'Kullanıcı adı veya şifre hatalı!'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ----------------- SOCKET.IO -----------------
@socketio.on('ping_server')
def handle_ping(data):
    username = data.get('user', 'Anonim')
    message = data.get('message', '')

    if message:
        new_msg = Message(username=username, content=message)
        db.session.add(new_msg)
        db.session.commit()

        emit('pong_client', {'user': username, 'message': message}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app)
