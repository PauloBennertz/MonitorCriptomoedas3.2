# help_window.py
import tkinter as tk
import ttkbootstrap as ttkb
from tkinter import scrolledtext

ALERT_SUMMARIES = {
    # RSI
    'RSI_SOBRECOMPRA': "RSI > 70: Ativo pode estar supervalorizado, risco de correção.",
    'RSI_SOBREVENDA': "RSI < 30: Ativo pode estar desvalorizado, potencial de alta.",
    # Bandas de Bollinger
    'PRECO_ACIMA_BANDA_SUPERIOR': "Preço acima da Banda de Bollinger Superior: Alta volatilidade, possível sobrecompra.",
    'PRECO_ABAIXO_BANDA_INFERIOR': "Preço abaixo da Banda de Bollinger Inferior: Alta volatilidade, possível sobrevenda.",
    # MACD
    'CRUZAMENTO_MACD_ALTA': "MACD cruzou para cima da linha de sinal: Sinal de momentum de alta.",
    'CRUZAMENTO_MACD_BAIXA': "MACD cruzou para baixo da linha de sinal: Sinal de momentum de baixa.",
    # Médias Móveis
    'CRUZ_DOURADA': "MME 50 cruzou acima da MME 200: Forte sinal de tendência de alta.",
    'CRUZ_DA_MORTE': "MME 50 cruzou abaixo da MME 200: Forte sinal de tendência de baixa.",
    # Padrão de Volume
    'VOLUME_ANORMAL': "Volume de negociação significativamente acima da média. Indica forte interesse ou evento.",
    # Padrão de Velas (Exemplo)
    'MARTELO_ALTA': "Padrão de vela 'Martelo': Pode indicar uma reversão de baixa para alta.",
    'ESTRELA_CADENTE_BAIXA': "Padrão de vela 'Estrela Cadente': Pode indicar uma reversão de alta para baixa."
}

class HelpWindow(ttkb.Toplevel):
    def __init__(self, parent_app):
        # CORREÇÃO AQUI: parent_app já é a instância da MainApplication, que é o root
        super().__init__(parent_app) 
        self.parent_app = parent_app
        self.title("Guia de Indicadores")
        self.geometry("700x500")
        self.transient(self.master)
        self.grab_set()

        self.setup_ui()
        self.parent_app.center_toplevel_on_main(self)

    def setup_ui(self):
        main_frame = ttkb.Frame(self, padding=15)
        main_frame.pack(expand=True, fill='both')

        text_content = """
        Guia Básico de Indicadores de Análise Técnica
        
        Este guia fornece uma breve explicação dos indicadores usados nesta aplicação.
        
        ----------------------------------------------------------------------
        1. RSI (Relative Strength Index - Índice de Força Relativa)
        ----------------------------------------------------------------------
        
        O RSI é um oscilador de momentum que mede a magnitude das recentes variações de preço para avaliar condições de sobrecompra ou sobrevenda.
        
        -   **Sobrecomprado (normalmente > 70):** Sugere que o ativo pode estar supervalorizado e pode haver uma reversão de baixa.
        -   **Sobrevendido (normalmente < 30):** Sugere que o ativo pode estar desvalorizado e pode haver uma reversão de alta.
        
        ----------------------------------------------------------------------
        2. Bandas de Bollinger (Bollinger Bands)
        ----------------------------------------------------------------------
        
        As Bandas de Bollinger são um indicador de volatilidade. Consistem em uma Média Móvel Simples (SMA) central e duas bandas que desviam por um número de desvios padrão da SMA.
        
        -   **Preço Abaixo da Banda Inferior:** O preço está relativamente baixo, indicando uma possível condição de sobrevenda ou que o movimento de queda pode ser exagerado.
        -   **Preço Acima da Banda Superior:** O preço está relativamente alto, indicando uma possível condição de sobrecompra ou que o movimento de alta pode ser exagerado.
        -   **Bandas Apertadas:** Sugerem baixa volatilidade, possivelmente antes de um grande movimento.
        -   **Bandas Abertas:** Indicam alta volatilidade.
        
        ----------------------------------------------------------------------
        3. MACD (Moving Average Convergence Divergence - Média Móvel Convergência Divergência)
        ----------------------------------------------------------------------
        
        O MACD é um indicador de momentum que mostra a relação entre duas médias móveis do preço de um ativo.
        
        -   **Linha MACD (azul):** Diferença entre a EMA de 12 períodos e a EMA de 26 períodos.
        -   **Linha de Sinal (vermelha):** EMA de 9 períodos da linha MACD.
        -   **Cruzamento de Alta (MACD cruza acima da Linha de Sinal):** Sinal de alta, indicando que o momentum de alta está crescendo.
        -   **Cruzamento de Baixa (MACD cruza abaixo da Linha de Sinal):** Sinal de baixa, indicando que o momentum de baixa está crescendo.
        
        ----------------------------------------------------------------------
        4. MMEs (Médias Móveis Exponenciais - Exponential Moving Averages)
        ----------------------------------------------------------------------
        
        As MMEs dão mais peso aos preços recentes, tornando-as mais responsivas às novas informações do que as SMAs.
        
        -   **MME 50:** Média de curto/médio prazo.
        -   **MME 200:** Média de longo prazo.
        -   **Cruz Dourada (Golden Cross - MME 50 cruza acima da MME 200):** Sinal de alta significativo, sugerindo que uma tendência de alta de longo prazo pode estar começando.
        -   **Cruz da Morte (Death Cross - MME 50 cruza abaixo da MME 200):** Sinal de baixa significativo, sugerindo que uma tendência de baixa de longo prazo pode estar começando.
        
        Lembre-se: Nenhum indicador é 100% preciso. Use-os em conjunto para confirmar sinais e como parte de uma estratégia de negociação mais ampla.
        """
        
        text_widget = scrolledtext.ScrolledText(main_frame, wrap='word', font=("Segoe UI", 10),
                                               bg="#2a2a2a", fg="white", insertbackground="white",
                                               state='disabled', relief='flat', padx=10, pady=10)
        text_widget.pack(expand=True, fill='both')

        text_widget.config(state='normal')
        text_widget.insert(tk.END, text_content)
        text_widget.config(state='disabled')