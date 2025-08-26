import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from monitoring_service import get_top_100_coins
import threading
import time

class DynamicViewWindow(ttkb.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Visão Dinâmica de Criptomoedas")
        self.geometry("1300x750")

        self.parent = parent
        self.running = True

        self.configure_styles()
        self.create_widgets()

        # Iniciar o carregamento de dados em uma thread para não bloquear a UI
        threading.Thread(target=self.load_data, daemon=True).start()
        self.start_auto_refresh()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_styles(self):
        style = ttkb.Style.get_instance()
        # Usando o tema 'cyborg' que é escuro e já tem um apelo tecnológico
        style.theme_use('cyborg')

        # Fontes
        self.data_font = ("Consolas", 11)
        self.header_font = ("Consolas", 12, "bold")

        style.configure('Futuristic.Treeview', rowheight=28, font=self.data_font)
        style.configure('Futuristic.Treeview.Heading', font=self.header_font)

        # Cores "neon"
        self.positive_color = "#00FFFF"  # Ciano
        self.negative_color = "#FF00FF"  # Magenta

        style.map('Futuristic.Treeview',
                  background=[('selected', '#004040')],
                  foreground=[('selected', self.positive_color)])

        self.tree_style = style

    def create_widgets(self):
        main_frame = ttkb.Frame(self, padding=15)
        main_frame.pack(expand=True, fill=BOTH)

        header_frame = ttkb.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        header = ttkb.Label(header_frame, text="[ DYNAMIC MARKET OVERVIEW ]", font=("Consolas", 18, "bold"), bootstyle="info")
        header.pack(side=LEFT)

        status_frame = ttkb.Frame(header_frame)
        status_frame.pack(side=RIGHT, padx=10)

        self.status_label = ttkb.Label(status_frame, text="SYNCING...", font=("Consolas", 10), bootstyle="secondary")
        self.status_label.pack(side=RIGHT, padx=10)

        self.status_meter = ttkb.Meter(
            status_frame,
            metersize=20,
            radius=10,
            metertype='semi',
            arcrange=359,
            arcoffset=180,
            amounttotal=60,
            amountused=0,
            bootstyle='info',
            subtext='',
            interactive=False
        )
        self.status_meter.pack(side=RIGHT)

        self.tree = ttkb.Treeview(
            main_frame,
            columns=("rank", "coin", "price", "change_24h", "volume_24h", "market_cap"),
            show="headings",
            style='Futuristic.Treeview'
        )

        self.tree.heading("rank", text="#")
        self.tree.heading("coin", text="MOEDA")
        self.tree.heading("price", text="PREÇO (USD)")
        self.tree.heading("change_24h", text="VARIAÇÃO (24H)")
        self.tree.heading("volume_24h", text="VOLUME (24H)")
        self.tree.heading("market_cap", text="CAP. DE MERCADO")

        self.tree.column("rank", width=50, anchor=CENTER)
        self.tree.column("coin", width=220, anchor=W)
        self.tree.column("price", width=160, anchor=E)
        self.tree.column("change_24h", width=160, anchor=E)
        self.tree.column("volume_24h", width=200, anchor=E)
        self.tree.column("market_cap", width=250, anchor=E)

        scrollbar = ttkb.Scrollbar(main_frame, orient=VERTICAL, command=self.tree.yview, bootstyle="round-info")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, expand=True, fill=BOTH)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.tag_configure('positive', foreground=self.positive_color)
        self.tree.tag_configure('negative', foreground=self.negative_color)

    def load_data(self):
        self.after(0, self._update_status, "SYNCING...")
        data = get_top_100_coins()
        self.after(0, self._populate_tree, data)

        timestamp = time.strftime('%H:%M:%S')
        self.after(0, self._update_status, f"LAST SYNC: {timestamp}")

    def _populate_tree(self, data):
        selected_item = self.tree.selection()
        scroll_pos = self.tree.yview()

        self.tree.delete(*self.tree.get_children())

        if not data:
            self.tree.insert("", END, values=("", "Falha na sincronização com a API.", "", "", "", ""))
            return

        for i, coin in enumerate(data):
            rank = coin.get('market_cap_rank', 'N/A')
            name = f"{coin.get('name', '???')} ({coin.get('symbol', 'N/A').upper()})"
            price = f"${coin.get('current_price', 0):,.4f}"
            change_24h = coin.get('price_change_percentage_24h', 0)
            change_24h_str = f"{change_24h:+.2f}%" if change_24h is not None else "N/A"
            volume_24h = f"${coin.get('total_volume', 0):,}"
            market_cap = f"${coin.get('market_cap', 0):,}"

            tag = ''
            if change_24h is not None:
                if change_24h > 0: tag = 'positive'
                elif change_24h < 0: tag = 'negative'

            values = (rank, name, price, change_24h_str, volume_24h, market_cap)
            self.tree.insert("", END, values=values, iid=i, tags=(tag,))

        if selected_item: self.tree.selection_set(selected_item)
        self.tree.yview_moveto(scroll_pos[0])

    def _update_status(self, message):
        self.status_label.config(text=message)

    def start_auto_refresh(self):
        self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
        self.refresh_thread.start()

    def _auto_refresh_loop(self):
        while self.running:
            for i in range(60):
                if not self.running: break
                self.after(0, self.status_meter.configure, {'amountused': 60 - i})
                time.sleep(1)

            if self.running:
                threading.Thread(target=self.load_data, daemon=True).start()

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == '__main__':
    # Usar o tema 'cyborg' para o teste local
    app = ttkb.Window(themename="cyborg")
    dynamic_window = DynamicViewWindow(app)
    app.mainloop()
