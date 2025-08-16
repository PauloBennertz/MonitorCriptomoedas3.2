import requests
import pandas as pd
import time
import logging
import copy
import robust_services
from indicators import calculate_rsi, calculate_bollinger_bands, calculate_macd, calculate_emas
from notification_service import send_telegram_alert
from pycoingecko import CoinGeckoAPI

cg_client = CoinGeckoAPI()

def get_klines_data(symbol, interval='1h', limit=300):
    """Busca dados de k-lines da Binance com cache, rate limiting e validação."""
    if not robust_services.DataValidator.validate_symbol(symbol):
        logging.warning(f"Tentativa de busca por símbolo inválido: {symbol}")
        return None
    
    cache_args = {'func': 'get_klines_data', 'symbol': symbol, 'interval': interval, 'limit': limit}
    cached_df = robust_services.data_cache.get(cache_args, ttl=180)
    if cached_df is not None:
        return cached_df
    
    robust_services.rate_limiter.wait_if_needed()
    url = "https://api.binance.com/api/v3/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        df = pd.DataFrame(response.json(), columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['close'] = df['close'].apply(robust_services.DataValidator.safe_price)
        df['high'] = df['high'].apply(robust_services.DataValidator.safe_price)
        df['low'] = df['low'].apply(robust_services.DataValidator.safe_price)
        robust_services.data_cache.set(cache_args, df)
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de rede ao buscar klines para {symbol}: {e}")
        return None

def get_ticker_data():
    """Busca os dados de ticker de 24h para todas as moedas, com cache."""
    cache_args = {'func': 'get_ticker_data'}
    cached_data = robust_services.data_cache.get(cache_args, ttl=60)
    if cached_data is not None: return cached_data
        
    robust_services.rate_limiter.wait_if_needed()
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=10)
        response.raise_for_status()
        ticker_data = {item['symbol']: item for item in response.json()}
        robust_services.data_cache.set(cache_args, ticker_data)
        return ticker_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar dados de 24h (ticker): {e}")
        return {}

def get_market_caps_coingecko(symbols_to_monitor, coingecko_mapping):
    """Busca o valor de mercado (market cap) para uma lista de moedas via CoinGecko."""
    market_caps = {}
    coin_ids_to_fetch = []
    symbol_to_coin_id = {}

    all_coins = cg_client.get_coins_list()

    for binance_symbol in symbols_to_monitor:
        base_asset = binance_symbol.replace('USDT', '').upper()
        coingecko_name = coingecko_mapping.get(base_asset)
        if coingecko_name:
            coin_id = next((item['id'] for item in all_coins if item['name'].lower() == coingecko_name.lower()), None)
            if coin_id:
                coin_ids_to_fetch.append(coin_id)
                symbol_to_coin_id[coin_id] = binance_symbol

    if not coin_ids_to_fetch: return {}

    cache_key = {'func': 'get_market_caps_coingecko', 'ids': tuple(sorted(coin_ids_to_fetch))}
    cached_data = robust_services.data_cache.get(cache_key, ttl=300)
    if cached_data is not None: return cached_data

    try:
        robust_services.rate_limiter.wait_if_needed()
        response = cg_client.get_coins_markets(vs_currency='usd', ids=','.join(coin_ids_to_fetch))
        for coin_data in response:
            original_binance_symbol = symbol_to_coin_id.get(coin_data['id'])
            if original_binance_symbol:
                market_caps[original_binance_symbol] = coin_data.get('market_cap')
        robust_services.data_cache.set(cache_key, market_caps)
        return market_caps
    except Exception as e:
        logging.error(f"Erro ao buscar market caps da CoinGecko: {e}")
        return {}

def get_coingecko_global_mapping():
    """Busca a lista de moedas da CoinGecko para mapear Símbolo -> Nome."""
    logging.info("Buscando mapeamento de nomes da CoinGecko...")
    robust_services.rate_limiter.wait_if_needed()
    try:
        coins_list = cg_client.get_coins_list()
        mapping = {coin['symbol'].upper(): coin['name'] for coin in coins_list}
        logging.info("Mapeamento de nomes CoinGecko carregado.")
        return mapping
    except Exception as e:
        logging.error(f"Não foi possível buscar mapeamento da CoinGecko: {e}")
        return {}

def fetch_all_binance_symbols_startup(existing_config):
    """Busca todos os símbolos USDT da Binance na inicialização."""
    logging.info("Buscando lista de moedas da Binance...")
    robust_services.rate_limiter.wait_if_needed()
    try:
        response = requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=15)
        response.raise_for_status()
        symbols = sorted([s['symbol'] for s in response.json()['symbols'] if s['symbol'].endswith('USDT')])
        logging.info(f"{len(symbols)} moedas encontradas na Binance.")
        return symbols
    except Exception as e:
        logging.error(f"Não foi possível buscar a lista de moedas da Binance: {e}")
        logging.warning("Retornando moedas da configuração existente como fallback.")
        return [c['symbol'] for c in existing_config.get('cryptos_to_monitor', [])]

def _get_sound_for_trigger(trigger_msg, sound_config):
    """Determina o som apropriado para um gatilho de alerta com base na configuração."""
    if not sound_config: return 'sons/Alerta.mp3'
    trigger_lower = trigger_msg.lower()
    if 'rsi sobrecomprado' in trigger_lower: return sound_config.get('overbought', 'sons/sobrecomprado.wav')
    if 'rsi sobrevendido' in trigger_lower: return sound_config.get('oversold', 'sons/sobrevendido.wav')
    if 'cruz dourada' in trigger_lower: return sound_config.get('golden_cross', 'sons/cruzamentoAlta.wav')
    if 'cruz da morte' in trigger_lower: return sound_config.get('death_cross', 'sons/cruzamentoBaixa.wav')
    if 'preço acima' in trigger_lower: return sound_config.get('price_above', 'sons/precoAcima.wav')
    if 'preço abaixo' in trigger_lower: return sound_config.get('price_below', 'sons/precoAbaixo.wav')
    if 'volume' in trigger_lower and 'alto' in trigger_lower: return sound_config.get('high_volume', 'sons/volumeAlto.wav')
    if 'fuga de capital' in trigger_lower or 'entrada de capital' in trigger_lower: return sound_config.get('critical_alert', 'sons/alertaCritico.wav')
    return sound_config.get('default_alert', 'sons/Alerta.mp3')

