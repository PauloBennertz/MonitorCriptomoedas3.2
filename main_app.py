import sys
import os
import json
import threading
import queue
import logging
import time
import webbrowser
from urllib.parse import quote
from datetime import datetime

# Importações do PyQt6
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QGridLayout, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont

# --- Importações do seu projeto original ---
# (Assumindo que esses arquivos estão no mesmo diretório ou no python path)
# (Alguns podem precisar de pequenas adaptações, mas a lógica principal é mantida)
from notification_service import send_telegram_alert, AlertConsolidator
import robust_services
from monitoring_service import (
    run_monitoring_cycle,
    get_coingecko_global_mapping,
    fetch_all_binance_symbols_startup,
    get_btc_dominance
)
from core_components import get_application_path
from coin_manager import CoinManager
# As janelas secundárias (AlertHistoryWindow, etc.) precisarão ser reescritas em PyQt6.
# Por enquanto, seus chamadores serão comentados.

# --- Funções de Configuração e Utilitários (do seu código original) ---
def get_app_version():
    """Lê a versão de um arquivo version.txt, com fallback."""
    try:
        version_path = os.path.join(get_application_path(), 'version.txt')
        with open(version_path, 'r') as f:
            version = f.read().strip()
            return version if version else "3.2-PyQt"
    except Exception:
        return "3.2-PyQt"

APP_VERSION = get_app_version()

def get_current_config():
    """Carrega a configuração do aplicativo a partir do arquivo config.json."""
    config_path = os.path.join(get_application_path(), "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cryptos_to_monitor": [], "telegram_bot_token": "", "telegram_chat_id": "", "check_interval_seconds": 300}

# --- Lógica de Backend em uma Classe Worker (Padrão PyQt) ---
class WorkerSignals(QObject):
    '''
    Define os sinais disponíveis para a thread de trabalho.
    '''
    data_updated = pyqtSignal(dict)  # Sinal para enviar dados de uma moeda
    alert = pyqtSignal(dict)         # Sinal para enviar um alerta
    countdown = pyqtSignal(int)      # Sinal para o contador

class MonitoringWorker(QObject):
    """
    Executa o ciclo de monitoramento em uma thread separada.
    """
    def __init__(self, config, coingecko_mapping):
        super().__init__()
        self.config = config
        self.coingecko_mapping = coingecko_mapping
        self.signals = WorkerSignals()
        self.data_queue = queue.Queue()
        self.stop_event = threading.Event()

    def run(self):
        """Inicia o monitoramento."""
        # A função run_monitoring_cycle precisa ser adaptada para usar os sinais
        # em vez de uma queue para a UI. Por simplicidade, vamos simular isso.
        
        # O ideal é modificar run_monitoring_cycle para aceitar um objeto de 'sinais'
        # e chamar self.signals.data_updated.emit(payload) em vez de data_queue.put().
        
        # Exemplo de adaptação:
        logging.info("Serviço de monitoramento em background iniciado.")
        while not self.stop_event.is_set():
            # Aqui entraria a lógica de run_monitoring_cycle
            # Simulando a recepção de dados:
            monitored_symbols = [c['symbol'] for c in self.config.get('cryptos_to_monitor', [])]
            for symbol in monitored_symbols:
                # Simulação de dados recebidos
                mock_data = {
                    'symbol': symbol,
                    'current_price': 50000.0 * (1 + (time.time() % 10 - 5) / 100),
                    'price_change_24h': (time.time() % 10 - 5),
                    'volume_24h': 1000000000,
                    'rsi_value': 50 + (time.time() % 40 - 20)
                }
                self.signals.data_updated.emit(mock_data)
                time.sleep(0.1) # Simula o tempo entre buscas

            interval = self.config.get('check_interval_seconds', 300)
            self.signals.countdown.emit(interval)
            
            for i in range(interval):
                if self.stop_event.is_set(): break
                time.sleep(1)

    def stop(self):
        self.stop_event.set()

