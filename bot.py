import ccxt
import time
import requests
from datetime import datetime

# ============= بيانات التيليجرام =============
TELEGRAM_TOKEN = "8665916676:AAESitl3yvoqTHjhWdCyCy32ol3djbwZTmY"
TELEGRAM_CHAT_ID = "5468997397"

# ============= العملات =============
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT',
    'XRP/USDT', 'DOT/USDT', 'LINK/USDT', 'XLM/USDT', 'AVAX/USDT',
    'NEAR/USDT', 'ATOM/USDT', 'ALGO/USDT', 'VET/USDT', 'HBAR/USDT',
    'ICP/USDT', 'ETC/USDT', 'EGLD/USDT', 'IMX/USDT', 'MATIC/USDT',
    'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'FIL/USDT', 'GRT/USDT'
]

# ============= الإعدادات =============
MIN_DROP = 1.8          # هبوط 1.8% (للاختبار خفف إلى 0.3)
RSI_MAX = 40            # RSI أقل من 40 (للاختبار ارفع إلى 70)
TAKE_PROFIT = 1.0       # هدف 1%
STOP_LOSS = 0.5         # وقف 0.5%

exchange = ccxt.binance({'enableRateLimit': True})
open_trades = {}

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}, timeout=10)
        print("✅ تم الإرسال")
    except Exception as e:
        print(f"❌ خطأ: {e}")

def calculate_rsi(closes):
    if len(closes) < 15:
        return 50
    gains, losses = 0, 0
    for i in range(-14, 0):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)
    avg_gain = gains / 14
    avg_loss = losses / 14
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + (avg_gain / avg_loss)))

def run_bot():
    print("🤖 بوت السكالبينج شغال...")
    send_telegram("🚀 <b>بوت السكالبينج شغال!</b>\n✅ 25 عملة حلال")
    
    last_alert = {}
    
    while True:
        try:
            for symbol in SYMBOLS:
                if symbol in last_alert:
                    if (datetime.now() - last_alert[symbol]).seconds < 1200:
                        continue
                
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=30)
                if len(ohlcv) < 20:
                    continue
                
                last = ohlcv[-1]
                prev = ohlcv[-2]
                close = last[4]
                prev_close = prev[4]
                
                drop = (prev_close - close) / prev_close * 100
                if drop < MIN_DROP:
                    continue
                
                closes = [c[4] for c in ohlcv]
                rsi = calculate_rsi(closes)
                if rsi > RSI_MAX:
                    continue
                
                tp = close * (1 + TAKE_PROFIT/100)
                sl = close * (1 - STOP_LOSS/100)
                
                msg = f"""🔥 <b>إشارة شراء!</b> 🔥

<b>{symbol}</b>
💰 السعر: {close:.4f}
📉 الهبوط: {drop:.1f}%
📊 RSI: {rsi:.1f}

🎯 الهدف: {tp:.4f} (+{TAKE_PROFIT}%)
🛡️ الوقف: {sl:.4f} (-{STOP_LOSS}%)"""
                
                print(f"\n✅ {symbol} - هبوط {drop:.1f}%")
                send_telegram(msg)
                last_alert[symbol] = datetime.now()
                time.sleep(5)
                
                time.sleep(1)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 يبحث عن إشارات...")
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