def _check_and_trigger_alerts(symbol, alert_config, analysis_data, data_queue, sound_config):
    """Verifica e dispara alertas para um símbolo com base nas condições configuradas."""
    conditions = alert_config.get('conditions', {})
    triggered_conditions = alert_config.get('triggered_conditions', [])
    current_price = analysis_data['current_price']
    rsi = analysis_data['rsi_value']
    volume_24h = analysis_data['volume_24h']
    price_change_24h = analysis_data['price_change_24h']
    market_cap = analysis_data.get('market_cap')

    triggers = []

    fuga_capital_config = conditions.get('fuga_capital_significativa', {})
    if fuga_capital_config.get('enabled') and market_cap is not None and market_cap > 0:
        try:
            percent_mcap_str, percent_price_str = fuga_capital_config['value'].split(',')
            if volume_as_percent_of_mcap := (volume_24h / market_cap * 100) > float(percent_mcap_str) and price_change_24h < float(percent_price_str):
                triggers.append(f"Fuga de Capital (Vol > {volume_as_percent_of_mcap:.2f}% Cap.Merc. e Var < {float(percent_price_str):.2f}%)")
        except (ValueError, TypeError):
            logging.warning(f"Configuração de alerta 'fuga de capital' inválida para {symbol}.")

    entrada_capital_config = conditions.get('entrada_capital_significativa', {})
    if entrada_capital_config.get('enabled') and market_cap is not None and market_cap > 0:
        try:
            percent_mcap_str, percent_price_str = entrada_capital_config['value'].split(',')
            if volume_as_percent_of_mcap := (volume_24h / market_cap * 100) > float(percent_mcap_str) and price_change_24h > float(percent_price_str):
                triggers.append(f"Entrada de Capital (Vol > {volume_as_percent_of_mcap:.2f}% Cap.Merc. e Var > {float(percent_price_str):.2f}%)")
        except (ValueError, TypeError):
            logging.warning(f"Configuração de alerta 'entrada de capital' inválida para {symbol}.")

    if conditions.get('preco_baixo', {}).get('enabled') and current_price <= conditions['preco_baixo']['value']: triggers.append(f"Preço Abaixo de ${conditions['preco_baixo']['value']:.2f} (Atual: ${current_price:.2f})")
    if conditions.get('preco_alto', {}).get('enabled') and current_price >= conditions['preco_alto']['value']: triggers.append(f"Preço Acima de ${conditions['preco_alto']['value']:.2f} (Atual: ${current_price:.2f})")
    if conditions.get('rsi_sobrevendido', {}).get('enabled') and rsi <= conditions['rsi_sobrevendido']['value']: triggers.append(f"RSI Sobrevendido (RSI <= {conditions['rsi_sobrevendido']['value']:.2f} | Atual: {rsi:.2f})")
    if conditions.get('rsi_sobrecomprado', {}).get('enabled') and rsi >= conditions['rsi_sobrecomprado']['value']: triggers.append(f"RSI Sobrecomprado (RSI >= {conditions['rsi_sobrecomprado']['value']:.2f} | Atual: {rsi:.2f})")
    if conditions.get('bollinger_abaixo', {}).get('enabled') and analysis_data.get('bollinger_signal') == "Abaixo da Banda": triggers.append("Preço Abaixo da Banda Inferior de Bollinger")
    if conditions.get('bollinger_acima', {}).get('enabled') and analysis_data.get('bollinger_signal') == "Acima da Banda": triggers.append("Preço Acima da Banda Superior de Bollinger")
    if conditions.get('macd_cruz_baixa', {}).get('enabled') and analysis_data.get('macd_signal') == "Cruzamento de Baixa": triggers.append("MACD: Cruzamento de Baixa")
    if conditions.get('macd_cruz_alta', {}).get('enabled') and analysis_data.get('macd_signal') == "Cruzamento de Alta": triggers.append("MACD: Cruzamento de Alta")
    if conditions.get('mme_cruz_morte', {}).get('enabled') and analysis_data.get('mme_cross') == "Cruz da Morte": triggers.append("MME: Cruz da Morte (MME 50 abaixo da MME 200)")
    if conditions.get('mme_cruz_dourada', {}).get('enabled') and analysis_data.get('mme_cross') == "Cruz Dourada": triggers.append("MME: Cruz Dourada (MME 50 acima da MME 200)")

    for trigger_msg in triggers:
        if trigger_msg not in triggered_conditions:
            market_cap_str = f"${market_cap:,.0f}" if market_cap is not None else "N/A"
            formatted_message = (f"🚨 ALERTA: {symbol} 🚨\n\nDisparo: {trigger_msg}\nPreço Atual: ${current_price:,.2f}\n"
                               f"Volume 24h: ${volume_24h:,.0f}\nCapitalização de Mercado: {market_cap_str}\n"
                               f"Variação 24h: {price_change_24h:.2f}%\n\nObservações: {alert_config.get('notes', 'Nenhuma')}")
            
            sound_path = _get_sound_for_trigger(trigger_msg, sound_config)
            alert_payload = {'symbol': symbol, 'message': formatted_message, 'sound': sound_path, 'trigger': trigger_msg, 'analysis_data': analysis_data}
            data_queue.put({'type': 'alert', 'payload': alert_payload})
            triggered_conditions.append(trigger_msg)
    alert_config['triggered_conditions'] = [t for t in triggered_conditions if t in set(triggers)]

def _analyze_symbol(symbol, ticker_data, market_cap=None):
    """Coleta e analisa todos os dados técnicos para um único símbolo."""
    analysis_result = {'symbol': symbol, 'current_price': 0.0, 'price_change_24h': 0.0, 'volume_24h': 0.0,
                       'rsi_value': 0.0, 'rsi_signal': "N/A", 'bollinger_signal': "Nenhum",
                       'macd_signal': "Nenhum", 'mme_cross': "Nenhum", 'market_cap': market_cap}

    symbol_ticker = ticker_data.get(symbol, {})
    analysis_result['current_price'] = robust_services.DataValidator.safe_price(symbol_ticker.get('lastPrice'))
    analysis_result['price_change_24h'] = robust_services.DataValidator.safe_float(symbol_ticker.get('priceChangePercent'))
    analysis_result['volume_24h'] = robust_services.DataValidator.safe_float(symbol_ticker.get('quoteVolume'))

    df = get_klines_data(symbol)
    if df is None or df.empty: return analysis_result

    rsi_value, _, _ = calculate_rsi(df)
    upper_band, lower_band, _, _ = calculate_bollinger_bands(df)
    macd_cross = calculate_macd(df)
    emas = calculate_emas(df, periods=[50, 200])

    analysis_result['rsi_value'] = rsi_value if rsi_value else 0.0
    analysis_result['rsi_signal'] = f"{rsi_value:.2f}" if rsi_value else "N/A"
    
    if upper_band > 0 and analysis_result['current_price'] > 0:
        if analysis_result['current_price'] > upper_band: analysis_result['bollinger_signal'] = "Acima da Banda"
        elif analysis_result['current_price'] < lower_band: analysis_result['bollinger_signal'] = "Abaixo da Banda"
            
    analysis_result['macd_signal'] = macd_cross
    
    if 50 in emas and 200 in emas and len(emas[50]) > 1 and len(emas[200]) > 1:
        if emas[50].iloc[-2] < emas[200].iloc[-2] and emas[50].iloc[-1] > emas[200].iloc[-1]: analysis_result['mme_cross'] = "Cruz Dourada"
        elif emas[50].iloc[-2] > emas[200].iloc[-2] and emas[50].iloc[-1] < emas[200].iloc[-1]: analysis_result['mme_cross'] = "Cruz da Morte"
    
    return analysis_result

