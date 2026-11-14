# 🖐️ Kamerayla Gerçek Zamanlı El Takibi ve Temassız Kontrol Sistemi

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-HandLandmarker-0097A7?style=for-the-badge&logo=google&logoColor=white)
![PyAutoGUI](https://img.shields.io/badge/PyAutoGUI-Desktop%20Automation-FF6F00?style=for-the-badge)

Bu proje, **OpenCV** ve **MediaPipe Tasks (`HandLandmarker`)** altyapısını kullanarak web kamerasından alınan canlı görüntü üzerinde el iskeletini (her el için 21 eklem noktasını) gerçek zamanlı tespit eden, çift el desteğiyle **0–10 arası** açık parmak sayısını hesaplayan ve el hareketleriyle bilgisayar/sunum kontrolü sağlayan bir bilgisayarla görü (Computer Vision) ve insan-bilgisayar etkileşimi (HCI) uygulamasıdır.

---

## 🎯 Temel Özellikler

* **Gerçek Zamanlı Çift El ve 21 Eklem İskelet Tespiti:** MediaPipe `HandLandmarker` modeli (`VIDEO` çalışma modu) ile aynı anda iki ele kadar (`num_hands=2`) tüm eklem noktaları ve kemik bağlantıları canlı video akışı üzerine çizilir.
* **0–10 Arası Geometrik Parmak Sayma:** Her eldeki eklemlerin birbirine göre uzamsal konumları analiz edilerek toplam açık parmak sayısı ve hangi parmakların (`Baş`, `İşaret`, `Orta`, `Yüzük`, `Serçe`) açık olduğu gerçek zamanlı HUD panelinde gösterilir.
* **Bonus — El Hareketleriyle Sistem ve Sunum Kontrolü (`PyAutoGUI`):**
  * **Ses Kontrolü Modu:** Parmak hareketleriyle Windows sistem sesini artırma, azaltma ve sessize alma (`volumeup`, `volumedown`, `volumemute`).
  * **Slayt Kontrolü Modu:** Kamera arayüzünün sağ alt köşesinde canlı durum kartı (`1/4` – `4/4`) ile senkronize şekilde klavye yön tuşlarını (`right`, `left`) tetikleyerek temassız sunum yönetimi.
  * **Sadece Sayım Modu:** Bilgisayar komutlarını devre dışı bırakarak yalnızca el takibi ve parmak sayımı yapma.
* **Odak Bağımsız Kısayol Yönetimi:** Windows API (`ctypes` / `GetAsyncKeyState`) entegrasyonu sayesinde kamera penceresi odakta olmasa dahi **`M`** tuşu ile modlar arasında anında geçiş yapılabilir.

---

## 🧠 Sistem Mimarisi ve Çalışma Mantığı

Uygulama her video karesinde aşağıdaki 5 aşamalı iş hattını (pipeline) çalıştırır:

1. **Görüntü Yakalama ve Ön İşleme:** OpenCV (`cv2.VideoCapture`) ile kameradan alınan kare, kullanıcıya doğal bir ayna deneyimi sunmak için yatay eksende çevrilir (`cv2.flip(kare, 1)`) ve MediaPipe'ın beklediği `BGR -> RGB` renk uzayına dönüştürülür.
2. **El ve Eklem Tespiti (`HandLandmarker`):** Yüksek doğruluk eşikleri (`min_hand_detection_confidence=0.7`, `min_tracking_confidence=0.7`) ve monoton artan milisaniye zaman damgası (`time.perf_counter`) ile el üzerindeki **21 eklem noktası** çıkarılır.
3. **Geometrik Parmak Açıklık Algoritması:** Derin öğrenme modelinden gelen normalize `(x, y)` koordinatları üzerinde anatomik kurallar uygulanır:

| Parmak | Uç İndeksi | Referans Eklemler | Açıklık Koşulu |
| :--- | :---: | :---: | :--- |
| **Başparmak** | `4` | `3` (Boğum), `17` (Serçe Tabanı) | Başparmak ucunun serçe parmak tabanına yatay uzaklığı (`\|x4 - x17\|`), alt boğumun uzaklığından (`\|x3 - x17\|`) büyükse **açık** |
| **İşaret Parmağı** | `8` | `6` (Orta Eklem) | Görüntü koordinatlarında `Y` yukarı çıkıldıkça küçüldüğü için `y8 < y6` ise **açık** |
| **Orta Parmak** | `12` | `10` (Orta Eklem) | `y12 < y10` ise **açık** |
| **Yüzük Parmağı** | `16` | `14` (Orta Eklem) | `y16 < y14` ise **açık** |
| **Serçe Parmak** | `20` | `18` (Orta Eklem) | `y20 < y18` ise **açık** |

4. **Zaman Damgalı Koruma (Debounce) ve Otomasyon:** Yanlış ve art arda istemsiz tetiklemeleri önlemek için komutlar arasında **`0.8 saniyelik`** bekleme süresi uygulanır; koşul sağlandığında `PyAutoGUI` üzerinden ilgili sistem tuşu tetiklenir.
5. **HUD Arayüz Çizimi:** Tespit edilen eklemler, kemik bağlantıları, açık parmak sayısı, aktif mod bilgisi ve slayt kontrol kartı OpenCV çizim fonksiyonlarıyla kare üzerine işlenir.

---

## 🎮 Bonus Kontrol Modları ve Jest Tablosu

Klavyeden **`M`** tuşuna basılarak aşağıdaki üç mod arasında döngüsel geçiş yapılır:

| Aktif Mod | Açık Parmak Sayısı | Tetiklenen Tuş | Gerçekleşen İşlem |
| :--- | :---: | :---: | :--- |
| **Ses Kontrolü** | `5` Parmak | `volumeup` | Sistem ses seviyesini artırır (`+`) |
| **Ses Kontrolü** | `0` Parmak (Yumruk) | `volumedown` | Sistem ses seviyesini azaltır (`-`) |
| **Ses Kontrolü** | `2` Parmak | `volumemute` | Sistem sesini susturur / açar |
| **Slayt Kontrolü** | `1` Parmak | `right` | Sonraki slayta geçer (Son slaytta `4/4` sınır koruması aktif) |
| **Slayt Kontrolü** | `2` Parmak | `left` | Önceki slayta döner (İlk slaytta `1/4` sınır koruması aktif) |
| **Sadece Sayım** | `0 – 10` Parmak | — | Otomasyon komutlarını durdurur, yalnızca parmak sayımı yapar |

---

## 🛠️ Teknik Çözümler ve Geliştirme Notları

* **Türkçe Karakterli Dosya Yolu Uyumu:** Windows ortamında kullanıcı ve klasör adlarında bulunan Türkçe karakterlerin (`Ş`, `ı` vb.) C++ tabanlı MediaPipe model yükleyicisinde `FileNotFoundError` oluşturmasını önlemek amacıyla `.task` model dosyası Python tarafında ikili (`rb`) modda okunup `model_asset_buffer` parametresiyle doğrudan bellekten yüklenmiştir.
* **Otomatik Model İndirme:** `hand_landmarker.task` dosyası çalışma dizininde mevcut değilse uygulama ilk açılışta `certifi` SSL doğrulaması ile modeli Google Cloud Storage üzerinden otomatik olarak indirir.
* **Temiz Pencere Kapanışı:** OpenCV penceresinin sağ üstündeki **`[X]`** kapatma butonu `cv2.getWindowProperty(..., cv2.WND_PROP_VISIBLE)` ile izlenerek kamera ve model kaynaklarının (`cap.release()`, `detector.close()`) güvenli biçimde serbest bırakılması sağlanmıştır.

---

## 📁 Proje Dizin Yapısı

```text
kamerayla-el-takibi/
│
├── proje2.py               # Ana uygulama, el iskeleti çizimi, parmak sayma ve otomasyon kodu
├── hand_landmarker.task    # MediaPipe el takip modeli (ilk çalıştırmada otomatik indirilir)
├── requirements.txt        # Proje bağımlılıkları
├── .gitignore              # Sanal ortam ve önbellek dosyaları hariç tutma listesi
└── README.md               # Proje dokümantasyonu
```

---

## 🚀 Kurulum ve Çalıştırma

### 1. Projeyi Klonlayın ve Klasöre Girin
```bash
git clone [https://github.com/azratashan/yzt-kamerayla-el-takibi.git](https://github.com/azratashan/yzt-kamerayla-el-takibi.git)
cd yzt-kamerayla-el-takibi
```

### 2. Sanal Ortam Oluşturun ve Bağımlılıkları Yükleyin
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Uygulamayı Başlatın
```bash
python proje2.py
```

### Kullanım Kontrolleri
* **`M` Tuşu:** Pencere odakta olmasa dahi *Ses Kontrolü*, *Slayt Kontrolü* ve *Sadece Sayım* modları arasında geçiş yapar.
* **`[X]` Butonu:** Kamera penceresini kapatır ve uygulamayı sonlandırır.

---

**Geliştirici:** Azra Taşhan ([@azratashan](https://github.com/azratashan)) — Bursa Uludağ Üniversitesi Yapay Zeka Topluluğu (YZT)