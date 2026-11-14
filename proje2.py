import ctypes
import os
import ssl
import time
import urllib.request
import certifi
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui

klasor = os.path.dirname(os.path.abspath(__file__))
os.chdir(klasor)

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_YOLU = os.path.join(klasor, "hand_landmarker.task")

if not os.path.exists(MODEL_YOLU):
    print("El takip modeli indiriliyor, lutfen bekleyin...")
    ssl_baglami = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(MODEL_URL, context=ssl_baglami) as yanit, open(MODEL_YOLU, "wb") as dosya:
        dosya.write(yanit.read())

with open(MODEL_YOLU, "rb") as dosya:
    model_verisi = dosya.read()

base_options = python.BaseOptions(model_asset_buffer=model_verisi)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
)
detector = vision.HandLandmarker.create_from_options(options)

EL_BAGLANTILARI = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
]

PARMAK_UCLARI = [4, 8, 12, 16, 20]
PARMAK_ISIMLERI = ["Bas", "Isaret", "Orta", "Yuzuk", "Serce"]

SLAYTLAR = [
    ("SLAYT 1 / 4", "Proje Tanitimi & Amac", (180, 90, 40)),
    ("SLAYT 2 / 4", "MediaPipe 21 El Eklemi", (40, 130, 90)),
    ("SLAYT 3 / 4", "Geometrik Parmak Sayma", (140, 70, 150)),
    ("SLAYT 4 / 4", "Temassiz Sunum Kontrolu", (45, 110, 175)),
]
aktif_slayt = 0

modlar = ["Ses Kontrolu", "Slayt Kontrolu", "Sadece Sayim"]
aktif_mod = 0
son_aksiyon_zamani = 0
aksiyon_mesaji = "Hazir"
son_zaman_damgasi = 0
m_onceki = False
PENCERE_ADI = "YZT - Kamerayla El Takibi"

def m_basili_mi():
    return (ctypes.windll.user32.GetAsyncKeyState(0x4D) & 0x8000) != 0

cap = cv2.VideoCapture(0)
print("Kamera baslatildi. Mod degistirmek icin [M] tusuna basin.")

