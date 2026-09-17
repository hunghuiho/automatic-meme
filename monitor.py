import os
import json
from datetime import datetime
import requests
import pandas as pd
import yfinance as yf

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
PA_API_URL = "https://hunghuiho.pythonanywhere.com/api/update_signals"

def send_line_broadcast(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    res = requests.post("https://api.line.me/v2/bot/message/broadcast", headers=headers, json=payload)
    return res.status_code

def check_daily_signals(is_friday=False):
    stocks_df = pd.read_csv("stocks.csv")
    signals = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    for _, row in stocks_df.iterrows():
        #260917 symbol = row['symbol']
        symbol = str(row["symbol"]).strip()

        name = row['name']

        #260917 df = yf.download(symbol, period="3mo", interval="1d")
        df = yf.download(
            symbol, period="3mo", interval="1d", multi_level_index=False
        )
        if df.empty:
            continue
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        #260917 # 簡易起漲條件範例（可依回測出來的 profile 彈性調整）
        #price_up = (latest['Close'] - prev['Close']) / prev['Close'] >= 0.03
        #vol_surge = latest['Volume'] > (df['Volume'].mean() * 1.8)
        ## 安全指數計算 (0 ~ 100)
        #safety_score = min(100, max(0, int(100 - (latest['Close'] / df['High'].max()) * 20 + (latest['Volume'] / df['Volume'].mean()) * 10)))
        #if price_up and vol_surge:
        #    signals.append({
        #        "symbol": symbol,
        #        "name": name,
        #        "close": round(float(latest['Close']), 2),
        #        "safety_score": safety_score
        #    })

        # ---------------------------------------------------------
        # 使用 float() / .item() 確保取得純數值 (Scalar)
        # ---------------------------------------------------------
        latest_close = float(latest["Close"])
        prev_close = float(prev["Close"])
        latest_vol = float(latest["Volume"])
        mean_vol = float(df["Volume"].mean())
        max_high = float(df["High"].max())

        # 1. 條件判斷（此時兩者皆為標準 bool 形態）
        price_up = ((latest_close - prev_close) / prev_close) >= 0.03
        vol_surge = latest_vol > (mean_vol * 1.8)
        
        # 2. 安全指數計算 (0 ~ 100)
        calc_score = 100 - (latest_close / max_high) * 20 + (latest_vol / mean_vol) * 10
        safety_score = min(100, max(0, int(calc_score)))
        
        # 只有當兩個條件同時滿足時才加入 signals
        if price_up and vol_surge:
            signals.append(
                {
                    "symbol": symbol,
                    "name": name,
                    "close": round(latest_close, 2),
                    "safety_score": safety_score,
                }
            )

    # 推送 LINE 廣播
    # 1. 根據是否有觸發訊號，組合 Line 廣播訊息    
    if signals:
        msg = "🚀 【強勢起漲訊號通知】\n" + "\n".join([f"• {s['name']}({s['symbol']}) | 價: {s['close']} | 安全指數: {s['safety_score']}" for s in signals])
    else:
        msg = f"📊 【股市監控日報】({today_str})\n今日無符合起漲條件之個股，市場平靜。"

    send_line_broadcast(msg)

    # 2. 週五額外發送總結訊息    
    if is_friday:
        summary_msg = f"📊 【週五市場快報】\n本週共監控 {len(stocks_df)} 檔標的，觸發起漲訊號次數：{len(signals)} 次。"
        send_line_broadcast(summary_msg)
        
    # 3. 同步至 PythonAnywhere（打包日期與狀態，方便網頁渲染）
    payload_to_pa = {
        "date": today_str,
        "has_signals": len(signals) > 0,
        "signals": signals,
    }
    try:
        requests.post(PA_API_URL, json=payload_to_pa, timeout=10)
    except Exception as e:
        print(f"同步至 PythonAnywhere 失敗: {e}")    
    # old file: requests.post(PA_API_URL, json=signals)

if __name__ == "__main__":
    import sys
    is_fri = "--friday" in sys.argv
    check_daily_signals(is_friday=is_fri)