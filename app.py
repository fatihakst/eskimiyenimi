import json
import random
from flask import Flask, jsonify, request, send_from_directory # send_from_directory eklendi
from flask_cors import CORS
from collections import defaultdict

app = Flask(__name__, static_folder='static') # static_folder belirtildi
CORS(app)

# ... (Diğer kodların hepsi aynı kalacak, aşağıya sadece yeni eklenen kısmı yazıyorum) ...
# ... (YAKINLIK_FAKTORU, verileri_yukle, vb. hepsi aynı) ...

YAKINLIK_FAKTORU = 50
AYNI_YIL_IHTIMALI = 0.15

def verileri_yukle():
    with open('tarih.json', 'r', encoding='utf-8') as f:
        return json.load(f)

TUM_OLAYLAR = verileri_yukle()
YILLARA_GORE_OLAYLAR = defaultdict(list)
for olay in TUM_OLAYLAR:
    YILLARA_GORE_OLAYLAR[olay['yil']].append(olay)

# --- YENİ EKLENEN KISIM (ANA SAYFAYI GÖSTERMEK İÇİN) ---
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)
# --- YENİ KISIM BİTİŞ ---

@app.route('/yeni-olay-cifti', methods=['POST'])
def yeni_olay_cifti_getir():
    gelen_veri = request.get_json()
    kullanilmis_idler = set(gelen_veri.get('kullanilmis_idler', []))
    sabit_olay = gelen_veri.get('sabit_olay', None)

    kullanilabilir_olaylar = [olay for olay in TUM_OLAYLAR if olay['id'] not in kullanilmis_idler]

    if len(kullanilabilir_olaylar) < 2 and not sabit_olay:
        return jsonify({"hata": "Tebrikler, tüm olayları tamamladınız!"}), 400
    if len(kullanilabilir_olaylar) < 1 and sabit_olay:
         return jsonify({"hata": "Tebrikler, tüm olayları tamamladınız!"}), 400

    if not sabit_olay and random.random() < AYNI_YIL_IHTIMALI:
        uygun_yillar = [
            yil for yil, olaylar in YILLARA_GORE_OLAYLAR.items()
            if len([o for o in olaylar if o['id'] not in kullanilmis_idler]) >= 2
        ]
        if uygun_yillar:
            secilen_yil = random.choice(uygun_yillar)
            uygun_olaylar = [o for o in YILLARA_GORE_OLAYLAR[secilen_yil] if o['id'] not in kullanilmis_idler]
            olay1, olay2 = random.sample(uygun_olaylar, 2)
            return jsonify({"olay1": olay1, "olay2": olay2})

    if sabit_olay:
        olay1 = sabit_olay
    else:
        olay1 = random.choice(kullanilabilir_olaylar)

    try:
        aday_olaylar = [o for o in kullanilabilir_olaylar if o['id'] != olay1['id'] and o['yil'] != olay1['yil']]
        if not aday_olaylar: raise ValueError("Farklı yılda aday bulunamadı.")
        agirliklar = [1 / (abs(aday['yil'] - olay1['yil']) + YAKINLIK_FAKTORU) for aday in aday_olaylar]
        olay2 = random.choices(aday_olaylar, weights=agirliklar, k=1)[0]
    except Exception:
        aday_olaylar = [o for o in kullanilmis_idler if o['id'] != olay1['id']]
        if not aday_olaylar: return jsonify({"hata": "Rakip bulunamadı"}), 400
        olay2 = random.choice(aday_olaylar)

    return jsonify({"olay1": olay1, "olay2": olay2})

if __name__ == '__main__':
    app.run(debug=True)