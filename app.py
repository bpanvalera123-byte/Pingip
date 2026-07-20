import subprocess
import platform
import threading
import time
import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ping Monitor (Max 10 IP)")
        self.geometry("520x600")
        self.resizable(False, False)

        self.ip_list = []
        self.max_ips = 10
        self.is_monitoring = True

        # === Верхняя панель ввода ===
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=15, padx=20, fill="x")

        self.ip_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Введите IP или домен (напр. 8.8.8.8)", width=300)
        self.ip_entry.pack(side="left", padx=10, pady=10)

        self.add_btn = ctk.CTkButton(self.input_frame, text="Добавить", command=self.add_ip, width=100)
        self.add_btn.pack(side="left", padx=5, pady=10)

        # Счетчищик
        self.counter_label = ctk.CTkLabel(self, text=f"Добавлено: 0 / {self.max_ips}", font=("Arial", 12))
        self.counter_label.pack(anchor="w", padx=25)

        # === Контейнер для карточек IP ===
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=470, height=450)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.cards = {}

        # Запуск фонового потока пинга
        self.ping_thread = threading.Thread(target=self.update_pings, daemon=True)
        self.ping_thread.start()

    def add_ip(self):
        ip = self.ip_entry.get().strip()

        if not ip:
            return
        if len(self.ip_list) >= self.max_ips:
            return
        if ip in self.ip_list:
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
        if len(self.ip_list) >= self.max_ips:
            self.add_btn.configure(state="disabled")
        else:
            self.add_btn.configure(state="normal")

    def create_card(self, ip):
        card_frame = ctk.CTkFrame(self.scroll_frame)
        card_frame.pack(fill="x", pady=5, padx=5)

        title_label = ctk.CTkLabel(card_frame, text=ip, font=("Arial", 14, "bold"), width=180, anchor="w")
        title_label.pack(side="left", padx=15, pady=10)

        status_label = ctk.CTkLabel(card_frame, text="Измерение...", font=("Arial", 12), width=150)
        status_label.pack(side="left", padx=10)

        del_btn = ctk.CTkButton(card_frame, text="✕", width=30, fg_color="#db524b", hover_color="#bc3b34",
                                 command=lambda: self.remove_ip(ip))
        del_btn.pack(side="right", padx=10)

        self.cards[ip] = {
            "frame": card_frame,
            "status": status_label
        }

    def ping_host(self, host):
        # Определение флага в зависимости от ОС
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
        
        # Команда 1 пакет с таймаутом 1000мс
        command = ['ping', param, '1', timeout_param, '1000', host]

        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
            if "TTL=" in output or "ttl=" in output:
                # Извлечение времени
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
