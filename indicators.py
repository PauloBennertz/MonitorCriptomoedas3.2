# indicators.py
import pandas as pd

def calculate_rsi(df, period=14):
    if df is None or df.empty or len(df) < period + 1: return 0, 0, 0
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    avg_gain, avg_loss = gain.iloc[-1], loss.iloc[-1]
    if pd.isna(avg_loss) or avg_loss == 0: return 100, avg_gain if not pd.isna(avg_gain) else 0, 0
    if pd.isna(avg_gain): return 0, 0, avg_loss
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs)), avg_gain, avg_loss

def calculate_bollinger_bands(df, period=20, std_dev=2):
    if df is None or df.empty or len(df) < period: return 0, 0, 0, 0
    sma = df['close'].rolling(window=period).mean().iloc[-1]
    std = df['close'].rolling(window=period).std().iloc[-1]
    if pd.isna(sma) or pd.isna(std): return 0, 0, sma, std
    return sma + (std * std_dev), sma - (std * std_dev), sma, std

def calculate_macd(df, fast=12, slow=26, signal=9):
    if df is None or len(df) < slow + signal: return "N/A"
    exp1, exp2 = df['close'].ewm(span=fast, adjust=False).mean(), df['close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    if len(macd) < 2 or len(signal_line) < 2: return "Nenhum"
    if macd.iloc[-2] < signal_line.iloc[-2] and macd.iloc[-1] > signal_line.iloc[-1]: return "Cruzamento de Alta"
    if macd.iloc[-2] > signal_line.iloc[-2] and macd.iloc[-1] < signal_line.iloc[-1]: return "Cruzamento de Baixa"
    return "Nenhum"

def calculate_emas(df, periods=[50, 200]):
    emas = {}
    if df is None or df.empty: return emas
    for period in periods:
        if len(df) >= period: emas[period] = df['close'].ewm(span=period, adjust=False).mean()
    return emas