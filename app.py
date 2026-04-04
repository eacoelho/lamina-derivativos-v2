# -*- coding: utf-8 -*-
"""
Options Structure Sheet Generator
Mesa de Derivativos - Agrocommodities
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as mtick
from datetime import datetime, timedelta
import io
import warnings
warnings.filterwarnings("ignore")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lâmina de Estruturas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background-color: #07090f; color: #e2e8f0; }

section[data-testid="stSidebar"] {
    background: #0b0f1e;
    border-right: 1px solid #1e293b;
}
section[data-testid="stSidebar"] label {
    color: #64748b !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stNumberInput input {
    background: #131929 !important;
    border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

h1,h2,h3,h4,h5 { font-family: 'IBM Plex Mono', monospace; color: #f1f5f9; }

.stButton > button {
    background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.06em !important;
    width: 100% !important;
    padding: 0.65rem !important;
    margin-top: 0.8rem !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

.report-header {
    background: linear-gradient(135deg,#0c1a3a,#07090f);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.4rem;
    position: relative;
    overflow: hidden;
}
.report-header::before {
    content:'';
    position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg,#38bdf8,#6366f1,#f472b6);
}
.report-header h2 {
    font-size:1.5rem; font-weight:600; color:#f8fafc; margin:0 0 .25rem;
    letter-spacing:-.03em;
}
.report-header .sub { font-size:.75rem; color:#475569; letter-spacing:.1em; text-transform:uppercase; }

.tag {
    display:inline-block; background:#1e293b; border:1px solid #334155;
    color:#94a3b8; font-size:.68rem; font-weight:700; letter-spacing:.08em;
    text-transform:uppercase; padding:.18rem .55rem; border-radius:4px; margin-right:.4rem;
}

.card {
    background:#0b0f1e; border:1px solid #1e293b; border-radius:10px;
    padding:1.2rem 1.4rem; height:100%;
}
.card h4 {
    font-size:.62rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
    color:#38bdf8; margin:0 0 .7rem; border-bottom:1px solid #1e293b; padding-bottom:.45rem;
}
.card p { font-size:.83rem; color:#94a3b8; line-height:1.65; margin:0; }

.disclaimer {
    font-size:.68rem; color:#334155; border-top:1px solid #1e293b;
    padding-top:.7rem; margin-top:.7rem; line-height:1.5;
}

div[data-testid="stDataFrame"] { border-radius:8px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Commodity data ───────────────────────────────────────────────────────────
COMMODITIES = {
    "Soja CBOT":   {"ticker": "ZS=F", "unit": "¢/bu",  "label": "CBOT Soybean"},
    "Milho CBOT":  {"ticker": "ZC=F", "unit": "¢/bu",  "label": "CBOT Corn"},
    "Algodão NY":  {"ticker": "CT=F", "unit": "¢/lb",  "label": "ICE Cotton #2"},
}

# Futures expiry months per commodity (CME/ICE standard)
EXPIRY_MONTHS = {
    "Soja CBOT":  ["Jan","Mar","May","Jul","Aug","Sep","Nov"],
    "Milho CBOT": ["Mar","May","Jul","Sep","Dec"],
    "Algodão NY": ["Mar","May","Jul","Oct","Dec"],
}

# ── Structure definitions ────────────────────────────────────────────────────
STRUCTURES = {
    "Long Put": {
        "n_levels": 1,
        "level_names": ["Strike Put (K1)"],
        "has_cost": True,
        "legs_desc": "Compra de 1 put (K1).",
        "description": (
            "Compra de uma opção de venda (put). Confere ao detentor o direito de vender "
            "o ativo subjacente ao preço de exercício K1 no vencimento. O custo é o prêmio "
            "pago."
        ),
        "use": (
            "Indicada para produtores rurais que desejam proteção total contra queda de "
            "preços, mantendo a participação em eventuais altas. Clássico instrumento de "
            "hedge de piso de preço."
        ),
        "payoff": lambda S, K1, K2, K3, cost: max(K1 - S, 0) - cost,
    },
    "Long Call": {
        "n_levels": 1,
        "level_names": ["Strike Call (K1)"],
        "has_cost": True,
        "legs_desc": "Compra de 1 call (K1).",
        "description": (
            "Compra de uma opção de compra (call). Garante ao detentor o direito de "
            "adquirir o ativo ao preço K1. Ganho ilimitado em caso de alta, perda limitada "
            "ao prêmio pago."
        ),
        "use": (
            "Utilizada por compradores (tradings, indústrias) para fixar um teto de compra, "
            "ou por produtores que já venderam fisicamente e desejam participar de eventual "
            "recuperação de preços."
        ),
        "payoff": lambda S, K1, K2, K3, cost: max(S - K1, 0) - cost,
    },
    "Put Spread": {
        "n_levels": 2,
        "level_names": ["Strike Put Comprada (K1)", "Strike Put Vendida (K2)"],
        "has_cost": True,
        "legs_desc": "Compra put K1 + Venda put K2 (K1 > K2).",
        "description": (
            "Compra de uma put com strike mais alto (K1) e venda de uma put com strike "
            "mais baixo (K2). Reduz o custo em relação à long put isolada, mas limita o "
            "ganho máximo à diferença K1−K2 menos o prêmio líquido."
        ),
        "use": (
            "Adequado para produtores que toleram certa exposição abaixo de K2, mas querem "
            "proteção entre K2 e K1 a custo reduzido."
        ),
        "payoff": lambda S, K1, K2, K3, cost: (max(K1 - S, 0) - max(K2 - S, 0)) - cost,
    },
    "Call Spread": {
        "n_levels": 2,
        "level_names": ["Strike Call Comprada (K1)", "Strike Call Vendida (K2)"],
        "has_cost": True,
        "legs_desc": "Compra call K1 + Venda call K2 (K1 < K2).",
        "description": (
            "Compra de uma call K1 e venda de uma call K2. Limita tanto o custo quanto o "
            "ganho potencial ao intervalo K2−K1 menos o prêmio líquido."
        ),
        "use": (
            "Indicado para compradores que desejam participar de alta até K2 pagando prêmio "
            "reduzido."
        ),
        "payoff": lambda S, K1, K2, K3, cost: (max(S - K1, 0) - max(S - K2, 0)) - cost,
    },
    "Bear Zero Cost Collar": {
        "n_levels": 2,
        "level_names": ["Strike Put Comprada (K1)", "Strike Call Vendida (K2)"],
        "has_cost": False,
        "legs_desc": "Compra put K1 + Venda call K2. Custo líquido zero.",
        "description": (
            "Compra de put K1 financiada pela venda de call K2 (K2 > K1). Estrutura de "
            "custo zero que garante um piso em K1, mas limita a participação em alta acima "
            "de K2."
        ),
        "use": (
            "Ideal para produtores com necessidade de proteção sem desembolso de caixa. "
            "Aceita-se abrir mão da alta acima de K2 em troca da proteção abaixo de K1."
        ),
        "payoff": lambda S, K1, K2, K3, cost: max(K1 - S, 0) - max(S - K2, 0),
    },
    "Bull Zero Cost Collar": {
        "n_levels": 2,
        "level_names": ["Strike Put Vendida (K1)", "Strike Call Comprada (K2)"],
        "has_cost": False,
        "legs_desc": "Venda put K1 + Compra call K2. Custo líquido zero.",
        "description": (
            "Venda de put K1 financiando a compra de call K2. O comprador de commodities "
            "define um teto de compra (K2) e aceita pagar o piso K1 se o mercado cair."
        ),
        "use": (
            "Indicado para tradings/indústrias que desejam capturar alta sem custo inicial, "
            "aceitando o risco de comprar a K1 caso o mercado caia abaixo deste nível."
        ),
        "payoff": lambda S, K1, K2, K3, cost: max(S - K2, 0) - max(K1 - S, 0),
    },
    "Bear Fence": {
        "n_levels": 3,
        "level_names": ["Strike Put Comprada (K1)", "Strike Put Vendida (K2)", "Strike Call Vendida (K3)"],
        "has_cost": True,
        "legs_desc": "Compra put K1 + Venda put K2 + Venda call K3.",
        "description": (
            "Extensão do bear collar com venda adicional de put K2 (K2 < K1 < K3). "
            "A venda da put K2 reduz ainda mais o custo, mas aumenta a exposição abaixo "
            "de K2. A venda da call K3 limita participação em alta."
        ),
        "use": (
            "Para produtores dispostos a aceitar maior risco abaixo de K2 em troca de "
            "proteção de custo mínimo ou zero entre K2 e K1."
        ),
        "payoff": lambda S, K1, K2, K3, cost: (
            max(K1 - S, 0) - max(K2 - S, 0) - max(S - K3, 0)
        ) - cost,
    },
    "Bull Fence": {
        "n_levels": 3,
        "level_names": ["Strike Put Vendida (K1)", "Strike Call Comprada (K2)", "Strike Call Vendida (K3)"],
        "has_cost": True,
        "legs_desc": "Venda put K1 + Compra call K2 + Venda call K3.",
        "description": (
            "Compra de call spread (K2/K3) financiada pela venda de put K1. Estrutura "
            "bullish de baixo custo que participa de alta entre K2 e K3, com risco de "
            "queda abaixo de K1."
        ),
        "use": (
            "Compradores que desejam participação em alta com custo reduzido, "
            "aceitando exposição se o mercado cair abaixo de K1."
        ),
        "payoff": lambda S, K1, K2, K3, cost: (
            max(S - K2, 0) - max(S - K3, 0) - max(K1 - S, 0)
        ) - cost,
    },
}

# ── Helper: expiry year list ──────────────────────────────────────────────────
def expiry_options(commodity: str) -> list[str]:
    months = EXPIRY_MONTHS[commodity]
    today = datetime.today()
    options = []
    for year in [today.year, today.year + 1]:
        for m in months:
            options.append(f"{m}/{year}")
    return options

# ── Helper: fetch price history ───────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_price_history(ticker: str) -> pd.Series:
    end = datetime.today()
    start = end - timedelta(days=370)
    try:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return pd.Series(dtype=float)
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        return close
    except Exception:
        return pd.Series(dtype=float)

# ── Helper: last price ────────────────────────────────────────────────────────
def get_last_price(ticker: str) -> float:
    s = get_price_history(ticker)
    if s.empty:
        return 0.0
    return float(s.iloc[-1])

# ── Payoff table ──────────────────────────────────────────────────────────────
def build_payoff_table(struct_name, spot, K1, K2, K3, cost, unit):
    fn = STRUCTURES[struct_name]["payoff"]
    scenarios = [-0.20, -0.10, 0.0, 0.10, 0.20]
    rows = []
    for pct in scenarios:
        s_price = spot * (1 + pct)
        pnl = fn(s_price, K1, K2, K3, cost)
        rows.append({
            "Cenário": f"{'+' if pct>0 else ''}{int(pct*100)}%",
            f"Preço ({unit})": round(s_price, 2),
            f"Payoff ({unit})": round(pnl, 2),
        })
    df = pd.DataFrame(rows)
    return df

# ── Chart ─────────────────────────────────────────────────────────────────────
def build_chart(price_series, spot, K1, K2, K3, n_levels, struct_name, commodity, expiry, unit):
    fig = plt.figure(figsize=(12, 4.5), facecolor="#07090f")
    gs = GridSpec(1, 2, figure=fig, width_ratios=[2.2, 1], wspace=0.04)

    # ── Left: price history ───────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor("#07090f")

    COLORS = {"K1": "#38bdf8", "K2": "#f472b6", "K3": "#facc15"}

    if not price_series.empty:
        dates = price_series.index
        prices = price_series.values
        ax1.plot(dates, prices, color="#94a3b8", linewidth=1.4, zorder=2, label="Futuro")
        ax1.fill_between(dates, prices, prices.min(), alpha=0.08, color="#38bdf8")

    level_map = {}
    labels = STRUCTURES[struct_name]["level_names"]
    for i, (val, lbl) in enumerate(zip([K1, K2, K3][:n_levels], labels)):
        key = f"K{i+1}"
        color = COLORS[key]
        ax1.axhline(val, color=color, linewidth=1.3, linestyle="--", alpha=0.9, zorder=3)
        short = lbl.split("(")[1].rstrip(")") if "(" in lbl else key
        level_map[short] = (val, color)

    ax1.axhline(spot, color="#4ade80", linewidth=1.1, linestyle=":", alpha=0.7, zorder=3)

    for spine in ax1.spines.values():
        spine.set_color("#1e293b")
    ax1.tick_params(colors="#475569", labelsize=7.5)
    ax1.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.1f"))
    ax1.set_title(
        f"{commodity}  —  {COMMODITIES[commodity]['label']}  |  Vcto {expiry}",
        color="#94a3b8", fontsize=8.5, pad=8, loc="left",
        fontfamily="IBM Plex Mono" if True else "monospace"
    )
    ax1.set_ylabel(unit, color="#475569", fontsize=8)
    ax1.grid(axis="y", color="#1e293b", linewidth=0.6, linestyle="-")
    ax1.grid(axis="x", color="#0f1629", linewidth=0.4)

    # Legend
    handles = [mpatches.Patch(color="#94a3b8", label="Preço Futuro"),
               mpatches.Patch(color="#4ade80", label=f"Spot {spot:.2f}")]
    for short, (val, col) in level_map.items():
        handles.append(mpatches.Patch(color=col, label=f"{short} = {val:.2f}"))
    ax1.legend(handles=handles, fontsize=7, loc="upper left",
               facecolor="#0b0f1e", edgecolor="#1e293b", labelcolor="#94a3b8")

    # ── Right: payoff diagram ─────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor("#07090f")

    fn = STRUCTURES[struct_name]["payoff"]
    price_range = np.linspace(spot * 0.65, spot * 1.35, 300)
    payoffs = np.array([fn(s, K1, K2, K3, 0) for s in price_range])

    pos = np.where(payoffs >= 0, payoffs, 0)
    neg = np.where(payoffs < 0, payoffs, 0)
    ax2.fill_between(price_range, pos, color="#4ade80", alpha=0.25)
    ax2.fill_between(price_range, neg, color="#f87171", alpha=0.25)
    ax2.plot(price_range, payoffs, color="#e2e8f0", linewidth=1.8)
    ax2.axhline(0, color="#334155", linewidth=0.8)
    ax2.axvline(spot, color="#4ade80", linewidth=0.9, linestyle=":", alpha=0.7)

    for i, (val, lbl) in enumerate(zip([K1, K2, K3][:n_levels], labels)):
        ax2.axvline(val, color=COLORS[f"K{i+1}"], linewidth=0.9, linestyle="--", alpha=0.7)

    for spine in ax2.spines.values():
        spine.set_color("#1e293b")
    ax2.tick_params(colors="#475569", labelsize=7.5)
    ax2.set_title("Diagrama de Payoff", color="#94a3b8", fontsize=8.5, pad=8, loc="left")
    ax2.set_xlabel(unit, color="#475569", fontsize=8)
    ax2.grid(axis="y", color="#1e293b", linewidth=0.5)
    ax2.grid(axis="x", color="#0f1629", linewidth=0.4)

    plt.tight_layout()
    return fig

# ── Full report figure (for export) ──────────────────────────────────────────
def build_full_report_figure(
    commodity, expiry, struct_name, spot, K1, K2, K3, cost, unit,
    price_series, payoff_df
):
    fig = plt.figure(figsize=(14, 18), facecolor="#07090f")
    fig.patch.set_facecolor("#07090f")

    # Title block
    fig.text(0.055, 0.972, "LÂMINA DE ESTRUTURA DE OPÇÕES",
             color="#38bdf8", fontsize=9, fontweight="bold",
             fontfamily="monospace", va="top")
    fig.text(0.055, 0.960,
             f"{struct_name.upper()}  ·  {commodity}  ·  Vcto {expiry}  ·  {datetime.today().strftime('%d/%m/%Y')}",
             color="#f1f5f9", fontsize=14, fontweight="bold", va="top")
    fig.text(0.055, 0.944,
             f"Spot referência: {spot:.2f} {unit}   |   {COMMODITIES[commodity]['label']}",
             color="#64748b", fontsize=9, va="top")
    fig.add_artist(plt.Line2D([0.055, 0.945], [0.938, 0.938],
                               transform=fig.transFigure, color="#1e293b", linewidth=0.8))

    struct = STRUCTURES[struct_name]
    n = struct["n_levels"]
    fn = struct["payoff"]

    # ── Price history chart ───────────────────────────────────────────────────
    ax_hist = fig.add_axes([0.055, 0.67, 0.56, 0.24])
    ax_hist.set_facecolor("#0b0f1e")
    COLORS = {"K1": "#38bdf8", "K2": "#f472b6", "K3": "#facc15"}

    if not price_series.empty:
        dates = price_series.index
        prices = price_series.values
        ax_hist.plot(dates, prices, color="#94a3b8", linewidth=1.2, label="Futuro")
        ax_hist.fill_between(dates, prices, prices.min(), alpha=0.07, color="#38bdf8")

    level_handles = []
    for i, (val, lbl) in enumerate(
        zip([K1, K2, K3][:n], struct["level_names"])
    ):
        col = COLORS[f"K{i+1}"]
        short = lbl.split("(")[1].rstrip(")") if "(" in lbl else f"K{i+1}"
        ax_hist.axhline(val, color=col, linewidth=1.1, linestyle="--", alpha=0.9)
        level_handles.append(mpatches.Patch(color=col, label=f"{short}={val:.2f}"))

    ax_hist.axhline(spot, color="#4ade80", linewidth=1.0, linestyle=":", alpha=0.7)
    for spine in ax_hist.spines.values():
        spine.set_color("#1e293b")
    ax_hist.tick_params(colors="#475569", labelsize=7)
    ax_hist.set_title("Histórico 12 meses + Níveis da Estrutura",
                       color="#94a3b8", fontsize=8, pad=6, loc="left")
    ax_hist.set_ylabel(unit, color="#475569", fontsize=7.5)
    ax_hist.grid(axis="y", color="#1e293b", linewidth=0.5)
    all_handles = [mpatches.Patch(color="#94a3b8", label="Futuro"),
                   mpatches.Patch(color="#4ade80", label=f"Spot {spot:.2f}")] + level_handles
    ax_hist.legend(handles=all_handles, fontsize=6.5, loc="upper left",
                   facecolor="#07090f", edgecolor="#1e293b", labelcolor="#94a3b8")

    # ── Payoff diagram ────────────────────────────────────────────────────────
    ax_pay = fig.add_axes([0.655, 0.67, 0.29, 0.24])
    ax_pay.set_facecolor("#0b0f1e")
    price_range = np.linspace(spot * 0.65, spot * 1.35, 300)
    payoffs = np.array([fn(s, K1, K2, K3, 0) for s in price_range])
    ax_pay.fill_between(price_range, np.where(payoffs >= 0, payoffs, 0), color="#4ade80", alpha=0.22)
    ax_pay.fill_between(price_range, np.where(payoffs < 0, payoffs, 0), color="#f87171", alpha=0.22)
    ax_pay.plot(price_range, payoffs, color="#e2e8f0", linewidth=1.6)
    ax_pay.axhline(0, color="#334155", linewidth=0.7)
    ax_pay.axvline(spot, color="#4ade80", linewidth=0.8, linestyle=":", alpha=0.7)
    for i, val in enumerate([K1, K2, K3][:n]):
        ax_pay.axvline(val, color=COLORS[f"K{i+1}"], linewidth=0.8, linestyle="--", alpha=0.7)
    for spine in ax_pay.spines.values():
        spine.set_color("#1e293b")
    ax_pay.tick_params(colors="#475569", labelsize=7)
    ax_pay.set_title("Diagrama de Payoff", color="#94a3b8", fontsize=8, pad=6, loc="left")
    ax_pay.set_xlabel(unit, color="#475569", fontsize=7.5)
    ax_pay.grid(axis="y", color="#1e293b", linewidth=0.5)

    # ── Description box ───────────────────────────────────────────────────────
    desc_ax = fig.add_axes([0.055, 0.50, 0.41, 0.145])
    desc_ax.set_facecolor("#0b0f1e")
    desc_ax.set_xticks([]); desc_ax.set_yticks([])
    for spine in desc_ax.spines.values():
        spine.set_color("#1e293b")
    desc_ax.text(0.02, 0.92, "DESCRIÇÃO DA ESTRUTURA", transform=desc_ax.transAxes,
                 color="#38bdf8", fontsize=7, fontweight="bold", va="top")
    desc_ax.text(0.02, 0.78, struct["description"], transform=desc_ax.transAxes,
                 color="#94a3b8", fontsize=7.5, va="top", wrap=True,
                 multialignment="left")

    # ── Use recommendation ────────────────────────────────────────────────────
    use_ax = fig.add_axes([0.51, 0.50, 0.435, 0.145])
    use_ax.set_facecolor("#0b0f1e")
    use_ax.set_xticks([]); use_ax.set_yticks([])
    for spine in use_ax.spines.values():
        spine.set_color("#1e293b")
    use_ax.text(0.02, 0.92, "RECOMENDAÇÃO DE USO", transform=use_ax.transAxes,
                color="#f472b6", fontsize=7, fontweight="bold", va="top")
    use_ax.text(0.02, 0.78, struct["use"], transform=use_ax.transAxes,
                color="#94a3b8", fontsize=7.5, va="top", wrap=True,
                multialignment="left")

    # ── Parameters box ────────────────────────────────────────────────────────
    param_ax = fig.add_axes([0.055, 0.375, 0.885, 0.095])
    param_ax.set_facecolor("#0b0f1e")
    param_ax.set_xticks([]); param_ax.set_yticks([])
    for spine in param_ax.spines.values():
        spine.set_color("#1e293b")
    param_ax.text(0.01, 0.88, "PARÂMETROS DA ESTRUTURA", transform=param_ax.transAxes,
                  color="#facc15", fontsize=7, fontweight="bold", va="top")

    params_text = (
        f"Legs: {struct['legs_desc']}    "
        f"Spot Ref: {spot:.2f} {unit}    "
    )
    lnames = struct["level_names"]
    for i, (v, l) in enumerate(zip([K1, K2, K3][:n], lnames)):
        params_text += f"{l}: {v:.2f} {unit}    "
    if struct["has_cost"]:
        params_text += f"Custo: {cost:.2f} {unit}"
    param_ax.text(0.01, 0.52, params_text, transform=param_ax.transAxes,
                  color="#e2e8f0", fontsize=8, va="top")

    # ── Payoff table ──────────────────────────────────────────────────────────
    tbl_ax = fig.add_axes([0.055, 0.16, 0.885, 0.185])
    tbl_ax.set_facecolor("#07090f")
    tbl_ax.set_xticks([]); tbl_ax.set_yticks([])
    for spine in tbl_ax.spines.values():
        spine.set_visible(False)
    tbl_ax.text(0, 0.97, "TABELA DE PAYOFF — SIMULAÇÃO DE CENÁRIOS",
                transform=tbl_ax.transAxes, color="#38bdf8",
                fontsize=7.5, fontweight="bold", va="top")

    scenarios = [-0.20, -0.10, 0.0, 0.10, 0.20]
    col_labels = ["Cenário", f"Preço ({unit})", f"Payoff ({unit})", "Resultado"]
    col_x = [0.05, 0.30, 0.55, 0.75]
    row_y = [0.80, 0.63, 0.46, 0.29, 0.12, -0.04]

    for j, cl in enumerate(col_labels):
        tbl_ax.text(col_x[j], row_y[0], cl, transform=tbl_ax.transAxes,
                    color="#64748b", fontsize=7.5, fontweight="bold", va="top")

    for i, pct in enumerate(scenarios):
        s_price = spot * (1 + pct)
        pnl = fn(s_price, K1, K2, K3, cost)
        result = "✓ Ganho" if pnl > 0 else ("✗ Perda" if pnl < 0 else "— Neutro")
        color = "#4ade80" if pnl > 0 else ("#f87171" if pnl < 0 else "#94a3b8")
        row = row_y[i + 1]
        bg = "#0b0f1e" if i % 2 == 0 else "#07090f"
        rect = mpatches.FancyBboxPatch((0, row - 0.02), 0.98, 0.14,
                                        boxstyle="round,pad=0.005",
                                        linewidth=0, facecolor=bg,
                                        transform=tbl_ax.transAxes, clip_on=False)
        tbl_ax.add_patch(rect)
        tbl_ax.text(col_x[0], row + 0.09, f"{'+' if pct>0 else ''}{int(pct*100)}%",
                    transform=tbl_ax.transAxes, color="#e2e8f0", fontsize=8.5,
                    fontfamily="monospace", va="top")
        tbl_ax.text(col_x[1], row + 0.09, f"{s_price:.2f}",
                    transform=tbl_ax.transAxes, color="#e2e8f0", fontsize=8.5,
                    fontfamily="monospace", va="top")
        tbl_ax.text(col_x[2], row + 0.09, f"{pnl:+.2f}",
                    transform=tbl_ax.transAxes, color=color, fontsize=8.5,
                    fontfamily="monospace", fontweight="bold", va="top")
        tbl_ax.text(col_x[3], row + 0.09, result,
                    transform=tbl_ax.transAxes, color=color, fontsize=8, va="top")

    # ── Footer ────────────────────────────────────────────────────────────────
    fig.text(0.055, 0.06,
             "Este documento tem caráter exclusivamente informativo e não constitui oferta ou recomendação de investimento. "
             "Opções envolvem riscos e podem resultar em perdas superiores ao capital investido. "
             "Verifique os contratos e especificações completas com sua mesa de operações.",
             color="#334155", fontsize=6.5, va="top",
             wrap=True, multialignment="left")

    fig.text(0.055, 0.038,
             f"Gerado em {datetime.today().strftime('%d/%m/%Y %H:%M')}  ·  Mesa de Derivativos  ·  Dados: Yahoo Finance",
             color="#1e3a5f", fontsize=6.5, va="top")

    return fig

# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:.8rem 0 1.4rem;border-bottom:1px solid #1e293b;margin-bottom:1.2rem">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:1rem;font-weight:600;
                    color:#38bdf8;letter-spacing:-.02em">DERIVATIVES DESK</div>
        <div style="font-size:.68rem;color:#334155;letter-spacing:.12em;
                    text-transform:uppercase;margin-top:.2rem">Lâmina de Estruturas</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="font-size:.65rem;font-weight:700;'
                'letter-spacing:.15em;text-transform:uppercase;color:#38bdf8;'
                'border-bottom:1px solid #1e293b;padding-bottom:.4rem;margin-bottom:.8rem">'
                'ATIVO & VENCIMENTO</div>', unsafe_allow_html=True)

    commodity = st.selectbox("Commodity", list(COMMODITIES.keys()), key="commodity")
    expiry_opts = expiry_options(commodity)
    expiry = st.selectbox("Vencimento", expiry_opts, key="expiry")

    ticker = COMMODITIES[commodity]["ticker"]
    unit = COMMODITIES[commodity]["unit"]

    with st.spinner("Carregando preço..."):
        spot_default = get_last_price(ticker)

    spot = st.number_input(
        f"Spot de referência ({unit})",
        min_value=0.01,
        value=round(spot_default, 2) if spot_default > 0 else 100.0,
        step=0.25,
        format="%.2f",
        key="spot"
    )

    st.markdown('<div class="section-label" style="font-size:.65rem;font-weight:700;'
                'letter-spacing:.15em;text-transform:uppercase;color:#38bdf8;'
                'border-bottom:1px solid #1e293b;padding-bottom:.4rem;margin:.8rem 0">'
                'ESTRUTURA</div>', unsafe_allow_html=True)

    struct_name = st.selectbox("Estrutura", list(STRUCTURES.keys()), key="struct")
    struct = STRUCTURES[struct_name]
    n = struct["n_levels"]

    K1 = K2 = K3 = spot
    lnames = struct["level_names"]

    K1 = st.number_input(
        lnames[0], min_value=0.01,
        value=round(spot * 0.95, 2), step=0.25, format="%.2f", key="K1"
    )
    if n >= 2:
        K2 = st.number_input(
            lnames[1], min_value=0.01,
            value=round(spot * 1.05, 2), step=0.25, format="%.2f", key="K2"
        )
    if n >= 3:
        K3 = st.number_input(
            lnames[2], min_value=0.01,
            value=round(spot * 1.12, 2), step=0.25, format="%.2f", key="K3"
        )

    cost = 0.0
    if struct["has_cost"]:
        cost = st.number_input(
            f"Custo / Prêmio líquido ({unit})",
            min_value=0.0, value=round(spot * 0.02, 2),
            step=0.01, format="%.2f", key="cost"
        )

    generate = st.button("⚡ Gerar Lâmina", key="generate")

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:700;
            letter-spacing:.15em;text-transform:uppercase;color:#38bdf8;
            margin-bottom:.4rem">MESA DE DERIVATIVOS</div>
<h1 style="margin:0 0 .1rem;font-family:'IBM Plex Mono',monospace;font-size:1.8rem;
           font-weight:600;color:#f8fafc;letter-spacing:-.04em">
    Lâmina de Estruturas de Opções
</h1>
<p style="color:#475569;font-size:.82rem;margin:0 0 1.5rem">
    Agrocommodities  ·  CBOT / ICE  ·  Configure a estrutura no painel lateral e clique em <b>Gerar Lâmina</b>
</p>
""", unsafe_allow_html=True)

