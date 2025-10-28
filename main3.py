#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
承認通知 常駐アプリ（トレイアイコン表示 + 起動自動化 + 管理者GUI）
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time
import json
import os
import webbrowser
import requests
import pystray
from PIL import Image, ImageDraw
import sys   # ←★ 追加！

# ======================
# 定数設定
# ======================
SETTING_FILE = "approval-notify-setting.json"
ICON_FILE = "icon.png"
DEFAULT_SETTING = {
    "user_id": 2,
    "size": 120,
    "x": None,
    "y": None,
    "refresh_interval": 60
}
ADMIN_PASSWORD = "Akioka55"

API_URL = "https://akioka.cloud/api/order_request/approval_requests"
APPROVAL_URL = "https://akioka.cloud/accept/order-request"
DEBUG = False
TEST_DATA = {"order_requests_count": 14, "danger_count": 8, "alert_count": 2}

# ======================
# 設定ファイル管理
# ======================
def load_settings():
    if not os.path.exists(SETTING_FILE):
        save_settings(DEFAULT_SETTING)
        return DEFAULT_SETTING
    try:
        with open(SETTING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULT_SETTING.items():
            if k not in data:
                data[k] = v
        return data
    except Exception as e:
        print("設定読み込みエラー:", e)
        return DEFAULT_SETTING


def save_settings(data):
    try:
        with open(SETTING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("[INFO] 設定保存:", data)
    except Exception as e:
        print("設定保存エラー:", e)


# ======================
# API呼び出し
# ======================
def fetch_data(user_id):
    if DEBUG:
        time.sleep(1)
        return TEST_DATA
    try:
        res = requests.get(API_URL, params={"user_id": user_id}, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            print("HTTPエラー:", res.status_code)
            return None
    except Exception as e:
        print("APIエラー:", e)
        return None


# ======================
# 承認ポップアップ
# ======================
def show_popup(data, setting):
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
    popup.configure(bg="white")

    title = tk.Label(popup, text=f"未承認の申請が {total} 件あります。",
                     font=("Meiryo", 28, "bold"), bg="white", pady=40)
    title.pack()

    frame = tk.Frame(popup, bg="white")
    frame.pack(pady=20)

    tk.Label(frame, text=str(danger), font=("Meiryo", 60, "bold"),
             fg="red", bg="white").grid(row=0, column=0, padx=100)
    tk.Label(frame, text=str(alert), font=("Meiryo", 60, "bold"),
             fg="orange", bg="white").grid(row=0, column=1, padx=100)

    label_row = tk.Frame(popup, bg="white")
    label_row.pack()
    tk.Label(label_row, text="すぐに承認が必要", font=("Meiryo", 18),
             bg="white", fg="red").grid(row=0, column=0, padx=120)
    tk.Label(label_row, text="期限が近い", font=("Meiryo", 18),
             bg="white", fg="orange").grid(row=0, column=1, padx=180)

    def open_approval_page():
        webbrowser.open(f"{APPROVAL_URL}?user_id={setting['user_id']}")
        popup.destroy()

    def open_admin_panel():
        password = simpledialog.askstring("管理者認証", "パスワードを入力してください:", show="*")
        if password == ADMIN_PASSWORD:
            popup.destroy()
            open_admin_window(setting)
        else:
            messagebox.showerror("エラー", "パスワードが違います。")

    btns = tk.Frame(popup, bg="white")
    btns.pack(pady=50)
    tk.Button(btns, text="閉じる", command=popup.destroy,
              width=15, height=2, font=("Meiryo", 16)).grid(row=0, column=0, padx=30)
    tk.Button(btns, text="承認ページを開く", command=open_approval_page,
              width=20, height=2, font=("Meiryo", 16), bg="#0078D7", fg="white").grid(row=0, column=1, padx=30)
    tk.Button(btns, text="管理者用", command=open_admin_panel,
              width=15, height=2, font=("Meiryo", 16), bg="gray", fg="white").grid(row=0, column=2, padx=30)

    popup.mainloop()


# ======================
# 管理者設定GUI
# ======================
def open_admin_window(setting):
    admin = tk.Tk()
    admin.title("承認通知 設定")
    admin.geometry("400x350")
    admin.configure(bg="white")

    def save_and_close():
        try:
            setting["user_id"] = int(entry_user_id.get())
            setting["size"] = int(entry_size.get())
            setting["x"] = int(entry_x.get()) if entry_x.get() else None
            setting["y"] = int(entry_y.get()) if entry_y.get() else None
            setting["refresh_interval"] = int(entry_interval.get())
            save_settings(setting)
            messagebox.showinfo("保存完了", "設定を保存しました。再起動時に反映されます。")
            admin.destroy()
        except Exception as e:
            messagebox.showerror("入力エラー", str(e))

    tk.Label(admin, text="設定値の編集", font=("Meiryo", 16, "bold"),
             bg="white", pady=10).pack()
    frame = tk.Frame(admin, bg="white")
    frame.pack(pady=10)

    labels = ["user_id", "size", "x", "y", "refresh_interval"]
    entries = {}
    for i, key in enumerate(labels):
        tk.Label(frame, text=key, font=("Meiryo", 12),
                 bg="white").grid(row=i, column=0, sticky="e", padx=10, pady=5)
        val = setting.get(key, "")
        e = tk.Entry(frame, font=("Meiryo", 12))
        e.insert(0, str(val) if val is not None else "")
        e.grid(row=i, column=1, pady=5)
        entries[key] = e

    entry_user_id = entries["user_id"]
    entry_size = entries["size"]
    entry_x = entries["x"]
    entry_y = entries["y"]
    entry_interval = entries["refresh_interval"]

    tk.Button(admin, text="保存して閉じる", command=save_and_close,
              font=("Meiryo", 12), bg="#0078D7", fg="white",
              width=20).pack(pady=20)

    admin.mainloop()


# ======================
# 常駐ウィンドウ（監視）
# ======================
def run_notifier():
    """承認状況を監視し、デスクトップ右下に通知バッジを表示"""
    setting = load_settings()
    user_id = setting["user_id"]
    refresh = setting["refresh_interval"]
    size = setting["size"]
    drag = {"x": 0, "y": 0}
    current_size = size
    prev_total = None
    first = True
    
    # 現在の表示状態を保存（リサイズ時の再描画用）
    current_display = {"count": "--", "color": "#546E7A"}

    # ----------------------------------------
    # メインウィンドウ設定
    # ----------------------------------------
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    
    # 透過背景の設定（黒を透過色として指定）
    TRANSPARENT_COLOR = "#000001"  # ほぼ黒だが完全な黒ではない
    root.configure(bg=TRANSPARENT_COLOR)
    root.attributes("-transparentcolor", TRANSPARENT_COLOR)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = setting["x"] or (screen_w - size - 40)
    y = setting["y"] or (screen_h - size - 80)
    root.geometry(f"{size}x{size}+{x}+{y}")

    # ----------------------------------------
    # Canvasによるモダンな円形デザイン
    # ----------------------------------------
    canvas = tk.Canvas(root, width=size, height=size, highlightthickness=0, bg=TRANSPARENT_COLOR)
    canvas.pack(expand=True, fill="both")

    def draw_badge(count="--", color="#555555"):
        """モダンでシンプルなバッジUIを描画"""
        nonlocal size, current_display
        
        # 現在の表示状態を保存
        current_display["count"] = count
        current_display["color"] = color
        
        canvas.delete("all")
        r = int(size / 2.2)
        cx, cy = size // 2, size // 2

        # ソフトな外側の影（透過背景に対応）
        shadow_colors = ["#1a1a1a", "#121212", "#0a0a0a"]
        for i, shadow_color in enumerate(shadow_colors):
            offset = 8 - i * 2
            canvas.create_oval(cx - r - offset, cy - r - offset, 
                             cx + r + offset, cy + r + offset,
                             fill=shadow_color, outline="", width=0)

        # メインの円形バッジ（フラットデザイン）
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                           fill=color, outline="", width=0)

        # 件数表示（より大きく、クリーンに）
        font_size = max(10, int(size / 2.8))  # 最小フォントサイズを保証
        canvas.create_text(cx, cy - int(size * 0.05), text=str(count),
                           font=("Segoe UI", font_size, "bold"), 
                           fill="white", anchor="center")

        # 下部ラベル（より小さく控えめに）
        label_font_size = max(8, int(size / 9))  # 最小フォントサイズを保証
        canvas.create_text(cx, cy + int(size * 0.18), text="承認待ち",
                           font=("Yu Gothic UI", label_font_size), 
                           fill="#FFFFFF", anchor="center")

    draw_badge("--", "#546E7A")

    # ----------------------------------------
    # ドラッグ・リサイズ
    # ----------------------------------------
    def drag_start(e):
        drag["x"], drag["y"] = e.x, e.y

    def drag_move(e):
        new_x = root.winfo_x() + e.x - drag["x"]
        new_y = root.winfo_y() + e.y - drag["y"]
        root.geometry(f"{current_size}x{current_size}+{new_x}+{new_y}")

    def resize(e):
        nonlocal current_size, size
        if e.state & 0x0004:  # Ctrlキー押下中
            delta = 10 if e.delta > 0 else -10
            current_size = max(80, min(300, current_size + delta))
            size = current_size  # 描画サイズを更新
            canvas.config(width=current_size, height=current_size)
            # 現在表示中の件数と色で再描画
            draw_badge(current_display["count"], current_display["color"])
            root.geometry(f"{current_size}x{current_size}+{root.winfo_x()}+{root.winfo_y()}")

    def on_close():
        setting.update(x=root.winfo_x(), y=root.winfo_y(), size=current_size)
        save_settings(setting)
        root.destroy()

    def open_page(e=None):
        webbrowser.open(f"{APPROVAL_URL}?user_id={user_id}")

    # ----------------------------------------
    # データ更新ループ
    # ----------------------------------------
    def update_label():
        nonlocal prev_total, first
        data = fetch_data(user_id)
        if not data:
            root.after(refresh * 1000, update_label)
            return

        total = data.get("order_requests_count", 0)
        danger, alert = data.get("danger_count", 0), data.get("alert_count", 0)

        # 状況によってカラー変更（モダンな配色）
        if danger > 0:
            color = "#FF5252"  # マテリアルレッド（より鮮やかで視認性が高い）
        elif alert > 0:
            color = "#FF9800"  # マテリアルオレンジ（温かみのある警告色）
        else:
            color = "#546E7A"  # マテリアルブルーグレー（濃い色で視認性向上）

        draw_badge(total, color)

        # ポップアップを安全に呼び出す
        if first:
            root.after(0, lambda: show_popup(data, setting))
            first = False
        elif prev_total is not None and total > prev_total:
            root.after(0, lambda: show_popup(data, setting))

        prev_total = total
        root.after(refresh * 1000, update_label)

    # ----------------------------------------
    # イベントバインド
    # ----------------------------------------
    canvas.bind("<Button-1>", drag_start)
    canvas.bind("<B1-Motion>", drag_move)
    canvas.bind("<MouseWheel>", resize)
    canvas.bind("<Double-Button-1>", open_page)
    root.protocol("WM_DELETE_WINDOW", on_close)

    # ----------------------------------------
    # 更新開始
    # ----------------------------------------
    threading.Thread(target=update_label, daemon=True).start()
    root.mainloop()


# ======================
# タスクトレイ制御
# ======================
def get_icon_image():
    if os.path.exists(ICON_FILE):
        return Image.open(ICON_FILE)

    # モダンな透明背景のアイコンを作成
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # メインの円形バッジ
    d.ellipse((8, 8, 56, 56), fill=(64, 128, 255, 220), outline=(255, 255, 255, 128), width=2)

    # 内側のハイライト効果
    d.ellipse((12, 12, 48, 48), fill=(128, 180, 255, 150))

    # シンプルなチェックマーク風のシンボル
    d.line((20, 28, 26, 34), fill=(255, 255, 255, 255), width=3, joint="curve")
    d.line((26, 34, 44, 22), fill=(255, 255, 255, 255), width=3, joint="curve")

    return img


def start_tray():
    def start(icon, item): threading.Thread(target=run_notifier, daemon=True).start()
    def restart(icon, item): os.execl(sys.executable, sys.executable, *sys.argv)
    def exit_app(icon, item): icon.stop(); os._exit(0)

    icon = pystray.Icon("approval_notifier", get_icon_image(), "承認通知")
    icon.menu = pystray.Menu(
        pystray.MenuItem("起動", start),
        pystray.MenuItem("再起動", restart),
        pystray.MenuItem("終了", exit_app)
    )

    # 🔸 デフォルトで起動状態にする
    threading.Thread(target=run_notifier, daemon=True).start()
    icon.run()


# ======================
# メイン実行
# ======================
if __name__ == "__main__":
    start_tray()