# --- Widgets Customizados da UI ---
class CryptoCardWidget(QFrame):
    """
    Um widget para exibir as informações de uma única criptomoeda.
    Substitui a classe CryptoCard do tkinter.
    """
    def __init__(self, symbol, coin_name):
        super().__init__()
        self.symbol = symbol
        self.previous_price = 0.0

        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyleSheet("""
            QFrame {
                background-color: #303841;
                border: 1px solid #444;
                border-radius: 8px;
            }
            QLabel {
                color: #e0e8f0;
                background-color: transparent;
                border: none;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(8)

        # Header do Card
        header_layout = QHBoxLayout()
        self.name_label = QLabel(f"{coin_name} ({symbol.replace('USDT', '')})")
        self.name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.name_label)
        self.layout.addLayout(header_layout)

        # Dados
        self.data_labels = {}
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        # Adiciona os campos de dados
        fields = {
            "current_price": "Preço Atual:",
            "price_change_24h": "Variação 24h:",
            "volume_24h": "Volume 24h:",
            "rsi_value": "RSI (14):"
        }
        
        row = 0
        for key, text in fields.items():
            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 10))
            value = QLabel("Carregando...")
            value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(value, row, 1)
            self.data_labels[key] = value
            row += 1
            
        self.layout.addLayout(grid_layout)

    def update_data(self, data):
        """Atualiza os labels com os novos dados recebidos."""
        new_price = data.get('current_price', 0.0)

        # Lógica de cor para o preço
        if self.previous_price != 0:
            if new_price > self.previous_price:
                self.data_labels['current_price'].setStyleSheet("color: #28a745;") # Verde
            elif new_price < self.previous_price:
                self.data_labels['current_price'].setStyleSheet("color: #dc3545;") # Vermelho
        
        self.previous_price = new_price

        # Atualiza os textos
        for key, label in self.data_labels.items():
            value = data.get(key, 'N/A')
            text = 'N/A'
            if isinstance(value, (int, float)):
                if key == 'current_price':
                    text = f"${value:,.2f}"
                elif key == 'price_change_24h':
                    text = f"{'▲' if value >= 0 else '▼'} {abs(value):.2f}%"
                    label.setStyleSheet("color: #28a745;" if value >= 0 else "color: #dc3545;")
                elif key == 'volume_24h':
                    text = f"${value/1_000_000_000:.2f}B"
                elif key == 'rsi_value':
                    text = f"{value:.1f}"
                    if value <= 30: label.setStyleSheet("color: #28a745;")
                    elif value >= 70: label.setStyleSheet("color: #dc3545;")
                    else: label.setStyleSheet("color: #e0e8f0;")
                else:
                    text = f"{value:.2f}"
            
            label.setText(text)

# --- Janela Principal da Aplicação ---
class CryptoAppPyQt(QMainWindow):
    def __init__(self, config, all_symbols, coin_manager, coingecko_mapping):
        super().__init__()
        self.config = config
        self.all_symbols = all_symbols
        self.coin_manager = coin_manager
        self.coingecko_mapping = coingecko_mapping
        
        self.coin_cards = {}
        
        self.setWindowTitle("Crypto Monitor Pro - PyQt Edition")
        self.setGeometry(100, 100, 1280, 800)
        self.setStyleSheet("background-color: #22282f;")

        self.initUI()
        self.start_monitoring_thread()

    def initUI(self):
        """Constrói a interface gráfica com widgets do PyQt6."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Topo: Botões de Controle ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(10, 10, 10, 10)
        top_bar_layout.setSpacing(15)

        self.config_button = QPushButton("⚙️ Gerenciar Alertas")
        self.alerts_button = QPushButton("🔔 Histórico de Alertas")
        self.help_button = QPushButton("❓ Ajuda")

        for button in [self.config_button, self.alerts_button, self.help_button]:
            button.setMinimumHeight(35)
            button.setFont(QFont("Segoe UI", 10))
            button.setStyleSheet("""
                QPushButton { color: #e0e8f0; background-color: #303841; border: 1px solid #444; border-radius: 5px; padding: 5px; }
                QPushButton:hover { background-color: #404851; }
            """)
            top_bar_layout.addWidget(button)
        top_bar_layout.addStretch() # Empurra os botões para a esquerda
        
        main_layout.addLayout(top_bar_layout)
        
        # --- Área Central: Cards de Criptomoedas ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        self.cards_layout = QGridLayout(content_widget)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # --- Base: Tabela de Histórico/Log ---
        self.history_table = QTableWidget()
        self.history_table.setRowCount(10)
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Timestamp", "Símbolo", "Evento"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setMaximumHeight(200)
        self.history_table.setStyleSheet("""
            QTableWidget { color: #e8cece; background-color: #303841; border: 1px solid #444; gridline-color: #444; }
            QHeaderView::section { background-color: #404851; color: #e0e8f0; border: 1px solid #444; padding: 4px; }
        """)
        main_layout.addWidget(self.history_table)

        self.update_coin_cards_display()
        
    def update_coin_cards_display(self):
        """Cria e posiciona os cards na grade."""
        # Limpa o layout antigo
        for i in reversed(range(self.cards_layout.count())): 
            self.cards_layout.itemAt(i).widget().setParent(None)
        
        monitored_symbols = [c['symbol'] for c in self.config.get('cryptos_to_monitor', [])]
        self.coin_cards = {}
        
        num_columns = 4 # Ajuste conforme necessário

        for i, symbol in enumerate(monitored_symbols):
            base_asset = symbol.replace('USDT', '').upper()
            coin_name = self.coingecko_mapping.get(base_asset, base_asset) 
            
            card = CryptoCardWidget(symbol, coin_name)
            self.coin_cards[symbol] = card
            
            row, col = divmod(i, num_columns)
            self.cards_layout.addWidget(card, row, col)

    def start_monitoring_thread(self):
        """Cria e inicia a thread para o worker de monitoramento."""
        self.monitoring_thread = QThread()
        self.worker = MonitoringWorker(self.config, self.coingecko_mapping)
        self.worker.moveToThread(self.monitoring_thread)

        # Conectar sinais e slots
        self.monitoring_thread.started.connect(self.worker.run)
        self.worker.signals.data_updated.connect(self.update_card_data)
        # self.worker.signals.alert.connect(self.handle_alert) -> Implementar
        # self.worker.signals.countdown.connect(self.update_countdown) -> Implementar

        self.monitoring_thread.start()
        logging.info("Thread de monitoramento iniciada.")

    def update_card_data(self, data):
        """Slot para receber dados da thread e atualizar o card correspondente."""
        symbol = data.get('symbol')
        card = self.coin_cards.get(symbol)
        if card:
            card.update_data(data)

    def closeEvent(self, event):
        """Função chamada ao fechar a janela."""
        reply = QMessageBox.question(self, 'Sair', 'Deseja realmente fechar o programa?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            logging.info("Fechando a aplicação...")
            self.worker.stop()
            self.monitoring_thread.quit()
            self.monitoring_thread.wait()
            event.accept()
        else:
            event.ignore()

def main():
    """Função principal que inicializa a aplicação PyQt6."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    app = QApplication(sys.argv)
    
    # Carregar configurações e dados iniciais (pode-se adicionar uma tela de splash aqui)
    config = get_current_config()
    all_symbols = fetch_all_binance_symbols_startup(config)
    mapping = get_coingecko_global_mapping()
    coin_manager = CoinManager()

    if not config.get("cryptos_to_monitor"):
        QMessageBox.warning(None, "Configuração Incompleta", "Nenhuma moeda está sendo monitorada. Por favor, adicione moedas através do gerenciador de alertas.")
        # Aqui você poderia abrir a janela de configuração primeiro
        
    main_window = CryptoAppPyQt(config, all_symbols, coin_manager, mapping)
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()