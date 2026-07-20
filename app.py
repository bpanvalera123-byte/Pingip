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

        # Параметры для скрытия окна консоли на Windows
        self.startupinfo = None
        self.creationflags = 0
        if platform.system().lower() == "windows":
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.creationflags = subprocess.CREATE_NO_WINDOW

        # === Панель ввода ===
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=15, padx=20, fill="x")

        # Поле для IP
        self.ip_entry = ctk.CTkEntry(self.input_frame, placeholder_text="IP / Домен (напр. 8.8.8.8)", width=220)
        self.ip_entry.grid(row=0, column=0, padx=10, pady=10)
        self.ip_entry.bind("<Return>", lambda event: self.add_ip())

        # Поле для Подписи
        self.label_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Название (напр. Сервер 1)", width=180)
        self.label_entry.grid(row=0, column=1, padx=5, pady=10)
        self.label_entry.bind("<Return>", lambda event: self.add_ip())

        # Кнопка добавления
        self.add_btn = ctk.CTkButton(self.input_frame, text="Добавить", command=self.add_ip, width=100)
        self.add_btn.grid(row=0, column=2, padx=10, pady=10)

        # Счётчик элементов
        self.counter_label = ctk.CTkLabel(self, text=f"Добавлено: 0 / {self.max_ips}", font=("Arial", 12))
        self.counter_label.pack(anchor="w", padx=25)

        # === Список элементов ===
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=580, height=530)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Загрузка сохраненных IP из файла
        self.load_config()

    def load_config(self):
        """Загрузка IP из JSON файла при запуске"""
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
        """Сохранение текущего списка IP в JSON файл"""
        data = []
        for ip, card in self.cards.items():
            data.append({
                "ip": ip,
                "name": card["name"]
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
            self.cards[ip]["is_active"] = False # Останавливаем поток пинга
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
        card_frame.pack(fill="x", pady=6, padx=5)

        # Подпись + IP
        display_title = name if name else ip
        title_label = ctk.CTkLabel(card_frame, text=display_title, font=("Arial", 14, "bold"), width=160, anchor="w")
        title_label.pack(side="left", padx=15, pady=8)

        # Описание (если есть имя, снизу выводим сам IP мелким шрифтом)
        if name:
            sub_label = ctk.CTkLabel(card_frame, text=f"({ip})", font=("Arial", 10), text_color="#888888", anchor="w")
            sub_label.pack(side="left", padx=(0, 10))

        # Поле реального времени для пинга
        ping_label = ctk.CTkLabel(card_frame, text="-- ms", font=("Arial", 15, "bold"), width=90, text_color="#A0A0A0")
        ping_label.pack(side="left", padx=5)

        # Поле таймера сбоя
        offline_label = ctk.CTkLabel(card_frame, text="", font=("Arial", 11), width=120, text_color="#F44336")
        offline_label.pack(side="left", padx=5)

        # Кнопка удаления
        del_btn = ctk.CTkButton(card_frame, text="✕", width=30, height=30, fg_color="#db524b", hover_color="#bc3b34",
                                 command=lambda: self.remove_ip(ip))
        del_btn.pack(side="right", padx=10)

        card_data = {
            "frame": card_frame,
            "ping_label": ping_label,
            "offline_label": offline_label,
            "offline_since": None,
            "name": name,
            "is_active": True
        }
        self.cards[ip] = card_data

        # Запускаем отдельный независимый поток для непрерывного пинга этого адреса
        t = threading.Thread(target=self.monitor_host, args=(ip,), daemon=True)
        t.start()

    def ping_host(self, host):
        is_win = platform.system().lower() == 'windows'
        param = '-n' if is_win else '-c'
        timeout_param = '-w' if is_win else '-W'
        
        command = ['ping', param, '1', timeout_param, '1000', host]

        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                startupinfo=self.startupinfo,
                creationflags=self.creationflags
            )
            
            if "TTL=" in output or "ttl=" in output:
                match = re.search(r'(?:time|время)[=<](\d+)\s*(?:ms|мс)', output, re.IGNORECASE)
                ms = match.group(1) if match else "1"
                return True, f"{ms} ms"
            else:
                return False, "Таймаут"
        except Exception:
            return False, "Оффлайн"

    def format_time(self, seconds):
        hrs, remainder = divmod(int(seconds), 3600)
        mins, secs = divmod(remainder, 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def monitor_host(self, ip):
        """Индивидуальный поток мониторинга конкретного IP в реальном времени"""
        while self.is_monitoring and ip in self.cards and self.cards[ip]["is_active"]:
            success, ping_str = self.ping_host(ip)
            
            if ip not in self.cards or not self.cards[ip]["is_active"]:
                break

            card = self.cards[ip]
            
            if success:
                card["offline_since"] = None
                card["ping_label"].configure(text=ping_str, text_color="#2ECC71") # Зелёный
                card["offline_label"].configure(text="")
            else:
                if card["offline_since"] is None:
                    card["offline_since"] = time.time()
                
                elapsed = time.time() - card["offline_since"]
                time_formatted = self.format_time(elapsed)
                
                card["ping_label"].configure(text=ping_str, text_color="#E74C3C") # Красный
                card["offline_label"].configure(text=f"Сбой: {time_formatted}")

            # Пауза 1 секунда между измерениями
            time.sleep(1.0)

if __name__ == "__main__":
    app = PingApp()
    app.mainloop()