def run_monitoring_cycle(config, data_queue, stop_event, coingecko_mapping):
    """Ciclo principal de monitoramento que roda em segundo plano para buscar e analisar dados."""
    logging.info("Ciclo de monitoramento iniciado.")
    
    while not stop_event.is_set():
        monitored_cryptos = copy.deepcopy(config.get("cryptos_to_monitor", []))
        sound_config = config.get('sound_config', {})
        if not monitored_cryptos:
            time.sleep(5)
            continue

        ticker_data = get_ticker_data()
        market_caps_data = get_market_caps_coingecko([c['symbol'] for c in monitored_cryptos], coingecko_mapping)

        if not ticker_data:
            logging.warning("Não foi possível obter os dados do ticker. Pulando este ciclo.")
            time.sleep(config.get("check_interval_seconds", 300))
            continue

        for crypto_config in monitored_cryptos:
            if stop_event.is_set(): break
            symbol = crypto_config.get('symbol')
            if not symbol or not robust_services.DataValidator.validate_symbol(symbol): continue

            analysis_data = _analyze_symbol(symbol, ticker_data, market_caps_data.get(symbol))
            data_queue.put({'type': 'data', 'payload': analysis_data})

            if alert_config := crypto_config.get('alert_config'):
                _check_and_trigger_alerts(symbol, alert_config, analysis_data, data_queue, sound_config)

            time.sleep(0.2)

        if not stop_event.is_set():
            logging.info(f"Ciclo de monitoramento completo. Aguardando {config.get('check_interval_seconds', 300)}s.")
            time.sleep(config.get("check_interval_seconds", 300))
    logging.info("Ciclo de monitoramento terminado.")

def run_single_symbol_update(symbol, config, data_queue, coingecko_mapping):
    """Executa uma atualização de dados para uma única moeda, usado para refresh manual."""
    logging.info(f"Iniciando atualização forçada para {symbol}...")
    crypto_config = next((c for c in config.get("cryptos_to_monitor", []) if c['symbol'] == symbol), None)
    if not crypto_config: return

    ticker_data = get_ticker_data()
    market_caps_data = get_market_caps_coingecko([symbol], coingecko_mapping)
    analysis_data = _analyze_symbol(symbol, ticker_data, market_caps_data.get(symbol))
    data_queue.put({'type': 'data', 'payload': analysis_data})
    logging.info(f"Atualização para {symbol} enviada para a interface.")

def get_btc_dominance():
    """Busca a dominância de mercado do BTC a partir da CoinGecko."""
    try:
        cache_key = {'func': 'get_btc_dominance'}
        if cached_data := robust_services.data_cache.get(cache_key, ttl=300): return cached_data
        
        robust_services.rate_limiter.wait_if_needed()
        global_data = cg_client.get_global()
        
        btc_dominance = 0
        if 'data' in global_data and 'market_cap_percentage' in global_data['data']:
            btc_dominance = global_data['data']['market_cap_percentage'].get('btc', 0)
        
        if btc_dominance > 0:
            result = f"{btc_dominance:.2f}%"
            robust_services.data_cache.set(cache_key, result)
            return result
        else:
            logging.warning("Dominância BTC não encontrada nos dados da API.")
            return "N/A"
            
    except Exception as e:
        logging.error(f"Não foi possível buscar a dominância do BTC: {e}")
        return "Erro"