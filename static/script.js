const API_URL = 'http://127.0.0.1:5000/yeni-olay-cifti';
 const OYUN_SURESI = 15;

 // --- HTML ELEMENTLERİNİ SEÇME ---
 const anaMenuEl = document.getElementById('ana-menu'), oyunEkraniEl = document.getElementById('oyun-ekrani'), liderlikEkraniEl = document.getElementById('liderlik-ekrani');
 const screens = [anaMenuEl, oyunEkraniEl, liderlikEkraniEl];
 const baslatBtn = document.getElementById('baslat-btn'), liderlikBtn = document.getElementById('liderlik-btn'), liderlikListesiEl = document.getElementById('liderlik-listesi'), anaMenuyeDonBtn1 = document.getElementById('ana-menuye-don-btn-1'), anaMenuyeDonBtn2 = document.getElementById('ana-menuye-don-btn-2'), tekrarOynaBtn = document.getElementById('tekrar-oyna-btn'), oyuncuAdiInput = document.getElementById('oyuncu-adi-input'), skoruKaydetBtn = document.getElementById('skoru-kaydet-btn'), skorKayitFormu = document.getElementById('skor-kayit-formu');
 const skorEl = document.getElementById('skor'), zamanCubuguEl = document.getElementById('zaman-cubugu'), olay1AdEl = document.getElementById('olay1-ad'), olay1YilEl = document.getElementById('olay1-yil'), olay2AdEl = document.getElementById('olay2-ad'), olay2YilEl = document.getElementById('olay2-yil'), tahminButonlariEl = document.getElementById('tahmin-butonlari'), sonucMesajiEl = document.getElementById('sonuc-mesaji'), oyunBittiEl = document.getElementById('oyun-bitti'), oyunSonuBasligiEl = document.getElementById('oyun-sonu-basligi'), finalSkorEl = document.getElementById('final-skor'), cardsContainer = document.querySelector('.cards-container'), higherBtn = document.querySelector('.higher-btn'), lowerBtn = document.querySelector('.lower-btn'), ayniYilBtn = document.getElementById('ayni-yil-btn');
 const kart1El = document.getElementById('kart1');
 const kart2El = document.getElementById('kart2');

 // --- OYUN DEĞİŞKENLERİ ---
 let olay1, olay2, sabitOlay = null, skor = 0, kullanilmis_idler = [], zamanlayici, kalan_saniye, isProcessing = true;

 // --- EKRAN YÖNETİMİ ---
 function ekranGoster(ekranId) { screens.forEach(screen => screen.classList.toggle('active', screen.id === ekranId)); }

 // --- LİDERLİK TABLOSU ---
 function skorlariGetir() { return JSON.parse(localStorage.getItem('liderlikTablosu')) || []; }
 function skoruKaydet(yeniSkor, oyuncuAdi) { if (yeniSkor === 0) return; const skorlar = skorlariGetir(); const yeniGirdi = { name: oyuncuAdi, score: yeniSkor }; skorlar.push(yeniGirdi); skorlar.sort((a, b) => b.score - a.score); localStorage.setItem('liderlikTablosu', JSON.stringify(skorlar.slice(0, 100))); }
 function liderlikTablosunuGoster() { const skorlar = skorlariGetir(); liderlikListesiEl.innerHTML = ""; if (skorlar.length === 0) { liderlikListesiEl.innerHTML = '<div class="score-entry placeholder">Henüz hiç skor kaydedilmedi.</div>'; } else { skorlar.forEach((girdi, index) => { const scoreEntry = document.createElement('div'); scoreEntry.classList.add('score-entry'); scoreEntry.innerHTML = `<span class="rank">#${index + 1}</span><span class="name">${girdi.name}</span><span class="score">${girdi.score} Puan</span>`; liderlikListesiEl.appendChild(scoreEntry); }); } ekranGoster('liderlik-ekrani'); }

 // --- OYUN MANTIĞI ---
 function oyunuBaslat() {
     skor = 0; kullanilmis_idler = []; sabitOlay = null; skorEl.textContent = skor; oyunBittiEl.style.display = 'none'; cardsContainer.style.display = 'flex'; sonucMesajiEl.style.display = 'block'; zamanCubuguEl.parentElement.style.display = 'block'; skorKayitFormu.style.display = 'flex'; oyuncuAdiInput.value = '';
     ekranGoster('oyun-ekrani');
     yeniCiftGetir(true); // 'true' parametresi ilk tur olduğunu belirtir
 }

 async function yeniCiftGetir(isFirstRound = false) {
     isProcessing = true;
     // Kartları yeni tur için gizle
     if (!isFirstRound) {
         kart1El.classList.add('is-exiting-down');
         kart2El.classList.add('is-exiting-left');
     }

     let requestBody = { kullanilmis_idler: kullanilmis_idler, sabit_olay: sabitOlay };
     const response = await fetch(API_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestBody) });
     const data = await response.json();
     if (data.hata) return void oyunuKazan();

     olay1 = data.olay1;
     olay2 = data.olay2;

     // Animasyonun bitmesini bekle ve sonra veriyi yerleştir
     setTimeout(ekranaYerlestir, isFirstRound ? 50 : 500);
 }

 function ekranaYerlestir() {
     kullanilmis_idler.push(olay1.id);

     // Verileri Yükle
     olay1AdEl.textContent = olay1.olay;
     olay1YilEl.textContent = formatYil(olay1.yil);
     olay2AdEl.textContent = olay2.olay;
     olay2YilEl.textContent = '?';
     olay2YilEl.style.color = '#e94560';
     sonucMesajiEl.textContent = '';

     // Kartların animasyon sınıflarını temizle ve giriş animasyonuna hazırla
     kart1El.className = 'card is-entering';
     kart2El.className = 'card is-entering';

     // Çok kısa bir gecikmeyle giriş animasyonunu tetikle
     setTimeout(() => {
         kart1El.classList.remove('is-entering');
         kart2El.classList.remove('is-entering');
         zamanlayiciyiBaslat();
     }, 50);
 }

 function zamanlayiciyiBaslat() {
     kalan_saniye = OYUN_SURESI; zamanCubuguEl.style.transition = 'none'; zamanCubuguEl.style.width = '100%'; setTimeout(() => { zamanCubuguEl.style.transition = `width ${OYUN_SURESI}s linear`; zamanCubuguEl.style.width = '0%'; }, 100); clearInterval(zamanlayici); zamanlayici = setInterval(() => { kalan_saniye--; if (kalan_saniye < 0) { clearInterval(zamanlayici); sonucMesajiEl.textContent = "Süre Doldu!"; setTimeout(oyunuBitir, 2000); } }, 1000);
     isProcessing = false;
 }

 function tahminEt(tahmin) {
     if (isProcessing) return;
     isProcessing = true;
     clearInterval(zamanlayici);
     zamanCubuguEl.style.transition = 'width 0.2s ease-out';
     zamanCubuguEl.style.width = zamanCubuguEl.offsetWidth + 'px';
     olay2YilEl.textContent = formatYil(olay2.yil);

     const gercekDurum = olay2.yil === olay1.yil ? "ayni" : olay2.yil > olay1.yil ? "yeni" : "eski";

     if (tahmin === gercekDurum) {
         const kazanilanPuan = kalan_saniye > 0 ? kalan_saniye : 1;
         skor += (tahmin === "ayni" ? kazanilanPuan * 10 : kazanilanPuan);
         skorEl.textContent = skor;
         sonucMesajiEl.textContent = `Doğru! +${(tahmin === "ayni" ? kazanilanPuan * 10 : kazanilanPuan)} Puan`;
         sonucMesajiEl.style.color = '#28a745';
         olay2YilEl.style.color = '#28a745';

         sabitOlay = tahmin === "ayni" ? null : olay2;
         kullanilmis_idler.push(olay2.id);

         setTimeout(() => {
             yeniCiftGetir(false);
         }, 1500);
     } else {
         sonucMesajiEl.textContent = 'Yanlış!';
         sonucMesajiEl.style.color = '#dc3545';
         olay2YilEl.style.color = '#dc3545';
         sabitOlay = null;
         setTimeout(oyunuBitir, 2000);
     }
 }

 function transitionToFinalScreen() { finalSkorEl.textContent = skor; oyunBittiEl.style.display = 'flex'; cardsContainer.style.display = 'none'; sonucMesajiEl.style.display = 'none'; zamanCubuguEl.parentElement.style.display = 'none'; }
 function oyunuBitir() { isProcessing = true; oyunSonuBasligiEl.textContent = "Oyun Bitti!"; oyunSonuBasligiEl.classList.remove('victory-title'); transitionToFinalScreen(); }
 function oyunuKazan() { isProcessing = true; oyunSonuBasligiEl.textContent = "TEBRİKLER! OYUNU BİTİRDİN!"; oyunSonuBasligiEl.classList.add('victory-title'); transitionToFinalScreen(); }
 function formatYil(yil) { return yil < 0 ? `M.Ö. ${Math.abs(yil)}` : yil; }

 // --- OLAY DİNLEYİCİLERİ ---
 baslatBtn.addEventListener('click', oyunuBaslat);
 liderlikBtn.addEventListener('click', liderlikTablosunuGoster);
 anaMenuyeDonBtn1.addEventListener('click', () => ekranGoster('ana-menu'));
 anaMenuyeDonBtn2.addEventListener('click', () => ekranGoster('ana-menu'));
 tekrarOynaBtn.addEventListener('click', oyunuBaslat);
 higherBtn.addEventListener('click', () => tahminEt('yeni'));
 lowerBtn.addEventListener('click', () => tahminEt('eski'));
 ayniYilBtn.addEventListener('click', () => tahminEt('ayni'));
 skoruKaydetBtn.addEventListener('click', () => { const oyuncuAdi = oyuncuAdiInput.value.trim(); if (oyuncuAdi) { skoruKaydet(skor, oyuncuAdi); skorKayitFormu.style.display = 'none'; liderlikTablosunuGoster(); } else { alert("Lütfen bir isim girin!"); } });

 ekranGoster('ana-menu');