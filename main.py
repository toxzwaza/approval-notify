#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
承認通知常駐アプリ（タスクトレイ対応＋大型UI版）
"""

import tkinter as tk
import threading
import time
import requests
import sys
import webbrowser
import pystray
from PIL import Image, ImageDraw

# ======================
# 設定
# ======================
API_URL = "https://akioka.cloud/api/order_request/approval_requests"
APPROVAL_URL = "https://akioka.cloud/accept/order-request"
CHECK_INTERVAL = 60 * 30  # 秒（本番は30分）
DEBUG = True
USER_ID = 2

TEST_DATA = {
    "order_requests_count": 14,
    "danger_count": 8,
    "alert_count": 2
}

# ======================
# ポップアップ表示
# ======================
def show_popup(data):
    total = data.get("order_requests_count", 0)
    danger = data.get("danger_count", 0)
    alert = data.get("alert_count", 0)

    root = tk.Tk()
    root.title("承認通知")
    root.geometry("960x600+{}+{}".format(
        (root.winfo_screenwidth() // 2) - 480,
        (root.winfo_screenheight() // 2) - 300
    ))
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="white")

    # タイトル
    title = tk.Label(root, text=f"未承認の申請が {total} 件あります。",
                     font=("Meiryo", 28, "bold"), bg="white", pady=40)
    title.pack()

    # 内訳
    frame = tk.Frame(root, bg="white")
    frame.pack(pady=20)

    danger_label = tk.Label(frame, text=str(danger),
                            font=("Meiryo", 60, "bold"), fg="red", bg="white")
    danger_label.grid(row=0, column=0, padx=100)

    alert_label = tk.Label(frame, text=str(alert),
                           font=("Meiryo", 60, "bold"), fg="orange", bg="white")
    alert_label.grid(row=0, column=1, padx=100)

    label_row = tk.Frame(root, bg="white")
    label_row.pack()
    tk.Label(label_row, text="すぐに承認が必要", font=("Meiryo", 18), bg="white", fg="red").grid(row=0, column=0, padx=120)
    tk.Label(label_row, text="期限が近い", font=("Meiryo", 18), bg="white", fg="orange").grid(row=0, column=1, padx=180)

    # ボタンエリア
    button_frame = tk.Frame(root, bg="white")
    button_frame.pack(pady=50)

    def open_approval_page():
        url = f"{APPROVAL_URL}?user_id={USER_ID}"
        webbrowser.open(url)
        root.destroy()

    close_btn = tk.Button(button_frame, text="閉じる", command=root.destroy,
                          width=15, height=2, font=("Meiryo", 16))
    close_btn.grid(row=0, column=0, padx=40)

    approve_btn = tk.Button(button_frame, text="承認ページを開く", command=open_approval_page,
                            width=22, height=2, font=("Meiryo", 16), bg="#0078D7", fg="white")
    approve_btn.grid(row=0, column=1, padx=40)

    root.mainloop()

# ======================
# APIチェック関数
# ======================
def check_pending_approvals():
    if DEBUG:
        print("[DEBUG] テストデータを使用中")
        time.sleep(1)
        return TEST_DATA

    try:
        response = requests.get(API_URL, params={"user_id": USER_ID}, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"HTTPエラー: {response.status_code}")
            return None
    except Exception as e:
        print(f"APIエラー: {e}")
        return None

# ======================
# 定期チェックループ
# ======================
def check_approval_loop(icon):
    while True:
        data = check_pending_approvals()
        if data and data.get("order_requests_count", 0) > 0:
            show_popup(data)
        else:
            print("未承認なし。")

        time.sleep(10 if DEBUG else CHECK_INTERVAL)

# ======================
# タスクトレイアイコン設定
# ======================
def create_image():
    """シンプルな赤丸アイコンを生成"""
    img = Image.new("RGB", (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill="red")
    return img

def on_quit(icon, item):
    icon.stop()
    sys.exit(0)

def manual_check(icon, item):
    data = check_pending_approvals()
    if data and data.get("order_requests_count", 0) > 0:
        show_popup(data)
    else:
        print("未承認なし。")

# ======================
# メイン処理
# ======================
def main():
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem("今すぐ確認", manual_check),
        pystray.MenuItem("終了", on_quit)
    )
    icon = pystray.Icon("approval_notifier", image, "承認通知", menu)
    threading.Thread(target=check_approval_loop, args=(icon,), daemon=True).start()
    icon.run()

if __name__ == "__main__":
    main()
