# ============================================================
# SECUREVAULT - MODERN CYBERSECURITY THEME & DESIGN SYSTEM
# ============================================================

import streamlit as st
import html
import textwrap

def render_html(html_str: str):
    """
    Safely renders custom HTML elements and SVGs into Streamlit via st.markdown(..., unsafe_allow_html=True).
    Strips leading indentation from every line to strictly prevent CommonMark
    from interpreting indented HTML/SVG as an indented code block (<pre><code>).
    """
    if not html_str:
        return
    cleaned = textwrap.dedent(html_str).strip()
    compact = "\n".join(line.strip() for line in cleaned.splitlines() if line.strip())
    st.markdown(compact, unsafe_allow_html=True)


def inject_cyber_theme():
    """Injects centralized modern cybersecurity CSS into Streamlit."""
    render_html("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        /* ========================================================
           GLOBAL DESIGN TOKENS & RESET
           ======================================================== */
        :root {
            --bg-base: #060a14;
            --bg-surface: #0a1020;
            --bg-card: rgba(13, 22, 42, 0.75);
            --bg-card-hover: rgba(20, 33, 62, 0.85);
            --border-subtle: rgba(56, 189, 248, 0.16);
            --border-glow: rgba(56, 189, 248, 0.45);
            --cyan-accent: #06b6d4;
            --cyan-glow: rgba(6, 182, 212, 0.35);
            --blue-accent: #0284c7;
            --sky-accent: #38bdf8;
            --emerald-accent: #10b981;
            --emerald-glow: rgba(16, 185, 129, 0.3);
            --amber-accent: #f59e0b;
            --rose-accent: #f43f5e;
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }

        /* Streamlit App Background with subtle cyber grid & radial glows */
        .stApp {
            background-color: #060a14 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(14, 165, 233, 0.14) 0px, transparent 48%),
                radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 45%),
                radial-gradient(at 50% 100%, rgba(6, 182, 212, 0.09) 0px, transparent 52%),
                linear-gradient(rgba(56, 189, 248, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(56, 189, 248, 0.02) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 100% 100%, 36px 36px, 36px 36px !important;
            color: #f1f5f9 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }

        [data-testid="stHeader"] {
            background: rgba(6, 10, 20, 0.75) !important;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(56, 189, 248, 0.12) !important;
        }

        .block-container {
            max-width: 1320px;
            padding-top: 1.6rem;
            padding-bottom: 3.5rem;
        }

        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
        }

        p, span, label, div {
            color: #cbd5e1;
            font-family: 'Inter', sans-serif;
        }

        .stCaption, [data-testid="stCaptionContainer"] {
            color: #94a3b8 !important;
            font-size: 12px !important;
        }

        /* ========================================================
           CYBER CARDS & GLASSMORPHISM
           ======================================================== */
        .secure-card, .cyber-card, .glass-panel {
            background: var(--bg-card) !important;
            backdrop-filter: blur(16px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
            border: 1px solid var(--border-subtle) !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.38), inset 0 0 12px 0 rgba(56, 189, 248, 0.04) !important;
            border-radius: 14px !important;
            padding: 18px 22px !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        .secure-card:hover, .cyber-card:hover, .glass-panel:hover {
            border-color: var(--border-glow) !important;
            box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.5), inset 0 0 18px 0 rgba(56, 189, 248, 0.08) !important;
            transform: translateY(-2px);
        }

        /* Metric Cards */
        .metric-card {
            background: linear-gradient(135deg, rgba(13, 22, 42, 0.85) 0%, rgba(18, 30, 58, 0.7) 100%) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(56, 189, 248, 0.18) !important;
            border-radius: 14px !important;
            padding: 18px 20px !important;
            position: relative;
            overflow: hidden;
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .metric-card:hover {
            border-color: #38bdf8 !important;
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(6, 182, 212, 0.22), inset 0 0 14px rgba(56, 189, 248, 0.08);
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #06b6d4, #38bdf8, transparent);
            opacity: 0.75;
        }
        .metric-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .metric-label {
            font-size: 11.5px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        .metric-icon {
            font-size: 20px;
            filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.5));
        }
        .metric-value {
            font-size: 32px;
            font-weight: 800;
            color: #f8fafc;
            line-height: 1.1;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: -0.03em;
        }

        /* Action Cards */
        .action-card {
            background: rgba(13, 22, 42, 0.75) !important;
            border: 1px solid rgba(56, 189, 248, 0.18) !important;
            border-radius: 12px !important;
            padding: 14px 18px !important;
            transition: all 0.25s ease !important;
        }
        .action-card:hover {
            border-color: #38bdf8 !important;
            box-shadow: 0 8px 24px rgba(6, 182, 212, 0.25) !important;
            transform: translateY(-2px);
        }

        /* Section Title & Headers */
        .section-title {
            font-size: 15px;
            font-weight: 700;
            color: #f8fafc !important;
            letter-spacing: -0.2px;
            margin: 18px 0 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Status Badges */
        .status-pill, .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11.5px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .pill-secure {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34d399;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);
        }
        .pill-warning {
            background: rgba(245, 158, 11, 0.12);
            border: 1px solid rgba(245, 158, 11, 0.35);
            color: #fbbf24;
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.15);
        }
        .pill-danger {
            background: rgba(244, 63, 94, 0.12);
            border: 1px solid rgba(244, 63, 94, 0.35);
            color: #fb7185;
            box-shadow: 0 0 10px rgba(244, 63, 94, 0.15);
        }
        .pill-cyber {
            background: rgba(6, 182, 212, 0.12);
            border: 1px solid rgba(6, 182, 212, 0.35);
            color: #38bdf8;
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.15);
        }
        .pill-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            display: inline-block;
        }
        .dot-green { background: #10b981; box-shadow: 0 0 6px #10b981; }
        .dot-amber { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
        .dot-red { background: #f43f5e; box-shadow: 0 0 6px #f43f5e; }
        .dot-blue { background: #06b6d4; box-shadow: 0 0 6px #06b6d4; }

        /* Masked Password text */
        .masked-pass {
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 2.5px;
            color: #64748b;
            font-size: 13px;
        }

        /* ========================================================
           INPUT FIELDS, SELECTBOXES & TEXTAREAS
           ======================================================== */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div {
            background: rgba(13, 22, 42, 0.82) !important;
            border: 1px solid rgba(56, 189, 248, 0.22) !important;
            border-radius: 10px !important;
            color: #f8fafc !important;
            box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.4) !important;
            transition: all 0.2s ease !important;
        }
        div[data-baseweb="input"]:focus-within > div,
        div[data-baseweb="select"]:focus-within > div,
        div[data-baseweb="textarea"]:focus-within > div {
            border-color: #06b6d4 !important;
            box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.3), inset 0 2px 5px rgba(0, 0, 0, 0.4) !important;
        }
        input, textarea {
            color: #f8fafc !important;
            background: transparent !important;
            font-size: 13.5px !important;
        }
        input::placeholder, textarea::placeholder {
            color: #64748b !important;
        }
        .stTextInput label, .stSelectbox label, .stTextArea label, .stDateInput label {
            color: #cbd5e1 !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
            letter-spacing: 0.3px;
        }

        /* Streamlit Select dropdown popover */
        div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
            background: #091122 !important;
            border: 1px solid rgba(56, 189, 248, 0.28) !important;
            border-radius: 10px !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6) !important;
        }
        li[role="option"] {
            color: #cbd5e1 !important;
            background: transparent !important;
        }
        li[role="option"]:hover, li[aria-selected="true"] {
            background: rgba(14, 165, 233, 0.18) !important;
            color: #38bdf8 !important;
        }

        /* ========================================================
           BUTTONS & ACTIONS
           ======================================================== */
        .stButton > button {
            background: linear-gradient(180deg, rgba(26, 38, 64, 0.85) 0%, rgba(13, 22, 42, 0.95) 100%) !important;
            color: #f1f5f9 !important;
            border: 1px solid rgba(56, 189, 248, 0.22) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 8px 16px !important;
            min-height: 40px !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }
        .stButton > button:hover {
            background: linear-gradient(180deg, rgba(40, 58, 96, 0.95) 0%, rgba(20, 34, 62, 1) 100%) !important;
            border-color: #38bdf8 !important;
            color: #38bdf8 !important;
            box-shadow: 0 4px 18px rgba(56, 189, 248, 0.25) !important;
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #0f766e 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(56, 189, 248, 0.5) !important;
            box-shadow: 0 4px 16px rgba(14, 165, 233, 0.35) !important;
            font-weight: 600 !important;
        }
        .stButton > button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #14b8a6 100%) !important;
            border-color: #7dd3fc !important;
            box-shadow: 0 6px 24px rgba(14, 165, 233, 0.5) !important;
            color: #ffffff !important;
            transform: translateY(-1px);
        }

        /* Download button */
        .stDownloadButton > button {
            background: linear-gradient(180deg, rgba(26, 38, 64, 0.85) 0%, rgba(13, 22, 42, 0.95) 100%) !important;
            color: #38bdf8 !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            min-height: 40px !important;
        }
        .stDownloadButton > button:hover {
            border-color: #38bdf8 !important;
            box-shadow: 0 4px 18px rgba(56, 189, 248, 0.25) !important;
        }

        /* ========================================================
           TABS & EXPANDERS
           ======================================================== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: transparent;
            border-bottom: 1px solid rgba(56, 189, 248, 0.16);
            padding-bottom: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(13, 22, 42, 0.6) !important;
            border: 1px solid rgba(56, 189, 248, 0.14) !important;
            border-bottom: none !important;
            border-radius: 8px 8px 0 0 !important;
            color: #94a3b8 !important;
            padding: 9px 18px !important;
            font-weight: 500 !important;
            font-size: 13.5px !important;
            transition: all 0.2s ease !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #f1f5f9 !important;
            border-color: rgba(56, 189, 248, 0.3) !important;
            background: rgba(26, 38, 64, 0.7) !important;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(14, 165, 233, 0.16) !important;
            border-color: #38bdf8 !important;
            color: #38bdf8 !important;
            font-weight: 700 !important;
            box-shadow: 0 -2px 14px rgba(56, 189, 248, 0.2) !important;
        }

        div[data-testid="stExpander"] {
            background: rgba(13, 22, 42, 0.65) !important;
            border: 1px solid rgba(56, 189, 248, 0.16) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        }
        div[data-testid="stExpander"] summary {
            color: #e2e8f0 !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
        }
        div[data-testid="stExpander"] summary:hover {
            color: #38bdf8 !important;
        }

        /* Streamlit Bordered Container Override */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid rgba(56, 189, 248, 0.18) !important;
            border-radius: 14px !important;
            background: rgba(13, 22, 42, 0.7) !important;
            backdrop-filter: blur(14px) !important;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3) !important;
        }

        /* Tables & Dataframes */
        .stDataFrame, div[data-testid="stDataFrame"] {
            background: rgba(13, 22, 42, 0.6) !important;
            border: 1px solid rgba(56, 189, 248, 0.16) !important;
            border-radius: 10px !important;
            overflow: hidden;
        }

        /* Streamlit Alerts / Info / Warning / Error */
        div[data-testid="stAlert"] {
            border-radius: 10px !important;
            backdrop-filter: blur(12px) !important;
        }
        div[data-testid="stAlert"][data-baseweb="notification"] {
            background-color: rgba(13, 22, 42, 0.85) !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
        }

        /* Custom Scrollbars */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #060a14;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(56, 189, 248, 0.25);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(56, 189, 248, 0.45);
        }

        /* ========================================================
           3D CYBER ANIMATIONS
           ======================================================== */
        @keyframes float-subtle {
            0%, 100% { transform: translateY(0px) rotateY(0deg); }
            50% { transform: translateY(-4px) rotateY(4deg); }
        }
        @keyframes cyber-glow {
            0%, 100% { filter: drop-shadow(0 0 8px rgba(6, 182, 212, 0.35)); }
            50% { filter: drop-shadow(0 0 18px rgba(6, 182, 212, 0.75)); }
        }
        @keyframes vault-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .element-3d-wrapper {
            perspective: 800px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            animation: float-subtle 4s ease-in-out infinite;
        }
        .element-3d-box {
            position: relative;
            transform-style: preserve-3d;
            animation: cyber-glow 3.5s ease-in-out infinite;
        }

        /* Hide Streamlit default branding */
        #MainMenu, footer, header { visibility: hidden; }
        div[data-testid="stToolbar"] { visibility: hidden; }
    </style>
    """)


# ============================================================
# 3D SECURITY ELEMENTS (Requirement 8)
# ============================================================

def render_3d_shield(size=56):
    """Renders a subtle 3D cybersecurity shield SVG with holographic depth and glow."""
    return (
        f'<div class="element-3d-wrapper"><div class="element-3d-box">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#38bdf8"/>'
        f'<stop offset="50%" stop-color="#0284c7"/>'
        f'<stop offset="100%" stop-color="#091122"/>'
        f'</linearGradient>'
        f'<linearGradient id="innerFacet" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#06b6d4" stop-opacity="0.6"/>'
        f'<stop offset="100%" stop-color="#0284c7" stop-opacity="0.1"/>'
        f'</linearGradient>'
        f'<linearGradient id="coreGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#ffffff"/>'
        f'<stop offset="100%" stop-color="#7dd3fc"/>'
        f'</linearGradient>'
        f'<filter id="shieldGlow" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feGaussianBlur stdDeviation="2.5" result="blur"/>'
        f'<feComposite in="SourceGraphic" in2="blur" operator="over"/>'
        f'</filter>'
        f'</defs>'
        f'<path d="M32 4L10 13V28C10 44 19.5 54 32 60C44.5 54 54 44 54 28V13L32 4Z" fill="url(#shieldGrad)" stroke="#38bdf8" stroke-width="1.6" filter="url(#shieldGlow)"/>'
        f'<path d="M32 7L13 15V28C13 41.5 21 50 32 55.5V7Z" fill="url(#innerFacet)"/>'
        f'<circle cx="32" cy="27" r="5" fill="url(#coreGrad)"/>'
        f'<path d="M29.5 29L28 39H36L34.5 29Z" fill="url(#coreGrad)"/>'
        f'<circle cx="32" cy="45" r="2" fill="#38bdf8"/>'
        f'<path d="M32 39V43" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="1 1"/>'
        f'</svg></div></div>'
    )


def render_3d_lock(size=56):
    """Renders a subtle 3D padlock SVG with illuminated cyber shackle."""
    return (
        f'<div class="element-3d-wrapper"><div class="element-3d-box">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<linearGradient id="lockBodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#1e293b"/>'
        f'<stop offset="50%" stop-color="#0f172a"/>'
        f'<stop offset="100%" stop-color="#0284c7"/>'
        f'</linearGradient>'
        f'<linearGradient id="shackleGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#38bdf8"/>'
        f'<stop offset="100%" stop-color="#0284c7"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<path d="M22 28V18C22 12.477 26.477 8 32 8C37.523 8 42 12.477 42 18V28" stroke="url(#shackleGrad)" stroke-width="4.5" stroke-linecap="round"/>'
        f'<rect x="14" y="26" width="36" height="30" rx="7" fill="url(#lockBodyGrad)" stroke="#38bdf8" stroke-width="1.5"/>'
        f'<circle cx="32" cy="38" r="3.5" fill="#38bdf8"/>'
        f'<path d="M30.5 40L29.5 47H34.5L33.5 40Z" fill="#38bdf8"/>'
        f'</svg></div></div>'
    )


def render_3d_vault(size=56):
    """Renders a 3D digital vault door with rotating bolts and cyber circuits."""
    return (
        f'<div class="element-3d-wrapper"><div class="element-3d-box">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<linearGradient id="vaultOuter" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#0f172a"/>'
        f'<stop offset="50%" stop-color="#1e293b"/>'
        f'<stop offset="100%" stop-color="#0284c7"/>'
        f'</linearGradient>'
        f'<linearGradient id="vaultRim" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#38bdf8"/>'
        f'<stop offset="100%" stop-color="#06b6d4"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<rect x="6" y="6" width="52" height="52" rx="12" fill="#091122" stroke="url(#vaultRim)" stroke-width="1.8"/>'
        f'<circle cx="32" cy="32" r="20" fill="url(#vaultOuter)" stroke="#38bdf8" stroke-width="2"/>'
        f'<circle cx="32" cy="32" r="14" stroke="#06b6d4" stroke-width="1" stroke-dasharray="3 3"/>'
        f'<circle cx="32" cy="32" r="6" fill="#38bdf8"/>'
        f'<path d="M32 18V26M32 38V46M18 32H26M38 32H46" stroke="#f8fafc" stroke-width="2.5" stroke-linecap="round"/>'
        f'</svg></div></div>'
    )


def render_3d_team(size=48):
    """Renders a subtle 3D holographic team node group badge."""
    return (
        f'<div class="element-3d-wrapper"><div class="element-3d-box">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<linearGradient id="teamGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#38bdf8"/>'
        f'<stop offset="100%" stop-color="#0284c7"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<circle cx="32" cy="22" r="7" fill="url(#teamGrad)" stroke="#7dd3fc" stroke-width="1.5"/>'
        f'<path d="M20 46C20 39 25 35 32 35C39 35 44 39 44 46" fill="rgba(14, 165, 233, 0.25)" stroke="#38bdf8" stroke-width="1.5"/>'
        f'<circle cx="16" cy="26" r="5" fill="#0ea5e9" opacity="0.8"/>'
        f'<path d="M8 47C8 42 11 39 16 39C19 39 21.5 40.5 23 43" stroke="#0ea5e9" stroke-width="1.2" opacity="0.8"/>'
        f'<circle cx="48" cy="26" r="5" fill="#0ea5e9" opacity="0.8"/>'
        f'<path d="M56 47C56 42 53 39 48 39C45 39 42.5 40.5 41 43" stroke="#0ea5e9" stroke-width="1.2" opacity="0.8"/>'
        f'</svg></div></div>'
    )


# ============================================================
# CRYPTOGRAPHIC VISUALIZATION PIPELINE (Requirement 10)
# ============================================================

def render_encryption_pipeline():
    """Renders visual architecture explaining vault security flow."""
    return (
        '<div class="glass-panel" style="padding: 16px 20px; margin-top: 10px;">'
        '<div style="font-size: 11.5px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">'
        '<span>🛡️</span> Zero-Knowledge Cryptographic Architecture'
        '</div>'
        '<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">'
        '<div style="text-align: center; flex: 1; min-width: 85px; background: rgba(13, 22, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 10px; padding: 10px 6px;">'
        '<div style="font-size: 18px; margin-bottom: 2px;">👤</div>'
        '<div style="font-size: 11px; font-weight: 600; color: #f1f5f9;">User Password</div>'
        '</div>'
        '<div style="color: #06b6d4; font-size: 15px; font-weight: 800;">↓</div>'
        '<div style="text-align: center; flex: 1; min-width: 85px; background: rgba(13, 22, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 10px; padding: 10px 6px;">'
        '<div style="font-size: 18px; margin-bottom: 2px;">🛡️</div>'
        '<div style="font-size: 11px; font-weight: 600; color: #f1f5f9;">Argon2id</div>'
        '</div>'
        '<div style="color: #06b6d4; font-size: 15px; font-weight: 800;">↓</div>'
        '<div style="text-align: center; flex: 1; min-width: 85px; background: rgba(13, 22, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 10px; padding: 10px 6px;">'
        '<div style="font-size: 18px; margin-bottom: 2px;">🔑</div>'
        '<div style="font-size: 11px; font-weight: 600; color: #f1f5f9;">256-bit Key</div>'
        '</div>'
        '<div style="color: #06b6d4; font-size: 15px; font-weight: 800;">↓</div>'
        '<div style="text-align: center; flex: 1; min-width: 85px; background: rgba(13, 22, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 10px; padding: 10px 6px;">'
        '<div style="font-size: 18px; margin-bottom: 2px;">🔐</div>'
        '<div style="font-size: 11px; font-weight: 600; color: #f1f5f9;">AES-256-GCM</div>'
        '</div>'
        '<div style="color: #06b6d4; font-size: 15px; font-weight: 800;">↓</div>'
        '<div style="text-align: center; flex: 1; min-width: 85px; background: rgba(13, 22, 42, 0.7); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 10px 6px;">'
        '<div style="font-size: 18px; margin-bottom: 2px;">🗄️</div>'
        '<div style="font-size: 11px; font-weight: 600; color: #34d399;">Encrypted Vault Data</div>'
        '</div>'
        '</div>'
        '</div>'
    )


# ============================================================
# SECURITY STATUS WIDGET (Requirement 9)
# ============================================================

def render_security_status_widget():
    """Renders compact Security Status widget with verified application states."""
    return (
        '<div class="glass-panel" style="padding: 14px 18px; margin-bottom: 18px;">'
        '<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">'
        '<div style="font-size: 13.5px; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 8px;">'
        '<span>🛡️</span> Security Status'
        '</div>'
        '<div class="status-pill pill-secure">'
        '<span class="pill-dot dot-green"></span> All Systems Operational'
        '</div>'
        '</div>'
        '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px;">'
        '<div style="background: rgba(13, 22, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 9px; padding: 9px 12px; display: flex; align-items: center; gap: 10px;">'
        '<span class="pill-dot dot-green"></span>'
        '<div>'
        '<div style="font-size: 12px; font-weight: 600; color: #f1f5f9;">Authentication Protected</div>'
        '<div style="font-size: 10.5px; color: #94a3b8;">Argon2id + Secure Session</div>'
        '</div>'
        '</div>'
        '<div style="background: rgba(13, 22, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 9px; padding: 9px 12px; display: flex; align-items: center; gap: 10px;">'
        '<span class="pill-dot dot-green"></span>'
        '<div>'
        '<div style="font-size: 12px; font-weight: 600; color: #f1f5f9;">Vault Encryption Active</div>'
        '<div style="font-size: 10.5px; color: #94a3b8;">AES-256-GCM Hardware-Acc.</div>'
        '</div>'
        '</div>'
        '<div style="background: rgba(13, 22, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 9px; padding: 9px 12px; display: flex; align-items: center; gap: 10px;">'
        '<span class="pill-dot dot-green"></span>'
        '<div>'
        '<div style="font-size: 12px; font-weight: 600; color: #f1f5f9;">Audit Logging Active</div>'
        '<div style="font-size: 10.5px; color: #94a3b8;">Immutable Event Stream</div>'
        '</div>'
        '</div>'
        '<div style="background: rgba(13, 22, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 9px; padding: 9px 12px; display: flex; align-items: center; gap: 10px;">'
        '<span class="pill-dot dot-green"></span>'
        '<div>'
        '<div style="font-size: 12px; font-weight: 600; color: #f1f5f9;">Notification Security Active</div>'
        '<div style="font-size: 10.5px; color: #94a3b8;">Real-time Alert Dispatch</div>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )
