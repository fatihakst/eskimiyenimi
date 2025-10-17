import os
import json
import random
import requests  # Yeni kütüphaneyi içeri aktar
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

# --- JSONBIN AYARLARI (RENDER'DAN GELECEK) ---
JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY')
BIN_ID = os.environ.get('JSONBIN_BIN_ID')
BIN_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    'Content-Type': 'application/json',
    'X-Master-Key': JSONBIN_API_KEY
}

basedir = os.path.abspath(os.path.dirname(__file__))


def verileri_yukle():
    json_yolu = os.path.join(basedir, 'tarih.json')
    with open(json_yolu, 'r', encoding='utf-8') as f:
        return json.load(f)


TUM_OLAYLAR = verileri_yukle()


@app.route('/')
def serve_index(): return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path): return send_from_directory(app.static_folder, path)


@app.route('/yeni-olay-cifti', methods=['POST'])
def yeni_olay_cifti_getir():
    # Bu fonksiyonun içeriği aynı, değişiklik yok
    gelen_veri = request.get_json()
    kullanilmis_idler = set(gelen_veri.get('kullanilmis_idler', []))
    sabit_olay = gelen_veri.get('sabit_olay', None)
    kullanilabilir_olaylar = [olay for olay in TUM_OLAYLAR if olay['id'] not in kullanilmis_idler]
    if (len(kullanilabilir_olaylar) < 2 and not sabit_olay) or (len(kullanilabilir_olaylar) < 1 and sabit_olay):
        return jsonify({"hata": "Tebrikler!"}), 400
    if sabit_olay: olay1 = next((olay for olay in TUM_OLAYLAR if olay['id'] == sabit_olay['id']), None)
    if not sabit_olay: olay1 = random.choice(kullanilabilir_olaylar)
    aday_olaylar = [o for o in kullanilabilir_olaylar if o['id'] != olay1['id']]
    if not aday_olaylar: return jsonify({"hata": "Rakip yok"}), 400
    olay2 = random.choice(aday_olaylar)
    return jsonify({"olay1": olay1, "olay2": olay2})


# --- YENİ LİDERLİK TABLOSU API'LARI (JSONBIN) ---
@app.route('/get-leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        # JSONBin'den en son veriyi oku
        res = requests.get(f"{BIN_URL}/latest", headers=HEADERS)
        res.raise_for_status()  # Hata varsa yakala
        return jsonify(res.json()['record'])
    except Exception as e:
        print(f"Liderlik tablosu okuma hatası: {e}")
        return jsonify([])  # Hata olursa boş liste döndür


@app.route('/add-score', methods=['POST'])
def add_score():
    try:
        # Önce mevcut liderlik tablosunu oku
        res = requests.get(f"{BIN_URL}/latest", headers=HEADERS)
        res.raise_for_status()
        skorlar = res.json()['record']

        # Yeni skoru ekle, sırala ve kes
        gelen_veri = request.get_json()
        yeni_skor = {"name": gelen_veri.get('name'), "score": gelen_veri.get('score')}
        skorlar.append(yeni_skor)
        skorlar.sort(key=lambda x: x['score'], reverse=True)
        guncel_skorlar = skorlar[:100]

        # Güncellenmiş listeyi JSONBin'e geri yaz (üzerine yaz)
        update_res = requests.put(BIN_URL, headers=HEADERS, json=guncel_skorlar)
        update_res.raise_for_status()

        return jsonify({"mesaj": "Skor eklendi"}), 201
    except Exception as e:
        print(f"Skor ekleme hatası: {e}")
        return jsonify({"hata": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)