if not generate:
    st.markdown("""
    <div style="background:#0b0f1e;border:1px dashed #1e293b;border-radius:12px;
                padding:3rem 2rem;text-align:center;color:#334155">
        <div style="font-size:2.5rem;margin-bottom:.8rem">📋</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:.85rem;
                    color:#475569;letter-spacing:.05em">
            Configure os parâmetros no painel lateral e clique em <b style="color:#38bdf8">⚡ Gerar Lâmina</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Fetch data & generate ─────────────────────────────────────────────────────
with st.spinner("Carregando dados de mercado..."):
    price_series = get_price_history(ticker)

# Header
st.markdown(f"""
<div class="report-header">
    <h2>{struct_name} — {commodity}</h2>
    <div class="sub">
        <span class="tag">{expiry}</span>
        <span class="tag">{COMMODITIES[commodity]['label']}</span>
        <span class="tag">Spot {spot:.2f} {unit}</span>
        <span class="tag">{datetime.today().strftime('%d/%m/%Y')}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Info cards
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""
    <div class="card">
        <h4>Descrição da Estrutura</h4>
        <p>{struct['legs_desc']}<br><br>{struct['description']}</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="card">
        <h4>Recomendação de Uso</h4>
        <p>{struct['use']}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# Parameters row
param_cols = st.columns(n + (2 if struct["has_cost"] else 1))
param_cols[0].metric("Spot Ref.", f"{spot:.2f} {unit}")
param_cols[1].metric(lnames[0], f"{K1:.2f} {unit}")
if n >= 2:
    param_cols[2].metric(lnames[1], f"{K2:.2f} {unit}")
if n >= 3:
    param_cols[3].metric(lnames[2], f"{K3:.2f} {unit}")
if struct["has_cost"]:
    param_cols[-1].metric("Custo / Prêmio", f"{cost:.2f} {unit}")

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# Chart
with st.spinner("Gerando gráficos..."):
    fig_chart = build_chart(price_series, spot, K1, K2, K3, n,
                             struct_name, commodity, expiry, unit)
st.pyplot(fig_chart, use_container_width=True)
plt.close(fig_chart)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# Payoff table
st.markdown("""
<div style="font-size:.65rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;
            color:#38bdf8;border-bottom:1px solid #1e293b;padding-bottom:.4rem;
            margin-bottom:.8rem">TABELA DE PAYOFF — SIMULAÇÃO DE CENÁRIOS</div>
""", unsafe_allow_html=True)

payoff_df = build_payoff_table(struct_name, spot, K1, K2, K3, cost, unit)

fn = STRUCTURES[struct_name]["payoff"]

def color_payoff(val):
    try:
        v = float(val)
        if v > 0:
            return "color: #4ade80; font-weight: bold"
        elif v < 0:
            return "color: #f87171; font-weight: bold"
        return "color: #94a3b8"
    except Exception:
        return ""

col_payoff = f"Payoff ({unit})"
styled = (
    payoff_df.style
    .map(color_payoff, subset=[col_payoff])
    .set_properties(**{
        "background-color": "#0b0f1e",
        "color": "#e2e8f0",
        "border": "1px solid #1e293b",
        "font-family": "IBM Plex Mono, monospace",
        "font-size": "0.85rem",
        "text-align": "center",
    })
    .set_table_styles([
        {"selector": "th", "props": [
            ("background-color", "#131929"),
            ("color", "#38bdf8"),
            ("font-size", "0.72rem"),
            ("letter-spacing", "0.1em"),
            ("text-transform", "uppercase"),
            ("border", "1px solid #1e293b"),
            ("text-align", "center"),
        ]},
        {"selector": "tr:nth-child(3)", "props": [
            ("background-color", "#0c1a3a"),
        ]},
    ])
    .hide(axis="index")
)
st.dataframe(payoff_df, use_container_width=True, hide_index=True)

st.markdown("""
<div class="disclaimer">
⚠️  Este documento tem caráter exclusivamente informativo e educacional. Não constitui oferta,
solicitação ou recomendação de compra ou venda de qualquer instrumento financeiro.
Operações com derivativos envolvem riscos significativos e podem resultar em perdas
superiores ao capital inicialmente comprometido. Consulte sua mesa de operações e
verifique as especificações completas dos contratos antes de operar.
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# Export
st.markdown("""
<div style="font-size:.65rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;
            color:#38bdf8;border-bottom:1px solid #1e293b;padding-bottom:.4rem;
            margin-bottom:.8rem">EXPORTAR LÂMINA</div>
""", unsafe_allow_html=True)

with st.spinner("Preparando exportação..."):
    fig_full = build_full_report_figure(
        commodity, expiry, struct_name, spot, K1, K2, K3, cost, unit,
        price_series, payoff_df
    )
    buf = io.BytesIO()
    fig_full.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                     facecolor="#07090f")
    buf.seek(0)
    plt.close(fig_full)

filename = (
    f"lamina_{struct_name.replace(' ', '_')}_{commodity.replace(' ', '_')}"
    f"_{expiry.replace('/', '-')}_{datetime.today().strftime('%Y%m%d')}.png"
)

st.download_button(
    label="⬇️  Baixar Lâmina (PNG)",
    data=buf,
    file_name=filename,
    mime="image/png",
    use_container_width=True,
)
