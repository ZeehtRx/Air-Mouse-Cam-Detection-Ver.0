import cv2
import mediapipe as mp
import pyautogui
import math

# --- Konfigurasi awal ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

screen_width, screen_height = pyautogui.size()
smoothening = 4
prev_mouse_x, prev_mouse_y = 0, 0
curr_mouse_x, curr_mouse_y = 0, 0

# State untuk mencegah spam
left_click_active = False
right_click_active = False
zoom_active = False
drag_active = False  # ✨ tambahan untuk drag and drop

# Fungsi bantu: hitung jarak Euklidian antara dua landmark
def calc_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

# --- Pilih device yang mau di gunakan (ubahnya di dialam index)---
cap = cv2.VideoCapture(1)

# 💡 Set resolusi kamera ke 1080p (1920x1080)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Ngecek resolusinya udah oke atau ga
actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"Resolusi kamera aktif: {int(actual_width)} x {int(actual_height)}")
#Apa aja yang bisa di lakuin
print("Kontrol Mouse dengan Tangan:")
print("• Gerakkan telunjuk → gerakkan kursor")
print("• Jempol + telunjuk RAPAT SEBENTAR → klik kiri")
print("• Jempol + telunjuk TAHAN RAPAT → drag and drop")
print("• Telunjuk + jari tengah rapat (jempol jauh) → klik kanan")
print("• Ubah jarak jempol–telunjuk → zoom in/out")
print("Tekan 'q' untuk keluar.")

while True:
    success, img = cap.read()
    if not success:
        print("Gagal membaca frame dari kamera.")
        break

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    img_height, img_width, _ = img.shape

    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)

        # Ambil landmark atau bagian bagian yang penting
        index_tip = hand.landmark[8]   # telunjuk
        thumb_tip = hand.landmark[4]   # jempol
        middle_tip = hand.landmark[12] # jari tengah

        # Hitung jarak antar jari ke jari yang lain
        dist_thumb_index = calc_distance(thumb_tip, index_tip)
        dist_index_middle = calc_distance(index_tip, middle_tip)
        dist_thumb_middle = calc_distance(thumb_tip, middle_tip)

        # --- Gerak kursor (selalu aktif) ---
        screen_x = screen_width * index_tip.x
        screen_y = screen_height * index_tip.y

        curr_mouse_x = prev_mouse_x + (screen_x - prev_mouse_x) / smoothening
        curr_mouse_y = prev_mouse_y + (screen_y - prev_mouse_y) / smoothening

        pyautogui.moveTo(curr_mouse_x, curr_mouse_y)
        prev_mouse_x, prev_mouse_y = curr_mouse_x, curr_mouse_y

        # --- Drag and Drop typa shit---
        if dist_thumb_index < 0.04:
            if not drag_active:
                # Mulai drag: tekan tombol kiri dan tahan
                pyautogui.mouseDown()
                drag_active = True
                cv2.circle(img, (int(index_tip.x * img_width), int(index_tip.y * img_height)), 15, (255, 255, 0), cv2.FILLED)
        elif dist_thumb_index >= 0.06:
            if drag_active:
                # Lepas drag
                pyautogui.mouseUp()
                drag_active = False
            left_click_active = False  # reset klik biasa


        # --- Klik Kanan dominant ---
        if dist_index_middle < 0.04 and dist_thumb_middle > 0.1 and not right_click_active:
            pyautogui.rightClick()
            right_click_active = True
            cv2.circle(img, (int(index_tip.x * img_width), int(index_tip.y * img_height)), 15, (255, 0, 0), cv2.FILLED)
        elif dist_index_middle >= 0.06 or dist_thumb_middle <= 0.08:
            right_click_active = False

        # --- Zoom In/Out (Ctrl + Scroll) masih perlu di debugging ---
        if 0.05 < dist_thumb_index < 0.25 and not drag_active:  # jangan zoom saat drag
            if not zoom_active:
                zoom_active = True
                scroll_amount = 1 if dist_thumb_index > 0.12 else -1
                pyautogui.keyDown('ctrl')
                pyautogui.scroll(scroll_amount)
                pyautogui.keyUp('ctrl')
        else:
            zoom_active = False

    # Tampilkan frame
    cv2.imshow("Advanced Hand Mouse Controller (1080p + Drag)", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        # Pastikan lepas drag saat keluar
        if drag_active:
            pyautogui.mouseUp()
        break

# --- Get ouuttttt ---
cap.release()
cv2.destroyAllWindows()