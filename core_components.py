# core_components.py
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import winsound
import ttkbootstrap as ttkb
import pandas as pd # Mantido, embora não diretamente usado pelas classes de UI, pode ser útil para outras funções dentro do core_components ou em futuras extensões que interajam com DataFrames em UI.

TOOLTIP_DEFINITIONS = {
    "preco_baixo": "Alerta quando o preço da moeda cai e atinge o valor que você definiu.",
    "preco_alto": "Alerta quando o preço da moeda sobe e atinge o valor que você definiu.",
    "rsi_sobrevendido": "RSI (Índice de Força Relativa) abaixo de 30. Sugere que o ativo pode estar desvalorizado.",
    "rsi_sobrecomprado": "RSI (Índice de Força Relativa) acima de 70. Sugere que o ativo pode estar supervalorizado.",
    "bollinger_abaixo": "O preço fechou abaixo da linha inferior das Bandas de Bollinger.",
    "bollinger_acima": "O preço fechou acima da linha superior das Bandas de Bollinger.",
    "macd_cruz_baixa": "Cruzamento de Baixa do MACD. A linha MACD cruza para baixo da linha de sinal.",
    "macd_cruz_alta": "Cruzamento de Alta do MACD. A linha MACD cruza para cima da linha de sinal.",
    "mme_cruz_morte": "Cruz da Morte (MME 50 cruza para baixo da 200).",
    "mme_cruz_dourada": "Cruz Dourada (MME 50 cruza para cima da 200).",
    "fuga_capital_significativa": "Volume de negociação alto combinado com queda de preço. Sugere grande saída de capital.",
    "entrada_capital_significativa": "Volume de negociação alto combinado com alta de preço. Sugere grande entrada de capital."
}

