"""
👻 Phantom Flow SMC 交易系統 (Streamlit Cloud Version)
Smart Money Concepts: BOS, CHoCH, Order Blocks, Liquidity, Buy/Sell Signals
零 C 擴展依賴，完全相容 Streamlit Cloud
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import warnings
warnings.filterwarnings('ignore')

# ─── 頁面配置 ─────────────────────────────────────────────
st.set_page_config(
    page_title="👻 Phantom Flow SMC",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 自訂 CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600&display=swap');

:root {
    --bg-primary: #0a0a0f;
    --bg-card: #0f0f1a;
    --bg-panel: #12121f;
    --accent-gold: #f0b429;
    --accent-cyan: #00d4ff;
    --accent-green: #00ff88;
    --accent-red: #ff3366;
    --accent-purple: #9d4edd;
    --text-primary: #e0e0f0;
    --text-dim: #6b6b8a;
    --border: #1e1e35;
}

.stApp {
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: 'Rajdhani', sans-serif;
}

/* 主標題 */
.phantom-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #f0b429, #00d4ff, #9d4edd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 3px;
    margin-bottom: 0.2rem;
}

.phantom-subtitle {
    text-align: center;
    color: var(--text-dim);
    font-size: 0.9rem;
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
}

/* 信號卡片 */
.signal-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.5rem 0;
    position: relative;
    overflow: hidden;
}

.signal-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-gold), transparent);
}

.signal-buy {
    border-left: 3px solid var(--accent-green);
    background: linear-gradient(135deg, #001a0d, #0f0f1a);
}

.signal-sell {
    border-left: 3px solid var(--accent-red);
    background: linear-gradient(135deg, #1a000d, #0f0f1a);
}

.signal-neutral {
    border-left: 3px solid var(--accent-gold);
    background: linear-gradient(135deg, #1a1200, #0f0f1a);
}

/* 指標徽章 */
.badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1px;
    margin: 0.15rem;
    font-family: 'Orbitron', monospace;
}

.badge-green { background: #00331a; color: #00ff88; border: 1px solid #00ff8844; }
.badge-red { background: #33000d; color: #ff3366; border: 1px solid #ff336644; }
.badge-gold { background: #332400; color: #f0b429; border: 1px solid #f0b42944; }
.badge-cyan { background: #001a33; color: #00d4ff; border: 1px solid #00d4ff44; }
.badge-purple { background: #1a0033; color: #9d4edd; border: 1px solid #9d4edd44; }

/* 指標數值 */
.metric-box {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    text-align: center;
}
.metric-label {
    font-size: 0.7rem;
    color: var(--text-dim);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-family: 'Orbitron', monospace;
}
.metric-value {
    font-size: 1.4rem;
    font-weight: 700;
    font-family: 'Orbitron', monospace;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 1px solid var(--border);
}

/* 模塊標題 */
.module-header {
    font-family: 'Orbitron', monospace;
    font-size: 0.85rem;
    color: var(--accent-cyan);
    letter-spacing: 2px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.5rem 0;
}

/* 隱藏 Streamlit 品牌 */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 📊 SMC 計算引擎 (純 Python / Pandas，無 C 擴展)
# ═══════════════════════════════════════════════════════════

def calculate_pivot_highs_lows(df, left=5, right=5):
    """識別 Pivot High / Pivot Low（用於市場結構）"""
    highs = []
    lows = []
    for i in range(left, len(df) - right):
        window_high = df['High'].iloc[i - left:i + right + 1]
        window_low = df['Low'].iloc[i - left:i + right + 1]
        if df['High'].iloc[i] == window_high.max():
            highs.append(i)
        if df['Low'].iloc[i] == window_low.min():
            lows.append(i)
    return highs, lows


def detect_market_structure(df, pivot_left=5, pivot_right=5):
    """
    市場結構識別：
    - BOS (Break of Structure)：趨勢延續突破
    - CHoCH (Change of Character)：趨勢反轉信號
    """
    ph_idx, pl_idx = calculate_pivot_highs_lows(df, pivot_left, pivot_right)

    bos_list = []    # {'idx', 'price', 'type': 'bullish'/'bearish'}
    choch_list = []

    # 追蹤最近的 pivot
    recent_ph = []
    recent_pl = []

    for i in range(len(df)):
        if i in ph_idx:
            recent_ph.append(i)
        if i in pl_idx:
            recent_pl.append(i)

        # 保留最近 3 個 pivot
        if len(recent_ph) > 3:
            recent_ph.pop(0)
        if len(recent_pl) > 3:
            recent_pl.pop(0)

        # BOS Bullish：價格突破最近高點
        if len(recent_ph) >= 2:
            last_ph = recent_ph[-2]
            if df['Close'].iloc[i] > df['High'].iloc[last_ph] and i > last_ph + pivot_right:
                bos_list.append({'idx': i, 'price': df['High'].iloc[last_ph], 'type': 'bullish', 'label': 'BOS'})

        # BOS Bearish：價格跌破最近低點
        if len(recent_pl) >= 2:
            last_pl = recent_pl[-2]
            if df['Close'].iloc[i] < df['Low'].iloc[last_pl] and i > last_pl + pivot_right:
                bos_list.append({'idx': i, 'price': df['Low'].iloc[last_pl], 'type': 'bearish', 'label': 'BOS'})

    # CHoCH：方向與最近 BOS 相反
    if len(bos_list) >= 2:
        for k in range(1, len(bos_list)):
            prev = bos_list[k - 1]
            curr = bos_list[k]
            if prev['type'] != curr['type']:
                curr['label'] = 'CHoCH'
                choch_list.append(curr)

    return bos_list, choch_list, ph_idx, pl_idx


def detect_order_blocks(df, ph_idx, pl_idx, atr_mult=0.5):
    """
    訂單塊識別（Order Blocks）：
    - 看漲 OB：突破前最後一根看跌蠟燭
    - 看跌 OB：突破前最後一根看漲蠟燭
    """
    atr = calculate_atr(df, 14)
    obs = []

    # 看漲 OB：pivot low 前的最後看跌蠟燭
    for idx in pl_idx:
        if idx < 3:
            continue
        for j in range(idx - 1, max(idx - 8, 0), -1):
            if df['Close'].iloc[j] < df['Open'].iloc[j]:  # 看跌蠟燭
                body_size = abs(df['Open'].iloc[j] - df['Close'].iloc[j])
                if body_size > atr.iloc[j] * atr_mult:
                    obs.append({
                        'idx': j,
                        'type': 'bullish',
                        'top': df['Open'].iloc[j],
                        'bottom': df['Close'].iloc[j],
                        'mid': (df['Open'].iloc[j] + df['Close'].iloc[j]) / 2,
                        'active': True
                    })
                break

    # 看跌 OB：pivot high 前的最後看漲蠟燭
    for idx in ph_idx:
        if idx < 3:
            continue
        for j in range(idx - 1, max(idx - 8, 0), -1):
            if df['Close'].iloc[j] > df['Open'].iloc[j]:  # 看漲蠟燭
                body_size = abs(df['Close'].iloc[j] - df['Open'].iloc[j])
                if body_size > atr.iloc[j] * atr_mult:
                    obs.append({
                        'idx': j,
                        'type': 'bearish',
                        'top': df['Close'].iloc[j],
                        'bottom': df['Open'].iloc[j],
                        'mid': (df['Close'].iloc[j] + df['Open'].iloc[j]) / 2,
                        'active': True
                    })
                break

    # 標記已被緩解的 OB
    for ob in obs:
        for i in range(ob['idx'] + 1, len(df)):
            if ob['type'] == 'bullish' and df['Close'].iloc[i] < ob['bottom']:
                ob['active'] = False
                break
            if ob['type'] == 'bearish' and df['Close'].iloc[i] > ob['top']:
                ob['active'] = False
                break

    return obs


def detect_liquidity_zones(df, ph_idx, pl_idx, atr_series, cluster_pct=0.003):
    """流動性區域（止損聚集點）"""
    zones = []
    highs = [(df['High'].iloc[i], i) for i in ph_idx]
    lows = [(df['Low'].iloc[i], i) for i in pl_idx]

    # 聚合相近價位
    for price, idx in highs[-15:]:
        zones.append({'price': price, 'idx': idx, 'type': 'sell_side', 'swept': False})

    for price, idx in lows[-15:]:
        zones.append({'price': price, 'idx': idx, 'type': 'buy_side', 'swept': False})

    # 標記已掃蕩的流動性
    for z in zones:
        for i in range(z['idx'] + 1, len(df)):
            if z['type'] == 'sell_side' and df['High'].iloc[i] > z['price']:
                z['swept'] = True
                z['sweep_idx'] = i
                break
            if z['type'] == 'buy_side' and df['Low'].iloc[i] < z['price']:
                z['swept'] = True
                z['sweep_idx'] = i
                break

    return zones


def detect_fair_value_gaps(df, min_gap_pct=0.001):
    """Fair Value Gaps (FVG) / 公允價值缺口"""
    fvgs = []
    for i in range(2, len(df)):
        prev_high = df['High'].iloc[i - 2]
        prev_low = df['Low'].iloc[i - 2]
        curr_high = df['High'].iloc[i]
        curr_low = df['Low'].iloc[i]
        mid_high = df['High'].iloc[i - 1]
        mid_low = df['Low'].iloc[i - 1]

        # 看漲 FVG：前蠟燭高點 < 後蠟燭低點
        if curr_low > prev_high:
            gap_size = (curr_low - prev_high) / prev_high
            if gap_size > min_gap_pct:
                fvgs.append({'idx': i - 1, 'type': 'bullish', 'top': curr_low, 'bottom': prev_high, 'filled': False})

        # 看跌 FVG：前蠟燭低點 > 後蠟燭高點
        if prev_low > curr_high:
            gap_size = (prev_low - curr_high) / curr_high
            if gap_size > min_gap_pct:
                fvgs.append({'idx': i - 1, 'type': 'bearish', 'top': prev_low, 'bottom': curr_high, 'filled': False})

    # 標記已填充 FVG
    for fvg in fvgs:
        for i in range(fvg['idx'] + 1, len(df)):
            if fvg['type'] == 'bullish' and df['Low'].iloc[i] <= fvg['bottom']:
                fvg['filled'] = True
                break
            if fvg['type'] == 'bearish' and df['High'].iloc[i] >= fvg['top']:
                fvg['filled'] = True
                break

    return fvgs


def calculate_atr(df, period=14):
    """Average True Range（純 Pandas）"""
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))


def calculate_momentum_oscillator(df):
    """動量振盪器（綜合 RSI + EMA 偏離）"""
    rsi = calculate_rsi(df['Close'], 14)
    ema20 = calculate_ema(df['Close'], 20)
    ema50 = calculate_ema(df['Close'], 50)
    ema_diff = ((ema20 - ema50) / ema50 * 100).clip(-10, 10)
    momentum = (rsi - 50) * 0.6 + ema_diff * 4
    return momentum.clip(-100, 100), rsi


def calculate_premium_discount_zone(df, lookback=50):
    """Premium/Discount Zone (上方20%=Premium賣區，下方20%=Discount買區)"""
    recent_high = df['High'].rolling(lookback).max()
    recent_low = df['Low'].rolling(lookback).min()
    rng = recent_high - recent_low
    position = (df['Close'] - recent_low) / (rng + 1e-10)
    return position, recent_high, recent_low


def generate_signals(df, bos_list, obs, fvgs, momentum, rsi):
    """
    多因素匯流買賣信號
    條件（看漲）：
    1. 最近 BOS = Bullish 或 CHoCH Bullish
    2. 價格在 Discount Zone
    3. 活躍 Bullish OB 附近
    4. RSI < 65（非超買）
    5. 動量 > 0
    """
    signals = pd.Series('NEUTRAL', index=df.index)
    signal_strength = pd.Series(0, index=df.index, dtype=float)

    zone_pos, _, _ = calculate_premium_discount_zone(df)

    for i in range(20, len(df)):
        score = 0

        # BOS 方向
        recent_bos = [b for b in bos_list if b['idx'] <= i]
        if recent_bos:
            last_bos = recent_bos[-1]
            if last_bos['type'] == 'bullish':
                score += 2
            else:
                score -= 2

        # Zone
        z = zone_pos.iloc[i]
        if z < 0.3:   # Discount
            score += 1.5
        elif z > 0.7:  # Premium
            score -= 1.5

        # Active OB
        active_bullish_ob = [ob for ob in obs if ob['active'] and ob['type'] == 'bullish'
                             and ob['bottom'] <= df['Close'].iloc[i] <= ob['top'] * 1.02]
        active_bearish_ob = [ob for ob in obs if ob['active'] and ob['type'] == 'bearish'
                             and ob['bottom'] * 0.98 <= df['Close'].iloc[i] <= ob['top']]

        if active_bullish_ob:
            score += 2
        if active_bearish_ob:
            score -= 2

        # RSI
        r = rsi.iloc[i]
        if not np.isnan(r):
            if r < 40:
                score += 1
            elif r > 60:
                score -= 1

        # Momentum
        m = momentum.iloc[i]
        if not np.isnan(m):
            score += m / 50

        # 未填充 FVG
        unfilled_bull_fvg = [f for f in fvgs if not f['filled'] and f['type'] == 'bullish'
                             and f['bottom'] <= df['Close'].iloc[i] <= f['top']]
        unfilled_bear_fvg = [f for f in fvgs if not f['filled'] and f['type'] == 'bearish'
                             and f['bottom'] <= df['Close'].iloc[i] <= f['top']]
        if unfilled_bull_fvg:
            score += 1
        if unfilled_bear_fvg:
            score -= 1

        signal_strength.iloc[i] = score

        if score >= 4:
            signals.iloc[i] = 'BUY'
        elif score <= -4:
            signals.iloc[i] = 'SELL'

    return signals, signal_strength


# ═══════════════════════════════════════════════════════════
# 📈 Plotly 圖表渲染
# ═══════════════════════════════════════════════════════════

def build_chart(df, bos_list, choch_list, obs, fvgs, liquidity, signals, momentum, rsi, show_ob, show_fvg, show_liq, show_bos, show_signals):
    """構建主圖 + 副圖"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.03,
        subplot_titles=["", "動量振盪器", "RSI"]
    )

    x = df.index

    # ── K 線圖 ──
    fig.add_trace(go.Candlestick(
        x=x,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff3366',
        increasing_fillcolor='rgba(0,255,136,0.8)',
        decreasing_fillcolor='rgba(255,51,102,0.8)',
        name='K線', showlegend=False
    ), row=1, col=1)

    # ── EMA ──
    ema20 = calculate_ema(df['Close'], 20)
    ema50 = calculate_ema(df['Close'], 50)
    fig.add_trace(go.Scatter(x=x, y=ema20, line=dict(color='#00d4ff', width=1.2), name='EMA20', opacity=0.8), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=ema50, line=dict(color='#f0b429', width=1.2), name='EMA50', opacity=0.8), row=1, col=1)

    # ── BOS / CHoCH ──
    if show_bos:
        for b in bos_list[-20:]:
            color = '#00ff88' if b['type'] == 'bullish' else '#ff3366'
            label = b['label']
            if b['idx'] < len(df):
                fig.add_hline(y=b['price'], line_color=color, line_width=0.8,
                              line_dash='dot', row=1, col=1, opacity=0.6)
                fig.add_annotation(
                    x=df.index[min(b['idx'], len(df)-1)],
                    y=b['price'],
                    text=f"<b>{label}</b>",
                    font=dict(color=color, size=10, family='Orbitron'),
                    bgcolor='rgba(0,0,0,0.7)',
                    bordercolor=color,
                    borderwidth=1,
                    row=1, col=1
                )

    # ── Order Blocks ──
    if show_ob:
        active_obs = [ob for ob in obs if ob['active']][-10:]
        for ob in active_obs:
            color = 'rgba(0,255,136,0.12)' if ob['type'] == 'bullish' else 'rgba(255,51,102,0.12)'
            border_color = '#00ff88' if ob['type'] == 'bullish' else '#ff3366'
            if ob['idx'] < len(df):
                fig.add_hrect(
                    y0=ob['bottom'], y1=ob['top'],
                    fillcolor=color,
                    line_color=border_color,
                    line_width=0.8,
                    opacity=1,
                    row=1, col=1
                )

    # ── Fair Value Gaps ──
    if show_fvg:
        unfilled_fvgs = [f for f in fvgs if not f['filled']][-8:]
        for fvg in unfilled_fvgs:
            color = 'rgba(0,212,255,0.08)' if fvg['type'] == 'bullish' else 'rgba(157,78,221,0.08)'
            border_color = '#00d4ff' if fvg['type'] == 'bullish' else '#9d4edd'
            if fvg['idx'] < len(df):
                fig.add_hrect(
                    y0=fvg['bottom'], y1=fvg['top'],
                    fillcolor=color,
                    line_color=border_color,
                    line_width=0.6,
                    line_dash='dash',
                    opacity=1,
                    row=1, col=1
                )

    # ── Liquidity Lines ──
    if show_liq:
        recent_liq = [z for z in liquidity if not z['swept']][-12:]
        for z in recent_liq:
            color = '#f0b429' if z['type'] == 'sell_side' else '#9d4edd'
            if z['idx'] < len(df):
                fig.add_hline(
                    y=z['price'],
                    line_color=color, line_width=0.7,
                    line_dash='dashdot', opacity=0.5,
                    row=1, col=1
                )

    # ── 買賣信號 ──
    if show_signals:
        buy_idx = [i for i in range(len(df)) if signals.iloc[i] == 'BUY']
        sell_idx = [i for i in range(len(df)) if signals.iloc[i] == 'SELL']

        if buy_idx:
            fig.add_trace(go.Scatter(
                x=df.index[buy_idx],
                y=df['Low'].iloc[buy_idx] * 0.998,
                mode='markers',
                marker=dict(symbol='triangle-up', size=14, color='#00ff88',
                            line=dict(color='white', width=1)),
                name='買入信號'
            ), row=1, col=1)

        if sell_idx:
            fig.add_trace(go.Scatter(
                x=df.index[sell_idx],
                y=df['High'].iloc[sell_idx] * 1.002,
                mode='markers',
                marker=dict(symbol='triangle-down', size=14, color='#ff3366',
                            line=dict(color='white', width=1)),
                name='賣出信號'
            ), row=1, col=1)

    # ── 動量振盪器 ──
    colors_mom = ['#00ff88' if v > 0 else '#ff3366' for v in momentum]
    fig.add_trace(go.Bar(
        x=x, y=momentum,
        marker_color=colors_mom,
        name='動量',
        opacity=0.8
    ), row=2, col=1)
    fig.add_hline(y=0, line_color='#6b6b8a', line_width=0.8, row=2, col=1)
    fig.add_hline(y=50, line_color='#ff3366', line_width=0.5, line_dash='dot', row=2, col=1)
    fig.add_hline(y=-50, line_color='#00ff88', line_width=0.5, line_dash='dot', row=2, col=1)

    # ── RSI ──
    fig.add_trace(go.Scatter(
        x=x, y=rsi,
        line=dict(color='#9d4edd', width=1.5),
        name='RSI', fill='tozeroy',
        fillcolor='rgba(157,78,221,0.1)'
    ), row=3, col=1)
    fig.add_hline(y=70, line_color='#ff3366', line_width=0.8, line_dash='dot', row=3, col=1)
    fig.add_hline(y=30, line_color='#00ff88', line_width=0.8, line_dash='dot', row=3, col=1)
    fig.add_hline(y=50, line_color='#6b6b8a', line_width=0.5, row=3, col=1)

    # ── 佈局 ──
    fig.update_layout(
        height=700,
        paper_bgcolor='#0a0a0f',
        plot_bgcolor='#0a0a0f',
        font=dict(family='Rajdhani', color='#e0e0f0', size=11),
        xaxis_rangeslider_visible=False,
        legend=dict(
            bgcolor='rgba(10,10,15,0.8)',
            bordercolor='#1e1e35',
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(l=60, r=20, t=20, b=20)
    )

    # 統一軸樣式
    for i in range(1, 4):
        fig.update_xaxes(
            gridcolor='#1e1e35', zerolinecolor='#1e1e35',
            showgrid=True, row=i, col=1
        )
        fig.update_yaxes(
            gridcolor='#1e1e35', zerolinecolor='#1e1e35',
            showgrid=True, row=i, col=1
        )

    return fig


# ═══════════════════════════════════════════════════════════
# 🚀 MAIN APP
# ═══════════════════════════════════════════════════════════

# 主標題
st.markdown('<div class="phantom-title">👻 PHANTOM FLOW SMC</div>', unsafe_allow_html=True)
st.markdown('<div class="phantom-subtitle">SMART MONEY CONCEPTS · BOS · CHoCH · ORDER BLOCKS · FVG · LIQUIDITY</div>', unsafe_allow_html=True)

# ─── Sidebar 設置 ─────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="module-header">⚙️ 系統設置</div>', unsafe_allow_html=True)

    symbol = st.text_input("股票代碼", value="TSLA", placeholder="TSLA / AAPL / NVDA").upper()

    col_a, col_b = st.columns(2)
    with col_a:
        interval = st.selectbox("時間週期", ['5m', '15m', '1h', '4h', '1d'], index=2)
    with col_b:
        period_map = {'5m': '5d', '15m': '10d', '1h': '60d', '4h': '60d', '1d': '1y'}
        period_label = {'5m': '5天', '15m': '10天', '1h': '60天', '4h': '60天', '1d': '1年'}
        st.text_input("數據範圍", value=period_label.get(interval, '60天'), disabled=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="module-header">📊 顯示模塊</div>', unsafe_allow_html=True)

    show_bos = st.toggle("BOS / CHoCH 市場結構", value=True)
    show_ob = st.toggle("訂單塊 (Order Blocks)", value=True)
    show_fvg = st.toggle("公允缺口 (FVG)", value=True)
    show_liq = st.toggle("流動性區域 (Liquidity)", value=True)
    show_signals = st.toggle("買賣信號", value=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="module-header">🔧 參數調整</div>', unsafe_allow_html=True)

    pivot_left = st.slider("Pivot 左側K線數", 3, 10, 5)
    pivot_right = st.slider("Pivot 右側K線數", 3, 10, 5)
    ob_atr_mult = st.slider("OB 最小ATR倍數", 0.2, 2.0, 0.5, 0.1)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="module-header">📡 Telegram 警報</div>', unsafe_allow_html=True)

    tg_token = st.text_input("Bot Token", type="password", placeholder="可選")
    tg_chat = st.text_input("Chat ID", placeholder="可選")

    refresh = st.button("🔄 刷新數據", use_container_width=True, type="primary")


# ─── 數據載入 ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data(sym, interval, period):
    try:
        ticker = yf.Ticker(sym)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None, None
        info = ticker.info
        return df, info
    except Exception as e:
        return None, str(e)

period = period_map.get(interval, '60d')
with st.spinner(f"📡 載入 {symbol} 數據..."):
    df, info = load_data(symbol, interval, period)

if df is None or len(df) < 30:
    st.error(f"⚠️ 無法取得 {symbol} 數據，請確認代碼是否正確。")
    st.stop()

# ─── 計算所有指標 ─────────────────────────────────────────
with st.spinner("🧠 SMC 引擎計算中..."):
    atr = calculate_atr(df)
    bos_list, choch_list, ph_idx, pl_idx = detect_market_structure(df, pivot_left, pivot_right)
    obs = detect_order_blocks(df, ph_idx, pl_idx, ob_atr_mult)
    fvgs = detect_fair_value_gaps(df)
    liquidity = detect_liquidity_zones(df, ph_idx, pl_idx, atr)
    momentum, rsi = calculate_momentum_oscillator(df)
    zone_pos, zone_high, zone_low = calculate_premium_discount_zone(df)
    signals, signal_strength = generate_signals(df, bos_list, obs, fvgs, momentum, rsi)

# ─── 最新數據提取 ─────────────────────────────────────────
last = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else last
price_chg = (last['Close'] - prev['Close']) / prev['Close'] * 100
current_signal = signals.iloc[-1]
current_strength = signal_strength.iloc[-1]
current_zone = zone_pos.iloc[-1]
current_rsi = rsi.iloc[-1]
current_mom = momentum.iloc[-1]
current_atr = atr.iloc[-1]

# 最近 BOS
recent_bos = [b for b in bos_list][-1] if bos_list else None
active_bull_ob = [ob for ob in obs if ob['active'] and ob['type'] == 'bullish']
active_bear_ob = [ob for ob in obs if ob['active'] and ob['type'] == 'bearish']
unfilled_fvg = [f for f in fvgs if not f['filled']]

# ─── 頂部指標列 ───────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)

price_color = '#00ff88' if price_chg >= 0 else '#ff3366'
arrow = '▲' if price_chg >= 0 else '▼'

with c1:
    st.markdown(f"""<div class="metric-box">
        <div class="metric-label">現價</div>
        <div class="metric-value" style="color:{price_color}">${last['Close']:.2f}</div>
        <div style="color:{price_color};font-size:0.8rem">{arrow} {abs(price_chg):.2f}%</div>
    </div>""", unsafe_allow_html=True)

with c2:
    sig_color = '#00ff88' if current_signal == 'BUY' else ('#ff3366' if current_signal == 'SELL' else '#f0b429')
    sig_icon = '🟢' if current_signal == 'BUY' else ('🔴' if current_signal == 'SELL' else '🟡')
    st.markdown(f"""<div class="metric-box">
        <div class="metric-label">信號</div>
        <div class="metric-value" style="color:{sig_color}">{sig_icon} {current_signal}</div>
        <div style="color:#6b6b8a;font-size:0.8rem">強度: {current_strength:.1f}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    zone_label = "🔵 DISCOUNT" if current_zone < 0.35 else ("🔴 PREMIUM" if current_zone > 0.65 else "⚪ EQUILIBRIUM")
    zone_col = '#00ff88' if current_zone < 0.35 else ('#ff3366' if current_zone > 0.65 else '#f0b429')
    st.markdown(f"""<div class="metric-box">
        <div class="metric-label">價格區域</div>
        <div class="metric-value" style="color:{zone_col};font-size:0.9rem">{zone_label}</div>
        <div style="color:#6b6b8a;font-size:0.8rem">{current_zone*100:.0f}% of range</div>
    </div>""", unsafe_allow_html=True)

with c4:
    rsi_color = '#ff3366' if current_rsi > 70 else ('#00ff88' if current_rsi < 30 else '#e0e0f0')
    st.markdown(f"""<div class="metric-box">
        <div class="metric-label">RSI(14)</div>
        <div class="metric-value" style="color:{rsi_color}">{current_rsi:.1f}</div>
        <div style="color:#6b6b8a;font-size:0.8rem">{'超買' if current_rsi > 70 else ('超賣' if current_rsi < 30 else '中性')}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    bos_label = recent_bos['label'] if recent_bos else 'N/A'
    bos_dir = recent_bos['type'] if recent_bos else 'neutral'
    bos_col = '#00ff88' if bos_dir == 'bullish' else '#ff3366'
    st.markdown(f"""<div class="metric-box">
        <div class="metric-label">最近結構</div>
        <div class="metric-value" style="color:{bos_col};font-size:1.1rem">{bos_label}</div>
        <div style="color:#6b6b8a;font-size:0.8rem">{bos_dir.upper()}</div>
    </div>""", unsafe_allow_html=True)

with c6:
    st.markdown(f"""<div class="metric-box">
        <div class="metric-label">ATR(14)</div>
        <div class="metric-value" style="color:#00d4ff">${current_atr:.2f}</div>
        <div style="color:#6b6b8a;font-size:0.8rem">{current_atr/last['Close']*100:.2f}% volatility</div>
    </div>""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── 主圖表 ───────────────────────────────────────────────
fig = build_chart(df, bos_list, choch_list, obs, fvgs, liquidity,
                  signals, momentum, rsi,
                  show_ob, show_fvg, show_liq, show_bos, show_signals)
st.plotly_chart(fig, use_container_width=True)

# ─── 信號面板 + SMC 摘要 ──────────────────────────────────
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown('<div class="module-header">🎯 最新交易信號分析</div>', unsafe_allow_html=True)

    # 信號卡片
    card_class = "signal-buy" if current_signal == "BUY" else ("signal-sell" if current_signal == "SELL" else "signal-neutral")

    # 建議止損/目標
    atr_val = current_atr
    if current_signal == "BUY":
        stop = last['Close'] - atr_val * 1.5
        target1 = last['Close'] + atr_val * 2
        target2 = last['Close'] + atr_val * 3.5
    elif current_signal == "SELL":
        stop = last['Close'] + atr_val * 1.5
        target1 = last['Close'] - atr_val * 2
        target2 = last['Close'] - atr_val * 3.5
    else:
        stop = target1 = target2 = None

    badges = []
    if recent_bos:
        color = 'green' if recent_bos['type'] == 'bullish' else 'red'
        badges.append(f'<span class="badge badge-{color}">{recent_bos["label"]} {recent_bos["type"].upper()}</span>')
    if active_bull_ob:
        badges.append(f'<span class="badge badge-green">🟩 BULL OB x{len(active_bull_ob)}</span>')
    if active_bear_ob:
        badges.append(f'<span class="badge badge-red">🟥 BEAR OB x{len(active_bear_ob)}</span>')
    if current_zone < 0.35:
        badges.append('<span class="badge badge-cyan">DISCOUNT ZONE</span>')
    elif current_zone > 0.65:
        badges.append('<span class="badge badge-purple">PREMIUM ZONE</span>')
    if unfilled_fvg:
        badges.append(f'<span class="badge badge-gold">⬜ FVG x{len(unfilled_fvg)}</span>')

    stop_html = f"🛑 止損: <b>${stop:.2f}</b> | 🎯 T1: <b>${target1:.2f}</b> | 🎯 T2: <b>${target2:.2f}</b>" if stop else "觀望，等待更多匯流確認"

    st.markdown(f"""<div class="signal-card {card_class}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem">
            <span style="font-family:Orbitron;font-size:1.1rem;color:{'#00ff88' if current_signal=='BUY' else ('#ff3366' if current_signal=='SELL' else '#f0b429')};font-weight:700">{current_signal}</span>
            <span style="color:#6b6b8a;font-size:0.8rem">{datetime.now().strftime('%H:%M:%S')}</span>
        </div>
        <div style="margin-bottom:0.6rem">{''.join(badges) if badges else '<span style="color:#6b6b8a">無活躍匯流條件</span>'}</div>
        <div style="font-size:0.85rem;color:#c0c0d8;margin-top:0.6rem">{stop_html}</div>
    </div>""", unsafe_allow_html=True)

    # 匯流強度條
    st.markdown("**信號匯流強度**")
    strength_norm = min(max((current_strength + 8) / 16, 0), 1)
    bar_color = "#00ff88" if current_strength > 0 else "#ff3366"
    st.markdown(f"""<div style="background:#1e1e35;border-radius:6px;height:12px;overflow:hidden;margin-top:4px">
        <div style="background:{bar_color};width:{strength_norm*100:.0f}%;height:100%;border-radius:6px;transition:width 0.5s"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#6b6b8a;margin-top:4px">
        <span>強看跌</span><span>中性</span><span>強看漲</span>
    </div>""", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="module-header">📋 SMC 結構摘要</div>', unsafe_allow_html=True)

    total_bos = len([b for b in bos_list if b['label'] == 'BOS'])
    total_choch = len(choch_list)
    bull_bos = len([b for b in bos_list if b['type'] == 'bullish'])
    bear_bos = len([b for b in bos_list if b['type'] == 'bearish'])

    metrics = [
        ("BOS 數量", f"{total_bos} (🟢{bull_bos} 🔴{bear_bos})"),
        ("CHoCH 數量", f"{total_choch}"),
        ("活躍 OB", f"🟢{len(active_bull_ob)} 🔴{len(active_bear_ob)}"),
        ("未填 FVG", f"{len(unfilled_fvg)} 個"),
        ("流動性區域", f"{len([z for z in liquidity if not z['swept']])} 個活躍"),
        ("掃蕩次數", f"{len([z for z in liquidity if z['swept']])} 次"),
    ]

    for label, val in metrics:
        st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:0.45rem 0.6rem;
            border-bottom:1px solid #1e1e35;font-size:0.88rem">
            <span style="color:#6b6b8a">{label}</span>
            <span style="color:#e0e0f0;font-weight:600">{val}</span>
        </div>""", unsafe_allow_html=True)

# ─── Telegram 警報 ────────────────────────────────────────
if tg_token and tg_chat and current_signal in ['BUY', 'SELL']:
    def send_tg(token, chat_id, msg):
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'}, timeout=5)
            return True
        except:
            return False

    if st.button("📡 發送 Telegram 警報", type="secondary"):
        stop_str = f"${stop:.2f}" if stop else "N/A"
        t1_str = f"${target1:.2f}" if target1 else "N/A"
        msg = f"""👻 <b>Phantom Flow SMC 信號</b>
        
📌 <b>{symbol}</b> | {interval} | {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎯 信號: <b>{current_signal}</b>
💰 現價: <b>${last['Close']:.2f}</b>
🔲 區域: <b>{'DISCOUNT' if current_zone < 0.35 else ('PREMIUM' if current_zone > 0.65 else 'EQUILIBRIUM')}</b>
📊 RSI: {current_rsi:.1f} | 動量: {current_mom:.1f}
🛑 止損: {stop_str}
🎯 目標1: {t1_str}
🏗️ 結構: {recent_bos['label'] if recent_bos else 'N/A'} {recent_bos['type'].upper() if recent_bos else ''}"""
        ok = send_tg(tg_token, tg_chat, msg)
        if ok:
            st.success("✅ Telegram 警報已發送！")
        else:
            st.error("❌ 發送失敗，請檢查 Token / Chat ID")

# ─── 最近信號歷史 ─────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="module-header">📜 近期信號歷史</div>', unsafe_allow_html=True)

sig_history = [(df.index[i], signals.iloc[i], df['Close'].iloc[i], signal_strength.iloc[i])
               for i in range(len(df)) if signals.iloc[i] in ['BUY', 'SELL']][-15:]

if sig_history:
    cols = st.columns(len(sig_history[-8:]) if len(sig_history) >= 8 else len(sig_history))
    for k, (ts, sig, price, strength) in enumerate(reversed(sig_history[-8:])):
        with cols[k]:
            color = '#00ff88' if sig == 'BUY' else '#ff3366'
            icon = '▲' if sig == 'BUY' else '▼'
            ts_str = ts.strftime('%m/%d %H:%M') if hasattr(ts, 'strftime') else str(ts)[:10]
            st.markdown(f"""<div class="metric-box" style="border-left:2px solid {color}">
                <div style="color:{color};font-size:0.85rem;font-weight:700">{icon} {sig}</div>
                <div style="font-size:0.8rem;color:#e0e0f0">${price:.2f}</div>
                <div style="font-size:0.7rem;color:#6b6b8a">{ts_str}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("目前無信號記錄，嘗試更長時間週期或調整參數。")

# ─── Footer ───────────────────────────────────────────────
st.markdown("""<div style="text-align:center;padding:2rem 0 1rem;color:#3a3a5a;font-size:0.75rem;letter-spacing:1px">
    👻 PHANTOM FLOW SMC · Fortune Foods Trading Research · 僅供教育研究用途，不構成投資建議
</div>""", unsafe_allow_html=True)