while cap.isOpened():
    basarili, kare = cap.read()
    if not basarili:
        print("Kameradan goruntu alinamadi!")
        break

    kare = cv2.flip(kare, 1)
    h, w, _ = kare.shape

    rgb_kare = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_kare)

    zaman_damgasi = int(time.perf_counter() * 1000)
    if zaman_damgasi <= son_zaman_damgasi:
        zaman_damgasi = son_zaman_damgasi + 1
    son_zaman_damgasi = zaman_damgasi

    sonuclar = detector.detect_for_video(mp_image, zaman_damgasi)

    acik_parmak_sayisi = 0
    acik_listesi = []

    if sonuclar.hand_landmarks:
        for eklemler in sonuclar.hand_landmarks:
            for baslangic, bitis in EL_BAGLANTILARI:
                x1, y1 = int(eklemler[baslangic].x * w), int(eklemler[baslangic].y * h)
                x2, y2 = int(eklemler[bitis].x * w), int(eklemler[bitis].y * h)
                cv2.line(kare, (x1, y1), (x2, y2), (255, 255, 255), 2)

            for idx, nokta in enumerate(eklemler):
                cx, cy = int(nokta.x * w), int(nokta.y * h)
                renk = (0, 120, 255) if idx in PARMAK_UCLARI else (0, 255, 120)
                cv2.circle(kare, (cx, cy), 5, renk, -1)

            parmak_durumu = []

            bas_acik = abs(eklemler[4].x - eklemler[17].x) > abs(eklemler[3].x - eklemler[17].x)
            parmak_durumu.append(1 if bas_acik else 0)

            for uc in PARMAK_UCLARI[1:]:
                parmak_durumu.append(1 if eklemler[uc].y < eklemler[uc - 2].y else 0)

            acik_parmak_sayisi += sum(parmak_durumu)
            acik_listesi += [PARMAK_ISIMLERI[i] for i, acik in enumerate(parmak_durumu) if acik == 1]

        su_an = time.time()
        if su_an - son_aksiyon_zamani > 0.8:
            if modlar[aktif_mod] == "Ses Kontrolu":
                if acik_parmak_sayisi == 5:
                    pyautogui.press("volumeup")
                    aksiyon_mesaji = "5 Parmak -> Ses Artirildi (+)"
                    son_aksiyon_zamani = su_an
                elif acik_parmak_sayisi == 0:
                    pyautogui.press("volumedown")
                    aksiyon_mesaji = "0 Parmak -> Ses Azaltildi (-)"
                    son_aksiyon_zamani = su_an
                elif acik_parmak_sayisi == 2:
                    pyautogui.press("volumemute")
                    aksiyon_mesaji = "2 Parmak -> Ses Sustur/Ac"
                    son_aksiyon_zamani = su_an

            elif modlar[aktif_mod] == "Slayt Kontrolu":
                if acik_parmak_sayisi == 1:
                    if aktif_slayt < len(SLAYTLAR) - 1:
                        aktif_slayt += 1
                        pyautogui.press("right")
                        aksiyon_mesaji = f"1 Parmak -> Sonraki ({SLAYTLAR[aktif_slayt][0]})"
                    else:
                        aksiyon_mesaji = "Son slayttasiniz (4 / 4)"
                    son_aksiyon_zamani = su_an
                elif acik_parmak_sayisi == 2:
                    if aktif_slayt > 0:
                        aktif_slayt -= 1
                        pyautogui.press("left")
                        aksiyon_mesaji = f"2 Parmak -> Onceki ({SLAYTLAR[aktif_slayt][0]})"
                    else:
                        aksiyon_mesaji = "Ilk slayttasiniz (1 / 4)"
                    son_aksiyon_zamani = su_an

    acik_metin = ", ".join(acik_listesi[:5]) + ("..." if len(acik_listesi) > 5 else "") if acik_listesi else "Yok"
    cv2.rectangle(kare, (10, 10), (455, 148), (20, 25, 35), -1)
    cv2.putText(kare, f"Acik Parmak Sayisi: {acik_parmak_sayisi}", (22, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 255, 150), 3)
    cv2.putText(kare, f"Aciklar: {acik_metin}", (22, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 2)
    cv2.putText(kare, f"Bonus Mod [M]: {modlar[aktif_mod]}", (22, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (100, 200, 255), 2)
    cv2.putText(kare, f"Son Komut: {aksiyon_mesaji}", (22, 136), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 220, 100), 2)

    if modlar[aktif_mod] == "Slayt Kontrolu":
        slayt_no, slayt_baslik, slayt_renk = SLAYTLAR[aktif_slayt]
        cv2.rectangle(kare, (w - 310, h - 130), (w - 12, h - 42), slayt_renk, -1)
        cv2.rectangle(kare, (w - 310, h - 130), (w - 12, h - 42), (255, 255, 255), 2)
        cv2.putText(kare, slayt_no, (w - 295, h - 98), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(kare, slayt_baslik, (w - 295, h - 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 2)

    cv2.putText(kare, "[M] Mod Degistir", (15, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    cv2.imshow(PENCERE_ADI, kare)
    cv2.waitKey(1)

    # Sağ üstteki [X] butonuna basıldıysa döngüden çık
    if cv2.getWindowProperty(PENCERE_ADI, cv2.WND_PROP_VISIBLE) < 1:
        break

    # Pencereye tıklamaya gerek kalmadan M tuşu ile mod değiştirme
    m_simdi = m_basili_mi()
    if m_simdi and not m_onceki:
        aktif_mod = (aktif_mod + 1) % len(modlar)
        aksiyon_mesaji = f"Mod: {modlar[aktif_mod]}"
    m_onceki = m_simdi

detector.close()
cap.release()
cv2.destroyAllWindows()