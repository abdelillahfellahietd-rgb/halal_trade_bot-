import ccxt
import time
from datetime import datetime, timedelta
import urllib.request
import urllib.parse

TOKEN = "8665916676:AAHUNeu0DR5_IC3nDJ_SDue2ZDoVXHjXV9k"
CHAT_ID = "5468997397"

exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

coins = [
    'SOL/USDT', 'XRP/USDT', 'DOGE/USDT', 'ADA/USDT', 'SUI/USDT',
    'AVAX/USDT', 'LINK/USDT', 'DOT/USDT', 'ARB/USDT', 'NEAR/USDT',
    'LTC/USDT', 'SEI/USDT', 'HBAR/USDT', 'XLM/USDT', 'OP/USDT',
    'FET/USDT', 'APT/USDT', 'ATOM/USDT', 'ALGO/USDT', 'FIL/USDT',
]

def send(msg):
    try:
        text = urllib.parse.quote(msg)
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        urllib.request.urlopen(url, timeout=10)
    except:
        pass

def get_rsi(prices):
    if len(prices) < 15: return 50
    g = sum(max(prices[i]-prices[i-1], 0) for i in range(len(prices)-14, len(prices)))
    l = sum(max(prices[i-1]-prices[i], 0) for i in range(len(prices)-14, len(prices)))
    if l == 0: return 100
    return 100 - (100 / (1 + g/l))

def get_ema(prices, period):
    if len(prices) < period: return prices[-1]
    k = 2 / (period + 1)
    e = sum(prices[:period]) / period
    for p in prices[period:]: e = p * k + e * (1 - k)
    return e

def get_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1: return 0
    trs = []
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i] - closes[i-1])
        trs.append(max(hl, hc, lc))
    return sum(trs[-period:]) / period

def get_vwap(prices, volumes):
    if len(prices) < 1: return prices[-1]
    total_vol = sum(volumes)
    if total_vol == 0: return prices[-1]
    return sum(p * v for p, v in zip(prices, volumes)) / total_vol

def btc_trend_bullish():
    """فلتر BTC: هل السوق العام صاعد؟"""
    try:
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '5m', limit=30)
        closes = [c[4] for c in ohlcv]
        ema9 = get_ema(closes, 9)
        ema21 = get_ema(closes, 21)
        return closes[-1] > ema9 and ema9 > ema21
    except:
        return True  # إذا فشل، اسمح بالدخول

# ═══════════════════════════
send("🟢 بوت محسن يعمل!\n✅ BTC Filter + VWAP + ATR + BE + Cooldown")
# ═══════════════════════════

trades = {}
wins = 0
losses = 0
consecutive_losses = 0
cooldown_until = datetime.now()
day = datetime.now().day

