import time
import requests
import pandas as pd
import pandas_ta as ta

# رابط الويب هوك الخاص بك في Make
WEBHOOK_URL = "https://hook.eu1.make.com/mcv7nm8lxiktbkvxnxiask6vmbvzfwrx"

# قائمة العملات التي سيتم مراقبتها (يمكنك إزالة أو إضافة ما تحب)
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]

def get_binance_data(symbol, interval="15m", limit=300):
    """جلب بيانات الشموع اليابانية من منصة بينانس"""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not isinstance(data, list):
            return None
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # تحويل الأعمدة إلى أرقام
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        return df
    except Exception as e:
        print(f"خطأ في جلب بيانات {symbol}: {e}")
        return None

def check_indicators(df):
    """فحص المؤشرات الأربعة المطلوبة (EMA200, MACD, RSI, Volume)"""
    try:
        # حساب المؤشرات باستخدام مكتبة pandas_ta
        df['EMA200'] = ta.ema(df['close'], length=200)
        
        macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            df['MACD'] = macd_df['MACD_12_26_9']
            df['MACD_signal'] = macd_df['MACDs_12_26_9']
        
        df['RSI'] = ta.rsi(df['close'], length=14)
        df['Volume_SMA'] = ta.sma(df['volume'], length=20)
        
        # أخذ آخر شمعة مكتملة (قبل الأخيرة) أو الشمعة الحالية
        last_row = df.iloc[-2]
        
        close_price = last_row['close']
        ema200 = last_row['EMA200']
        macd = last_row['MACD']
        macd_signal = last_row['MACD_signal']
        rsi = last_row['RSI']
        volume = last_row['volume']
        volume_sma = last_row['Volume_SMA']
        
        # شروط الإشارة الصاعدة (100% بناءً على التقاء المؤشرات الأربعة)
        # 1. السعر فوق EMA200
        # 2. خط MACD أعلى من خط الإشارة (Signal)
        # 3. مؤشر RSI في منطقة مناسبة للصعود (مثلاً أكبر من 50 وأقل من 70)
        # 4. الفوليوم أعلى من متوسط الفوليوم لآخر 20 شمعة
        condition_ema = close_price > ema200
        condition_macd = macd > macd_signal
        condition_rsi = 50 < rsi < 75
        condition_volume = volume > volume_sma
        
        if condition_ema and condition_macd and condition_rsi and condition_volume:
            return {
                "price": close_price,
                "rsi": round(rsi, 2),
                "macd": round(macd, 4),
                "volume": round(volume, 2)
            }
    except Exception as e:
        print(f"خطأ في حساب المؤشرات: {e}")
        
    return None

def send_to_make(symbol, data):
    """إرسال البيانات إلى الويب هوك الخاص بـ Make"""
    payload = {
        "symbol": symbol,
        "price": data["price"],
        "rsi": data["rsi"],
        "macd": data["macd"],
        "volume": data["volume"],
        "message": f"🔥 فرصة صعود قوية لـ {symbol} على إطار 15 دقيقة مطابقة للشروط الأربعة!"
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"تم إرسال تنبيه {symbol} بنجاح إلى Make!")
        else:
            print(f"فشل الإرسال لـ {symbol}, رمز الاستجابة: {response.status_code}")
    except Exception as e:
        print(f"خطأ في إرسال الويب هوك: {e}")

def main():
    print("🚀 بدء تشغيل بوت مراقبة العملات على إطار 15 دقيقة...")
        for symbol in SYMBOLS:
        print(f"فحص {symbol}...")
        df = get_binance_data(symbol)
        if df is not None:
            signal_data = check_indicators(df)
            if signal_data:
                print(f"🔥 تم العثور على فرصة مطابقة لـ {symbol}!")
                send_to_make(symbol, signal_data)
        time.sleep(2)

if __name__ == "__main__":
    main()


            
        
