import pandas as pd
import yfinance as yf
import numpy as np

def analyze_stock_patterns(symbol):
    df = yf.download(symbol, period="10y", interval="1d")
    if df.empty:
        return None
    
    # 計算基礎技術指標
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['Vol_MA20'] = df['Volume'].rolling(20).mean()
    df['RSI14'] = calculate_rsi(df['Close'], 14)
    
    # 標記未來 40 個交易日（約 2 個月）的最大漲幅
    df['Future_Max_Return'] = (df['High'].rolling(40).max().shift(-40) - df['Close']) / df['Close']
    
    # 篩選「2 個月漲 > 20%」的起漲點
    breakout_events = df[df['Future_Max_Return'] >= 0.20].copy()
    
    # 統計起漲前 3 天的技術面特徵（量價/均線距離）
    profile = {
        'symbol': symbol,
        'avg_rsi_before_breakout': float(breakout_events['RSI14'].mean()),
        'volume_ratio_trigger': float((breakout_events['Volume'] / breakout_events['Vol_MA20']).quantile(0.7)),
        'ma_alignment_req': float((breakout_events['Close'] / breakout_events['MA20']).mean())
    }
    return profile

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))