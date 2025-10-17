import os
import json
import random
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

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
    # Sadece basit ve güvenilir seçim mantığı
    gelen_veri = request.get_json()
    kullanilmis_idler = set(gelen_veri.get('kullanilmis_idler', []))
    sabit_olay = gelen_veri.get('sabit_olay', None)
    kullanilabilir_olaylar = [olay for olay in TUM_OLAYLAR if olay['id'] not in kullanilmis_idler]

    if (len(kullanilabilir_olaylar) < 2 and not sabit_olay) or (len(kullanilabilir_olaylar) < 1 and sabit_olay):
        return jsonify({"hata": "Tebrikler!"}), 400

    if sabit_olay:
        olay1 = next((olay for olay in TUM_OLAYLAR if olay['id'] == sabit_olay['id']), None)
        if not olay1: sabit_olay = None

    if not sabit_olay:
        olay1 = random.choice(kullanilabilir_olaylar)

    aday_olaylar = [o for o in kullanilabilir_olaylar if o['id'] != olay1['id']]
    if not aday_olaylar:
        return jsonify({"hata": "Rakip yok"}), 400

    olay2 = random.choice(aday_olaylar)

    return jsonify({"olay1": olay1, "olay2": olay2})


if __name__ == '__main__':
    app.run(debug=True)