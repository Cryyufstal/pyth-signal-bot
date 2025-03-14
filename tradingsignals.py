import ccxt
import ta
import numpy as np
import telebot
import time
import pandas as pd

# إعدادات Binance API
exchange = ccxt.okx()
SYMBOLS = ['ETH/USDT', 'ADA/USDT', 'XRP/USDT']
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# إعدادات Telegram
TELEGRAM_BOT_TOKEN = "7318761843:AAH_px4QlkQgrtoVohxy8b0Gs80WzJA9ieU"
CHAT_ID = "6973330942"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# إرسال رسالة عند تشغيل البوت
bot.send_message(CHAT_ID, "🚀 بوت التداول بدأ العمل! سيتم إرسال إشعارات عند تحقق الشروط.")

def get_candles(symbol, timeframe='1m', limit=100):
    """جلب بيانات الأسعار"""
    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    if not candles or len(candles) < 50:  # التحقق من البيانات
        return None
    close_prices = np.array([candle[4] for candle in candles], dtype=np.float64)
    return close_prices

def calculate_rsi(prices, period=14):
    """حساب مؤشر القوة النسبية (RSI)"""
    if prices is None or len(prices) < period:
        return None
    df = pd.DataFrame({'close': prices})
    rsi = ta.momentum.RSIIndicator(df['close'], window=period).rsi().iloc[-1]
    return rsi  # ✅ إصلاح الخطأ بإضافة return

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """حساب مؤشر MACD"""
    if prices is None or len(prices) < slow:
        return None, None
    df = pd.DataFrame({'close': prices})
    macd_indicator = ta.trend.MACD(df['close'], window_slow=slow, window_fast=fast, window_sign=signal)
    return macd_indicator.macd().iloc[-1], macd_indicator.macd_signal().iloc[-1]  # ✅ إصلاح الخطأ بإضافة return

while True:
    for symbol in SYMBOLS:
        try:
            prices = get_candles(symbol)

            if prices is None:
                print(f"⚠️ لا توجد بيانات كافية لـ {symbol}")
                continue  # تخطي هذه العملة

            rsi = calculate_rsi(prices, RSI_PERIOD)
            macd, signal = calculate_macd(prices, MACD_FAST, MACD_SLOW, MACD_SIGNAL)

            if rsi is None or macd is None or signal is None:
                print(f"⚠️ البيانات غير كافية لحساب RSI أو MACD لـ {symbol}")
                continue  

            if rsi < 30 and macd > signal:  # إشارة شراء
                bot.send_message(CHAT_ID, f'🔔 شراء محتمل: {symbol}\nRSI: {rsi:.2f}, MACD: {macd:.4f}')
            elif rsi > 70 and macd < signal:  # إشارة بيع
                bot.send_message(CHAT_ID, f'⚠️ بيع محتمل: {symbol}\nRSI: {rsi:.2f}, MACD: {macd:.4f}')
        
        except Exception as e:
            print(f"⚠️ خطأ في {symbol}: {e}")
    
    time.sleep(60)  # انتظار دقيقة بين الفحوصات
