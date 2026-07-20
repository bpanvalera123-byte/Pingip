import subprocess
import platform
import threading
import time
import re
import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ping Monitor")
        self.geometry("600x650")
        self.resizable(False, False)

        self.ip_list = []
        self.max_ips = 10
        self.is_monitoring = True

        # Параметры скрытия окна для Windows
        self.startupinfo = None
        self.creationflags = 0
        if platform.system().lower() == "windows":
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.creationflags = subprocess.CREATE_NO_WINDOW

        # === Верхняя панель ввода ===
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=15, padx=20, fill="x")

        self.ip_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Введите IP или домен (напр. 8.8.8.8)", width=350)
        self.ip_entry.pack(side="left", padx=10, pady=10)
        self.ip_entry.bind("<Return>", lambda event: self.add_ip())

        self.add_btn = ctk.CTkButton(self.input_frame, text="Добавить", command=self.add_ip, width=100)
        self.add_btn.pack(side="left", padx=5, pady=10)

        # Счетчик IP
        self.counter_label = ctk.CTkLabel(self, text=f"Добавлено: 0 / {self.max_ips}", font=("Arial", 12))
        self.counter_label.pack(anchor="w", padx=25)

        # === Контейнер для карточек IP ===
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=540, height=500)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.cards = {}

        # Фоновый поток пинга
        self.ping_thread = threading.Thread(target=self.update_pings, daemon=True)
        self.ping_thread.start()

    def add_ip(self):
        ip = self.ip_entry.get().strip()

        if not ip or len(self.ip_list) >= self.max_ips or ip in self.ip_list:
            self.ip_entry.delete(0, 'end')
            return

        self.ip_list.append(ip)
        self.create_card(ip)
        self.ip_entry.delete(0, 'end')
        self.update_counter()

    def remove_ip(self, ip):
        if ip in self.ip_list:
            self.ip_list.remove(ip)
            self.cards[ip]["frame"].destroy()
            del self.cards[ip]
            self.update_counter()

    def update_counter(self):
        self.counter_label.configure(text=f"Добавлено: {len(self.ip_list)} / {self.max_ips}")
        self.add_btn.configure(state="disabled" if len(self.ip_list) >= self.max_ips else "normal")

    def create_card(self, ip):
        card_frame = ctk.CTkFrame(self.scroll_frame)
        card_frame.pack(fill="x", pady=6, padx=5)

        # IP/Домен
        title_label = ctk.CTkLabel(card_frame, text=ip, font=("Arial", 14, "bold"), width=160, anchor="w")
        title_label.pack(side="left", padx=15, pady=12)

        # Поле для отображения самого ПИНГА (в цифрах)
        ping_label = ctk.CTkLabel(card_frame, text="-- ms", font=("Arial", 15, "bold"), width=100, text_color="#A0A0A0")
        ping_label.pack(side="left", padx=5)

        # Поле таймера потери связи
        offline_label = ctk.CTkLabel(card_frame, text="", font=("Arial", 11), width=130, text_color="#F44336")
        offline_label.pack(side="left", padx=5)

        # Кнопка удаления
        del_btn = ctk.CTkButton(card_frame, text="✕", width=32, height=32, fg_color="#db524b", hover_color="#bc3b34",
                                 command=lambda: self.remove_ip(ip))
        del_btn.pack(side="right", padx=10)

        self.cards[ip] = {
            "frame": card_frame,
            "ping_label": ping_label,
            "offline_label": offline_label,
            "offline_since": None  # Время начала сбоя
        }

    def ping_host(self, host):
        is_win = platform.system().lower() == 'windows'
        param = '-n' if is_win else '-c'
        timeout_param = '-w' if is_win else '-W'
        
        command = ['ping', param, '1', timeout_param, '1000', host]

        try:
            # Передаём параметры скрытия окна консоли
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                startupinfo=self.startupinfo,
                creationflags=self.creationflags
            )
            
            if "TTL=" in output or "ttl=" in output:
                # Надёжное извлечение миллисекунд через регулярные выражения
                match = re.search(r'(?:time|время)[=<](\d+)\s*ms', output, re.IGNORECASE)
                if not match:
                    match = re.search(r'(?:time|время)[=<](\d+)\s*мс', output, re.IGNORECASE)
                
                ms = match.group(1) if match else "1"
                return True, f"{ms} ms"
            else:
                return False, "Таймаут"
        except Exception:
            return False, "Оффлайн"

    def format_time(self, seconds):
        """Форматирование секунд в чч:мм:сс"""
        hrs, remainder = divmod(int(seconds), 3600)
        mins, secs = divmod(remainder, 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def update_pings(self):
        while self.is_monitoring:
            current_ips = list(self.ip_list)
            for ip in current_ips:
                success, ping_str = self.ping_host(ip)
                
                if ip in self.cards:
                    card = self.cards[ip]
                    
                    if success:
                        card["offline_since"] = None
                        card["ping_label"].configure(text=ping_str, text_color="#2ECC71") # Ярко-зелёный
                        card["offline_label"].configure(text="")
                    else:
                        # Фиксируем время первой потери связи
                        if card["offline_since"] is None:
                            card["offline_since"] = time.time()
                        
                        elapsed = time.time() - card["offline_since"]
                        time_formatted = self.format_time(elapsed)
                        
                        card["ping_label"].configure(text=ping_str, text_color="#E74C3C") # Красный
                        card["offline_label"].configure(text=f"Сбой: {time_formatted}")

            time.sleep(1.2)

if __name__ == "__main__":
    app = PingApp()
    app.mainloop()
                for line in output.splitlines():
                    if "время=" in line.lower() or "time=" in line.lower():
                        parts = line.split()
                        for p in parts:
                            if "время=" in p.lower() or "time=" in p.lower():
                                time_str = p.split("=")[-1].replace("ms", "").replace("мс", "").strip()
                                return f"{time_str} ms", "#4CAF50" # Зеленый
                return "Доступен", "#4CAF50"
            else:
                return "Таймаут", "#F44336" # Красный
        except Exception:
            return "Недоступен", "#F44336"

    def update_pings(self):
        while self.is_monitoring:
            current_ips = list(self.ip_list)
            for ip in current_ips:
                result_text, color = self.ping_host(ip)
                if ip in self.cards:
                    # Обновление UI из потока
                    self.cards[ip]["status"].configure(text=result_text, text_color=color)
            time.sleep(1.5)

if __name__ == "__main__":
    app = PingApp()
    app.mainloop()
