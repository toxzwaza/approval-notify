#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デスクトップ常駐型 承認件数インジケータ
・ドラッグ移動・サイズ変更対応
・新規承認発生時ポップアップ
・初回起動時にもダイアログ表示
"""

import tkinter as tk
import requests
import threading
import time
import json
import os
import webbrowser

# ======================
# 設定
# ======================
API_URL = "https://akioka.cloud/api/order_request/approval_requests"
APPROVAL_URL = "https://akioka.cloud/accept/order-request"
USER_ID = 2
DEBUG = True
REFRESH_INTERVAL = 60  # 秒
SETTINGS_FILE = "settings.json"

TEST_DATA = {"order_requests_count": 14, "danger_count": 8, "alert_count": 2}

# ======================
# 設定ファイル読み込み・保存
# ======================
def load_settings():
    default = {"x": None, "y": None, "size": 100}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default.update(data)
        except Exception as e:
            print("設定読み込みエラー:", e)
    return default


def save_settings(x, y, size):
    data = {"x": x, "y": y, "size": size}
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("設定保存エラー:", e)


# ======================
# API呼び出し
# ======================
def fetch_data():
    if DEBUG:
        print("[DEBUG] ダミーデータ使用中")
        time.sleep(1)
        return TEST_DATA
    try:
        res = requests.get(API_URL, params={"user_id": USER_ID}, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            print("HTTPエラー:", res.status_code)
            return None
    except Exception as e:
        print("APIエラー:", e)
        return None


# ======================
# 大きなポップアップウィンドウ（新規承認発生時 or 初回）
# ======================
def show_popup(data):
    total = data.get("order_requests_count", 0)
    danger = data.get("danger_count", 0)
    alert = data.get("alert_count", 0)

    popup = tk.Toplevel()
    popup.title("承認通知")
    popup.geometry("960x600+{}+{}".format(
        (popup.winfo_screenwidth() // 2) - 480,
        (popup.winfo_screenheight() // 2) - 300
    ))
    popup.attributes("-topmost", True)
    popup.resizable(False, False)
    popup.configure(bg="white")

    title = tk.Label(popup, text=f"未承認の申請が {total} 件あります。",
                     font=("Meiryo", 28, "bold"), bg="white", pady=40)
    title.pack()

    frame = tk.Frame(popup, bg="white")
    frame.pack(pady=20)

    danger_label = tk.Label(frame, text=str(danger),
                            font=("Meiryo", 60, "bold"), fg="red", bg="white")
    danger_label.grid(row=0, column=0, padx=100)

    alert_label = tk.Label(frame, text=str(alert),
                           font=("Meiryo", 60, "bold"), fg="orange", bg="white")
    alert_label.grid(row=0, column=1, padx=100)

    label_row = tk.Frame(popup, bg="white")
    label_row.pack()
    tk.Label(label_row, text="すぐに承認が必要", font=("Meiryo", 18), bg="white", fg="red").grid(row=0, column=0, padx=120)
    tk.Label(label_row, text="期限が近い", font=("Meiryo", 18), bg="white", fg="orange").grid(row=0, column=1, padx=180)

    def open_approval_page():
        url = f"{APPROVAL_URL}?user_id={USER_ID}"
        webbrowser.open(url)
        popup.destroy()

    button_frame = tk.Frame(popup, bg="white")
    button_frame.pack(pady=50)

    close_btn = tk.Button(button_frame, text="閉じる", command=popup.destroy,
                          width=15, height=2, font=("Meiryo", 16))
    close_btn.grid(row=0, column=0, padx=40)

    approve_btn = tk.Button(button_frame, text="承認ページを開く", command=open_approval_page,
                            width=22, height=2, font=("Meiryo", 16), bg="#0078D7", fg="white")
    approve_btn.grid(row=0, column=1, padx=40)

    popup.mainloop()


# ======================
# データ更新 + 新規承認検出
# ======================
previous_total = None
first_run = True  # 初回実行フラグ


def update_label():
    global previous_total, first_run

    data = fetch_data()
    if not data:
        root.after(REFRESH_INTERVAL * 1000, update_label)
        return

    total = data.get("order_requests_count", 0)
    danger = data.get("danger_count", 0)
    alert = data.get("alert_count", 0)

    # 色を危険度で変更
    if danger > 0:
        color = "red"
    elif alert > 0:
        color = "orange"
    else:
        color = "gray"

    label.config(text=str(total), bg=color)

    # 初回のみ強制表示
    if first_run:
        print("[INFO] 初回実行 → ダイアログ表示")
        threading.Thread(target=show_popup, args=(data,), daemon=True).start()
        first_run = False

    # 2回目以降 → 新規承認が増加した場合のみ表示
    elif previous_total is not None and total > previous_total:
        print(f"[INFO] 新規承認 {total - previous_total} 件発生 → ダイアログ表示")
        threading.Thread(target=show_popup, args=(data,), daemon=True).start()

    previous_total = total
    root.after(REFRESH_INTERVAL * 1000, update_label)


# ======================
# 承認ページを開く
# ======================
def open_page(event=None):
    url = f"{APPROVAL_URL}?user_id={USER_ID}"
    webbrowser.open(url)


# ======================
# ドラッグ・リサイズ関連
# ======================
drag_data = {"x": 0, "y": 0}
settings = load_settings()
current_size = settings.get("size", 100)


def start_drag(event):
    drag_data["x"] = event.x
    drag_data["y"] = event.y


def do_drag(event):
    x = root.winfo_x() + event.x - drag_data["x"]
    y = root.winfo_y() + event.y - drag_data["y"]
    root.geometry(f"{current_size}x{current_size}+{x}+{y}")


def resize(event):
    global current_size
    if event.state & 0x0004:  # Ctrlキー押下中
        delta = 10 if event.delta > 0 else -10
        current_size = max(50, min(300, current_size + delta))
        label.config(font=("Meiryo", int(current_size / 3), "bold"))
        root.geometry(f"{current_size}x{current_size}+{root.winfo_x()}+{root.winfo_y()}")


def on_close():
    save_settings(root.winfo_x(), root.winfo_y(), current_size)
    root.destroy()


# ======================
# メインウィンドウ（右下常駐）
# ======================
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)
root.configure(bg="white")

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
x = settings["x"] or (screen_w - current_size - 50)
y = settings["y"] or (screen_h - current_size - 100)
root.geometry(f"{current_size}x{current_size}+{x}+{y}")

label = tk.Label(root, text="--", font=("Meiryo", int(current_size / 3), "bold"),
                 width=4, height=2, bg="gray", fg="white", relief="ridge")
label.pack(expand=True, fill="both")

label.bind("<Double-Button-1>", open_page)
label.bind("<Button-1>", start_drag)
label.bind("<B1-Motion>", do_drag)
label.bind("<MouseWheel>", resize)
root.protocol("WM_DELETE_WINDOW", on_close)

threading.Thread(target=update_label, daemon=True).start()
root.mainloop()
