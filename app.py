from datetime import datetime
import os
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexus_smp_central_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Skinlerin kaydedileceği klasör
SKIN_DIR = os.path.join(app.root_path, 'static', 'skins')
os.makedirs(SKIN_DIR, exist_ok=True)

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins='*')


# --- VERİTABANI MODELLERİ ---
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(120), nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), nullable=False)
  content = db.Column(db.Text, nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
  db.create_all()


# --- KAYIT (REGISTER) API ---
@app.route('/api/register', methods=['POST'])
def register():
  data = request.get_json() or {}
  username = data.get('username', '').strip()
  password = data.get('password', '').strip()

  if not username or not password:
    return jsonify({'status': 'error', 'message': 'Tüm alanları doldurun!'}), 400

  existing_user = User.query.filter_by(username=username).first()
  if existing_user:
    return jsonify(
        {'status': 'error', 'message': 'Bu kullanıcı adı zaten alınmış!'}
    ), 400

  new_user = User(username=username, password=password)
  db.session.add(new_user)
  db.session.commit()

  return jsonify(
      {'status': 'success', 'message': 'Kayıt başarılı! Giriş yapabilirsiniz.'}
  )


# --- GİRİŞ (LOGIN) API ---
@app.route('/api/login', methods=['POST'])
def login():
  data = request.get_json() or {}
  username = data.get('username', '').strip()
  password = data.get('password', '').strip()

  user = User.query.filter_by(username=username).first()

  if user and user.password == password:
    return jsonify({
        'status': 'success',
        'message': 'Giriş başarılı!',
        'username': user.username,
    })

  return jsonify(
      {'status': 'error', 'message': 'Kullanıcı adı veya şifre hatalı!'}
  ), 401


# --- SKIN YÜKLEME VE SERVİS ETME API ---
@app.route('/api/upload_skin', methods=['POST'])
def upload_skin():
  username = request.form.get('username')
  if 'file' not in request.files or not username:
    return jsonify({'status': 'error', 'message': 'Geçersiz istek!'}), 400

  file = request.files['file']
  if file and file.filename.endswith('.png'):
    save_path = os.path.join(SKIN_DIR, f'{username}.png')
    file.save(save_path)
    return jsonify(
        {'status': 'success', 'message': 'Skin başarıyla yüklendi!'}
    )

  return jsonify({'status': 'error', 'message': 'Sadece .png yükleyebilirsiniz!'}), 400


@app.route('/static/skins/<filename>')
def serve_skin(filename):
  return send_from_directory(SKIN_DIR, filename)


# --- SOHBET MESAJ GEÇMİŞİ API ---
@app.route('/api/messages', methods=['GET'])
def get_messages():
  messages = Message.query.order_by(Message.timestamp.asc()).limit(100).all()
  return jsonify([{
      'username': m.username,
      'content': m.content,
      'timestamp': m.timestamp.strftime('%H:%M'),
  } for m in messages])


# --- CANLI SOHBET SOCKETIO ---
@socketio.on('send_message')
def handle_message(data):
  username = data.get('username')
  content = data.get('content', '').strip()

  if username and content:
    msg = Message(username=username, content=content)
    db.session.add(msg)
    db.session.commit()

    emit(
        'receive_message',
        {
            'username': username,
            'content': content,
            'timestamp': msg.timestamp.strftime('%H:%M'),
        },
        broadcast=True,
    )


if __name__ == '__main__':
  # 0.0.0.0 sayesinde yerel ağdaki/dışarıdaki diğer istemciler de bağlanabilir
  socketio.run(app, host='0.0.0.0', port=5000, debug=True)