while True:
    try:
        if datetime.now().day != day:
            wins = 0; losses = 0; trades = {}; day = datetime.now().day
        
        # تبريد
        if datetime.now() < cooldown_until:
            time.sleep(30)
            continue
        
        # فلتر BTC
        btc_ok = btc_trend_bullish()
        if not btc_ok:
            time.sleep(60)
            continue
        
        # مراقبة الصفقات
        closed = []
        for coin, trade in list(trades.items()):
            try:
                t = exchange.fetch_ticker(coin)
                current = t['last']
                entry = trade['entry']
                pnl_pct = (current - entry) / entry * 100
                
                # نقطة تعادل
                if not trade.get('be_active') and pnl_pct >= 0.5:
                    trade['sl'] = entry * 1.001
                    trade['be_active'] = True
                    send(f"🔄 {coin}: نقطة تعادل!")
                
                # وقف متحرك (بعد +1%)
                if pnl_pct >= 1.0:
                    new_sl = current * 0.995
                    if new_sl > trade['sl']:
                        trade['sl'] = new_sl
                
                # هدف
                if current >= trade['tp']:
                    wins += 1; consecutive_losses = 0
                    send(f"🎯 *هدف!* {coin}\n💰 +1.5% ✅ | {wins}✅/{losses}❌")
                    closed.append(coin)
                # وقف
                elif current <= trade['sl']:
                    losses += 1; consecutive_losses += 1
                    send(f"🛑 *وقف* {coin}\n💸 {pnl_pct:.2f}% ❌ | {wins}✅/{losses}❌")
                    closed.append(coin)
                    # تبريد
                    if consecutive_losses >= 2:
                        cooldown_until = datetime.now() + timedelta(minutes=30)
                        send(f"🔴 تبريد 30 دقيقة! ({consecutive_losses} خسائر)")
                # وقت
                elif time.time() - trade['time'] > 900:
                    if current > entry:
                        wins += 1; consecutive_losses = 0
                        send(f"⏰ *وقت* {coin}\n💰 ربح ✅")
                    else:
                        losses += 1; consecutive_losses += 1
                        send(f"⏰ *وقت* {coin}\n💸 خسارة ❌")
                    closed.append(coin)
            except:
                pass
        
        for c in closed:
            del trades[c]
        
        # بحث عن فرص
        if len(trades) < 8:
            for coin in coins:
                if coin in trades or len(trades) >= 8:
                    break
                
                try:
                    ohlcv_1m = exchange.fetch_ohlcv(coin, '1m', limit=60)
                    closes = [c[4] for c in ohlcv_1m]
                    highs = [c[2] for c in ohlcv_1m]
                    lows = [c[3] for c in ohlcv_1m]
                    volumes = [c[5] for c in ohlcv_1m]
                    current = closes[-1]
                    
                    change_5m = (closes[-1]-closes[-6])/closes[-6]*100 if len(closes)>5 else 0
                    rsi = get_rsi(closes)
                    atr = get_atr(highs, lows, closes)
                    atr_pct = atr / current * 100
                    ema9 = get_ema(closes, 9)
                    ema21 = get_ema(closes, 21)
                    vwap = get_vwap(closes[-30:], volumes[-30:])
                    avg_vol = sum(volumes[-15:])/15 if len(volumes)>=15 else volumes[-1]
                    vol_ratio = volumes[-1]/avg_vol if avg_vol>0 else 1
                    
                    score = 0
                    reasons = []
                    
                    # BTC فلتر (2pts)
                    if btc_ok: score += 2; reasons.append("BTC صاعد")
                    
                    # VWAP فلتر (2pts)
                    if current > vwap: score += 2; reasons.append("فوق VWAP")
                    
                    # EMA فلتر (1pt)
                    if ema9 > ema21: score += 1; reasons.append("EMA9>EMA21")
                    
                    # RSI (2pts)
                    if rsi < 35: score += 2; reasons.append(f"RSI={rsi:.0f}")
                    
                    # حجم (2pts)
                    if vol_ratio > 2: score += 2; reasons.append(f"حجم {vol_ratio:.0f}x")
                    
                    # هبوط (2pts)
                    if change_5m < -2: score += 2; reasons.append(f"هبوط {change_5m:.1f}%")
                    
                    # ارتداد (1pt)
                    if closes[-1] > closes[-2]: score += 1; reasons.append("ارتداد")
                    
                    # ATR فلتر - تجنب التذبذب المنخفض جداً
                    if atr_pct < 0.1:
                        score -= 3
                        reasons.append("تذبذب منخفض")
                    
                    if score >= 7:
                        entry = current
                        sl = entry * 0.99
                        tp = entry * 1.015
                        
                        trades[coin] = {
                            'entry': entry, 'sl': sl, 'tp': tp,
                            'time': time.time(), 'score': score,
                            'be_active': False
                        }
                        
                        wr = wins/(wins+losses)*100 if (wins+losses)>0 else 0
                        send(f"""🟢 *فرصة!*
{coin} | ${entry:.4f}
📉 هبوط: {change_5m:.1f}% | RSI: {rsi:.0f}
📊 ATR: {atr_pct:.2f}% | VWAP: ${vwap:.4f}
🛑 وقف: ${sl:.4f} | 🎯 هدف: ${tp:.4f}
⭐ {score}/10 | {chr(10).join('✅ '+r for r in reasons)}
📊 {wins}✅/{losses}❌ | {wr:.0f}%""")
                        time.sleep(0.5)
                    
                    time.sleep(0.05)
                except:
                    pass
        
        # تحديث كل 10 دقائق
        if datetime.now().minute % 10 == 0:
            wr = wins/(wins+losses)*100 if (wins+losses)>0 else 0
            cd = ""
            if datetime.now() < cooldown_until:
                remaining = int((cooldown_until - datetime.now()).total_seconds() / 60)
                cd = f" | 🔴 تبريد {remaining}د"
            send(f"📊 مفتوحة: {len(trades)} | {wins}✅/{losses}❌ | {wr:.0f}% | BTC:{'🟢' if btc_ok else '🔴'}{cd}")
        
        time.sleep(15)
        
    except KeyboardInterrupt:
        send("🔴 توقف البوت")
        break
    except:
        time.sleep(10)