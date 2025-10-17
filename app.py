import os
import json
import random
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static')
CORS(app)

# --- VERİTABANI YAPILANDIRMASI ---
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local_leaderboard.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- VERİTABANI MODELİ ---
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    score = db.Column(db.Integer, nullable=False)


# --- OYUN AYARLARI (GERİ GELDİ!) ---
YAKINLIK_FAKTORU = 50
AYNI_YIL_IHTIMALI = 0.16

basedir = os.path.abspath(os.path.dirname(__file__))


def verileri_yukle():
    json_yolu = os.path.join(basedir, 'tarih.json')
    with open(json_yolu, 'r', encoding='utf-8') as f:
        return json.load(f)


TUM_OLAYLAR = verileri_yukle()
# Aynı yıl algoritması için veriyi başlangıçta hazırla
YILLARA_GORE_OLAYLAR = defaultdict(list)
for olay in TUM_OLAYLAR:
    YILLARA_GORE_OLAYLAR[olay['yil']].append(olay)


# --- ANA API ADRESLERİ ---
@app.route('/')
def serve_index(): return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path): return send_from_directory(app.static_folder, path)


@app.route('/yeni-olay-cifti', methods=['POST'])
def yeni_olay_cifti_getir():
    try:
        gelen_veri = request.get_json()
        kullanilmis_idler = set(gelen_veri.get('kullanilmis_idler', []))
        sabit_olay = gelen_veri.get('sabit_olay', None)
        kullanilabilir_olaylar = [olay for olay in TUM_OLAYLAR if olay['id'] not in kullanilmis_idler]

        if (len(kullanilabilir_olaylar) < 2 and not sabit_olay) or (len(kullanilabilir_olaylar) < 1 and sabit_olay):
            return jsonify({"hata": "Tebrikler!"}), 400

        # 1. Adım: Aynı Yıl Algoritmasını Dene
        if not sabit_olay and random.random() < AYNI_YIL_IHTIMALI:
            uygun_yillar = [yil for yil, olaylar in YILLARA_GORE_OLAYLAR.items() if
                            len([o for o in olaylar if o['id'] not in kullanilmis_idler]) >= 2]
            if uygun_yillar:
                secilen_yil = random.choice(uygun_yillar)
                uygun_olaylar = [o for o in YILLARA_GORE_OLAYLAR[secilen_yil] if o['id'] not in kullanilmis_idler]
                olay1, olay2 = random.sample(uygun_olaylar, 2)
                return jsonify({"olay1": olay1, "olay2": olay2})

        # 2. Adım: Şampiyonu Belirle
        if sabit_olay:
            olay1 = next((olay for olay in TUM_OLAYLAR if olay['id'] == sabit_olay['id']), None)
            if not olay1: sabit_olay = None

        if not sabit_olay:
            olay1 = random.choice(kullanilabilir_olaylar)

        # 3. Adım: Akıllı Zorluk Algoritmasını (Plan A) Dene
        try:
            aday_olaylar = [o for o in kullanilabilir_olaylar if o['id'] != olay1['id'] and o['yil'] != olay1['yil']]
            if not aday_olaylar: raise ValueError("Farklı yılda aday bulunamadı.")
            agirliklar = [1 / (abs(aday['yil'] - olay1['yil']) + YAKINLIK_FAKTORU) for aday in aday_olaylar]
            olay2 = random.choices(aday_olaylar, weights=agirliklar, k=1)[0]
        # 4. Adım: Eğer Plan A çalışmazsa, Güvenilir B Planı'nı kullan
        except Exception:
            aday_olaylar = [o for o in kullanilabilir_olaylar if o['id'] != olay1['id']]
            if not aday_olaylar: return jsonify({"hata": "Rakip yok"}), 400
            olay2 = random.choice(aday_olaylar)

        return jsonify({"olay1": olay1, "olay2": olay2})

    except Exception as e:
        # En kötü senaryoda bile sunucunun çökmesini engelle
        print(f"!!! KRİTİK HATA /yeni-olay-cifti: {e}")
        return jsonify({"hata": "Sunucuda kritik bir hata oluştu."}), 500


# ... (Diğer /get-leaderboard ve /add-score fonksiyonları aynı kalacak) ...

@app.route('/get-leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        scores = Score.query.order_by(Score.score.desc()).limit(100).all()
        leaderboard = [{"name": score.name, "score": score.score} for score in scores]
        return jsonify(leaderboard)
    except Exception as e:
        print(f"Liderlik tablosu hatası: {e}")
        return jsonify([])


@app.route('/add-score', methods=['POST'])
def add_score():
    try:
        data = request.get_json();
        name = data.get('name');
        score = data.get('score')
        if not name or score is None: return jsonify({"hata": "İsim ve skor gerekli"}), 400
        new_score = Score(name=name, score=score)
        db.session.add(new_score);
        db.session.commit()
        return jsonify({"mesaj": "Skor eklendi"}), 201
    except Exception as e:
        print(f"Skor ekleme hatası: {e}")
        return jsonify({"hata": str(e)}), 500


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)