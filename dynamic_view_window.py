import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from monitoring_service import get_top_coins
import threading
import time

class DynamicViewWindow(ttkb.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Top 20 Criptomoedas - Visão Analítica")
        self.geometry("1600x750") # Aumentar a largura da janela

        self.parent = parent
        self.running = True

        self.configure_styles()
        self.create_widgets()

        threading.Thread(target=self.load_data, daemon=True).start()
        self.start_auto_refresh()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_styles(self):
        style = ttkb.Style.get_instance()
        style.theme_use('cyborg')

        self.data_font = ("Consolas", 11)
        self.header_font = ("Consolas", 12, "bold")

        style.configure('Futuristic.Treeview', rowheight=28, font=self.data_font)
        style.configure('Futuristic.Treeview.Heading', font=self.header_font)

        self.positive_color = "#00FFFF"
        self.negative_color = "#FF00FF"

        style.map('Futuristic.Treeview',
                  background=[('selected', '#004040')],
                  foreground=[('selected', self.positive_color)])

        self.tree_style = style

    def create_widgets(self):
        self.main_frame = ttkb.Frame(self, padding=15)
        self.main_frame.pack(expand=True, fill=BOTH)

        header_frame = ttkb.Frame(self.main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        header = ttkb.Label(header_frame, text="[ TOP 20 MARKET OVERVIEW - ANALYTICAL ]", font=("Consolas", 18, "bold"), bootstyle="info")
        header.pack(side=LEFT)

        status_frame = ttkb.Frame(header_frame)
        status_frame.pack(side=RIGHT, padx=10)

        self.status_label = ttkb.Label(status_frame, text="SYNCING...", font=("Consolas", 10), bootstyle="secondary")
        self.status_label.pack(side=RIGHT, padx=10, pady=(5,0))

        self.status_progressbar = ttkb.Progressbar(
            status_frame, orient=HORIZONTAL, length=100, mode='determinate',
            maximum=60, bootstyle='info-striped'
        )
        self.status_progressbar.pack(side=RIGHT)

        columns = ("rank", "coin", "price", "change_24h", "high_24h", "low_24h", "ath", "ath_change", "volume_24h", "market_cap")
        self.tree = ttkb.Treeview(self.main_frame, columns=columns, show="headings", style='Futuristic.Treeview')

        self.tree.heading("rank", text="#")
        self.tree.heading("coin", text="MOEDA")
        self.tree.heading("price", text="PREÇO (USD)")
        self.tree.heading("change_24h", text="VARIAÇÃO (24H)")
        self.tree.heading("high_24h", text="MÁXIMA (24H)")
        self.tree.heading("low_24h", text="MÍNIMA (24H)")
        self.tree.heading("ath", text="ATH (USD)")
        self.tree.heading("ath_change", text="% DO ATH")
        self.tree.heading("volume_24h", text="VOLUME (24H)")
        self.tree.heading("market_cap", text="CAP. DE MERCADO")

        self.tree.column("rank", width=40, anchor=CENTER)
        self.tree.column("coin", width=200, anchor=W)
        self.tree.column("price", width=140, anchor=E)
        self.tree.column("change_24h", width=140, anchor=E)
        self.tree.column("high_24h", width=140, anchor=E)
        self.tree.column("low_24h", width=140, anchor=E)
        self.tree.column("ath", width=140, anchor=E)
        self.tree.column("ath_change", width=120, anchor=E)
        self.tree.column("volume_24h", width=180, anchor=E)
        self.tree.column("market_cap", width=200, anchor=E)

        self.tree_scrollbar = ttkb.Scrollbar(self.main_frame, orient=VERTICAL, command=self.tree.yview, bootstyle="round-info")
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)

        self.tree.pack(side=LEFT, expand=True, fill=BOTH)
        self.tree_scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.tag_configure('positive', foreground=self.positive_color)
        self.tree.tag_configure('negative', foreground=self.negative_color)

        self.error_label = ttkb.Label(self.main_frame, text="", font=("Consolas", 14, "bold"), bootstyle="danger", anchor=CENTER)

    def load_data(self):
        self.after(0, self._update_status, "SYNCING...")
        try:
            data = get_top_coins(20)
            self.after(0, self._populate_tree, data)
        except Exception as e:
            self.after(0, self._populate_tree, None)

    def _populate_tree(self, data):
        if self.error_label.winfo_ismapped(): self.error_label.pack_forget()
        if not self.tree.winfo_ismapped():
            self.tree.pack(side=LEFT, expand=True, fill=BOTH)
            self.tree_scrollbar.pack(side=RIGHT, fill=Y)

        selected_item = self.tree.selection()
        scroll_pos = self.tree.yview()

        self.tree.delete(*self.tree.get_children())

        if data is None:
            self.tree.pack_forget()
            self.tree_scrollbar.pack_forget()
            self.error_label.config(text="ERRO DE API: Não foi possível carregar os dados.\nVerifique a conexão ou tente novamente mais tarde.")
            self.error_label.pack(expand=True, fill=BOTH, padx=20, pady=20)
            self._update_status("API Error")
            return

        if not data:
             self.tree.insert("", END, values=("", "Nenhum dado retornado pela API.", "", "", "", "", "", "", "", ""))
             self._update_status("Dados não disponíveis")
             return

        for i, coin in enumerate(data):
            # Extração dos dados
            rank = coin.get('market_cap_rank', 'N/A')
            name = f"{coin.get('name', '???')} ({coin.get('symbol', 'N/A').upper()})"
            price = f"${coin.get('current_price', 0):,.4f}"
            change_24h = coin.get('price_change_percentage_24h', 0)
            high_24h = f"${coin.get('high_24h', 0):,.4f}"
            low_24h = f"${coin.get('low_24h', 0):,.4f}"
            ath = f"${coin.get('ath', 0):,.4f}"
            ath_change = coin.get('ath_change_percentage', 0)
            volume_24h = f"${coin.get('total_volume', 0):,}"
            market_cap = f"${coin.get('market_cap', 0):,}"

            # Formatação
            change_24h_str = f"{change_24h:+.2f}%" if change_24h is not None else "N/A"
            ath_change_str = f"{ath_change:+.2f}%" if ath_change is not None else "N/A"

            # Tag de cor
            tag = ''
            if change_24h is not None:
                if change_24h > 0: tag = 'positive'
                elif change_24h < 0: tag = 'negative'

            values = (rank, name, price, change_24h_str, high_24h, low_24h, ath, ath_change_str, volume_24h, market_cap)
            self.tree.insert("", END, values=values, iid=i, tags=(tag,))

        if selected_item: self.tree.selection_set(selected_item)
        self.tree.yview_moveto(scroll_pos[0])

        timestamp = time.strftime('%H:%M:%S')
        self._update_status(f"LAST SYNC: {timestamp}")

    def _update_status(self, message):
        self.status_label.config(text=message)

    def start_auto_refresh(self):
        self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
        self.refresh_thread.start()

    def _auto_refresh_loop(self):
        while self.running:
            for i in range(60):
                if not self.running: break
                self.after(0, self.status_progressbar.config, {'value': 60 - i})
                time.sleep(1)

            if self.running:
                self.after(0, self.status_progressbar.config, {'value': 0})
                threading.Thread(target=self.load_data, daemon=True).start()

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == '__main__':
    app = ttkb.Window(themename="cyborg")
    dynamic_window = DynamicViewWindow(app)
    app.mainloop()
