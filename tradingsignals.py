import ccxt
import pandas as pd
import time
import requests
from ta.trend import MACD

# إعدادات تيليجرام
TELEGRAM_TOKEN = '7679583380:AAFzYwz9FKmrKmas6sE1oOZwTcQoMvgHRDY'
CHAT_ID = '7767987992'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

# تحميل البيانات
def fetch_latest_data(symbol="ETH/USDT", timeframe="5m", limit=100, exchange_name="kucoin"):
    exchange = getattr(ccxt, exchange_name)()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df

# حساب MACD
def apply_macd(df):
    macd = MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    return df

# العملات التي نراقبها
symbols = ["ETH/USDT", "ADA/USDT", "XRP/USDT"]

# تخزين آخر إشارة لكل عملة
last_signals = {symbol: None for symbol in symbols}

# بدء الحلقة المستمرة
while True:
    for symbol in symbols:
        try:
            print(f"\nChecking {symbol}...")
            df = fetch_latest_data(symbol=symbol, timeframe="5m", limit=100)
            df = apply_macd(df)

            # التأكد من وجود بيانات كافية
            if len(df) >= 2:
                macd_now = df["MACD"].iloc[-1]
                signal_now = df["MACD_signal"].iloc[-1]
                macd_prev = df["MACD"].iloc[-2]
                signal_prev = df["MACD_signal"].iloc[-2]

                # تقاطع لأعلى = LONG
                if macd_now > signal_now and macd_prev <= signal_prev and last_signals[symbol] != "BUY":
                    price = df["close"].iloc[-1]
                    send_telegram_message(f"🚀 LONG Signal!\nSymbol: {symbol}\nEntry Price: {price:.4f}\nTime: {df.index[-1]}")
                    print(f"Sent LONG signal for {symbol}")
                    last_signals[symbol] = "BUY"

                # تقاطع لأسفل = SHORT
                elif macd_now < signal_now and macd_prev >= signal_prev and last_signals[symbol] != "SELL":
                    price = df["close"].iloc[-1]
                    send_telegram_message(f"🔻 SHORT Signal!\nSymbol: {symbol}\nEntry Price: {price:.4f}\nTime: {df.index[-1]}")
                    print(f"Sent SHORT signal for {symbol}")
                    last_signals[symbol] = "SELL"

                else:
                    print(f"No signal for {symbol} at {df.index[-1]}")

        except Exception as e:
            print(f"Error fetching/analyzing {symbol}: {e}")

    # الانتظار حتى الشمعة التالية (5 دقائق = 300 ثانية)
    print("\nWaiting for next update...")
    time.sleep(300)