def get_application_path():
    """Retorna o caminho do diretório da aplicação."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class CryptoCard(ttkb.Frame):
    """
    Componente visual para exibir os dados de uma criptomoeda.
    Esta é a versão redesenhada com visual moderno.
    """
    def __init__(self, parent, symbol, coin_name=""):
        # CORREÇÃO: Chamar super().__init__ primeiro e passar os argumentos de estilo.
        # Os argumentos de estilo como 'relief' e 'borderwidth' devem ser passados aqui.
        super().__init__(parent, padding=10, relief="solid", borderwidth=1, bootstyle="dark")
        
        # Armazena os dados
        self.symbol = symbol
        self.previous_price = 0.0  # Atributo para o efeito "Live Ticker"

        # --- CABEÇALHO DO CARD ---
        header_frame = ttkb.Frame(self, bootstyle="dark")
        header_frame.pack(fill='x', pady=(0, 12))
        
        # Símbolo da moeda com destaque principal (MUDANÇA AQUI)
        self.symbol_label = ttkb.Label(
            header_frame, 
            text=f"{symbol}", # Sem parênteses
            font=("Segoe UI", 16, "bold"), # Fonte maior e em negrito
            bootstyle="info" # Usar "info" para dar destaque ou "light"
        )
        self.symbol_label.pack(side='left', padx=(0, 5)) 

        # Nome completo da moeda com estilo secundário (menos destaque) (MUDANÇA AQUI)
        self.full_name_label = ttkb.Label(
            header_frame, 
            text=f"({coin_name})", # Agora com parênteses
            font=("Segoe UI", 11), # Fonte menor
            bootstyle="secondary" # Menos destaque
        )
        self.full_name_label.pack(side='left')

        # --- DIVISOR ---
        divider = ttkb.Separator(self, bootstyle="secondary") 
        divider.pack(fill='x', pady=8)

        # --- PREÇO DESTAQUE ---
        price_frame = ttkb.Frame(self, bootstyle="dark")
        price_frame.pack(fill='x', pady=(0, 10))
        
        price_label = ttkb.Label(
            price_frame, 
            text="Preço:", 
            font=("Segoe UI", 12, "bold"),
            bootstyle="light"
        )
        price_label.pack(side='left')
        
        self.price_value = ttkb.Label(
            price_frame, 
            text="Carregando...", 
            font=("Segoe UI", 14, "bold"),
            bootstyle="success"
        )
        self.price_value.pack(side='right')

        # --- DADOS DO CARD ---
        self.data_labels = {"current_price": self.price_value}
        data_frame = ttkb.Frame(self, bootstyle="dark")
        data_frame.pack(fill='x')
        
        # Cria layout em duas colunas para os indicadores
        left_col = ttkb.Frame(data_frame, bootstyle="dark")
        right_col = ttkb.Frame(data_frame, bootstyle="dark")
        left_col.pack(side='left', fill='both', expand=True)
        right_col.pack(side='right', fill='both', expand=True)
        
        # Define os dados a exibir
        left_labels = {
            "price_change_24h": "Variação (24h):",
            "volume_24h": "Volume (24h):",
            "rsi_value": "RSI:"
        }
        
        right_labels = {
            "bollinger_signal": "Bollinger:",
            "macd_signal": "MACD:",
            "mme_cross": "MME:"
        }
        
        # Cria os labels para a coluna da esquerda
        for i, (key, text) in enumerate(left_labels.items()):
            indicator_frame = ttkb.Frame(left_col, bootstyle="dark")
            indicator_frame.pack(fill='x', pady=4)
            
            label = ttkb.Label(
                indicator_frame, 
                text=text, 
                font=("Segoe UI", 10), 
                bootstyle="light" 
            )
            label.pack(side='left')
            
            value = ttkb.Label(
                indicator_frame, 
                text="Carregando...",
                font=("Segoe UI", 10, "bold")
            )
            value.pack(side='right')
            self.data_labels[key] = value

        # Cria os labels para a coluna da direita
        for i, (key, text) in enumerate(right_labels.items()):
            indicator_frame = ttkb.Frame(right_col, bootstyle="dark")
            indicator_frame.pack(fill='x', pady=4)
            
            label = ttkb.Label(
                indicator_frame, 
                text=text, 
                font=("Segoe UI", 10), 
                bootstyle="light" 
            )
            label.pack(side='left')
            
            value = ttkb.Label(
                indicator_frame, 
                text="Carregando...",
                font=("Segoe UI", 10, "bold")
            )
            value.pack(side='right')
            self.data_labels[key] = value

class Tooltip:
    """Cria uma caixa de dicas que aparece ao passar o mouse sobre um widget."""
    def __init__(self, widget):
        self.widget = widget
        self.tooltip_window = None

    def show_tooltip(self, text):
        self.hide_tooltip()
        if not text: return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = ttkb.Label(self.tooltip_window, text=text, justify='left', background="#1c1c1c", foreground="white", relief='solid', borderwidth=1, font=("Helvetica", 10, "normal"), padding=8, wraplength=400)
        label.pack(ipadx=1)

    def hide_tooltip(self):
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = None

# AS FUNÇÕES calculate_rsi, calculate_bollinger_bands, calculate_macd, calculate_emas
# FORAM REMOVIDAS DAQUI E ESTÃO AGORA EM indicators.py

# --- CLASSES DE DIÁLOGO ---
class StartupConfigDialog(ttkb.Toplevel):
    def __init__(self, parent, all_symbols_list, config):
        super().__init__(parent)
        self.title("Configuração de Sessão de Monitoramento")
        self.config = config
        self.all_symbols_master = all_symbols_list
        self.session_started = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grab_set()
        self.geometry("800x600")

        main_frame = ttkb.Frame(self, padding=15)
        main_frame.pack(expand=True, fill='both')

        telegram_frame = ttkb.LabelFrame(main_frame, text="Configuração do Telegram", padding=15)
        telegram_frame.pack(fill='x', pady=(0, 15))
        
        ttkb.Label(telegram_frame, text="Bot Token:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.token_var = tk.StringVar(value=self.config.get("telegram_bot_token", ""))
        self.token_entry = ttkb.Entry(telegram_frame, textvariable=self.token_var, width=60)
        self.token_entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        ttkb.Label(telegram_frame, text="Chat ID:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.chat_id_var = tk.StringVar(value=self.config.get("telegram_chat_id", ""))
        self.chat_id_entry = ttkb.Entry(telegram_frame, textvariable=self.chat_id_var, width=60)
        self.chat_id_entry.grid(row=1, column=1, sticky='ew', padx=5)
        telegram_frame.columnconfigure(1, weight=1)

        paned_window = ttkb.PanedWindow(main_frame, orient='horizontal')
        paned_window.pack(fill='both', expand=True)

        left_pane = ttkb.Frame(paned_window, padding=5)
        paned_window.add(left_pane, weight=1)

        ttkb.Label(left_pane, text="Moedas Disponíveis").pack(anchor='w')
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_available_list)
        search_entry = ttkb.Entry(left_pane, textvariable=self.search_var)
        search_entry.pack(fill='x', pady=(5, 10))
        
        self.available_listbox = tk.Listbox(left_pane, selectmode='extended', exportselection=False, height=15)
        self.available_listbox.pack(fill='both', expand=True)

        buttons_frame = ttkb.Frame(paned_window)
        paned_window.add(buttons_frame)
        
        ttkb.Button(buttons_frame, text=">>", command=self._add_symbols, bootstyle="outline").pack(pady=20, padx=10)
        ttkb.Button(buttons_frame, text="<<", command=self._remove_symbols, bootstyle="outline").pack(pady=20, padx=10)

        right_pane = ttkb.Frame(paned_window, padding=5)
        paned_window.add(right_pane, weight=1)
        
        ttkb.Label(right_pane, text="Moedas Monitoradas").pack(anchor='w')
        self.monitored_listbox = tk.Listbox(right_pane, selectmode='extended', exportselection=False)
        self.monitored_listbox.pack(fill='both', expand=True, pady=(5,0))

        start_button = ttkb.Button(main_frame, text="Iniciar Monitoramento", command=self.on_start, bootstyle="success", padding=10)
        start_button.pack(side='bottom', pady=(15, 0))

        self._populate_lists()
        self.center_window()

    def _populate_lists(self):
        self.available_listbox.delete(0, tk.END)
        self.monitored_listbox.delete(0, tk.END)
        
        monitored_symbols = {crypto.get('symbol') for crypto in self.config.get("cryptos_to_monitor", []) if crypto.get('symbol')}
        
        for symbol in sorted(self.all_symbols_master):
            if symbol not in monitored_symbols:
                self.available_listbox.insert(tk.END, symbol)
        
        for symbol in sorted(list(monitored_symbols)):
            self.monitored_listbox.insert(tk.END, symbol)

    def _filter_available_list(self, *args):
        search_term = self.search_var.get().upper()
        
        self.available_listbox.delete(0, tk.END)
        
        monitored_symbols = set(self.monitored_listbox.get(0, tk.END))

        if not search_term:
            for symbol in sorted(self.all_symbols_master):
                if symbol not in monitored_symbols:
                    self.available_listbox.insert(tk.END, symbol)
        else:
            for symbol in self.all_symbols_master:
                if search_term in symbol.upper() and symbol not in monitored_symbols:
                    self.available_listbox.insert(tk.END, symbol)

    def _add_symbols(self):
        selected_indices = self.available_listbox.curselection()
        if not selected_indices: return
        
        symbols_to_move = [self.available_listbox.get(i) for i in selected_indices]
        for symbol in sorted(symbols_to_move):
            self.monitored_listbox.insert(tk.END, symbol)
        
        for i in sorted(selected_indices, reverse=True):
            self.available_listbox.delete(i)

    def _remove_symbols(self):
        selected_indices = self.monitored_listbox.curselection()
        if not selected_indices: return
        
        symbols_to_move = [self.monitored_listbox.get(i) for i in selected_indices]
        for symbol in symbols_to_move:
             all_items = list(self.available_listbox.get(0, tk.END))
             all_items.append(symbol)
             all_items.sort()
             self.available_listbox.delete(0, tk.END)
             for item in all_items:
                 self.available_listbox.insert(tk.END, item)

        for i in sorted(selected_indices, reverse=True):
            self.monitored_listbox.delete(i)
        
        self._filter_available_list()

    def on_save(self):
        self.config["telegram_bot_token"] = self.token_var.get()
        self.config["telegram_chat_id"] = self.chat_id_var.get()
        
        new_monitored_symbols = set(self.monitored_listbox.get(0, tk.END))
        
        current_configs = {crypto['symbol']: crypto for crypto in self.config.get("cryptos_to_monitor", []) if 'symbol' in crypto}
        
        new_config_list = []
        for symbol in sorted(list(new_monitored_symbols)):
            if symbol in current_configs:
                new_config_list.append(current_configs[symbol])
            else:
                # Inclui configurações de alerta padrão para novas moedas
                default_alert_config = {
                    "notes": "",
                    "sound": "sons/Alerta.mp3",
                    "conditions": {
                        "preco_baixo": {"enabled": False, "value": 0.0},
                        "preco_alto": {"enabled": False, "value": 0.0},
                        "rsi_sobrevendido": {"enabled": True, "value": 30.0},
                        "rsi_sobrecomprado": {"enabled": True, "value": 70.0},
                        "bollinger_abaixo": {"enabled": True},
                        "bollinger_acima": {"enabled": True},
                        "macd_cruz_baixa": {"enabled": True},
                        "macd_cruz_alta": {"enabled": True},
                        "mme_cruz_morte": {"enabled": True},
                        "mme_cruz_dourada": {"enabled": True},
                        "fuga_capital_significativa": {"enabled": False, "value": "0.5, -2.0"}, 
                        "entrada_capital_significativa": {"enabled": False, "value": "0.3, 1.0"} 
                    },
                    "triggered_conditions": []
                }
                new_config_list.append({"symbol": symbol, "alert_config": default_alert_config})

        self.parent_app.config["cryptos_to_monitor"] = new_config_list
        self.parent_app.save_config()
        self.parent_app.update_coin_cards_display()
        messagebox.showinfo("Sucesso", "Lista de moedas atualizada.", parent=self)
        self.destroy()

    def on_close(self):
        self.session_started = False
        self.destroy()
    
    def center_window(self):
        self.update_idletasks()
        self.resizable(True, True)
        min_width = 700
        min_height = 500
        self.minsize(min_width, min_height)
        width, height = self.winfo_width(), self.winfo_height()
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class AlertConfigDialog(ttkb.Toplevel):
    def __init__(self, parent_app, symbol, alert_config_data=None):
        # CORREÇÃO AQUI: parent_app deve ser o master (janela principal), não parent_app.root
        super().__init__(parent_app) 
        self.parent_app = parent_app
        self.result = None
        self.title(f"Configurar Alertas para {symbol}")
        self.geometry("700x750")
        self.transient(self.master)
        self.grab_set()
        self.symbol = symbol
        self.config_data = alert_config_data if alert_config_data else self._get_default_config()
        self.vars = {} 
        
        # Container principal com tema escuro
        main_container = ttkb.Frame(self, bootstyle="dark", padding=20)
        main_container.pack(expand=True, fill="both")
        
        # Cabeçalho com título destacado
        header_frame = ttkb.Frame(main_container, bootstyle="dark")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ttkb.Label(
            header_frame, 
            text=f"Alertas para {symbol}", 
            font=("Segoe UI", 16, "bold"),
            bootstyle="info"
        )
        title_label.pack(side="left")
        
        subtitle_label = ttkb.Label(
            header_frame, 
            text="Configure os parâmetros dos alertas", 
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        subtitle_label.pack(side="left", padx=(10, 0))
        
        # Seção de configurações gerais
        common_frame = ttkb.LabelFrame(
            main_container, 
            text="Configurações Gerais", 
            padding=15,
            bootstyle="dark"
        )
        common_frame.pack(side="top", fill="x", pady=(0, 15))
        
        # Campo de observações
        notes_frame = ttkb.Frame(common_frame, bootstyle="dark")
        notes_frame.pack(fill="x", pady=5)
        
        ttkb.Label(
            notes_frame, 
            text="📝 Observações:", 
            font=("Segoe UI", 10, "bold"),
            bootstyle="light"
        ).pack(side="left")
        
        self.notes_var = ttkb.StringVar(value=self.config_data.get('notes', ''))
        self.notes_entry = ttkb.Entry(
            notes_frame, 
            textvariable=self.notes_var,
            font=("Segoe UI", 10),
            bootstyle="dark"
        )
        self.notes_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Campo de arquivo de som
        sound_frame = ttkb.Frame(common_frame, bootstyle="dark")
        sound_frame.pack(fill="x", pady=10)
        
        ttkb.Label(
            sound_frame, 
            text="🔊 Arquivo de Som:", 
            font=("Segoe UI", 10, "bold"),
            bootstyle="light"
        ).pack(side="left")
        
        sound_controls = ttkb.Frame(sound_frame, bootstyle="dark")
        sound_controls.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        self.sound_var = ttkb.StringVar(value=self.config_data.get('sound', 'sons/Alerta.mp3'))
        self.sound_entry = ttkb.Entry(
            sound_controls, 
            textvariable=self.sound_var, 
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="dark"
        )
        self.sound_entry.pack(side="left", fill="x", expand=True)
        
        ttkb.Button(
            sound_controls, 
            text="📁", 
            command=self.browse_sound_file, 
            bootstyle="info", 
            width=3
        ).pack(side="left", padx=5)
        
        ttkb.Button(
            sound_controls, 
            text="▶", 
            command=self.preview_sound, 
            bootstyle="success", 
            width=3
        ).pack(side="left")
        
        # Separador visual
        ttkb.Separator(main_container, bootstyle="info").pack(fill="x", pady=10)
        
        # Seção de gatilhos de alerta
        conditions_header = ttkb.Frame(main_container, bootstyle="dark")
        conditions_header.pack(fill="x", pady=(0, 10))
        
        ttkb.Label(
            conditions_header, 
            text="Gatilhos de Alerta", 
            font=("Segoe UI", 14, "bold"),
            bootstyle="info"
        ).pack(side="left")
        
        help_button = ttkb.Button(
            conditions_header, 
            text="❓", 
            bootstyle="secondary", 
            width=3
        )
        help_button.pack(side="right")
        
        # Tooltip para o botão de ajuda
        tooltip = Tooltip(help_button)
        help_button.bind("<Enter>", lambda e: tooltip.show_tooltip("Configure os alertas que deseja receber para esta moeda."))
        help_button.bind("<Leave>", lambda e: tooltip.hide_tooltip())
        
        # Frame para condições com scroll
        conditions_outer_frame = ttkb.Frame(main_container, bootstyle="dark")
        conditions_outer_frame.pack(side="top", fill="both", expand=True)
        
        canvas = tk.Canvas(
            conditions_outer_frame, 
            borderwidth=0, 
            highlightthickness=0,
            bg=conditions_outer_frame.cget('bg')
        )
        
        scrollbar = ttkb.Scrollbar(
            conditions_outer_frame, 
            orient="vertical", 
            command=canvas.yview, 
            bootstyle="round-dark"
        )
        
        conditions_frame = ttkb.Frame(canvas, bootstyle="dark", padding=(10, 0))
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas_frame_id = canvas.create_window((0, 0), window=conditions_frame, anchor="nw")
        
        def on_frame_configure(event): 
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        def on_canvas_configure(event): 
            canvas.itemconfig(canvas_frame_id, width=event.width)
            
        conditions_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Cria widgets de condição com visuais modernos
        self._create_condition_widgets(conditions_frame)
        
        # Barra de ações na parte inferior
        btn_frame = ttkb.Frame(main_container, bootstyle="dark", padding=(0, 15, 0, 0))
        btn_frame.pack(side="bottom", fill="x")
        
        ttkb.Button(
            btn_frame, 
            text="✅ Salvar", 
            command=self.on_save, 
            bootstyle="success",
            padding=10
        ).pack(side="left", padx=5)
        
        ttkb.Button(
            btn_frame, 
            text="❌ Cancelar", 
            command=self.destroy, 
            bootstyle="danger-outline",
            padding=10
        ).pack(side="left", padx=5)
        
        # Centraliza a janela
        self.parent_app.center_toplevel_on_main(self)
        self.resizable(False, True)

    def _get_default_config(self):
        return {"notes": "", "sound": "sons/Alerta.mp3", "conditions": {"preco_baixo": {"enabled": False, "value": 0.0}, "preco_alto": {"enabled": False, "value": 0.0}, "rsi_sobrevendido": {"enabled": False, "value": 30.0}, "rsi_sobrecomprado": {"enabled": False, "value": 70.0}, "bollinger_abaixo": {"enabled": False}, "bollinger_acima": {"enabled": False}, "macd_cruz_baixa": {"enabled": False}, "macd_cruz_alta": {"enabled": False}, "mme_cruz_morte": {"enabled": False}, "mme_cruz_dourada": {"enabled": False}}, "triggered_conditions": []}

    def _create_condition_widgets(self, parent_frame):
        """Cria widgets modernos para configuração de condições de alerta"""
        
        # Ícones para os tipos de alertas
        icons = {
            'preco_baixo': '⬇️',
            'preco_alto': '⬆️',
            'rsi_sobrevendido': '🟢',
            'rsi_sobrecomprado': '🔴',
            'bollinger_abaixo': '↘️',
            'bollinger_acima': '↗️',
            'macd_cruz_baixa': '📉',
            'macd_cruz_alta': '📈',
            'mme_cruz_morte': '☠️',
            'mme_cruz_dourada': '🌟',
            'fuga_capital_significativa': '💸',
            'entrada_capital_significativa': '💰'
        }
        
        # Definições de condições com ícones
        condition_definitions = {
            'preco_baixo': {
                'text': 'Preço Abaixo de ($)', 
                'has_value': True, 
                'default': 0.0,
                'icon': icons['preco_baixo'],
                'category': 'price'
            },
            'preco_alto': {
                'text': 'Preço Acima de ($)', 
                'has_value': True, 
                'default': 0.0,
                'icon': icons['preco_alto'],
                'category': 'price'
            },
            'rsi_sobrevendido': {
                'text': 'RSI Sobrevendido (<=)', 
                'has_value': True, 
                'default': 30.0,
                'icon': icons['rsi_sobrevendido'],
                'category': 'indicator'
            },
            'rsi_sobrecomprado': {
                'text': 'RSI Sobrecomprado (>=)', 
                'has_value': True, 
                'default': 70.0,
                'icon': icons['rsi_sobrecomprado'],
                'category': 'indicator'
            },
            'bollinger_abaixo': {
                'text': 'Abaixo da Banda Inferior', 
                'has_value': False,
                'icon': icons['bollinger_abaixo'],
                'category': 'indicator'
            },
            'bollinger_acima': {
                'text': 'Acima da Banda Superior', 
                'has_value': False,
                'icon': icons['bollinger_acima'],
                'category': 'indicator'
            },
            'macd_cruz_baixa': {
                'text': 'MACD: Cruzamento de Baixa', 
                'has_value': False,
                'icon': icons['macd_cruz_baixa'],
                'category': 'indicator'
            },
            'macd_cruz_alta': {
                'text': 'MACD: Cruzamento de Alta', 
                'has_value': False,
                'icon': icons['macd_cruz_alta'],
                'category': 'indicator'
            },
            'mme_cruz_morte': {
                'text': 'MME: Cruz da Morte (50/200)', 
                'has_value': False,
                'icon': icons['mme_cruz_morte'],
                'category': 'indicator'
            },
            'mme_cruz_dourada': {
                'text': 'MME: Cruz Dourada (50/200)', 
                'has_value': False,
                'icon': icons['mme_cruz_dourada'],
                'category': 'indicator'
            },
            'fuga_capital_significativa': {
                'text': 'Fuga de Capital (Vol %, Var %)', 
                'has_value': True, 
                'default': "0.5, -2.0", 
                'icon': icons['fuga_capital_significativa'],
                'category': 'volume',
                'info_tooltip': 'Ex: "0.5, -2.0" para 0.5% do Cap.Merc. e variação menor que -2%.'
            },
            'entrada_capital_significativa': {
                'text': 'Entrada de Capital (Vol %, Var %)', 
                'has_value': True, 
                'default': "0.3, 1.0", 
                'icon': icons['entrada_capital_significativa'],
                'category': 'volume',
                'info_tooltip': 'Ex: "0.3, 1.0" para 0.3% do Cap.Merc. e variação maior que 1%.'
            }
        }
        
        # Categorias para organização visual
        categories = {
            'price': {
                'title': 'Alertas de Preço',
                'color': 'info',
                'icon': '💲'
            },
            'indicator': {
                'title': 'Alertas de Indicadores Técnicos',
                'color': 'warning',
                'icon': '📊'
            },
            'volume': {
                'title': 'Alertas de Volume e Capital',
                'color': 'success',
                'icon': '📈'
            }
        }
        
        # Agrupa condições por categoria
        categorized_conditions = {}
        for key, details in condition_definitions.items():
            category = details.get('category', 'other')
            if category not in categorized_conditions:
                categorized_conditions[category] = []
            categorized_conditions[category].append((key, details))
        
        # Linha atual para posicionamento
        row = 0
        
        # Cria seções por categoria
        for category, cat_info in categories.items():
            if category in categorized_conditions:
                # Cria cabeçalho da categoria
                category_frame = ttkb.Frame(parent_frame, bootstyle="dark")
                category_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(15, 5))
                
                # Título da categoria com ícone
                ttkb.Label(
                    category_frame,
                    text=f"{cat_info['icon']} {cat_info['title']}",
                    font=("Segoe UI", 12, "bold"),
                    bootstyle=cat_info['color']
                ).pack(side="left")
                
                # Separador para destacar a categoria
                ttkb.Separator(
                    parent_frame, 
                    bootstyle=cat_info['color']
                ).grid(row=row+1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
                
                row += 2  # Avança para além do cabeçalho e separador
                
                # Cria widgets para cada condição na categoria
                for key, details in categorized_conditions[category]:
                    current_cond_config = self.config_data.get('conditions', {}).get(key, {})
                    enabled_var = tk.BooleanVar(value=current_cond_config.get('enabled', False))
                    value_var = None
                    
                    # Frame para cada condição
                    condition_frame = ttkb.Frame(parent_frame, bootstyle="dark")
                    condition_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=5)
                    
                    # Gerencia valores para condições com entrada
                    if details['has_value']:
                        default_value = str(details.get('default', 0.0))
                        current_value = current_cond_config.get('value', default_value)
                        
                        if key in ['fuga_capital_significativa', 'entrada_capital_significativa']:
                            value_var = tk.StringVar(value=current_value)
                        else:
                            value_var = tk.DoubleVar(value=float(current_value))
                    
                    # Armazena as variáveis para uso posterior
                    self.vars[key] = {'enabled': enabled_var, 'value': value_var}
                    
                    # Checkbox com texto e ícone
                    cb_text = f"{details.get('icon', '')} {details['text']}"
                    cb = ttkb.Checkbutton(
                        condition_frame, 
                        text=cb_text, 
                        variable=enabled_var, 
                        bootstyle=f"{cat_info['color']}"
                    )
                    cb.pack(side="left", padx=(5, 10))
                    
                    # Tooltip para informações adicionais
                    tooltip_text = TOOLTIP_DEFINITIONS.get(key, "Sem descrição.")
                    if 'info_tooltip' in details:
                        tooltip_text += f"\n\nDica: {details['info_tooltip']}"
                    
                    tooltip = Tooltip(cb)
                    cb.bind("<Enter>", lambda e, text=tooltip_text, tt=tooltip: tt.show_tooltip(text))
                    cb.bind("<Leave>", lambda e, tt=tooltip: tt.hide_tooltip())
                    
                    # Entrada de valor se aplicável
                    if details['has_value']:
                        entry = ttkb.Entry(
                            condition_frame, 
                            textvariable=value_var, 
                            width=15,
                            font=("Segoe UI", 10),
                            bootstyle="dark"
                        )
                        entry.pack(side="right", padx=5)
                        
                        # Função para habilitar/desabilitar a entrada
                        def toggle_entry_state(entry_widget=entry, check_var=enabled_var):
                            entry_widget.config(state='normal' if check_var.get() else 'disabled')
                        
                        # Configura o callback do checkbox
                        cb.config(command=toggle_entry_state)
                        
                        # Estado inicial da entrada
                        toggle_entry_state()
                    
                    row += 1
        
        # Configura o layout
        parent_frame.columnconfigure(0, weight=1)

    def browse_sound_file(self):
        app_path = get_application_path()
        initial_dir = os.path.join(app_path, 'sons')
        if not os.path.isdir(initial_dir): initial_dir = app_path
        filepath = filedialog.askopenfilename(title="Selecione um arquivo .wav", initialdir=initial_dir, filetypes=[("Arquivos de Som", "*.wav")])
        if filepath: self.sound_var.set(os.path.relpath(filepath, app_path).replace("\\", "/"))

    def preview_sound(self):
        sound_path_str = self.sound_var.get()
        if not sound_path_str: 
            messagebox.showwarning("Aviso", "Nenhum arquivo de som selecionado.", parent=self); return
        sound_path = sound_path_str if os.path.isabs(sound_path_str) else os.path.join(get_application_path(), sound_path_str)
        if os.path.exists(sound_path):
            try: winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e: messagebox.showerror("Erro", f"Não foi possível tocar o som:\n{e}", parent=self)
        else: messagebox.showerror("Erro", "Arquivo de som não encontrado.", parent=self)
    
    def on_save(self):
        final_config = {"symbol": self.symbol, "alert_config": {"notes": self.notes_var.get(), "sound": self.sound_var.get(), "conditions": {}, "triggered_conditions": self.config_data.get('triggered_conditions', [])}}
        for key, var_dict in self.vars.items():
            is_enabled = var_dict['enabled'].get()
            condition_data = {"enabled": is_enabled}
            if var_dict['value'] is not None:
                try:
                    value = var_dict['value'].get()
                    # Validação específica para valores numéricos, permitindo strings para as novas condições
                    if key in ['preco_baixo', 'preco_alto', 'rsi_sobrevendido', 'rsi_sobrecomprado']:
                        value = float(value) # Tenta converter para float para validação
                        if is_enabled and value <= 0 and key in ['preco_baixo', 'preco_alto']:
                             messagebox.showerror("Erro de Validação", f"O valor para '{key}' deve ser maior que zero.", parent=self); return
                    condition_data["value"] = value # Salva o valor (float ou string)
                except tk.TclError:
                    messagebox.showerror("Erro de Validação", f"Por favor, insira um número válido para '{key}'.", parent=self); return
                except ValueError: # Captura erro se float() falhar para as novas strings
                    if key in ['fuga_capital_significativa', 'entrada_capital_significativa']:
                        # Validação simples para o formato "num, num"
                        parts = str(value).split(',')
                        if len(parts) != 2 or not all(self._is_float(p.strip()) for p in parts):
                            messagebox.showerror("Erro de Validação", f"Formato inválido para '{key}'. Use 'num,num'.", parent=self); return
                        condition_data["value"] = value # Salva a string original
                    else:
                        messagebox.showerror("Erro de Validação", f"Por favor, insira um número válido para '{key}'.", parent=self); return

            final_config["alert_config"]["conditions"][key] = condition_data
        self.result = final_config
        self.destroy()

    def _is_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

class AlertManagerWindow(ttkb.Toplevel):
    def __init__(self, parent_app):
        # CORREÇÃO AQUI: parent_app deve ser o master (janela principal), não parent_app.root
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.title("Gerenciador de Alertas")
        self.geometry("1200x700")
        self.transient(self.master)
        self.grab_set()
        
        # Container principal com padding
        main_container = ttkb.Frame(self, padding=15, bootstyle="dark")
        main_container.pack(expand=True, fill='both')
        
        # Cabeçalho
        header_frame = ttkb.Frame(main_container, bootstyle="dark")
        header_frame.pack(fill='x', pady=(0, 15))
        
        header_title = ttkb.Label(
            header_frame, 
            text="GERENCIADOR DE ALERTAS", 
            font=("Segoe UI", 16, "bold"),
            bootstyle="info"
        )
        header_title.pack(side="left")
        
        header_subtitle = ttkb.Label(
            header_frame, 
            text="Configuração personalizada por moeda", 
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        header_subtitle.pack(side="left", padx=(10, 0))
        
        # Painel dividido
        self.paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        self.paned_window.pack(expand=True, fill='both')
        
        # Painel esquerdo - Lista de moedas
        symbols_container = ttkb.Frame(self.paned_window, padding=5, bootstyle="dark")
        self.paned_window.add(symbols_container, weight=1)
        
        # Título da seção de moedas
        symbols_header = ttkb.Frame(symbols_container, bootstyle="dark")
        symbols_header.pack(fill='x', pady=(0, 10))
        
        ttkb.Label(
            symbols_header, 
            text="Moedas Monitoradas", 
            font=("Segoe UI", 13, "bold"),
            bootstyle="light"
        ).pack(side="left")
        
        # Campo de busca para moedas
        search_frame = ttkb.Frame(symbols_container, bootstyle="dark")
        search_frame.pack(fill='x', pady=(0, 10))
        
        search_icon = ttkb.Label(
            search_frame, 
            text="🔍", 
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        search_icon.pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = ttkb.Entry(
            search_frame, 
            textvariable=self.search_var,
            bootstyle="dark"
        )
        search_entry.pack(side="left", fill="x", expand=True)
        
        # Lista de moedas com estilo moderno
        symbols_frame = ttkb.Frame(symbols_container, bootstyle="dark")
        symbols_frame.pack(fill='both', expand=True)
        
        self.symbols_tree = ttkb.Treeview(
            symbols_frame, 
            columns=('symbol',), 
            show='headings', 
            bootstyle="dark",
            height=20
        )
        self.symbols_tree.heading('symbol', text='Símbolo')
        self.symbols_tree.column('symbol', width=150, anchor=tk.W)
        
        # Barra de rolagem para a lista de moedas
        symbols_scrollbar = ttkb.Scrollbar(
            symbols_frame,
            orient="vertical",
            command=self.symbols_tree.yview,
            bootstyle="round-dark"
        )
        self.symbols_tree.configure(yscrollcommand=symbols_scrollbar.set)
        
        self.symbols_tree.pack(side="left", expand=True, fill='both')
        symbols_scrollbar.pack(side="right", fill='y')
        
        # Vincula evento de seleção
        self.symbols_tree.bind("<<TreeviewSelect>>", self.on_symbol_selected)
        
        # Botão para gerenciar moedas
        manage_btn = ttkb.Button(
            symbols_container, 
            text="➕ Adicionar/Remover Moedas", 
            command=self.manage_monitored_symbols,
            bootstyle="success",
            padding=10
        )
        manage_btn.pack(side='bottom', fill='x', pady=(10, 0))
        
        # Painel direito - Detalhes e alertas
        alerts_container = ttkb.Frame(self.paned_window, padding=5, bootstyle="dark")
        self.paned_window.add(alerts_container, weight=2)
        
        # Cabeçalho da seção de alertas
        alerts_header = ttkb.Frame(alerts_container, bootstyle="dark")
        alerts_header.pack(fill='x', pady=(0, 10))
        
        self.alert_title = ttkb.Label(
            alerts_header, 
            text="Condições de Alerta", 
            font=("Segoe UI", 13, "bold"),
            bootstyle="light"
        )
        self.alert_title.pack(side="left")
        
        self.selected_coin = ttkb.Label(
            alerts_header, 
            text="", 
            font=("Segoe UI", 13, "bold"),
            bootstyle="warning"
        )
        self.selected_coin.pack(side="left", padx=(10, 0))
        
        # Tabela de condições
        alerts_table_frame = ttkb.LabelFrame(
            alerts_container, 
            text="Condições de Alerta Ativadas", 
            padding=15,
            bootstyle="dark"
        )
        alerts_table_frame.pack(expand=True, fill='both', pady=(0, 15))
        
        self.conditions_tree = ttkb.Treeview(
            alerts_table_frame, 
            columns=('condition', 'value'), 
            show='headings', 
            bootstyle="dark",
            height=15
        )
        
        # Configuração das colunas
        self.conditions_tree.heading('condition', text='Condição')
        self.conditions_tree.column('condition', width=300, anchor=tk.W)
        self.conditions_tree.heading('value', text='Valor/Estado')
        self.conditions_tree.column('value', width=200, anchor=tk.W)
        
        # Barra de rolagem para a tabela de condições
        conditions_scrollbar = ttkb.Scrollbar(
            alerts_table_frame,
            orient="vertical",
            command=self.conditions_tree.yview,
            bootstyle="round-dark"
        )
        self.conditions_tree.configure(yscrollcommand=conditions_scrollbar.set)
        
        self.conditions_tree.pack(side="left", expand=True, fill='both')
        conditions_scrollbar.pack(side="right", fill='y')
        
        # Controles para configuração de alertas
        alerts_controls_frame = ttkb.Frame(alerts_container, bootstyle="dark", padding=5)
        alerts_controls_frame.pack(fill='x')
        
        # Botão de configuração com ícone
        self.config_alert_btn = ttkb.Button(
            alerts_controls_frame, 
            text="⚙️ Configurar Alertas", 
            command=self.open_config_alert_dialog, 
            bootstyle="info", 
            state="disabled",
            padding=10
        )
        self.config_alert_btn.pack(side='left', padx=5)
        
        # Botão de ajuda
        help_btn = ttkb.Button(
            alerts_controls_frame, 
            text="❓ Ajuda", 
            bootstyle="secondary", 
            padding=10
        )
        help_btn.pack(side='right', padx=5)
        
        # Barra de status na parte inferior
        status_bar = ttkb.Frame(main_container, bootstyle="dark", padding=(0, 10, 0, 0))
        status_bar.pack(fill='x', side="bottom")
        
        status_label = ttkb.Label(
            status_bar, 
            text="Selecione uma moeda para visualizar ou configurar seus alertas", 
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        status_label.pack(side="left")
        
        # Preenche a lista de símbolos
        self._populate_symbols_tree()
        
        # Busca em tempo real
        self.search_var.trace_add("write", self._filter_symbols)
        
        # Centraliza a janela
        self.parent_app.center_toplevel_on_main(self)
        
    def _populate_symbols_tree(self):
        """Preenche a árvore de símbolos com as moedas monitoradas"""
        self.symbols_tree.selection_remove(self.symbols_tree.selection())
        for i in self.symbols_tree.get_children(): 
            self.symbols_tree.delete(i)
            
        monitored_symbols = [crypto.get('symbol') for crypto in self.parent_app.config.get("cryptos_to_monitor", []) if crypto.get('symbol')]
        
        # Ordena os símbolos alfabeticamente
        for symbol in sorted(monitored_symbols): 
            # Ícone para cada moeda
            icon_text = "💰"
            self.symbols_tree.insert('', tk.END, iid=symbol, values=(f"{icon_text} {symbol}",))
            
        self.on_symbol_selected()

    def on_symbol_selected(self, event=None):
        selected_items = self.symbols_tree.selection()
        if not selected_items:
            for i in self.conditions_tree.get_children(): self.conditions_tree.delete(i)
            self.config_alert_btn['state'] = 'disabled'
            return
        self.config_alert_btn['state'] = 'normal'
        self._populate_conditions_summary(selected_items[0])
        
    def _populate_conditions_summary(self, symbol):
        for i in self.conditions_tree.get_children(): self.conditions_tree.delete(i)
        crypto_config = next((c for c in self.parent_app.config.get("cryptos_to_monitor", []) if c.get('symbol') == symbol), None)
        if not crypto_config or 'alert_config' not in crypto_config:
            self.conditions_tree.insert('', tk.END, values=("Nenhuma configuração encontrada.", ""))
            return
        conditions = crypto_config['alert_config'].get('conditions', {})
        any_enabled = False
        for key, details in conditions.items():
            if details.get('enabled'):
                any_enabled = True
                value_str = f"{details.get('value', '')}" if 'value' in details else "Ativado"
                self.conditions_tree.insert('', tk.END, values=(key.replace('_', ' ').title(), value_str))
        if not any_enabled:
             self.conditions_tree.insert('', tk.END, values=("Nenhuma condição habilitada.", ""))

    def get_selected_symbol(self):
        selected_items = self.symbols_tree.selection()
        return selected_items[0] if selected_items else None
        
    def open_config_alert_dialog(self):
        selected_symbol = self.get_selected_symbol()
        if not selected_symbol: return
        crypto_config = next((c for c in self.parent_app.config.get("cryptos_to_monitor", []) if c.get('symbol') == selected_symbol), None)
        alert_data = crypto_config.get('alert_config') if crypto_config else None
        dialog = AlertConfigDialog(self.parent_app, selected_symbol, alert_config_data=alert_data)
        self.wait_window(dialog)
        if dialog.result:
            symbol_to_update = dialog.result.pop('symbol')
            found = False
            for crypto in self.parent_app.config.get("cryptos_to_monitor", []):
                if crypto.get('symbol') == symbol_to_update:
                    crypto['alert_config'] = dialog.result['alert_config']; found = True; break
            if not found: self.parent_app.config["cryptos_to_monitor"].append(dialog.result)
            self.parent_app.save_config()
            messagebox.showinfo("Sucesso", "Configuração de alerta salva!", parent=self)
            self._populate_conditions_summary(selected_symbol)

    def manage_monitored_symbols(self):
        dialog = ManageSymbolsDialog(self)
        self.wait_window(dialog)
        self._populate_symbols_tree()

class ManageSymbolsDialog(ttkb.Toplevel):
    def __init__(self, parent_manager):
        # CORREÇÃO AQUI: parent_manager.parent_app deve ser o master (janela principal), não parent_manager.parent_app.root
        super().__init__(parent_manager.parent_app)
        self.parent_app = parent_manager.parent_app
        self.parent_manager = parent_manager
        self.title("Gerenciar Moedas Monitoradas")
        self.geometry("800x600")
        self.transient(self.master)
        self.grab_set()
        main_frame = ttkb.Frame(self, padding=10)
        main_frame.pack(expand=True, fill='both')
        left_frame = ttkb.LabelFrame(main_frame, text="Moedas Disponíveis", padding=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        self.available_search_var = ttkb.StringVar()
        self.available_search_var.trace_add("write", self._filter_available)
        self.available_entry = ttkb.Entry(left_frame, textvariable=self.available_search_var)
        self.available_entry.pack(fill='x', pady=(0, 5))
        self.available_listbox = tk.Listbox(left_frame, selectmode='extended', exportselection=False)
        self.available_listbox.pack(fill='both', expand=True)
        buttons_frame = ttkb.Frame(main_frame, padding=10)
        buttons_frame.pack(side='left', fill='y', anchor='center')
        ttkb.Button(buttons_frame, text="Adicionar >>", command=self._add_symbols, bootstyle="success-outline").pack(pady=5)
        ttkb.Button(buttons_frame, text="<< Remover", command=self._remove_symbols, bootstyle="danger-outline").pack(pady=5)
        right_frame = ttkb.LabelFrame(main_frame, text="Moedas Monitoradas", padding=10)
        right_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        self.monitored_search_var = ttkb.StringVar()
        self.monitored_search_var.trace_add("write", self._filter_monitored)
        self.monitored_entry = ttkb.Entry(right_frame, textvariable=self.monitored_search_var)
        self.monitored_entry.pack(fill='x', pady=(0, 5))
        self.monitored_listbox = tk.Listbox(right_frame, selectmode='extended', exportselection=False)
        self.monitored_listbox.pack(fill='both', expand=True)
        bottom_frame = ttkb.Frame(self, padding=10)
        bottom_frame.pack(side='bottom', fill='x')
        ttkb.Button(bottom_frame, text="Salvar Alterações", command=self.on_save, bootstyle="success").pack(side='left')
        ttkb.Button(bottom_frame, text="Cancelar", command=self.destroy, bootstyle="secondary").pack(side='left', padx=10)
        self._populate_lists()
        self.parent_app.center_toplevel_on_main(self)
            
    def _populate_lists(self):
        # CORREÇÃO AQUI: Acessar a lista de símbolos do monitoring_service que está na parent_app
        self.all_symbols_master = sorted([coin.get('symbol') for coin in self.parent_app.monitoring_service.all_cg_coins_list if coin.get('symbol')])
        monitored_symbols = {crypto['symbol'] for crypto in self.parent_app.config.get("cryptos_to_monitor", [])}
        self.available_listbox.delete(0, tk.END); self.monitored_listbox.delete(0, tk.END)
        for symbol in self.all_symbols_master:
            if symbol not in monitored_symbols: self.available_listbox.insert(tk.END, symbol)
        for symbol in sorted(list(monitored_symbols)): self.monitored_listbox.insert(tk.END, symbol)
        
    def _filter_available(self, *args):
        search_term = self.available_search_var.get().upper()
        self.available_listbox.delete(0, tk.END)
        monitored_symbols = set(self.monitored_listbox.get(0, tk.END))
        for symbol in self.all_symbols_master:
            if search_term in symbol.upper() and symbol not in monitored_symbols:
                self.available_listbox.insert(tk.END, symbol)
            
    def _filter_monitored(self, *args):
        search_term = self.monitored_search_var.get().upper()
        current_monitored = sorted([c['symbol'] for c in self.parent_app.config.get("cryptos_to_monitor", [])])
        self.monitored_listbox.delete(0, tk.END)
        for symbol in current_monitored:
            if search_term in symbol.upper(): self.monitored_listbox.insert(tk.END, symbol)
            
    def _add_symbols(self):
        selected_indices = self.available_listbox.curselection()
        if not selected_indices: return
        symbols_to_move = [self.available_listbox.get(i) for i in selected_indices]
        for i in sorted(selected_indices, reverse=True): self.available_listbox.delete(i)
        
        current_monitored = list(self.monitored_listbox.get(0, tk.END))
        for symbol in symbols_to_move:
            if symbol not in current_monitored: current_monitored.append(symbol)
        
        self.monitored_listbox.delete(0, tk.END)
        for symbol in sorted(current_monitored):
            self.monitored_listbox.insert(tk.END, symbol)

    def _remove_symbols(self):
        selected_indices = self.monitored_listbox.curselection()
        if not selected_indices: return
        symbols_to_move = [self.monitored_listbox.get(i) for i in selected_indices]
        for i in sorted(selected_indices, reverse=True): self.monitored_listbox.delete(i)
        
        current_available = list(self.available_listbox.get(0, tk.END))
        for symbol in symbols_to_move:
            if symbol not in current_available: current_available.append(symbol)
        
        self.available_listbox.delete(0, tk.END)
        for symbol in sorted(current_available):
            self.available_listbox.insert(tk.END, symbol)
        
    def on_save(self):
        new_monitored_symbols = set(self.monitored_listbox.get(0, tk.END))
        current_configs = {crypto['symbol']: crypto for crypto in self.parent_app.config.get("cryptos_to_monitor", [])}
        
        new_config_list = []
        for symbol in sorted(list(new_monitored_symbols)):
            if symbol in current_configs:
                new_config_list.append(current_configs[symbol])
            else:
                new_config_list.append({"symbol": symbol})

        self.parent_app.config["cryptos_to_monitor"] = new_config_list
        self.parent_app.save_config()
        messagebox.showinfo("Sucesso", "Lista de moedas atualizada.", parent=self)
        self.destroy()

class AlertHistoryWindow(ttkb.Toplevel):
    def __init__(self, parent_app):
        # CORREÇÃO AQUI: parent_app deve ser o master (janela principal), não parent_app.root
        super().__init__(parent_app)
        self.parent_app = parent_app
        self.title("Histórico de Alertas")
        self.geometry("1100x600")
        self.transient(self.master)
        self.grab_set()
        
        # Container principal com tema escuro
        main_container = ttkb.Frame(self, padding=15, bootstyle="dark")
        main_container.pack(expand=True, fill='both')
        
        # Cabeçalho com título
        header_frame = ttkb.Frame(main_container, bootstyle="dark")
        header_frame.pack(fill='x', pady=(0, 15))
        
        header_title = ttkb.Label(
            header_frame, 
            text="HISTÓRICO DE ALERTAS", 
            font=("Segoe UI", 16, "bold"),
            bootstyle="info"
        )
        header_title.pack(side="left")
        
        header_subtitle = ttkb.Label(
            header_frame, 
            text="Registro cronológico de todos os alertas disparados", 
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        header_subtitle.pack(side="left", padx=(15, 0))

        # Ferramentas de filtragem
        filter_frame = ttkb.Frame(main_container, bootstyle="dark")
        filter_frame.pack(fill='x', pady=(0, 15))
        
        # Campo de busca
        search_frame = ttkb.Frame(filter_frame, bootstyle="dark")
        search_frame.pack(side="left", fill='x', expand=True)
        
        search_icon = ttkb.Label(
            search_frame, 
            text="🔍", 
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        search_icon.pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = ttkb.Entry(
            search_frame, 
            textvariable=self.search_var,
            width=30,
            font=("Segoe UI", 10),
            bootstyle="dark",
            placeholder="Buscar por símbolo ou tipo de alerta..."
        )
        search_entry.pack(side="left", padx=(0, 15))
        
        # Filtros de período
        period_frame = ttkb.Frame(filter_frame, bootstyle="dark")
        period_frame.pack(side="right")
        
        ttkb.Label(
            period_frame,
            text="Período:",
            font=("Segoe UI", 10),
            bootstyle="light"
        ).pack(side="left", padx=(0, 5))
        
        self.period_var = tk.StringVar(value="all")
        period_combobox = ttkb.Combobox(
            period_frame,
            values=["Todos", "Hoje", "7 dias", "30 dias"],
            textvariable=self.period_var,
            width=10,
            bootstyle="dark"
        )
        period_combobox.pack(side="left", padx=(0, 10))
        period_combobox.current(0)
        
        # Container principal para a tabela de alertas
        tree_container = ttkb.Frame(main_container, bootstyle="dark")
        tree_container.pack(expand=True, fill='both', pady=(0, 15))
        
        # Tabela de histórico de alertas com visual moderno
        self.tree = ttkb.Treeview(
            tree_container, 
            columns=('timestamp', 'symbol', 'trigger'), 
            show='headings', 
            bootstyle="dark",
            height=15
        )
        
        # Configuração das colunas
        self.tree.heading('timestamp', text='Data/Hora')
        self.tree.column('timestamp', width=180, anchor='w')
        
        self.tree.heading('symbol', text='Símbolo')
        self.tree.column('symbol', width=120, anchor='w')
        
        self.tree.heading('trigger', text='Gatilho do Alerta')
        self.tree.column('trigger', width=450, anchor='w')
        
        # Barra de rolagem
        vsb = ttkb.Scrollbar(
            tree_container, 
            orient="vertical", 
            command=self.tree.yview, 
            bootstyle="round-dark"
        )
        self.tree.configure(yscrollcommand=vsb.set)
        
        # Posicionamento da tabela e barra de rolagem
        self.tree.pack(side='left', expand=True, fill='both')
        vsb.pack(side='right', fill='y')
        
        # Painel de detalhes (inicialmente vazio)
        self.details_frame = ttkb.LabelFrame(
            main_container, 
            text="Detalhes do Alerta", 
            padding=15,
            height=150,
            bootstyle="dark"
        )
        self.details_frame.pack(fill='x')
        
        # Força o frame de detalhes a manter uma altura mínima
        self.details_frame.pack_propagate(False)
        
        # Texto de placeholder para detalhes
        self.details_placeholder = ttkb.Label(
            self.details_frame,
            text="Selecione um alerta para ver os detalhes",
            font=("Segoe UI", 11),
            bootstyle="secondary"
        )
        self.details_placeholder.pack(pady=40)
        
        # Container para os botões de ação
        btn_frame = ttkb.Frame(main_container, bootstyle="dark", padding=(0, 15, 0, 0))
        btn_frame.pack(fill='x')
        
        # Botões de ação com ícones
        self.analyze_btn = ttkb.Button(
            btn_frame, 
            text="🔍 Análise Detalhada", 
            command=self._open_analysis, 
            bootstyle="info",
            padding=10,
            state="disabled"
        )
        self.analyze_btn.pack(side='left', padx=5)
        
        ttkb.Button(
            btn_frame, 
            text="🔄 Atualizar", 
            command=self._load_history,
            padding=10,
            bootstyle="secondary"
        ).pack(side='left', padx=5)
        
        ttkb.Button(
            btn_frame, 
            text="🗑️ Limpar Histórico", 
            command=self._clear_history, 
            padding=10,
            bootstyle="danger-outline"
        ).pack(side='left', padx=5)
        
        ttkb.Button(
            btn_frame, 
            text="✖️ Fechar", 
            command=self.destroy, 
            padding=10,
            bootstyle="secondary-outline"
        ).pack(side='right', padx=5)
        
        # Barra de status
        status_bar = ttkb.Frame(main_container, bootstyle="dark", padding=(0, 15, 0, 0))
        status_bar.pack(fill='x', side="bottom")
        
        self.status_label = ttkb.Label(
            status_bar, 
            text="", 
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        self.status_label.pack(side="left")

        # Vincula eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_selection)
        self.search_var.trace_add("write", self._filter_history)
        self.period_var.trace_add("write", self._filter_history)
        
        # Carrega o histórico
        self._load_history()
        
        # Centraliza a janela
        self.parent_app.center_toplevel_on_main(self)

    def _load_history(self):
        """Carrega o histórico de alertas do aplicativo"""
        # Limpa a tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtém os dados do histórico
        self.history_data = self.parent_app.alert_history
        
        # Formata a data/hora para exibição
        for i, record in enumerate(self.history_data):
            # Processa o timestamp para um formato legível
            timestamp = record.get('timestamp', 'N/A')
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                formatted_time = timestamp
                
            # Adiciona ícones baseados no tipo de gatilho
            symbol = record.get('symbol', 'N/A')
            trigger = record.get('trigger', 'N/A')
            
            # Adiciona ícones de acordo com o tipo de alerta
            trigger_icon = "⚠️"
            if 'preço' in trigger.lower():
                trigger_icon = "💲"
            elif 'rsi' in trigger.lower():
                trigger_icon = "📊"
            elif 'bollinger' in trigger.lower():
                trigger_icon = "📈"
            elif 'macd' in trigger.lower():
                trigger_icon = "📉"
            elif 'cruz' in trigger.lower():
                trigger_icon = "✖️"
            elif 'capital' in trigger.lower():
                trigger_icon = "💰"
                
            # Insere na tabela
            self.tree.insert(
                '', 
                tk.END, 
                iid=i, 
                values=(
                    formatted_time,
                    f"{symbol}",
                    f"{trigger_icon} {trigger}"
                ),
                tags=('alert',)
            )
            
        # Configura tags para colorir as linhas
        self.tree.tag_configure('alert', background="#1e1e2d")
            
        # Atualiza status
        count = len(self.history_data)
        self.status_label.config(text=f"{count} alertas encontrados")
        
        # Restaura o estado do botão de análise
        self._on_selection()

    def _filter_history(self, *args):
        """Filtra o histórico com base nos critérios selecionados"""
        # Limpa a tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Obtém os critérios de filtro
        search_term = self.search_var.get().lower()
        period = self.period_var.get()
        
        # Filtra por período
        from datetime import datetime, timedelta
        filtered_data = self.history_data
        
        if period == "Hoje":
            today = datetime.now().date()
            filtered_data = [
                record for record in self.history_data 
                if self._get_date_from_record(record) == today
            ]
        elif period == "7 dias":
            cutoff = (datetime.now() - timedelta(days=7)).date()
            filtered_data = [
                record for record in self.history_data 
                if self._get_date_from_record(record) >= cutoff
            ]
        elif period == "30 dias":
            cutoff = (datetime.now() - timedelta(days=30)).date()
            filtered_data = [
                record for record in self.history_data 
                if self._get_date_from_record(record) >= cutoff
            ]
            
        # Filtra por termo de busca
        if search_term:
            filtered_data = [
                record for record in filtered_data
                if (search_term in record.get('symbol', '').lower() or 
                    search_term in record.get('trigger', '').lower())
            ]
            
        # Preenche a tabela com os dados filtrados
        for i, record in enumerate(filtered_data):
            # Processa o timestamp para um formato legível
            timestamp = record.get('timestamp', 'N/A')
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                formatted_time = timestamp
                
            # Adiciona ícones baseados no tipo de gatilho
            symbol = record.get('symbol', 'N/A')
            trigger = record.get('trigger', 'N/A')
            
            # Adiciona ícones de acordo com o tipo de alerta
            trigger_icon = "⚠️"
            if 'preço' in trigger.lower():
                trigger_icon = "💲"
            elif 'rsi' in trigger.lower():
                trigger_icon = "📊"
            elif 'bollinger' in trigger.lower():
                trigger_icon = "📈"
            elif 'macd' in trigger.lower():
                trigger_icon = "📉"
            elif 'cruz' in trigger.lower():
                trigger_icon = "✖️"
            elif 'capital' in trigger.lower():
                trigger_icon = "💰"
                
            # Insere na tabela com o índice original para manter a referência
            self.tree.insert(
                '', 
                tk.END, 
                iid=self.history_data.index(record),  # Usa o índice original
                values=(
                    formatted_time,
                    f"{symbol}",
                    f"{trigger_icon} {trigger}"
                ),
                tags=('alert',)
            )
            
        # Atualiza status
        count = len(self.tree.get_children())
        self.status_label.config(text=f"{count} alertas encontrados")
            
    def _get_date_from_record(self, record):
        """Extrai a data de um registro de alerta"""
        try:
            from datetime import datetime
            timestamp = record.get('timestamp', '')
            dt = datetime.fromisoformat(timestamp)
            return dt.date()
        except:
            # Em caso de erro, retorna uma data muito antiga
            return datetime(1970, 1, 1).date()

    def _on_selection(self, event=None):
        """Trata o evento de seleção de um alerta na tabela"""
        selected_item = self.tree.selection()
        
        # Se nada estiver selecionado, desabilita o botão de análise
        if not selected_item:
            self.analyze_btn['state'] = 'disabled'
            # Mostra o placeholder
            self.details_placeholder.pack(pady=40)
            return
            
        # Habilita o botão de análise
        self.analyze_btn['state'] = 'normal'
        
        # Mostra detalhes resumidos do alerta selecionado
        item_index = int(selected_item[0])
        record = self.history_data[item_index]
        
        # Limpa o frame de detalhes
        for widget in self.details_frame.winfo_children():
            widget.destroy()
            
        # Cria layout de duas colunas para os detalhes
        details_content = ttkb.Frame(self.details_frame, bootstyle="dark")
        details_content.pack(fill="both", expand=True)
        
        left_col = ttkb.Frame(details_content, bootstyle="dark")
        right_col = ttkb.Frame(details_content, bootstyle="dark")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right_col.pack(side="left", fill="both", expand=True)
        
        # Extrai informações básicas
        symbol = record.get('symbol', 'N/A')
        trigger = record.get('trigger', 'N/A')
        timestamp = record.get('timestamp', 'N/A')
        
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%d/%m/%Y %H:%M:%S")
        except:
            formatted_time = timestamp
            
        # Informações na coluna da esquerda
        ttkb.Label(
            left_col, 
            text="Símbolo:", 
            font=("Segoe UI", 10, "bold"),
            bootstyle="secondary"
        ).grid(row=0, column=0, sticky="w", pady=3)
        
        ttkb.Label(
            left_col, 
            text=symbol, 
            font=("Segoe UI", 10, "bold"),
            bootstyle="info"
        ).grid(row=0, column=1, sticky="w", pady=3, padx=5)
        
        ttkb.Label(
            left_col, 
            text="Gatilho:", 
            font=("Segoe UI", 10, "bold"),
            bootstyle="secondary"
        ).grid(row=1, column=0, sticky="w", pady=3)
        
        ttkb.Label(
            left_col, 
            text=trigger, 
            font=("Segoe UI", 10),
            bootstyle="light"
        ).grid(row=1, column=1, sticky="w", pady=3, padx=5)
        
        # Informações na coluna da direita
        ttkb.Label(
            right_col, 
            text="Data/Hora:", 
            font=("Segoe UI", 10, "bold"),
            bootstyle="secondary"
        ).grid(row=0, column=0, sticky="w", pady=3)
        
        ttkb.Label(
            right_col, 
            text=formatted_time, 
            font=("Segoe UI", 10),
            bootstyle="light"
        ).grid(row=0, column=1, sticky="w", pady=3, padx=5)
        
        # Verificar se há dados de análise
        has_data = 'data' in record and record['data']
        data_status = "Disponíveis" if has_data else "Não disponíveis"
        data_style = "success" if has_data else "danger"
        
        ttkb.Label(
            right_col, 
            text="Dados de análise:", 
            font=("Segoe UI", 10, "bold"),
            bootstyle="secondary"
        ).grid(row=1, column=0, sticky="w", pady=3)
        
        ttkb.Label(
            right_col, 
            text=data_status, 
            font=("Segoe UI", 10),
            bootstyle=data_style
        ).grid(row=1, column=1, sticky="w", pady=3, padx=5)
        
        # Configura as colunas para crescimento proporcional
        left_col.columnconfigure(1, weight=1)
        right_col.columnconfigure(1, weight=1)

    def _open_analysis(self):
        """Abre uma janela com análise detalhada do alerta selecionado"""
        selected_item = self.tree.selection()
        if not selected_item: 
            return
        
        # Obtém os dados do alerta selecionado
        item_index = int(selected_item[0])
        record = self.history_data[item_index]
        
        # Verifica se há dados de análise disponíveis
        if 'data' in record and record['data']:
            # Abre a janela de análise com design moderno
            AlertAnalysisWindow(self, record['data'])
        else:
            # Exibe mensagem se não houver dados detalhados
            messagebox.showinfo(
                "Sem Dados", 
                "Não há dados de análise detalhada para este alerta.", 
                parent=self
            )

    def _clear_history(self):
        """Limpa o histórico de alertas após confirmação"""
        # Pede confirmação ao usuário
        if messagebox.askyesno(
            "Confirmar", 
            "Tem certeza que deseja apagar todo o histórico de alertas?\n\nEsta ação não pode ser desfeita.",
            parent=self
        ):
            # Limpa o histórico
            self.parent_app.alert_history.clear()
            self.parent_app.save_alert_history()
            
            # Recarrega a visualização
            self._load_history()
            
            # Notifica o usuário
            self.status_label.config(text="Histórico de alertas apagado")
            
            # Limpa o painel de detalhes
            for widget in self.details_frame.winfo_children():
                widget.destroy()
                
            # Restaura o placeholder
            self.details_placeholder = ttkb.Label(
                self.details_frame,
                text="Histórico de alertas vazio",
                font=("Segoe UI", 11),
                bootstyle="secondary"
            )
            self.details_placeholder.pack(pady=40)

class AlertAnalysisWindow(ttkb.Toplevel):
    def __init__(self, parent, analysis_data):
        super().__init__(parent)
        
        # Configura a janela
        symbol = analysis_data.get('symbol', 'N/A')
        self.title(f"Análise Detalhada - {symbol}")
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()
        
        # Container principal com tema escuro
        main_container = ttkb.Frame(self, bootstyle="dark", padding=20)
        main_container.pack(expand=True, fill='both')
        
        # Cabeçalho com símbolo da moeda
        header_frame = ttkb.Frame(main_container, bootstyle="dark")
        header_frame.pack(fill='x', pady=(0, 20))
        
        header_title = ttkb.Label(
            header_frame, 
            text=f"Análise Detalhada: {symbol}", 
            font=("Segoe UI", 16, "bold"),
            bootstyle="info"
        )
        header_title.pack(side="left")
        
        # Extrai os dados para análise
        data = analysis_data
        
        # Painel de preço e variação em destaque
        price_panel = ttkb.Frame(main_container, bootstyle="dark")
        price_panel.pack(fill='x', pady=(0, 20))
        
        # Preço atual
        price_value = data.get('current_price', 0.0)
        price_text = f"${price_value:,.4f}" if price_value is not None else "N/A"
        
        price_change = data.get('price_change_24h', 0.0)
        price_change_text = f"{price_change:.2f}%" if price_change is not None else "N/A"
        
        price_change_color = "success" if price_change is not None and price_change >= 0 else "danger"
        price_change_icon = "▲" if price_change is not None and price_change >= 0 else "▼"
        
        # Frame para preço
        price_frame = ttkb.LabelFrame(
            price_panel, 
            text="Preço no Alerta", 
            bootstyle="dark",
            padding=10
        )
        price_frame.pack(side="left", fill='y', expand=True, padx=(0, 10))
        
        price_label = ttkb.Label(
            price_frame,
            text=price_text,
            font=("Segoe UI", 22, "bold"),
            bootstyle="light"
        )
        price_label.pack(pady=5)
        
        # Frame para variação
        change_frame = ttkb.LabelFrame(
            price_panel, 
            text="Variação 24h", 
            bootstyle="dark",
            padding=10
        )
        change_frame.pack(side="left", fill='y', expand=True, padx=10)
        
        change_label = ttkb.Label(
            change_frame,
            text=f"{price_change_icon} {price_change_text}",
            font=("Segoe UI", 22, "bold"),
            bootstyle=price_change_color
        )
        change_label.pack(pady=5)
        
        # Frame para volume
        volume_value = data.get('volume_24h', 0.0)
        if volume_value is not None:
            if volume_value >= 1_000_000_000:
                volume_text = f"${volume_value/1_000_000_000:.2f}B"
            elif volume_value >= 1_000_000:
                volume_text = f"${volume_value/1_000_000:.2f}M"
            else:
                volume_text = f"${volume_value/1_000:.2f}K"
        else:
            volume_text = "N/A"
        
        volume_frame = ttkb.LabelFrame(
            price_panel, 
            text="Volume 24h", 
            bootstyle="dark",
            padding=10
        )
        volume_frame.pack(side="left", fill='y', expand=True, padx=(10, 0))
        
        volume_label = ttkb.Label(
            volume_frame,
            text=volume_text,
            font=("Segoe UI", 22, "bold"),
            bootstyle="secondary"
        )
        volume_label.pack(pady=5)
        
        # Separador
        ttkb.Separator(main_container, bootstyle="info").pack(fill='x', pady=10)
        
        # Painel de indicadores técnicos
        indicators_title = ttkb.Label(
            main_container,
            text="Indicadores Técnicos",
            font=("Segoe UI", 14, "bold"),
            bootstyle="light"
        )
        indicators_title.pack(anchor="w", pady=(10, 15))
        
        # Grid para indicadores técnicos
        indicators_grid = ttkb.Frame(main_container, bootstyle="dark")
        indicators_grid.pack(fill='both', expand=True)
        
        # Definição dos indicadores com cores e ícones
        indicators = {
            "rsi_value": {
                "label": "RSI",
                "icon": "📊",
                "format": lambda v: f"{v:.2f}" if v is not None else "N/A",
                "color": lambda v: "success" if v is not None and v <= 30 else (
                    "danger" if v is not None and v >= 70 else "light"
                )
            },
            "bollinger_signal": {
                "label": "Bollinger",
                "icon": "📈",
                "format": lambda v: str(v) if v is not None else "N/A",
                "color": lambda v: "light"
            },
            "macd_signal": {
                "label": "MACD",
                "icon": "📉",
                "format": lambda v: str(v) if v is not None else "N/A",
                "color": lambda v: "success" if v == "Cruzamento de Alta" else (
                    "danger" if v == "Cruzamento de Baixa" else "light"
                )
            },
            "mme_cross": {
                "label": "MME",
                "icon": "✖️",
                "format": lambda v: str(v) if v is not None else "N/A",
                "color": lambda v: "success" if v == "Cruz Dourada" else (
                    "danger" if v == "Cruz da Morte" else "light"
                )
            }
        }
        
        # Cria cards para cada indicador
        col = 0
        row = 0
        for key, details in indicators.items():
            value = data.get(key)
            formatted_value = details["format"](value)
            color = details["color"](value)
            
            # Card para o indicador
            indicator_card = ttkb.LabelFrame(
                indicators_grid,
                text=f"{details['icon']} {details['label']}",
                bootstyle="dark",
                padding=10
            )
            indicator_card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Valor do indicador
            ttkb.Label(
                indicator_card,
                text=formatted_value,
                font=("Segoe UI", 14, "bold"),
                bootstyle=color
            ).pack(pady=5)
            
            # Avança para próxima posição na grid
            col += 1
            if col > 1:  # 2 colunas
                col = 0
                row += 1
                
        # Configura o grid para expansão
        indicators_grid.columnconfigure(0, weight=1)
        indicators_grid.columnconfigure(1, weight=1)
        
        # Notas adicionais ou conclusão
        notes_frame = ttkb.LabelFrame(
            main_container,
            text="Conclusão da Análise",
            bootstyle="dark",
            padding=15
        )
        notes_frame.pack(fill='x', pady=(15, 0))
        
        # Determina o tipo de alerta
        trigger_text = "Alerta gerado com base nos critérios configurados."
        
        if value and key == "rsi_value" and value <= 30:
            trigger_text = f"RSI em condição de sobrevendido ({value:.2f}). Potencial ponto de reversão de baixa."
        elif value and key == "rsi_value" and value >= 70:
            trigger_text = f"RSI em condição de sobrecomprado ({value:.2f}). Potencial ponto de reversão de alta."
        elif data.get("macd_signal") == "Cruzamento de Alta":
            trigger_text = "Cruzamento de alta no MACD. Possível tendência de alta."
        elif data.get("macd_signal") == "Cruzamento de Baixa":
            trigger_text = "Cruzamento de baixa no MACD. Possível tendência de baixa."
        elif data.get("bollinger_signal") == "Acima da Banda Superior":
            trigger_text = "Preço acima da Banda Superior de Bollinger. Possível sobrecompra."
        elif data.get("bollinger_signal") == "Abaixo da Banda Inferior":
            trigger_text = "Preço abaixo da Banda Inferior de Bollinger. Possível sobrevenda."
        elif data.get("mme_cross") == "Cruz Dourada":
            trigger_text = "Cruzamento de Cruz Dourada (MME 50 cruzou acima da MME 200). Sinal de tendência de alta."
        elif data.get("mme_cross") == "Cruz da Morte":
            trigger_text = "Cruzamento de Cruz da Morte (MME 50 cruzou abaixo da MME 200). Sinal de tendência de baixa."
        
        ttkb.Label(
            notes_frame,
            text=trigger_text,
            font=("Segoe UI", 11),
            bootstyle="light",
            wraplength=620
        ).pack(pady=10, fill='x')
        
        # Botão para fechar a janela
        close_button = ttkb.Button(
            main_container, 
            text="✖️ Fechar", 
            command=self.destroy, 
            bootstyle="secondary",
            padding=10
        )
        close_button.pack(side="right", pady=(15, 0))