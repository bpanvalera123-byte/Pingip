import subprocess
import platform
import threading
import time
import json
import os
import re
import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

class PingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ping Monitor")
        self.geometry("640x700")
        self.resizable(False, False)

        self.max_ips = 10
        self.is_monitoring = True
        self.cards = {}

        # Настройки скрытия окна консоли
        self.startupinfo = None
        self.creationflags = 0
        if platform.system().lower() == "windows":
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.creationflags = subprocess.CREATE_NO_WINDOW

        # === Панель ввода ===
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=15, padx=20, fill="x")

        self.ip_entry = ctk.CTkEntry(self.input_frame, placeholder_text="IP / Домен (напр. 8.8.8.8)", width=220)
        self.ip_entry.grid(row=0, column=0, padx=10, pady=10)
        self.ip_entry.bind("<Return>", lambda event: self.add_ip())

        self.label_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Название (напр. Сервер)", width=180)
        self.label_entry.grid(row=0, column=1, padx=5, pady=10)
        self.label_entry.bind("<Return>", lambda event: self.add_ip())

        self.add_btn = ctk.CTkButton(self.input_frame, text="Добавить", command=self.add_ip, width=100)
        self.add_btn.grid(row=0, column=2, padx=10, pady=10)

        # Счётчик
        self.counter_label = ctk.CTkLabel(self, text=f"Добавлено: 0 / {self.max_ips}", font=("Arial", 12))
        self.counter_label.pack(anchor="w", padx=25)

        # === Список элементов ===
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=580, height=530)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved_items = json.load(f)
                    for item in saved_items:
                        if len(self.cards) < self.max_ips:
                            self.add_card_to_ui(item["ip"], item.get("name", ""))
            except Exception as e:
                print(f"Ошибка чтения конфига: {e}")
        self.update_counter()

    def save_config(self):
        data = [{"ip": ip, "name": card["name"]} for ip, card in self.cards.items()]
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")

    def add_ip(self):
        ip = self.ip_entry.get().strip()
        name = self.label_entry.get().strip()

        if not ip or len(self.cards) >= self.max_ips or ip in self.cards:
            self.ip_entry.delete(0, 'end')
            return

        self.add_card_to_ui(ip, name)
        self.save_config()
        
        self.ip_entry.delete(0, 'end')
        self.label_entry.delete(0, 'end')
        self.update_counter()

    def remove_ip(self, ip):
        if ip in self.cards:
            self.cards[ip]["is_active"] = False
            self.cards[ip]["frame"].destroy()
            del self.cards[ip]
            self.save_config()
            self.update_counter()

    def update_counter(self):
        count = len(self.cards)
        self.counter_label.configure(text=f"Добавлено: {count} / {self.max_ips}")
        self.add_btn.configure(state="disabled" if count >= self.max_ips else "normal")

    def add_card_to_ui(self, ip, name=""):
        card_frame = ctk.CTkFrame(self.scroll_frame)
import subprocess
import platform
import threading
import time
import json
import os
import re
import customtkinter as ctk
from tkinter import colorchooser

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

class SettingsDialog(ctk.CTkToplevel):
    """Окно индивидуальных настроек карточки IP"""
    def __init__(self, parent, ip, current_interval, current_color, on_save_callback):
        super().__init__(parent)
        self.title(f"Настройки: {ip}")
        self.geometry("360x280")
        self.resizable(False, False)
        self.grab_set()

        self.on_save_callback = on_save_callback
        self.selected_color = current_color

        title_lbl = ctk.CTkLabel(self, text=f"Настройки для {ip}", font=("Arial", 14, "bold"))
        title_lbl.pack(pady=(15, 10))

        # --- Интервал ---
        interval_frame = ctk.CTkFrame(self)
        interval_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(interval_frame, text="Интервал пинга (сек):").pack(side="left", padx=10, pady=10)
        
        self.interval_var = ctk.DoubleVar(value=current_interval)
        self.slider_label = ctk.CTkLabel(interval_frame, text=f"{current_interval:.1f}s", font=("Arial", 12, "bold"), width=40)
        self.slider_label.pack(side="right", padx=10)

        self.slider = ctk.CTkSlider(
            interval_frame, 
            from_=0.5, 
            to=15.0, 
            number_of_steps=29, 
            variable=self.interval_var,
            command=self._on_slider_change
        )
        self.slider.pack(side="right", fill="x", expand=True, padx=5)

        # --- Цвет фона ---
        color_frame = ctk.CTkFrame(self)
        color_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(color_frame, text="Цвет строки:").pack(side="left", padx=10, pady=10)
        
        self.color_preview = ctk.CTkFrame(color_frame, width=24, height=24, fg_color=self.selected_color or "#2B2B2B")
        self.color_preview.pack(side="left", padx=5)

        pick_btn = ctk.CTkButton(color_frame, text="Выбрать цвет", command=self._pick_color, width=110)
        pick_btn.pack(side="right", padx=10)

        reset_color_btn = ctk.CTkButton(color_frame, text="Сброс", command=self._reset_color, width=60, fg_color="#555555")
        reset_color_btn.pack(side="right", padx=(0, 5))

        # --- Кнопка Сохранить ---
        save_btn = ctk.CTkButton(self, text="Сохранить", command=self._save)
        save_btn.pack(pady=15)

    def _on_slider_change(self, value):
        self.slider_label.configure(text=f"{value:.1f}s")

    def _pick_color(self):
        color = colorchooser.askcolor(title="Выберите цвет строки", initialcolor=self.selected_color or "#2B2B2B")
        if color[1]:
            self.selected_color = color[1]
            self.color_preview.configure(fg_color=self.selected_color)

    def _reset_color(self):
        self.selected_color = None
        self.color_preview.configure(fg_color="#2B2B2B")

    def _save(self):
        interval = round(self.interval_var.get(), 1)
        self.on_save_callback(interval, self.selected_color)
        self.destroy()


class PingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ping Monitor Pro")
        self.geometry("680x700")
        
        self.resizable(True, True)
        self.minsize(580, 400)

        self.max_ips = 10
        self.is_monitoring = True
        self.cards = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.startupinfo = None
        self.creationflags = 0
        if platform.system().lower() == "windows":
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.creationflags = subprocess.CREATE_NO_WINDOW

        # === Панель ввода ===
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, pady=15, padx=20, sticky="ew")

        self.input_frame.grid_columnconfigure(0, weight=3)
        self.input_frame.grid_columnconfigure(1, weight=2)
        self.input_frame.grid_columnconfigure(2, weight=0)

        self.ip_entry = ctk.CTkEntry(self.input_frame, placeholder_text="IP / Домен (напр. 8.8.8.8)")
        self.ip_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.ip_entry.bind("<Return>", lambda event: self.add_ip())

        self.label_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Название (напр. Сервер)")
        self.label_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.label_entry.bind("<Return>", lambda event: self.add_ip())

        self.add_btn = ctk.CTkButton(self.input_frame, text="Добавить", command=self.add_ip, width=100)
        self.add_btn.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Счётчик
        self.counter_label = ctk.CTkLabel(self, text=f"Добавлено: 0 / {self.max_ips}", font=("Arial", 12))
        self.counter_label.grid(row=1, column=0, anchor="w", padx=25, pady=(0, 5))

        # === Список элементов ===
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=2, column=0, pady=(0, 15), padx=20, sticky="nsew")

        self.load_config()

        self.monitor_thread = threading.Thread(target=self.global_monitor_loop, daemon=True)
        self.monitor_thread.start()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved_items = json.load(f)
                    for item in saved_items:
                        if len(self.cards) < self.max_ips:
                            self.add_card_to_ui(
                                ip=item["ip"], 
                                name=item.get("name", ""),
                                interval=item.get("interval", 1.0),
                                color=item.get("color", None),
                                offline_since=item.get("offline_since", None)
                            )
            except Exception as e:
                print(f"Ошибка чтения конфига: {e}")
        self.update_counter()

    def save_config(self):
        data = []
        for ip, card in self.cards.items():
            data.append({
                "ip": ip,
                "name": card["name"],
                "interval": card["interval"],
                "color": card["color"],
                "offline_since": card["offline_since"]
            })
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")

    def add_ip(self):
        ip = self.ip_entry.get().strip()
        name = self.label_entry.get().strip()

        if not ip or len(self.cards) >= self.max_ips or ip in self.cards:
            self.ip_entry.delete(0, 'end')
            return

        self.add_card_to_ui(ip, name)
        self.save_config()
        
        self.ip_entry.delete(0, 'end')
        self.label_entry.delete(0, 'end')
        self.update_counter()

    def remove_ip(self, ip):
        if ip in self.cards:
            self.cards[ip]["frame"].destroy()
            del self.cards[ip]
            self.save_config()
            self.update_counter()

    def update_counter(self):
        count = len(self.cards)
        self.counter_label.configure(text=f"Добавлено: {count} / {self.max_ips}")
        self.add_btn.configure(state="disabled" if count >= self.max_ips else "normal")

    def open_settings(self, ip):
        card = self.cards.get(ip)
        if not card:
            return

        def save_callback(new_interval, new_color):
            card["interval"] = new_interval
            card["color"] = new_color
            
            if new_color:
                card["frame"].configure(fg_color=new_color)
            else:
                card["frame"].configure(fg_color=["#3b3b3b", "#2b2b2b"])
                
            self.save_config()

        SettingsDialog(self, ip, card["interval"], card["color"], save_callback)

    def add_card_to_ui(self, ip, name="", interval=1.0, color=None, offline_since=None):
        card_frame = ctk.CTkFrame(self.scroll_frame)
        if color:
            card_frame.configure(fg_color=color)
            
        card_frame.pack(fill="x", pady=6, padx=5)

        display_title = name if name else ip
        title_label = ctk.CTkLabel(card_frame, text=display_title, font=("Arial", 14, "bold"), width=130, anchor="w")
        title_label.pack(side="left", padx=12, pady=8)

        if name:
            sub_label = ctk.CTkLabel(card_frame, text=f"({ip})", font=("Arial", 10), text_color="#888888", anchor="w")
            sub_label.pack(side="left", padx=(0, 5))

        ping_label = ctk.CTkLabel(card_frame, text="-- ms", font=("Arial", 15, "bold"), width=85, text_color="#A0A0A0")
        ping_label.pack(side="left", padx=5)

        offline_label = ctk.CTkLabel(card_frame, text="", font=("Arial", 11), width=110, text_color="#F44336")
        offline_label.pack(side="left", padx=5)

        del_btn = ctk.CTkButton(card_frame, text="✕", width=30, height=30, fg_color="#db524b", hover_color="#bc3b34",
                                 command=lambda: self.remove_ip(ip))
        del_btn.pack(side="right", padx=(5, 10))

        settings_btn = ctk.CTkButton(card_frame, text="⚙", width=30, height=30, fg_color="#555555", hover_color="#666666",
                                     command=lambda: self.open_settings(ip))
        settings_btn.pack(side="right", padx=2)

        self.cards[ip] = {
            "frame": card_frame,
            "ping_label": ping_label,
            "offline_label": offline_label,
            "offline_since": offline_since,
            "name": name,
            "interval": interval,
            "color": color,
            "is_pinging": False,
            "last_ping_time": 0
        }

    def ping_host(self, host):
        is_win = platform.system().lower() == 'windows'
        param = '-n' if is_win else '-c'
        timeout_param = '-w' if is_win else '-W'
        
        command = ['ping', param, '1', timeout_param, '1000', host]

        try:
            start_time = time.time()
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                startupinfo=self.startupinfo,
                creationflags=self.creationflags
            )
            
            if "TTL=" in output or "ttl=" in output:
                match = re.search(r'(?:time|время)[=<]\s*(\d+)\s*(?:ms|мс)?', output, re.IGNORECASE)
                if match:
                    ms_val = int(match.group(1))
                    return True, ms_val
                else:
                    calc_ms = int((time.time() - start_time) * 1000)
                    return True, max(1, calc_ms)
            else:
                return False, "Таймаут"
        except Exception:
            return False, "Недоступен"

    def format_time(self, seconds):
        hrs, remainder = divmod(int(seconds), 3600)
        mins, secs = divmod(remainder, 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def global_monitor_loop(self):
        while self.is_monitoring:
            now = time.time()
            active_ips = list(self.cards.keys())
            
            for ip in active_ips:
                if ip not in self.cards:
                    continue

                card = self.cards[ip]
                if not card["is_pinging"] and (now - card["last_ping_time"] >= card["interval"]):
                    card["is_pinging"] = True
                    card["last_ping_time"] = now
                    threading.Thread(target=self._ping_worker, args=(ip,), daemon=True).start()

            time.sleep(0.1)

    def _ping_worker(self, ip):
        try:
            if ip not in self.cards:
                return

            success, ping_result = self.ping_host(ip)

            if ip not in self.cards:
                return

            card = self.cards[ip]

            if success:
                # Восстановление связи
                if card["offline_since"] is not None:
                    card["offline_since"] = None
                    self.save_config()

                ms_value = ping_result
                display_text = f"{ms_value} ms"

                # Выбор цвета текста на основе порога в 100 ms
                if ms_value > 100:
                    text_color = "#E67E22"  # Оранжевый
                else:
                    text_color = "#2ECC71"  # Зеленый

                card["ping_label"].configure(text=display_text, text_color=text_color)
                card["offline_label"].configure(text="")
            else:
                # Фиксация времени обрыва
                if card["offline_since"] is None:
                    card["offline_since"] = time.time()
                    self.save_config()

                elapsed = time.time() - card["offline_since"]
                time_formatted = self.format_time(elapsed)

                card["ping_label"].configure(text=str(ping_result), text_color="#E74C3C")  # Красный
                card["offline_label"].configure(text=f"Сбой: {time_formatted}")
        finally:
            if ip in self.cards:
                self.cards[ip]["is_pinging"] = False

if __name__ == "__main__":
    app = PingApp()
    app.mainloop()
