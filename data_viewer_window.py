import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
import threading
from datetime import datetime
from tkinter import messagebox

class DataViewerWindow(ttkb.Toplevel):
    def __init__(self, master, parent_app, cg_client, data_cache_instance, rate_limiter_instance):
        super().__init__(master)
        self.parent_app = parent_app
        self.cg_client = cg_client
        self.data_cache = data_cache_instance
        self.rate_limiter = rate_limiter_instance

        self.title("Visualizador de Dados do Mercado")
        self.geometry("1366x768")
        self.minsize(1024, 600)

        self.setup_ui()
        self.parent_app.center_toplevel_on_main(self)
        self.transient(self.master)
        self.grab_set()

        # Inicia a busca de dados ao abrir a janela
        self.start_data_fetch_thread()

    def setup_ui(self):
        main_frame = ttkb.Frame(self, padding=10)
        main_frame.pack(expand=True, fill='both')

        # Frame para os controles (botão de atualizar)
        controls_frame = ttkb.Frame(main_frame)
        controls_frame.pack(fill='x', pady=(0, 10))

        self.run_button = ttkb.Button(controls_frame, text="🔄 Atualizar Dados", command=self.start_data_fetch_thread, bootstyle="info")
        self.run_button.pack(side='left')

        self.status_label = ttkb.Label(controls_frame, text="", font=("Segoe UI", 10))
        self.status_label.pack(side='right', padx=10)

        # Treeview para exibir os dados
        tree_frame = ttkb.Frame(main_frame)
        tree_frame.pack(expand=True, fill='both')

        columns = ("#", "name", "price", "24h", "market_cap", "volume")
        self.tree = ttkb.Treeview(tree_frame, columns=columns, show='headings', bootstyle="primary")

        # Definindo os cabeçalhos
        self.tree.heading("#", text="Rank")
        self.tree.heading("name", text="Nome")
        self.tree.heading("price", text="Preço (USD)")
        self.tree.heading("24h", text="Variação (24h)")
        self.tree.heading("market_cap", text="Capitalização de Mercado")
        self.tree.heading("volume", text="Volume (24h)")

        # Configurando as colunas
        self.tree.column("#", width=60, anchor='center')
        self.tree.column("name", width=250)
        self.tree.column("price", width=150, anchor='e')
        self.tree.column("24h", width=120, anchor='e')
        self.tree.column("market_cap", width=220, anchor='e')
        self.tree.column("volume", width=220, anchor='e')

        # Scrollbar
        scrollbar = ttkb.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')

        # Tags de estilo para as linhas
        self.tree.tag_configure('gain', foreground='#28a745') # Verde
        self.tree.tag_configure('loss', foreground='#dc3545') # Vermelho

    def start_data_fetch_thread(self):
        self.run_button.config(state="disabled", text="Atualizando...")
        self.status_label.config(text="Buscando dados, por favor aguarde...")
        for i in self.tree.get_children():
            self.tree.delete(i)
        threading.Thread(target=self.fetch_market_data, daemon=True).start()

    def fetch_market_data(self):
        try:
            # Usando o cliente CoinGecko passado na inicialização
            market_data = self.cg_client.get_coins_markets(
                vs_currency='usd',
                order='market_cap_desc',
                per_page=250,
                page=1,
                sparkline=False
            )
            self.after(0, self.display_data, market_data)
        except Exception as e:
            self.after(0, self.display_error, str(e))
        finally:
            self.after(0, self.finalize_ui_update)

    def display_data(self, data):
        if not data:
            self.display_error("Nenhum dado recebido da API.")
            return

        for i, coin in enumerate(data, 1):
            price = coin.get('current_price', 0)
            price_change_24h = coin.get('price_change_percentage_24h', 0)
            market_cap = coin.get('market_cap', 0)
            volume = coin.get('total_volume', 0)

            # Formatação dos valores
            price_str = f"${price:,.8f}" if price < 0.01 else f"${price:,.2f}"
            change_str = f"{price_change_24h:+.2f}%" if price_change_24h is not None else "N/A"
            market_cap_str = f"${market_cap:,}"
            volume_str = f"${volume:,}"

            # Define a cor da linha com base na variação de preço
            tag = ''
            if price_change_24h is not None:
                if price_change_24h > 0:
                    tag = 'gain'
                elif price_change_24h < 0:
                    tag = 'loss'

            values = (
                i,
                f"{coin['name']} ({coin['symbol'].upper()})",
                price_str,
                change_str,
                market_cap_str,
                volume_str
            )
            self.tree.insert("", "end", values=values, tags=(tag,))

    def display_error(self, error_message):
        messagebox.showerror("Erro ao Buscar Dados", f"Ocorreu um erro:\n\n{error_message}", parent=self)
        self.status_label.config(text=f"Erro: {error_message}", bootstyle="danger")

    def finalize_ui_update(self):
        self.run_button.config(state="normal", text="🔄 Atualizar Dados")
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.status_label.config(text=f"Dados atualizados em: {timestamp}")

if __name__ == '__main__':
    # Este bloco é para teste e não será executado quando importado pelo main_app.py
    # Para testar, você precisaria de um mock do CoinGeckoAPI e do parent_app

    # Exemplo de como a janela poderia ser iniciada (requer mocks)
    class MockCoinGecko:
        def get_coins_markets(self, **kwargs):
            # Retorna dados de exemplo para teste
            return [
                {'name': 'Bitcoin', 'symbol': 'btc', 'current_price': 68000, 'price_change_percentage_24h': 1.5, 'market_cap': 1300000000000, 'total_volume': 25000000000},
                {'name': 'Ethereum', 'symbol': 'eth', 'current_price': 3500, 'price_change_percentage_24h': -0.5, 'market_cap': 420000000000, 'total_volume': 15000000000},
            ]

    class MockApp:
        def center_toplevel_on_main(self, window):
            pass

    root = ttkb.Window(themename="darkly")
    app = DataViewerWindow(root, MockApp(), MockCoinGecko(), None, None)
    root.mainloop()
