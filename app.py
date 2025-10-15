import os
import json
import random
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static')
CORS(app)

# --- VERİTABANI YAPILANDIRMASI (YENİ) ---
# Ortam değişkenlerinden veritabanı URL'sini al, eğer yoksa yerel bir dosya kullan (test için)
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local_leaderboard.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ... (Geri kalan kodun tamamı aynı, hiçbir değişiklik yok) ...

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    score = db.Column(db.Integer, nullable=False)

YAKINLIK_FAKTORU = 50
AYNI_YIL_IHTIMALI = 0.15

def verileri_yukle():
    with open('tarih.json', 'r', encoding='utf-8') as f:
        return json.load(f)
TUM_OLAYLAR = verileri_yukle()
YILLARA_GORE_OLAYLAR = defaultdict(list)
for olay in TUM_OLAYLAR:
    YILLARA_GORE_OLAYLAR[olay['yil']].append(olay)

@app.route('/')
def serve_index(): return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path): return send_from_directory(app.static_folder, path)

@app.route('/yeni-olay-cifti', methods=['POST'])
def yeni_olay_cifti_getir():
    gelen_veri = request.get_json()
    kullanilmis_idler = set(gelen_veri.get('kullanilmis_idler', []))
    sabit_olay = gelen_veri.get('sabit_olay', None)
    kullanilabilir_olaylar = [olay for olay in TUM_OLAYLAR if olay['id'] not in kullanilmis_idler]
    if len(kullanilabilir_olaylar) < 2 and not sabit_olay: return jsonify({"hata": "Tebrikler!"}), 400
    if len(kullanilabilir_olaylar) < 1 and sabit_olay: return jsonify({"hata": "Tebrikler!"}), 400
    if not sabit_olay and random.random() < AYNI_YIL_IHTIMALI:
        uygun_yillar = [yil for yil, olaylar in YILLARA_GORE_OLAYLAR.items() if len([o for o in olaylar if o['id'] not in kullanilmis_idler]) >= 2]
        if uygun_yillar:
            secilen_yil = random.choice(uygun_yillar)
            uygun_olaylar = [o for o in YILLARA_GORE_OLAYLAR[secilen_yil] if o['id'] not in kullanilmis_idler]
            olay1, olay2 = random.sample(uygun_olaylar, 2)
            return jsonify({"olay1": olay1, "olay2": olay2})
    if sabit_olay: olay1 = sabit_olay
    else: olay1 = random.choice(kullanilabilir_olaylar)
    try:
        aday_olaylar = [o for o in kullanilabilir_olaylar if o['id'] != olay1['id'] and o['yil'] != olay1['yil']]
        if not aday_olaylar: raise ValueError("Aday bulunamadı.")
        agirliklar = [1 / (abs(aday['yil'] - olay1['yil']) + YAKINLIK_FAKTORU) for aday in aday_olaylar]
        olay2 = random.choices(aday_olaylar, weights=agirliklar, k=1)[0]
    except Exception:
        aday_olaylar = [o for o in kullanilabilir_olaylar if o['id'] != olay1['id']]
        if not aday_olaylar: return jsonify({"hata": "Rakip yok"}), 400
        olay2 = random.choice(aday_olaylar)
    return jsonify({"olay1": olay1, "olay2": olay2})

@app.route('/get-leaderboard', methods=['GET'])
def get_leaderboard():
    scores = Score.query.order_by(Score.score.desc()).limit(100).all()
    leaderboard = [{"name": score.name, "score": score.score} for score in scores]
    return jsonify(leaderboard)

@app.route('/add-score', methods=['POST'])
def add_score():
    data = request.get_json(); name = data.get('name'); score = data.get('score')
    if not name or score is None: return jsonify({"hata": "İsim ve skor gerekli"}), 400
    new_score = Score(name=name, score=score)
    db.session.add(new_score); db.session.commit()
    return jsonify({"mesaj": "Skor eklendi"}), 201

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)