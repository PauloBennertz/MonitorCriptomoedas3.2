# main_app.py (VERSÃO CORRIGIDA E COMPLETA)

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

# Importações de seus serviços e componentes.
from notification_service import play_alert_sound, show_windows_ok_popup, send_telegram_alert, AlertConsolidator
import robust_services

# Importa as funções de API e o ciclo de monitoramento
from monitoring_service import (
    run_monitoring_cycle,
    run_single_symbol_update,
    get_coingecko_global_mapping,
    fetch_all_binance_symbols_startup,
    get_btc_dominance
)

# Importa os componentes de UI
from core_components import (
    get_application_path,
    CryptoCard,
    AlertConfigDialog,
    AlertHistoryWindow,
    AlertManagerWindow,
    StartupConfigDialog
)

# Importando as janelas Toplevel
from api_config_window import ApiConfigWindow
from capital_flow_window import CapitalFlowWindow
from token_movers_window import TokenMoversWindow
from help_window import HelpWindow
from support_material_window import SupportMaterialWindow
from market_analysis_config_window import MarketAnalysisConfigWindow

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Biblioteca Faltando", "A biblioteca 'Pillow' é necessária. Instale com 'pip install Pillow'")
    sys.exit()


class CryptoApp:
    def __init__(self, root, config, all_symbols):
        print("DEBUG: Iniciando __init__ da CryptoApp...")
        self.root = root
        self.config = config
        self.all_symbols = all_symbols
        
        print("LOG: Inicializando CryptoApp: Buscando mapeamento CoinGecko...")
        self.coingecko_mapping = get_coingecko_global_mapping()
        print("LOG: Mapeamento CoinGecko carregado. Inicializando fila de dados...")
        
        self.data_queue = queue.Queue()
        self.monitoring_thread = None
        self.stop_monitoring_event = threading.Event()
        self.coin_cards = {}
        
        print("LOG: Carregando histórico de alertas...")
        self.alert_history = self.load_alert_history()
        
        print("LOG: Configurando logging...")
        self.setup_logging()
        
        print("LOG: Configurando UI...")
        self.setup_ui()
        
        print("LOG: Inicializando sistema de consolidação de alertas...")
        self.alert_consolidator = AlertConsolidator(self.root, self)
        
        print("LOG: UI configurada. Iniciando monitoramento...")
        self.start_monitoring()
        
        print("LOG: Monitoramento iniciado. Agendando processamento da fila...")
        self.root.after(100, self.process_queue)
        self.update_dominance_display()
        
        print("LOG: __init__ da CryptoApp finalizado com sucesso.")

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def setup_ui(self):
        # Configura a janela principal com tema escuro
        self.root.title("Crypto Monitor Pro")
        self.root.geometry("1280x800")
        
        # Cria menu moderno com ícones
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

        # Header principal com gradiente
        header_frame = ttkb.Frame(self.root, bootstyle="dark")
        header_frame.pack(side="top", fill="x")
        
        # Título da aplicação
        title_frame = ttkb.Frame(header_frame, bootstyle="dark", padding=10)
        title_frame.pack(side="top", fill="x")
        
        title_label = ttkb.Label(
            title_frame, 
            text="CRYPTO MONITOR PRO", 
            font=("Segoe UI", 16, "bold"),
            bootstyle="info"
        )
        title_label.pack(side="left")
        
        # Status frame com visual moderno
        status_frame = ttkb.Frame(header_frame, padding=(15, 10), bootstyle="secondary")
        status_frame.pack(side="top", fill="x")

        # Frame para dominância BTC com visual moderno
        dominance_frame = ttkb.Frame(status_frame, bootstyle="secondary")
        dominance_frame.pack(side="left")
        
        # Ícone para dominância BTC
        btc_icon_label = ttkb.Label(
            dominance_frame, 
            text="₿", 
            font=("Arial", 16, "bold"), 
            bootstyle="warning"
        )
        btc_icon_label.pack(side="left", padx=(0, 5))
        
        # Label para texto de dominância
        ttkb.Label(
            dominance_frame, 
            text="Dominância BTC:", 
            font=("Segoe UI", 11, "bold"), 
            bootstyle="light"
        ).pack(side="left")
        
        # Valor de dominância com destaque
        self.dominance_label = ttkb.Label(
            dominance_frame, 
            text="Carregando...", 
            font=("Segoe UI", 12, "bold"), 
            bootstyle="warning", 
            width=12
        )
        self.dominance_label.pack(side="left", padx=(8, 0))
        
        # Separador vertical
        ttkb.Separator(status_frame, orient="vertical", bootstyle="light").pack(side="left", fill="y", padx=15, pady=5)
        
        # Status da API
        api_status_frame = ttkb.Frame(status_frame, bootstyle="secondary")
        api_status_frame.pack(side="left")
        
        ttkb.Label(
            api_status_frame, 
            text="Status API:", 
            font=("Segoe UI", 11), 
            bootstyle="light"
        ).pack(side="left")
        
        self.update_status_label = ttkb.Label(
            api_status_frame, 
            text="", 
            font=("Segoe UI", 11, "bold"), 
            bootstyle="secondary"
        )
        self.update_status_label.pack(side="left", padx=(8, 0))
        
        # Botão de atualização manual com design moderno
        self.update_button = ttkb.Button(
            status_frame, 
            text="🔄 Atualizar Dados", 
            command=self.manual_update_prices, 
            bootstyle="info", 
            width=18
        )
        self.update_button.pack(side="right", padx=(0, 10))
        
        # Inicia verificação contínua do status da API
        self.check_api_status()
        
        # Container principal com fundo escuro
        main_container = ttkb.Frame(self.root, bootstyle="dark")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Cabeçalho para as moedas
        coins_header = ttkb.Frame(main_container, bootstyle="dark")
        coins_header.pack(fill="x", pady=(0, 10))
        
        ttkb.Label(
            coins_header, 
            text="Suas Criptomoedas Monitoradas", 
            font=("Segoe UI", 14, "bold"),
            bootstyle="info"
        ).pack(side="left")
        
        # Frame principal com scroll
        main_frame = ttkb.Frame(main_container, bootstyle="dark", padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas com scrollbar para os cards
        self.canvas = tk.Canvas(
            main_frame, 
            highlightthickness=0, 
            bg="#2a2a2a" # CORREÇÃO: Cor de fundo explícita para o canvas
        )
        
        # Scrollbar moderna
        self.scrollbar = ttkb.Scrollbar(
            main_frame, 
            orient="vertical", 
            command=self.canvas.yview, 
            bootstyle="rounded"
        )
        
        # Frame scrollável para os cards
        self.scrollable_frame = ttkb.Frame(self.canvas, bootstyle="dark")
        self.scrollable_frame.bind(
            "<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.root.bind('<MouseWheel>', self._on_mousewheel)
        
        # Footer com informações de status
        footer_frame = ttkb.Frame(self.root, padding=(15, 8), bootstyle="dark")
        footer_frame.pack(side="bottom", fill="x")
        
        # Status da sessão
        ttkb.Label(
            footer_frame, 
            text=f"Sessão iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(side="left")
        
        # Copyright
        ttkb.Label(
            footer_frame, 
            text="© 2023 Crypto Monitor Pro",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(side="right")
        
        # Atualiza a exibição dos cards
        self.update_coin_cards_display()

    def update_coin_cards_display(self):
        # Limpa todos os widgets existentes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        # Obtém a lista de moedas monitoradas
        monitored_symbols = [c['symbol'] for c in self.config.get('cryptos_to_monitor', [])]
        self.coin_cards = {}
        
        # Define o número de colunas com base na resolução
        screen_width = self.root.winfo_screenwidth()
        if screen_width >= 1920:
            num_columns = 5  # Para telas grandes
        elif screen_width >= 1440:
            num_columns = 4  # Para telas médias
        else:
            num_columns = 3  # Para telas menores
        
        # Cria um card para cada moeda
        for i, symbol in enumerate(monitored_symbols):
            base_asset = symbol.replace('USDT', '').upper()
            coin_name = self.coingecko_mapping.get(base_asset, base_asset) 
            
            # Cria frame de container para o card com espaçamento
            card_container = ttkb.Frame(self.scrollable_frame, bootstyle="dark")
            
            # Cria o card dentro do container
            card = CryptoCard(card_container, symbol, coin_name)
            card.pack(fill='both', expand=True)
            self.coin_cards[symbol] = card
            
            # Posiciona o container na grade
            row, col = divmod(i, num_columns)
            card_container.grid(
                row=row, 
                column=col, 
                padx=12,  # Espaçamento horizontal
                pady=12,  # Espaçamento vertical
                sticky="nsew"  # Expande em todas as direções
            )
            
            # Configura a coluna para crescer proporcionalmente
            self.scrollable_frame.columnconfigure(col, weight=1)
            
        # Se não houver moedas monitoradas, mostra mensagem informativa
        if not monitored_symbols:
            empty_frame = ttkb.Frame(self.scrollable_frame, bootstyle="dark", padding=50)
            empty_frame.grid(row=0, column=0, sticky="nsew")
            
            ttkb.Label(
                empty_frame,
                text="Nenhuma moeda monitorada",
                font=("Segoe UI", 16, "bold"),
                bootstyle="secondary"
            ).pack(pady=(20, 10))
            
            ttkb.Label(
                empty_frame,
                text="Use o menu 'Arquivo > Gerenciar Alertas' para adicionar moedas",
                font=("Segoe UI", 12),
                bootstyle="secondary"
            ).pack()

    def update_card_data(self, data):
        """
        Atualiza os dados de um card de criptomoeda com animação e efeitos visuais.
        """
        symbol = data.get('symbol')
        card = self.coin_cards.get(symbol)
        if not card: 
            return  # Se o card não existir, sai da função

        # Obtém o novo preço
        new_price = data.get('current_price', 0.0)
        price_label = card.data_labels.get('current_price')
        
        # Efeito visual para mudança de preço
        if price_label:
            # Define a cor com base na variação
            if card.previous_price != 0:
                if new_price > card.previous_price: 
                    price_color = 'success'
                    # Adiciona efeito de pulsação para aumento
                    self._pulse_label(price_label, 'success')
                elif new_price < card.previous_price: 
                    price_color = 'danger'
                    # Adiciona efeito de pulsação para diminuição
                    self._pulse_label(price_label, 'danger')
                else:
                    price_color = 'info'
            else:
                price_color = 'info'
            
            # Configura a cor do label
            price_label.config(bootstyle=price_color)
        
        # Atualiza o preço anterior
        card.previous_price = new_price

        # Atualiza todos os labels com os novos dados
        for key, label in card.data_labels.items():
            value = data.get(key, 'N/A')
            
            # Formata valores numéricos
            if isinstance(value, (int, float)):
                if key == 'current_price': 
                    # Formata preço com precisão adaptativa
                    if value < 0.001:
                        text = f"${value:.8f}"
                    elif value < 0.01:
                        text = f"${value:.6f}"
                    elif value < 1:
                        text = f"${value:.4f}"
                    else:
                        text = f"${value:,.2f}"
                        
                elif key == 'price_change_24h': 
                    # Adiciona seta indicativa para variação
                    arrow = "▲" if value >= 0 else "▼"
                    text = f"{arrow} {abs(value):.2f}%"
                    
                elif key == 'volume_24h':
                    # Formata volumes grandes
                    if value >= 1_000_000_000: 
                        text = f"${value/1_000_000_000:.2f}B"
                    elif value >= 1_000_000: 
                        text = f"${value/1_000_000:.2f}M"
                    else: 
                        text = f"${value/1_000:.2f}K"
                        
                elif key == 'rsi_value':
                    # Formata RSI com cor indicativa
                    text = f"{value:.1f}"
                    if value <= 30:
                        label.config(bootstyle="success")  # Sobrevendido
                    elif value >= 70:
                        label.config(bootstyle="danger")   # Sobrecomprado
                    else:
                        label.config(bootstyle="light")  # Normal
                else: 
                    text = f"{value:.2f}"
            else:
                # Valores não numéricos
                text = str(value)

            # Atualiza o texto do label
            label.config(text=text)
            
            # Configura cores específicas para alguns tipos de dados
            if key == 'price_change_24h' and isinstance(value, (int, float)):
                color = "success" if value >= 0 else "danger"
                label.config(bootstyle=color)

    def _pulse_label(self, label, color_style):
        """
        Cria um efeito de pulsação no label para destacar mudanças de preço
        """
        # Salva o estilo atual
        original_style = label.cget('bootstyle')
        
        # Sequência de pulsação: forte -> fraco -> normal
        self.root.after(0, lambda: label.config(bootstyle=f"{color_style}"))
        self.root.after(600, lambda: label.config(bootstyle=f"{color_style}-outline"))
        self.root.after(1200, lambda: label.config(bootstyle=original_style))

    def start_monitoring(self):
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        self.stop_monitoring_event.clear()
        self.monitoring_thread = threading.Thread(
            target=run_monitoring_cycle,
            args=(self.config, self.data_queue, self.stop_monitoring_event, self.coingecko_mapping),
            daemon=True
        )
        self.monitoring_thread.start()
        logging.info("Serviço de monitoramento iniciado.")

    def process_queue(self):
        try:
            while not self.data_queue.empty():
                item = self.data_queue.get_nowait()
                if item['type'] == 'data':
                    self.update_card_data(item['payload'])
                elif item['type'] == 'alert':
                    self.handle_alert(item['payload'])
        finally:
            self.root.after(200, self.process_queue)

    def handle_alert(self, payload):
        message = payload.get('message', 'Alerta genérico')
        sound = payload.get('sound')
        symbol = payload.get('symbol')
        trigger = payload.get('trigger')
        analysis_data = payload.get('analysis_data')
        
        # Salva no histórico
        self.log_and_save_alert(symbol, trigger, analysis_data)
        
        # Adiciona ao consolidador de alertas (em vez de mostrar popup individual)
        self.alert_consolidator.add_alert(symbol, trigger, message, sound)
        
        # Envia para Telegram (mantido para compatibilidade)
        send_telegram_alert(self.config.get('telegram_bot_token'), self.config.get('telegram_chat_id'), message)

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja realmente fechar o programa?"):
            logging.info("Fechando o programa...")
            self.stop_monitoring_event.set()
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            self.save_config()
            self.save_alert_history()
            self.root.destroy()
            sys.exit()

    def save_config(self):
        config_path = os.path.join(get_application_path(), "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logging.info("Configurações salvas com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao salvar configurações: {e}")

    def load_alert_history(self):
        history_path = os.path.join(get_application_path(), "alert_history.json")
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_alert_history(self):
        history_path = os.path.join(get_application_path(), "alert_history.json")
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, indent=2)
            print("LOG: Histórico de alertas salvo.")
        except Exception as e:
            print(f"ERRO: Não foi possível salvar o histórico de alertas: {e}")

    def log_and_save_alert(self, symbol, trigger, data):
        alert_entry = {'timestamp': datetime.now().isoformat(), 'symbol': symbol, 'trigger': trigger, 'data': data}
        self.alert_history.insert(0, alert_entry)
        if len(self.alert_history) > 200:
            self.alert_history = self.alert_history[:200]

    def show_alert_manager(self):
        AlertManagerWindow(self)

    def show_capital_flow_window(self):
        print("LOG: Abrindo a janela de Fluxo de Capital.")
        from pycoingecko import CoinGeckoAPI
        cg_client = CoinGeckoAPI()
        # CORREÇÃO: Argumento 'self.config' removido
        CapitalFlowWindow(self.root, self, cg_client, robust_services.data_cache, robust_services.rate_limiter)

    def show_token_movers_window(self):
        print("LOG: Abrindo a janela de Ganhadores e Perdedores.")
        from pycoingecko import CoinGeckoAPI
        cg_client = CoinGeckoAPI()
        # CORREÇÃO: Argumento 'self.config' removido
        TokenMoversWindow(self.root, self, cg_client, robust_services.data_cache, robust_services.rate_limiter)

    def show_alert_history_window(self):
        AlertHistoryWindow(self)
    
    def show_sound_config_window(self):
        """Abre a janela de configuração de sons."""
        from sound_config_window import SoundConfigWindow
        SoundConfigWindow(self.root, self)

    def center_toplevel_on_main(self, toplevel_window):
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        top_width = toplevel_window.winfo_width()
        top_height = toplevel_window.winfo_height()

        x = main_x + (main_width - top_width) // 2
        y = main_y + (main_height - top_height) // 2

        screen_width = toplevel_window.winfo_screenwidth()
        screen_height = toplevel_window.winfo_screenheight()
        x = max(0, min(x, screen_width - top_width))
        y = max(0, min(y, screen_height - top_height))

        toplevel_window.geometry(f"+{x}+{y}")
        
    def update_dominance_display(self):
        """Busca e atualiza o label da dominância do BTC em uma thread."""
        
        def update_task():
            try:
                dominance = get_btc_dominance()
                # Atualiza a UI na thread principal
                self.root.after(0, lambda: self.dominance_label.config(text=dominance))
                print(f"LOG: Dominância BTC atualizada: {dominance}")
            except Exception as e:
                print(f"ERRO: Erro ao atualizar dominância BTC: {e}")
                # Em caso de erro, agenda próxima tentativa
                self.root.after(60000, self.update_dominance_display)
                return
            
            # Agenda próxima atualização em 5 minutos
            self.root.after(300000, self.update_dominance_display)

        threading.Thread(target=update_task, daemon=True).start()

    def manual_update_prices(self):
        """Atualiza os preços manualmente, respeitando os limites da API."""
        # Verifica se é seguro realizar a atualização
        can_update, status_message = robust_services.rate_limiter.can_perform_manual_update()
        
        if not can_update:
            # Mostra mensagem de erro e não permite atualização
            self.update_status_label.config(text=f"⚠️ {status_message}", bootstyle="danger")
            print(f"LOG: Atualização manual bloqueada - {status_message}")
            
            # Remove a mensagem após 5 segundos
            self.root.after(5000, lambda: self.update_status_label.config(text=""))
            return
        
        # Se for seguro, mostra o status e continua
        usage = robust_services.rate_limiter.get_current_usage()
        status_text = f"🔄 {status_message}"
        self.update_status_label.config(text=status_text, bootstyle="info")
        
        # Pequena pausa para mostrar o status
        self.root.after(1000, lambda: self._start_manual_update())
    
    def _start_manual_update(self):
        """Inicia a atualização manual após verificação de segurança."""
        # Desabilita o botão durante a atualização
        self.update_button.config(state='disabled', text='Atualizando...')
        self.update_status_label.config(text="Atualizando preços...", bootstyle="warning")
        
        # Executa a atualização em uma thread separada para não bloquear a UI
        threading.Thread(target=self._perform_manual_update, daemon=True).start()
    
    def _perform_manual_update(self):
        """Executa a atualização manual dos preços."""
        try:
            # Ativa modo conservador para atualização manual
            robust_services.rate_limiter.set_manual_update_mode(True)
            
            # Limpa o cache para forçar atualização
            robust_services.data_cache.cache.clear()
            print("LOG: Cache limpo para atualização manual")
            
            # Força uma atualização de todos os símbolos monitorados
            monitored_symbols = [c['symbol'] for c in self.config.get('cryptos_to_monitor', [])]
            
            for i, symbol in enumerate(monitored_symbols):
                # Respeita o rate limiting
                robust_services.rate_limiter.wait_if_needed()
                
                # Atualiza dados do símbolo
                from monitoring_service import run_single_symbol_update
                run_single_symbol_update(symbol, self.config, self.data_queue, self.coingecko_mapping)
                
                # Pausa maior entre símbolos durante atualização manual
                time.sleep(0.2)
                
                # Atualiza o status a cada 5 símbolos
                if (i + 1) % 5 == 0:
                    self.root.after(0, lambda i=i: self.update_status_label.config(
                        text=f"Atualizando... ({i+1}/{len(monitored_symbols)})"
                    ))
            
            # Atualiza a dominância do BTC
            self.update_dominance_display()
            
            # Desativa modo conservador
            robust_services.rate_limiter.set_manual_update_mode(False)
            
            # Atualiza a UI na thread principal
            self.root.after(0, self._update_complete)
            
        except Exception as e:
            print(f"ERRO: Erro durante atualização manual: {e}")
            # Desativa modo conservador em caso de erro
            robust_services.rate_limiter.set_manual_update_mode(False)
            self.root.after(0, self._update_error, str(e))
    
    def _update_complete(self):
        """Chamado quando a atualização manual é concluída com sucesso."""
        self.update_button.config(state='normal', text='🔄 Atualizar Preços')
        self.update_status_label.config(text="✓ Atualizado", bootstyle="success")
        
        # Remove a mensagem de sucesso após 3 segundos
        self.root.after(3000, lambda: self.update_status_label.config(text=""))
    
    def check_api_status(self):
        """Verifica o status da API e atualiza o botão dinamicamente."""
        try:
            can_update, status_message = robust_services.rate_limiter.can_perform_manual_update()
            usage = robust_services.rate_limiter.get_current_usage()
            
            if can_update:
                # API segura - botão habilitado
                self.update_button.config(state='normal', text='🔄 Atualizar Preços', bootstyle="info-outline")
                # Atualiza tooltip com informações detalhadas
                self.update_button.bind('<Enter>', lambda e: self.show_api_tooltip(usage))
            else:
                # API em limite - botão desabilitado
                self.update_button.config(state='disabled', text='⏸️ API Limitada', bootstyle="secondary-outline")
                # Atualiza tooltip com informações detalhadas
                self.update_button.bind('<Enter>', lambda e: self.show_api_tooltip(usage))
            
            # Agenda próxima verificação em 10 segundos
            self.root.after(10000, self.check_api_status)
            
        except Exception as e:
            print(f"ERRO: Erro ao verificar status da API: {e}")
            # Em caso de erro, agenda próxima verificação
            self.root.after(10000, self.check_api_status)
    
    def show_api_tooltip(self, usage):
        """Mostra tooltip com informações detalhadas da API."""
        tooltip_text = f"""Status da API:
1 min: {usage['requests_1min']}/{usage['limit_1min']} ({usage['1min']:.1f}%)
5 min: {usage['requests_5min']}/{usage['limit_5min']} ({usage['5min']:.1f}%)"""
        
        # Cria tooltip temporário
        x, y, _, _ = self.update_button.bbox("insert")
        x += self.update_button.winfo_rootx() + 25
        y += self.update_button.winfo_rooty() + 20
        
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=tooltip_text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()
        
        # Remove tooltip após 3 segundos
        self.root.after(3000, lambda: self.tooltip.destroy() if hasattr(self, 'tooltip') else None)

    def _update_error(self, error_msg):
        """Chamado quando há erro na atualização manual."""
        self.update_button.config(state='normal', text='🔄 Atualizar Preços')
        self.update_status_label.config(text="✗ Erro", bootstyle="danger")
        
        # Remove a mensagem de erro após 5 segundos
        self.root.after(5000, lambda: self.update_status_label.config(text=""))

    def _on_mousewheel(self, event):
        """Manipula o evento de rolagem do mouse para o canvas"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _pulse_label(self, label, color_style):
        """
        Cria um efeito de pulsação no label para destacar mudanças de preço
        """
        # Salva o estilo atual
        original_style = label.cget('bootstyle')
        
        # Sequência de pulsação: forte -> fraco -> normal
        self.root.after(0, lambda: label.config(bootstyle=f"{color_style}"))
        self.root.after(600, lambda: label.config(bootstyle=f"{color_style}-outline"))
        self.root.after(1200, lambda: label.config(bootstyle=original_style))

def get_current_config():
    """Retorna a configuração atual do aplicativo."""
    config_path = os.path.join(get_application_path(), "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "cryptos_to_monitor": [],
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "check_interval_seconds": 300
        }

if __name__ == "__main__":
    config = get_current_config()
    
    if 'market_analysis_config' not in config:
        config['market_analysis_config'] = {
            'top_n': 25,
            'min_market_cap': 50000000
        }
        
    all_symbols_list = fetch_all_binance_symbols_startup(config)
    
    startup_root = ttkb.Window(themename="darkly")
    
    if not config.get("cryptos_to_monitor"):
        startup_root.withdraw()
        config_dialog = StartupConfigDialog(startup_root, all_symbols_list, config)
        startup_root.wait_window(config_dialog)
        if not config_dialog.session_started:
            sys.exit("Configuração inicial cancelada.")
            
    app = CryptoApp(startup_root, config, all_symbols_list)
    startup_root.protocol("WM_DELETE_WINDOW", app.on_closing)
    startup_root.mainloop()