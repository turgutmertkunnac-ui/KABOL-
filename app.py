import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexus_secret_key_123'

# Vercel dosya sistemine yazmayı engelleyebileceği için /tmp klasörünü kullanıyoruz
db_path = os.path.join('/tmp', 'nexus.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Örnek Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "Nexus SMP Serverless Sunucu Aktif!"

@app.route('/api/status')
def status():
    return jsonify({"status": "online", "server": "Nexus SMP"})

@socketio.on('ping_server')
def handle_ping(data):
    emit('pong_client', {'message': 'Nexus SMP Bağlantısı Başarılı!'})

# Vercel WSGI Handler (Vercel'in uygulamayı çökmeksizin tetiklemesi için şarttır)
app = app

if __name__ == '__main__':
    socketio.run(app, debug=True)
