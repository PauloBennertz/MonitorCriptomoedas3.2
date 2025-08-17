import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from datetime import datetime
import json
import os
import threading
import sys
import queue
import logging
import time
from notification_service import send_telegram_alert, AlertConsolidator
import robust_services
from monitoring_service import (
    run_monitoring_cycle,
    get_coingecko_global_mapping,
    fetch_all_binance_symbols_startup,
    get_btc_dominance
)
from core_components import (
    get_application_path,
    CryptoCard,
    AlertHistoryWindow,
    AlertManagerWindow,
    StartupConfigDialog
)
from api_config_window import ApiConfigWindow
from capital_flow_window import CapitalFlowWindow
from token_movers_window import TokenMoversWindow
from sound_config_window import SoundConfigWindow
from coin_manager import CoinManager
from help_window import HelpWindow
try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Biblioteca Faltando", "A biblioteca 'Pillow' é necessária. Instale com 'pip install Pillow'")
    sys.exit()

class CryptoApp:
    """Classe principal da aplicação que gerencia a UI e os serviços de backend."""
    def __init__(self, root, config, all_symbols, coin_manager):
        """Inicializa a aplicação, configura a UI e inicia os serviços."""
        self.root = root
        self.config = config
        self.all_symbols = all_symbols
        self.coin_manager = coin_manager
        self.coingecko_mapping = get_coingecko_global_mapping()
        self.data_queue = queue.Queue()
        self.monitoring_thread = None
        self.stop_monitoring_event = threading.Event()
        self.coin_cards = {}
        self.alert_history = self.load_alert_history()
        
        self.setup_logging()
        self.setup_ui()
        
        self.alert_consolidator = AlertConsolidator(self.root, self)
        self.start_monitoring()
        
        self.root.after(100, self.process_queue)
        self.update_dominance_display()
        logging.info("CryptoApp inicializada com sucesso.")

    def setup_logging(self):
        """Configura o sistema de logging básico."""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def setup_ui(self):
        """Constrói todos os elementos da interface gráfica principal."""
        self.root.title("Crypto Monitor Pro")
        self.root.geometry("1280x800")
        
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="⚙️ Gerenciar Alertas", command=self.show_alert_manager)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Sair", command=self.on_closing)
        
        analysis_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="📊 Análise de Mercado", menu=analysis_menu)
        analysis_menu.add_command(label="💹 Fluxo de Capital (Categorias)", command=self.show_capital_flow_window)
        analysis_menu.add_command(label="📈 Ganhadores e Perdedores", command=self.show_token_movers_window)
        analysis_menu.add_command(label="🔔 Histórico de Alertas", command=self.show_alert_history_window)
        
        config_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="⚙️ Configurações", menu=config_menu)
        config_menu.add_command(label="🔊 Configurar Sons", command=self.show_sound_config_window)
        config_menu.add_command(label="Chaves de API", command=self.show_api_config_window)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Guia de Indicadores", command=self.show_help_window)

        header_frame = ttkb.Frame(self.root, bootstyle="dark")
        header_frame.pack(side="top", fill="x")
        
        title_frame = ttkb.Frame(header_frame, bootstyle="dark", padding=10)
        title_frame.pack(side="top", fill="x")
        
        ttkb.Label(title_frame, text="CRYPTO MONITOR PRO", font=("Segoe UI", 16, "bold"), bootstyle="info").pack(side="left")
        
        status_frame = ttkb.Frame(header_frame, padding=(15, 10), bootstyle="secondary")
        status_frame.pack(side="top", fill="x")

        dominance_frame = ttkb.Frame(status_frame, bootstyle="secondary")
        dominance_frame.pack(side="left")
        
        ttkb.Label(dominance_frame, text="₿", font=("Arial", 16, "bold"), bootstyle="warning").pack(side="left", padx=(0, 5))
        ttkb.Label(dominance_frame, text="Dominância BTC:", font=("Segoe UI", 11, "bold"), bootstyle="light").pack(side="left")

        self.dominance_label = ttkb.Label(dominance_frame, text="Carregando...", font=("Segoe UI", 12, "bold"), bootstyle="warning", width=12)
        self.dominance_label.pack(side="left", padx=(8, 0))
        
        ttkb.Separator(status_frame, orient="vertical", bootstyle="light").pack(side="left", fill="y", padx=15, pady=5)
        
        api_status_frame = ttkb.Frame(status_frame, bootstyle="secondary")
        api_status_frame.pack(side="left")
        
        ttkb.Label(api_status_frame, text="Status API:", font=("Segoe UI", 11), bootstyle="light").pack(side="left")

        self.update_status_label = ttkb.Label(api_status_frame, text="", font=("Segoe UI", 11, "bold"), bootstyle="secondary")
        self.update_status_label.pack(side="left", padx=(8, 0))
        
        self.update_button = ttkb.Button(status_frame, text="🔄 Atualizar Dados", command=self.manual_update_prices, bootstyle="info", width=18)
        self.update_button.pack(side="right", padx=(0, 10))
        
        self.check_api_status()
        
        main_container = ttkb.Frame(self.root, bootstyle="dark")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        coins_header = ttkb.Frame(main_container, bootstyle="dark")
        coins_header.pack(fill="x", pady=(0, 10))
        
        ttkb.Label(coins_header, text="Suas Criptomoedas Monitoradas", font=("Segoe UI", 14, "bold"), bootstyle="info").pack(side="left")
        
        main_frame = ttkb.Frame(main_container, bootstyle="dark", padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(main_frame, highlightthickness=0, bg="#2a2a2a")
        self.scrollbar = ttkb.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview, bootstyle="rounded")
        self.scrollable_frame = ttkb.Frame(self.canvas, bootstyle="dark")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(canvas_window_id, width=e.width))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.root.bind('<MouseWheel>', self._on_mousewheel)
        
        footer_frame = ttkb.Frame(self.root, padding=(15, 8), bootstyle="dark")
        footer_frame.pack(side="bottom", fill="x")
        
        ttkb.Label(footer_frame, text=f"Sessão iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M')}", font=("Segoe UI", 9), bootstyle="secondary").pack(side="left")
        ttkb.Label(footer_frame, text="© 2023 Crypto Monitor Pro", font=("Segoe UI", 9), bootstyle="secondary").pack(side="right")

        self.update_coin_cards_display()

    def update_coin_cards_display(self):
        """Recria a grade de cards de criptomoedas com base na configuração atual."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        monitored_symbols = [c['symbol'] for c in self.config.get('cryptos_to_monitor', [])]
        self.coin_cards = {}
        
        screen_width = self.root.winfo_screenwidth()
        num_columns = 5 if screen_width >= 1920 else 4 if screen_width >= 1440 else 3

        for i, symbol in enumerate(monitored_symbols):
            base_asset = symbol.replace('USDT', '').upper()
            coin_name = self.coingecko_mapping.get(base_asset, base_asset) 
            
            card_container = ttkb.Frame(self.scrollable_frame, bootstyle="dark")
            
            card = CryptoCard(card_container, symbol, coin_name)
            card.pack(fill='both', expand=True)
            self.coin_cards[symbol] = card
            
            row, col = divmod(i, num_columns)
            card_container.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
            self.scrollable_frame.columnconfigure(col, weight=1)
            
        if not monitored_symbols:
            empty_frame = ttkb.Frame(self.scrollable_frame, bootstyle="dark", padding=50)
            empty_frame.grid(row=0, column=0, sticky="nsew")
            ttkb.Label(empty_frame, text="Nenhuma moeda monitorada", font=("Segoe UI", 16, "bold"), bootstyle="secondary").pack(pady=(20, 10))
            ttkb.Label(empty_frame, text="Use o menu 'Arquivo > Gerenciar Alertas' para adicionar moedas", font=("Segoe UI", 12), bootstyle="secondary").pack()

    def update_card_data(self, data):
        """Atualiza os dados de um card de criptomoeda com novos dados da fila."""
        symbol = data.get('symbol')
        card = self.coin_cards.get(symbol)
        if not card: return

        new_price = data.get('current_price', 0.0)
        price_label = card.data_labels.get('current_price')
        
        if price_label:
            price_color = 'info'
            if card.previous_price != 0:
                if new_price > card.previous_price: price_color = 'success'
                elif new_price < card.previous_price: price_color = 'danger'
            
            if price_color in ['success', 'danger']: self._pulse_label(price_label, price_color)
            price_label.config(bootstyle=price_color)
        
        card.previous_price = new_price

        for key, label in card.data_labels.items():
            value = data.get(key, 'N/A')
            if isinstance(value, (int, float)):
                if key == 'current_price': text = f"${value:.8f}" if value < 0.001 else f"${value:.6f}" if value < 0.01 else f"${value:.4f}" if value < 1 else f"${value:,.2f}"
                elif key == 'price_change_24h': text = f"{'▲' if value >= 0 else '▼'} {abs(value):.2f}%"
                elif key == 'volume_24h': text = f"${value/1_000_000_000:.2f}B" if value >= 1_000_000_000 else f"${value/1_000_000:.2f}M" if value >= 1_000_000 else f"${value/1_000:.2f}K"
                elif key == 'rsi_value':
                    text = f"{value:.1f}"
                    if value <= 30: label.config(bootstyle="success")
                    elif value >= 70: label.config(bootstyle="danger")
                    else: label.config(bootstyle="light")
                else: text = f"{value:.2f}"
            else: text = str(value)

            label.config(text=text)
            if key == 'price_change_24h' and isinstance(value, (int, float)):
                label.config(bootstyle="success" if value >= 0 else "danger")

    def _pulse_label(self, label, color_style):
        """Cria um efeito de pulsação visual em um label."""
        original_style = label.cget('bootstyle')
        self.root.after(0, lambda: label.config(bootstyle=f"{color_style}"))
        self.root.after(600, lambda: label.config(bootstyle=f"{color_style}-outline"))
        self.root.after(1200, lambda: label.config(bootstyle=original_style))

    def start_monitoring(self):
        """Inicia o thread de monitoramento em segundo plano."""
        if self.monitoring_thread and self.monitoring_thread.is_alive(): return
        self.stop_monitoring_event.clear()
        self.monitoring_thread = threading.Thread(target=run_monitoring_cycle, args=(self.config, self.data_queue, self.stop_monitoring_event, self.coingecko_mapping), daemon=True)
        self.monitoring_thread.start()
        logging.info("Serviço de monitoramento em segundo plano iniciado.")

    def process_queue(self):
        """Processa itens da fila de dados (UI e alertas) na thread principal."""
        try:
            while not self.data_queue.empty():
                item = self.data_queue.get_nowait()
                if item['type'] == 'data': self.update_card_data(item['payload'])
                elif item['type'] == 'alert': self.handle_alert(item['payload'])
        finally:
            self.root.after(200, self.process_queue)

    def handle_alert(self, payload):
        """Processa um alerta recebido do serviço de monitoramento."""
        self.log_and_save_alert(payload.get('symbol'), payload.get('trigger'), payload.get('analysis_data'))
        self.alert_consolidator.add_alert(payload.get('symbol'), payload.get('trigger'), payload.get('message'), payload.get('sound'))
        send_telegram_alert(self.config.get('telegram_bot_token'), self.config.get('telegram_chat_id'), payload.get('message'))

    def on_closing(self):
        """Executa procedimentos de limpeza ao fechar a aplicação."""
        if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa?"):
            logging.info("Fechando a aplicação...")
            self.stop_monitoring_event.set()
            if self.monitoring_thread: self.monitoring_thread.join(timeout=5)
            self.save_config()
            self.save_alert_history()
            self.root.destroy()
            sys.exit()

    def save_config(self):
        """Salva a configuração atual no arquivo config.json."""
        config_path = os.path.join(get_application_path(), "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f: json.dump(self.config, f, indent=2)
            logging.info("Configurações salvas com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao salvar configurações: {e}")

    def load_alert_history(self):
        """Carrega o histórico de alertas do arquivo alert_history.json."""
        history_path = os.path.join(get_application_path(), "alert_history.json")
        try:
            with open(history_path, 'r', encoding='utf-8') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_alert_history(self):
        """Salva o histórico de alertas atual no arquivo alert_history.json."""
        history_path = os.path.join(get_application_path(), "alert_history.json")
        try:
            with open(history_path, 'w', encoding='utf-8') as f: json.dump(self.alert_history, f, indent=2)
            logging.info("Histórico de alertas salvo com sucesso.")
        except Exception as e:
            logging.error(f"Não foi possível salvar o histórico de alertas: {e}")

    def log_and_save_alert(self, symbol, trigger, data):
        """Adiciona uma nova entrada de alerta ao histórico."""
        alert_entry = {'timestamp': datetime.now().isoformat(), 'symbol': symbol, 'trigger': trigger, 'data': data}
        self.alert_history.insert(0, alert_entry)
        if len(self.alert_history) > 200: self.alert_history = self.alert_history[:200]

    def show_alert_manager(self):
        """Abre a janela do gerenciador de alertas."""
        AlertManagerWindow(self, self.coin_manager)

    def show_capital_flow_window(self):
        """Abre a janela de análise de fluxo de capital."""
        from pycoingecko import CoinGeckoAPI
        cg_client = CoinGeckoAPI()
        CapitalFlowWindow(self.root, self, cg_client, robust_services.data_cache, robust_services.rate_limiter)

    def show_token_movers_window(self):
        """Abre a janela de análise de ganhadores e perdedores."""
        from pycoingecko import CoinGeckoAPI
        cg_client = CoinGeckoAPI()
        TokenMoversWindow(self.root, self, cg_client, robust_services.data_cache, robust_services.rate_limiter)

    def show_alert_history_window(self):
        """Abre a janela do histórico de alertas."""
        AlertHistoryWindow(self)
    
    def show_sound_config_window(self):
        """Abre a janela de configuração de sons."""
        from sound_config_window import SoundConfigWindow
        SoundConfigWindow(self.root, self)

    def show_api_config_window(self):
        """Abre a janela de configuração de chaves de API."""
        ApiConfigWindow(self.root, self)

    def show_help_window(self):
        """Abre a janela de ajuda com o guia de indicadores."""
        HelpWindow(self.root)

    def center_toplevel_on_main(self, toplevel_window):
        """Centraliza uma janela Toplevel em relação à janela principal."""
        self.root.update_idletasks()
        main_x, main_y = self.root.winfo_x(), self.root.winfo_y()
        main_width, main_height = self.root.winfo_width(), self.root.winfo_height()
        top_width, top_height = toplevel_window.winfo_width(), toplevel_window.winfo_height()
        x = main_x + (main_width - top_width) // 2
        y = main_y + (main_height - top_height) // 2
        screen_width, screen_height = toplevel_window.winfo_screenwidth(), toplevel_window.winfo_screenheight()
        x = max(0, min(x, screen_width - top_width))
        y = max(0, min(y, screen_height - top_height))
        toplevel_window.geometry(f"+{x}+{y}")
        
    def update_dominance_display(self):
        """Busca e atualiza o label da dominância do BTC em uma thread separada."""
        def update_task():
            try:
                logging.info("Buscando dominância do BTC...")
                dominance = get_btc_dominance()
                logging.info(f"Valor da dominância recebido: {dominance}")
                self.root.after(0, lambda: self.dominance_label.config(text=dominance))
            except Exception as e:
                logging.error(f"Erro ao atualizar dominância BTC: {e}")
                self.root.after(60000, self.update_dominance_display)
                return
            self.root.after(300000, self.update_dominance_display)
        threading.Thread(target=update_task, daemon=True).start()

    def manual_update_prices(self):
        """Inicia uma atualização manual dos preços, verificando os limites da API."""
        can_update, status_message = robust_services.rate_limiter.can_perform_manual_update()
        if not can_update:
            self.update_status_label.config(text=f"⚠️ {status_message}", bootstyle="danger")
            self.root.after(5000, lambda: self.update_status_label.config(text=""))
            return
        
        status_text = f"🔄 {status_message}"
        self.update_status_label.config(text=status_text, bootstyle="info")
        self.root.after(1000, lambda: self._start_manual_update())
    
    def _start_manual_update(self):
        """Prepara e inicia a thread de atualização manual."""
        self.update_button.config(state='disabled', text='Atualizando...')
        self.update_status_label.config(text="Atualizando preços...", bootstyle="warning")
        threading.Thread(target=self._perform_manual_update, daemon=True).start()
    
    def _perform_manual_update(self):
        """Executa a lógica de atualização manual dos preços em uma thread."""
        try:
            robust_services.rate_limiter.set_manual_update_mode(True)
            robust_services.data_cache.cache.clear()
            logging.info("Cache limpo para atualização manual.")
            
            monitored_symbols = [c['symbol'] for c in self.config.get('cryptos_to_monitor', [])]
            
            from monitoring_service import run_single_symbol_update
            for i, symbol in enumerate(monitored_symbols):
                robust_services.rate_limiter.wait_if_needed()
                run_single_symbol_update(symbol, self.config, self.data_queue, self.coingecko_mapping)
                time.sleep(0.2)
                if (i + 1) % 5 == 0:
                    self.root.after(0, lambda i=i: self.update_status_label.config(text=f"Atualizando... ({i+1}/{len(monitored_symbols)})"))
            
            self.update_dominance_display()
            self.root.after(0, self._update_complete)
            
        except Exception as e:
            logging.error(f"Erro durante atualização manual: {e}")
            self.root.after(0, self._update_error, str(e))
        finally:
            robust_services.rate_limiter.set_manual_update_mode(False)
    
    def _update_complete(self):
        """Atualiza a UI após a conclusão bem-sucedida da atualização manual."""
        self.update_button.config(state='normal', text='🔄 Atualizar Preços')
        self.update_status_label.config(text="✓ Atualizado", bootstyle="success")
        self.root.after(3000, lambda: self.update_status_label.config(text=""))
    
    def check_api_status(self):
        """Verifica periodicamente o status do rate limit da API e atualiza a UI."""
        try:
            can_update, status_message = robust_services.rate_limiter.can_perform_manual_update()
            if can_update:
                self.update_button.config(state='normal', text='🔄 Atualizar Preços', bootstyle="info")
                self.update_status_label.config(text="API: OK", bootstyle="success")
            else:
                self.update_button.config(state='disabled', text='⏸️ API Limitada', bootstyle="secondary")
                self.update_status_label.config(text=f"API: {status_message}", bootstyle="danger")
                self._pulse_button(self.update_button, 'danger')
            self.root.after(10000, self.check_api_status)
        except Exception as e:
            logging.error(f"Erro ao verificar status da API: {e}")
            self.update_status_label.config(text="API: Erro", bootstyle="danger")
            self.root.after(10000, self.check_api_status)
    
    def show_api_tooltip(self, usage):
        """Mostra um tooltip com informações detalhadas do uso da API."""
        tooltip_text = f"Status da API:\n1 min: {usage['requests_1min']}/{usage['limit_1min']} ({usage['1min']:.1f}%)\n5 min: {usage['requests_5min']}/{usage['limit_5min']} ({usage['5min']:.1f}%)"
        x, y, _, _ = self.update_button.bbox("insert")
        x += self.update_button.winfo_rootx() + 25
        y += self.update_button.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = ttkb.Label(self.tooltip, text=tooltip_text, justify=tk.LEFT, background="#ffffe0", foreground="black", relief=tk.SOLID, borderwidth=1, font=("Segoe UI", 9), padding=5)
        label.pack()
        self.root.after(3000, lambda: self.tooltip.destroy() if hasattr(self, 'tooltip') else None)

    def _update_error(self, error_msg):
        """Atualiza a UI em caso de erro na atualização manual."""
        self.update_button.config(state='normal', text='🔄 Atualizar Preços')
        self.update_status_label.config(text="✗ Erro", bootstyle="danger")
        self.root.after(5000, lambda: self.update_status_label.config(text=""))

    def _on_mousewheel(self, event):
        """Permite a rolagem da lista de cards com o scroll do mouse."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _pulse_button(self, button, color_style):
        """Cria um efeito de pulsação visual em um botão."""
        if hasattr(button, '_pulsing') and button._pulsing: return
        button._pulsing = True
        original_style = button.cget('bootstyle')
        def animate_pulse(count=0):
            if not button.winfo_exists():
                button._pulsing = False
                return
            if count % 2 == 0: button.config(bootstyle=f"{color_style}")
            else: button.config(bootstyle=f"{color_style}-outline")
            if button._pulsing: self.root.after(500, lambda: animate_pulse(count + 1))
            else: button.config(bootstyle=original_style)
        animate_pulse()

def get_current_config():
    """Carrega a configuração do aplicativo a partir do arquivo config.json."""
    config_path = os.path.join(get_application_path(), "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cryptos_to_monitor": [], "telegram_bot_token": "", "telegram_chat_id": "", "check_interval_seconds": 300}

if __name__ == "__main__":
    config = get_current_config()
    if 'market_analysis_config' not in config:
        config['market_analysis_config'] = {'top_n': 25, 'min_market_cap': 50000000}
        
    all_symbols_list = fetch_all_binance_symbols_startup(config)
    
    coin_manager = CoinManager()

    startup_root = ttkb.Window(themename="darkly")
    
    if not config.get("cryptos_to_monitor"):
        startup_root.withdraw()
        config_dialog = StartupConfigDialog(startup_root, all_symbols_list, config)
        startup_root.wait_window(config_dialog)
        if not config_dialog.session_started:
            sys.exit("Configuração inicial cancelada.")
            
    app = CryptoApp(startup_root, config, all_symbols_list, coin_manager)
    startup_root.protocol("WM_DELETE_WINDOW", app.on_closing)
    startup_root.mainloop()