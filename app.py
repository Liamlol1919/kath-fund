"""
===============================================================================
                     KATH. FUND - DIGITALE FUNDBÜRO APP
===============================================================================
Inspirationsbasis: Originale Papier-Skizze (Kath. Fund Layout & Workflow)
Optimiert für Streamlit >= 1.40
KI-Modell: MobileNetV2 (optional, sonst Heuristik)
===============================================================================
"""

import os
import io
import json
import base64
import html
import datetime
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import numpy as np
import pandas as pd

# =============================================================================
# 1. STREAMLIT CONFIG & CUSTOM STYLING
# =============================================================================

st.set_page_config(
    page_title="Kath. Fund - Fundbüro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Archivo:wght@500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --paper: #F2EEE3;
        --card: #FFFCF4;
        --field: #FFFDF7;
        --ink: #16130E;
        --ink-2: #3B362C;
        --ink-soft: #6B6353;
        --line: #DCD4BF;
        --red: #B23A2A;
        --green: #2C6B37;
        --blue: #2B4C7E;
        --amber: #94641A;
        --hard: 3px 3px 0 rgba(22, 19, 14, .16);
    }

    ::selection { background: var(--red); color: #FFF7EE; }
    html { font-size: 16.5px; }

    /* ================= Grundfläche ================= */
    [data-testid="stAppViewContainer"] {
        background-color: var(--paper);
        background-image: radial-gradient(#E3DAC2 1px, transparent 1.2px);
        background-size: 22px 22px;
    }
    .block-container, [data-testid="stMainBlockContainer"] {
        max-width: 1560px !important;
        padding: 1.1rem 1.9rem 3.5rem !important;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        color: var(--ink);
    }
    /* dichter, aber großzügig groß */
    [data-testid="stVerticalBlock"] { gap: .5rem; }
    [data-testid="stHorizontalBlock"] { gap: .7rem; }
    hr { border: none; border-top: 1px solid var(--line); margin: 1rem 0; }

    /* ================= Streamlit-Chrome weg ================= */
    #MainMenu, footer,
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stAppDeployButton"] { display: none !important; visibility: hidden !important; }

    /* ================= Masthead ================= */
    .mast { padding-bottom: 12px; border-bottom: 3px double var(--ink); }
    .mast .kicker {
        display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center;
        font-family: 'IBM Plex Mono', monospace; font-size: .66rem;
        letter-spacing: .16em; text-transform: uppercase; color: var(--ink-soft);
    }
    .mast .kicker em { font-style: normal; color: var(--red); font-weight: 600; }
    .mast h1 {
        font-family: 'Archivo Black', sans-serif; font-weight: 400;
        font-size: clamp(2.4rem, 3.6vw, 3.4rem); line-height: .98;
        letter-spacing: -.025em; margin: .3rem 0 .25rem;
    }
    .mast .sub { font-size: .98rem; color: var(--ink-soft); }
    .mast .sub b { color: var(--ink); font-weight: 600; }

    /* ================= Kennzahlen-Leiste ================= */
    .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 10px; margin: 14px 0 16px; }
    .kpi {
        background: var(--card); border: 1.5px solid var(--ink); border-radius: 10px;
        padding: 9px 13px 10px; box-shadow: var(--hard);
    }
    .kpi span {
        display: block; font-family: 'IBM Plex Mono', monospace; font-size: .62rem;
        letter-spacing: .12em; text-transform: uppercase; color: var(--ink-soft);
    }
    .kpi b { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.85rem; line-height: 1.15; letter-spacing: -.02em; }
    .kpi.accent { background: var(--ink); border-color: var(--ink); }
    .kpi.accent span { color: #B9AF95; }
    .kpi.accent b { color: var(--paper); }

    /* ================= Chip-Gruppen (Radio) ================= */
    div[data-testid="stRadio"] [role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 7px; }
    div[data-testid="stRadio"] [role="radiogroup"] > label {
        margin: 0; padding: 7px 14px; border: 1.5px solid var(--line); border-radius: 999px;
        background: var(--card); cursor: pointer; transition: all .12s ease;
        box-shadow: 0 1px 0 rgba(22, 19, 14, .05);
    }
    div[data-testid="stRadio"] [role="radiogroup"] > label > span:first-child { display: none; }
    div[data-testid="stRadio"] [role="radiogroup"] > label > div > div > div:first-child { display: none; }
    div[data-testid="stRadio"] [role="radiogroup"] > label[data-selected="true"] {
        background: var(--ink); border-color: var(--ink); box-shadow: 3px 3px 0 rgba(22, 19, 14, .22);
    }
    div[data-testid="stRadio"] [role="radiogroup"] > label[data-selected="true"] p { color: var(--paper) !important; }
    div[data-testid="stRadio"] [role="radiogroup"] > label p {
        font-family: 'IBM Plex Mono', monospace !important; font-size: .72rem !important;
        font-weight: 600 !important; letter-spacing: .07em !important; text-transform: uppercase;
        color: var(--ink-soft) !important; margin: 0 !important; line-height: 1.2;
    }
    div[data-testid="stRadio"] [role="radiogroup"] > label:hover { border-color: var(--ink); }
    div[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {
        background: var(--ink); border-color: var(--ink); box-shadow: 3px 3px 0 rgba(22, 19, 14, .22);
    }
    div[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) p { color: var(--paper) !important; }

    /* Hauptnavigation: groß und unübersehbar */
    .st-key-nav [role="radiogroup"] > label, .st-key-navwrap [role="radiogroup"] > label { padding: 11px 24px; border-width: 2px; border-radius: 10px; }
    .st-key-nav [role="radiogroup"] > label p, .st-key-navwrap [role="radiogroup"] > label p { font-size: .84rem !important; letter-spacing: .1em !important; }
    .st-key-nav [role="radiogroup"], .st-key-navwrap [role="radiogroup"] { gap: 9px; padding-bottom: 2px; }

    /* Ansichtsmodus laut Skizze */
    .st-key-modefilter [role="radiogroup"] > label { padding: 9px 18px; }
    .st-key-modefilter [role="radiogroup"] > label p { font-size: .76rem !important; }
    .st-key-layoutsel [role="radiogroup"] { justify-content: flex-end; }

    /* ================= Abschnittsköpfe ================= */
    .sec { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin: 16px 0 4px; }
    .sec h2 { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.55rem; letter-spacing: -.02em; margin: 0; }
    .sec .tag {
        font-family: 'IBM Plex Mono', monospace; font-size: .64rem; letter-spacing: .14em;
        text-transform: uppercase; color: var(--ink-soft);
        border: 1px solid var(--line); border-radius: 4px; padding: 2px 8px;
    }
    .sec-note { font-family: 'IBM Plex Mono', monospace; font-size: .72rem; color: var(--ink-soft); margin-bottom: 14px; }
    .sec-note b { color: var(--ink); }
    .ctl-lbl {
        font-family: 'IBM Plex Mono', monospace; font-size: .62rem; letter-spacing: .14em;
        text-transform: uppercase; color: var(--ink-soft); margin-bottom: 4px;
    }
    .stMarkdown h4 {
        font-family: 'IBM Plex Mono', monospace !important; font-size: .72rem !important;
        letter-spacing: .14em !important; text-transform: uppercase !important;
        color: var(--ink-soft) !important; margin: .9rem 0 .2rem !important;
    }
    .stMarkdown h5 { font-family: 'Archivo', sans-serif; font-weight: 700; font-size: 1rem; }
    .stMarkdown p { font-size: .94rem; }
    [data-testid="stCaptionContainer"] { font-family: 'IBM Plex Mono', monospace; font-size: .7rem; color: var(--ink-soft); }

    /* ================= Belegkarte ================= */
    .ticket {
        background: var(--card); border: 1.5px solid var(--ink); border-radius: 11px;
        overflow: hidden; box-shadow: var(--hard); display: flex; flex-direction: column; height: 100%;
    }
    .ticket-head {
        display: flex; justify-content: space-between; align-items: center; gap: 8px;
        padding: 8px 12px; background: #F5EFDC; border-bottom: 1.5px solid var(--ink);
    }
    .ticket-id { font-family: 'IBM Plex Mono', monospace; font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-soft); }
    .ticket-photo { position: relative; }
    .ticket-photo img { display: block; width: 100%; height: 218px; object-fit: cover; border-bottom: 1.5px solid var(--ink); }
    .ticket-photo.ph {
        height: 218px; display: grid; place-items: center; border-bottom: 1.5px solid var(--ink);
        background: repeating-linear-gradient(45deg, #EFE8D2 0 11px, #F8F3E4 11px 22px);
        font-family: 'IBM Plex Mono', monospace; font-size: .74rem; letter-spacing: .14em;
        text-transform: uppercase; color: #9A9078; text-align: center; padding: 0 18px;
    }
    .ticket-body { padding: 12px 13px 13px; display: flex; flex-direction: column; flex: 1; }
    .ticket-title { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.16rem; letter-spacing: -.015em; line-height: 1.22; margin-bottom: 9px; }
    .tgrid { display: grid; grid-template-columns: auto 1fr; gap: 4px 10px; margin-bottom: 10px; }
    .tgrid dt { font-family: 'IBM Plex Mono', monospace; font-size: .62rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-soft); padding-top: 2px; }
    .tgrid dd { font-size: .86rem; font-weight: 600; text-align: right; margin: 0; }
    .tdesc { font-size: .84rem; color: var(--ink-2); line-height: 1.45; border-top: 1px dotted var(--line); padding-top: 8px; margin-bottom: 9px; }
    .tchips { margin-top: auto; }
    .chip {
        display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: .64rem;
        letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2);
        border: 1px solid var(--line); border-radius: 4px; padding: 2px 7px;
        margin: 0 5px 5px 0; background: var(--field);
    }

    /* ================= Stempel ================= */
    .stamp {
        display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: .62rem;
        font-weight: 600; letter-spacing: .12em; text-transform: uppercase; white-space: nowrap;
        padding: 3px 9px; border: 1.5px solid currentColor; border-radius: 4px;
        box-shadow: inset 0 0 0 2px var(--card), inset 0 0 0 3.5px currentColor;
        transform: rotate(-3deg); background: var(--card);
    }
    .s-offen { color: var(--amber); } .s-beansprucht { color: var(--blue); }
    .s-abgeholt { color: var(--green); } .s-entsorgt { color: var(--red); }
    .newflag {
        display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: .58rem;
        letter-spacing: .12em; text-transform: uppercase; color: var(--red);
        border: 1px solid var(--red); border-radius: 3px; padding: 1px 6px; margin-left: 6px;
    }

    /* ================= Listenansicht ================= */
    .row-item {
        display: flex; gap: 15px; align-items: center; background: var(--card);
        border: 1.5px solid var(--ink); border-radius: 11px; padding: 10px 15px;
        box-shadow: var(--hard); margin-bottom: 9px;
    }
    .row-item img.thumb { width: 84px; height: 84px; object-fit: cover; border-radius: 8px; border: 1.5px solid var(--line); flex: none; }
    .row-item .thumb.ph {
        width: 84px; height: 84px; flex: none; border-radius: 8px; border: 1.5px solid var(--line);
        display: grid; place-items: center; text-align: center;
        background: repeating-linear-gradient(45deg, #EFE8D2 0 8px, #F8F3E4 8px 16px);
        font-family: 'IBM Plex Mono', monospace; font-size: .5rem; letter-spacing: .08em;
        text-transform: uppercase; color: #9A9078; padding: 4px;
    }
    .ri-main { flex: 1; min-width: 0; }
    .ri-title { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.12rem; letter-spacing: -.015em; }
    .ri-meta { font-family: 'IBM Plex Mono', monospace; font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; color: var(--ink-soft); margin-top: 3px; }
    .ri-desc { font-size: .84rem; color: var(--ink-2); margin-top: 5px; }

    /* ================= Hinweise / Prüfvermerk ================= */
    .note { border-left: 3px solid var(--ink); background: #F5EFDC; padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: .88rem; margin-bottom: 12px; }
    .note span { display: block; color: var(--ink-soft); font-size: .8rem; margin-top: 2px; }
    .verdict {
        display: flex; gap: 15px; align-items: center; background: var(--card);
        border: 1.5px solid var(--ink); border-radius: 11px; padding: 14px 17px; margin-top: 13px; box-shadow: var(--hard);
    }
    .verdict-stamp {
        font-family: 'IBM Plex Mono', monospace; text-transform: uppercase; font-size: .66rem;
        letter-spacing: .12em; color: var(--red); border: 2px solid var(--red); border-radius: 6px;
        padding: 8px 12px; transform: rotate(-4deg); white-space: nowrap; font-weight: 600;
        box-shadow: inset 0 0 0 2px var(--card), inset 0 0 0 3.5px var(--red);
    }
    .verdict-cat { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.16rem; letter-spacing: -.015em; }
    .verdict-meta { font-family: 'IBM Plex Mono', monospace; font-size: .7rem; color: var(--ink-soft); margin-top: 3px; }
    .ai-result-card {
        background: var(--card); border: 1.5px solid var(--ink); border-radius: 10px;
        padding: 13px 15px; box-shadow: var(--hard); margin-top: 10px;
    }
    .ai-result-card .result-label { font-family: 'IBM Plex Mono', monospace; font-size: .62rem; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-soft); }
    .ai-result-card .result-title { font-family: 'Archivo', sans-serif; font-size: 1.2rem; font-weight: 800; margin-top: 3px; }
    .ai-result-card .result-meta { font-family: 'IBM Plex Mono', monospace; font-size: .68rem; color: var(--ink-soft); margin-top: 3px; }
    .ai-warn { border-left: 3px solid var(--amber); background: #F5EFDC; padding: 9px 12px; font-size: .8rem; color: var(--ink-2); margin-top: 9px; border-radius: 0 6px 6px 0; }

    /* ================= Formulare & Buttons ================= */
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button,
    [data-testid="stFileUploader"] button, [data-testid="stCameraInput"] button {
        font-family: 'IBM Plex Mono', monospace !important; text-transform: uppercase !important;
        letter-spacing: .1em !important; font-size: .71rem !important; font-weight: 600 !important;
        background: var(--card) !important; color: var(--ink) !important;
        border: 1.5px solid var(--ink) !important; border-radius: 8px !important;
        box-shadow: 3px 3px 0 var(--ink); padding: .62rem 1.1rem !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        transform: translate(-1px, -1px); box-shadow: 4px 4px 0 var(--ink);
    }
    .stButton > button:active, .stDownloadButton > button:active, [data-testid="stFormSubmitButton"] > button:active {
        transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--ink);
    }
    [data-testid="stFormSubmitButton"] > button { background: var(--red) !important; border-color: var(--red) !important; color: #FFF6EA !important; box-shadow: 3px 3px 0 rgba(22,19,14,.5); }
    .stDownloadButton > button { background: var(--ink) !important; color: var(--paper) !important; }
    .st-key-cta_new button { background: var(--ink) !important; color: var(--paper) !important; }

    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div, div[data-testid="stNumberInput"] input {
        background: var(--field) !important; border: 1.5px solid var(--line) !important;
        border-radius: 8px !important; font-size: .92rem !important; color: var(--ink) !important;
        min-height: 2.65rem;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: var(--ink) !important; box-shadow: 2px 2px 0 var(--ink) !important;
    }
    div[data-testid="stTextInput"] input::placeholder, div[data-testid="stTextArea"] textarea::placeholder { color: #A79D86; }
    /* Schnellsuche: groß */
    .st-key-q input { font-size: 1.05rem !important; min-height: 3.1rem; padding-left: .95rem !important; }
    .st-key-searchwrap input { font-size: 1.05rem !important; min-height: 3.1rem; padding-left: .95rem !important; }
    div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed var(--ink); background: var(--field); border-radius: 11px;
    }
    div[data-testid="stRadio"] label { font-size: .9rem; }
    input[type="radio"], input[type="checkbox"] { accent-color: var(--red); }

    /* ================= Tabs (Verwaltung) ================= */
    [data-testid="stTabs"] [role="tablist"] { display: flex; gap: 7px; border-bottom: 1.5px solid var(--ink); }
    [data-testid="stTabs"] [data-testid="stTab"] {
        font-family: 'IBM Plex Mono', monospace; font-size: .69rem; letter-spacing: .1em;
        text-transform: uppercase; color: var(--ink-soft); padding: 9px 15px;
        border: 1.5px solid transparent !important; border-bottom: none !important; border-radius: 8px 8px 0 0;
        box-shadow: none !important; background: transparent !important;
    }
    [data-testid="stTabs"] [data-testid="stTab"]::before, [data-testid="stTabs"] [data-testid="stTab"]::after { display: none !important; }
    [data-testid="stTabs"] [data-testid="stTab"][data-selected="true"] {
        color: var(--ink); background: var(--card) !important; border-color: var(--ink) !important;
        border-bottom: none !important; font-weight: 600;
    }

    /* ================= Sonstiges ================= */
    div[data-testid="stAlert"] { border: 1.5px solid var(--ink); border-radius: 9px; background: var(--card); box-shadow: var(--hard); }
    details[data-testid="stExpander"] { border: 1.5px solid var(--ink); border-radius: 9px; background: var(--card); }
    details[data-testid="stExpander"] summary { font-family: 'IBM Plex Mono', monospace; font-size: .71rem; letter-spacing: .08em; text-transform: uppercase; }
    details[data-testid="stExpander"] summary:hover { color: var(--red); }
    div[data-testid="stDataFrame"] { border: 1.5px solid var(--ink); border-radius: 9px; overflow: hidden; }
    div[data-testid="stImage"] figcaption { font-family: 'IBM Plex Mono', monospace; font-size: .68rem; color: var(--ink-soft); }
    div[data-testid="stSpinner"] p { font-family: 'IBM Plex Mono', monospace; font-size: .74rem; text-transform: uppercase; letter-spacing: .1em; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. DATA PERSISTENCE & SESSION ENGINE
# =============================================================================

STORAGE_DIR = Path("data")
STORAGE_DIR.mkdir(exist_ok=True)
IMG_DIR = STORAGE_DIR / "images"
IMG_DIR.mkdir(exist_ok=True)
ITEMS_FILE = STORAGE_DIR / "items.json"
CLAIMS_FILE = STORAGE_DIR / "claims.json"
LOGS_FILE = STORAGE_DIR / "logs.json"

CATEGORIES = [
    "Kleidung & Textilien",
    "Trinkflaschen & Brotdosen",
    "Rucksäcke & Taschen",
    "Elektronik & Kabel",
    "Schlüssel & Wertsachen",
    "Schulmaterial & Bücher",
    "Sportbekleidung",
    "Sonstiges"
]

LOCATIONS = [
    "Hauptgebäude - Foyer",
    "Pausenhof",
    "Sporthalle",
    "Mensa / Cafeteria",
    "Bibliothek",
    "Fachräume / MINT",
    "Musiksaal",
    "Unbekannt"
]

DEFAULT_ITEMS = [
    {
        "id": 1001,
        "titel": "Derbe Regenjacke Dunkelblau",
        "kategorie": "Kleidung & Textilien",
        "fundort": "Pausenhof",
        "abgabeort": "Hausmeisterbüro (Raum 001)",
        "kontakt_kuerzel": "S-MUELLER",
        "finder_rolle": "Schüler:in",
        "datum_fund": "2026-09-01",
        "datum_ablauf": "2026-12-01",
        "status": "Offen",
        "beschreibung": "Größe M, gelber Reißverschluss, Name im Etikett leicht verwischt.",
        "image_file": None,
        "tags": ["Jacke", "Blau", "Größe M"]
    },
    {
        "id": 1002,
        "titel": "AirPods Pro Case",
        "kategorie": "Elektronik & Kabel",
        "fundort": "Mensa / Cafeteria",
        "abgabeort": "Sekretariat (Tresor)",
        "kontakt_kuerzel": "HAUSMEISTER-K",
        "finder_rolle": "Hausmeister",
        "datum_fund": "2026-09-05",
        "datum_ablauf": "2026-12-05",
        "status": "Beansprucht",
        "beschreibung": "Kratzer auf der Rückseite, schwarze Silikon-Schutzhülle.",
        "image_file": None,
        "tags": ["Apple", "Audio", "Schwarz"]
    },
    {
        "id": 1003,
        "titel": "Edelstahl Trinkflasche 1L",
        "kategorie": "Trinkflaschen & Brotdosen",
        "fundort": "Sporthalle",
        "abgabeort": "Sporthalle Regallager",
        "kontakt_kuerzel": "L-SCHMIDT",
        "finder_rolle": "Lehrkraft",
        "datum_fund": "2026-08-28",
        "datum_ablauf": "2026-11-28",
        "status": "Abgeholt",
        "beschreibung": "Marke 720°DGREE, mattgrün mit Sport-Aufklebern.",
        "image_file": None,
        "tags": ["720°DGREE", "Grün", "Metall"]
    }
]

def load_json_file(file_path: Path, default_value):
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_value
    return default_value

def save_json_file(file_path: Path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")

if "fundstuecke_liste" not in st.session_state:
    st.session_state["fundstuecke_liste"] = load_json_file(ITEMS_FILE, DEFAULT_ITEMS)

if "claims" not in st.session_state:
    st.session_state["claims"] = load_json_file(CLAIMS_FILE, [
        {
            "claim_id": 501,
            "item_id": 1002,
            "name": "Lukas M. (9b)",
            "proof": "Seriennummer auf OVP vorhanden, kleine Macke am Scharnier.",
            "datum": "2026-09-06",
            "status": "In Prüfung"
        }
    ])

if "audit_logs" not in st.session_state:
    st.session_state["audit_logs"] = load_json_file(LOGS_FILE, [
        {"timestamp": "2026-09-01 08:30:00", "user": "SYSTEM", "action": "Datenbank gestartet"},
        {"timestamp": "2026-09-05 14:12:05", "user": "HAUSMEISTER-K", "action": "Fundstück #1002 angelegt"}
    ])

if "current_role" not in st.session_state:
    st.session_state["current_role"] = "Schüler:in"

if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False

if "search_input" not in st.session_state:
    st.session_state["search_input"] = ""

def sync_storage():
    save_json_file(ITEMS_FILE, st.session_state["fundstuecke_liste"])
    save_json_file(CLAIMS_FILE, st.session_state["claims"])
    save_json_file(LOGS_FILE, st.session_state["audit_logs"])

def log_action(user: str, action: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["audit_logs"].insert(0, {
        "timestamp": now,
        "user": user,
        "action": action
    })
    sync_storage()

def save_uploaded_image(pil_img: Image.Image, item_id: int) -> str:
    filename = f"item_{item_id}_{int(datetime.datetime.now().timestamp())}.jpg"
    filepath = IMG_DIR / filename
    pil_img.save(filepath, format="JPEG", quality=85)
    return filename

def load_item_image(filename: str):
    if not filename:
        return None
    filepath = IMG_DIR / filename
    if filepath.exists():
        try:
            return Image.open(filepath)
        except Exception:
            return None
    return None

def image_to_data_uri(pil_img: Image.Image, max_dim: int = 500) -> str:
    """Wandelt PIL Image in ein Data-URI um, damit HTML-Karten komplett custom gerendert werden können."""
    img = pil_img.copy()
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"

# =============================================================================
# 3. AI VISION ENGINE (OPTIONAL: MOBILENETV2, SONST HEURISTIK)
# =============================================================================

# Mapping von ImageNet-Klassen (MobileNetV2) auf unsere Kategorien
IMAGENET_CLASS_TO_CATEGORY = {
    # Kleidung
    "t-shirt": "Kleidung & Textilien",
    "jersey": "Kleidung & Textilien",
    "sweatshirt": "Kleidung & Textilien",
    "pullover": "Kleidung & Textilien",
    "cardigan": "Kleidung & Textilien",
    "sweater": "Kleidung & Textilien",
    "jacket": "Kleidung & Textilien",
    "coat": "Kleidung & Textilien",
    "jean": "Kleidung & Textilien",
    "trousers": "Kleidung & Textilien",
    "dress": "Kleidung & Textilien",
    "scarf": "Kleidung & Textilien",
    "hat": "Kleidung & Textilien",
    "glove": "Kleidung & Textilien",
    # Elektronik
    "ipad": "Elektronik & Kabel",
    "tablet": "Elektronik & Kabel",
    "laptop": "Elektronik & Kabel",
    "notebook": "Elektronik & Kabel",
    "computer": "Elektronik & Kabel",
    "keyboard": "Elektronik & Kabel",
    "mouse": "Elektronik & Kabel",
    "cellular telephone": "Elektronik & Kabel",
    "mobile phone": "Elektronik & Kabel",
    "smartphone": "Elektronik & Kabel",
    "headphone": "Elektronik & Kabel",
    "earphone": "Elektronik & Kabel",
    "microphone": "Elektronik & Kabel",
    "charger": "Elektronik & Kabel",
    "cable": "Elektronik & Kabel",
    "adapter": "Elektronik & Kabel",
    "camera": "Elektronik & Kabel",
    "smartwatch": "Elektronik & Kabel",
    # Taschen & Rucksäcke
    "backpack": "Rucksäcke & Taschen",
    "rucksack": "Rucksäcke & Taschen",
    "bag": "Rucksäcke & Taschen",
    "purse": "Rucksäcke & Taschen",
    "handbag": "Rucksäcke & Taschen",
    "wallet": "Rucksäcke & Taschen",
    "briefcase": "Rucksäcke & Taschen",
    "suitcase": "Rucksäcke & Taschen",
    # Trinkflaschen & Brotdosen
    "water bottle": "Trinkflaschen & Brotdosen",
    "water jug": "Trinkflaschen & Brotdosen",
    "bottle": "Trinkflaschen & Brotdosen",
    "thermos": "Trinkflaschen & Brotdosen",
    "lunch box": "Trinkflaschen & Brotdosen",
    "food container": "Trinkflaschen & Brotdosen",
    "mug": "Trinkflaschen & Brotdosen",
    "cup": "Trinkflaschen & Brotdosen",
    # Schulmaterial & Bücher
    "book": "Schulmaterial & Bücher",
    "textbook": "Schulmaterial & Bücher",
    "notebook": "Schulmaterial & Bücher",
    "pencil": "Schulmaterial & Bücher",
    "pen": "Schulmaterial & Bücher",
    "pencil case": "Schulmaterial & Bücher",
    "pencil box": "Schulmaterial & Bücher",
    "eraser": "Schulmaterial & Bücher",
    "ruler": "Schulmaterial & Bücher",
    "calculator": "Schulmaterial & Bücher",
    # Schlüssel & Wertsachen
    "key": "Schlüssel & Wertsachen",
    "keyring": "Schlüssel & Wertsachen",
    "necklace": "Schlüssel & Wertsachen",
    "ring": "Schlüssel & Wertsachen",
    "bracelet": "Schlüssel & Wertsachen",
    "watch": "Schlüssel & Wertsachen",
    "coin": "Schlüssel & Wertsachen",
    # Sportbekleidung
    "sports shoe": "Sportbekleidung",
    "sneaker": "Sportbekleidung",
    "running shoe": "Sportbekleidung",
    "football helmet": "Sportbekleidung",
    "baseball glove": "Sportbekleidung",
    "tennis ball": "Sportbekleidung",
    "volleyball": "Sportbekleidung",
    "basketball": "Sportbekleidung",
    "swimming trunks": "Sportbekleidung",
    "tracksuit": "Sportbekleidung",
}

@st.cache_resource(show_spinner=False)
def load_vision_model():
    """Leichtes ONNX-Modell; kein TensorFlow nötig."""
    try:
        import onnxruntime as ort
        model_path = Path("mobilenetv2.onnx")
        labels_path = Path("imagenet_labels.json")
        if not model_path.exists() or not labels_path.exists():
            return None
        session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        return session, labels
    except Exception:
        return None

# ImageNet kennt keine Schul-Fundbüro-Kategorien. Diese 50 häufigen visuellen
# Klassen werden deshalb auf unsere acht Katalogkategorien zusammengeführt.
VISION_CLASS_TO_CATEGORY = {
    "mobile phone": "Elektronik & Kabel", "cellular telephone": "Elektronik & Kabel",
    "hand-held computer": "Elektronik & Kabel", "laptop computer": "Elektronik & Kabel",
    "notebook computer": "Elektronik & Kabel", "desktop computer": "Elektronik & Kabel",
    "computer keyboard": "Elektronik & Kabel", "computer mouse": "Elektronik & Kabel",
    "remote control": "Elektronik & Kabel", "digital clock": "Elektronik & Kabel",
    "microphone": "Elektronik & Kabel", "camera": "Elektronik & Kabel",
    "headphone": "Elektronik & Kabel", "radio": "Elektronik & Kabel",
    "backpack": "Rucksäcke & Taschen", "purse": "Rucksäcke & Taschen",
    "handbag": "Rucksäcke & Taschen", "wallet": "Rucksäcke & Taschen",
    "briefcase": "Rucksäcke & Taschen", "suitcase": "Rucksäcke & Taschen",
    "shopping basket": "Rucksäcke & Taschen", "mailbag": "Rucksäcke & Taschen",
    "water bottle": "Trinkflaschen & Brotdosen", "bottle": "Trinkflaschen & Brotdosen",
    "beer bottle": "Trinkflaschen & Brotdosen", "coffee mug": "Trinkflaschen & Brotdosen",
    "cup": "Trinkflaschen & Brotdosen", "pitcher": "Trinkflaschen & Brotdosen",
    "t-shirt": "Kleidung & Textilien", "jersey": "Kleidung & Textilien",
    "sweatshirt": "Kleidung & Textilien", "pullover": "Kleidung & Textilien",
    "cardigan": "Kleidung & Textilien", "sweater": "Kleidung & Textilien",
    "jacket": "Kleidung & Textilien", "coat": "Kleidung & Textilien",
    "jean": "Kleidung & Textilien", "trousers": "Kleidung & Textilien",
    "dress": "Kleidung & Textilien", "scarf": "Kleidung & Textilien",
    "hat": "Kleidung & Textilien", "glove": "Kleidung & Textilien",
    "running shoe": "Sportbekleidung", "tennis ball": "Sportbekleidung",
    "volleyball": "Sportbekleidung", "basketball": "Sportbekleidung",
    "football helmet": "Sportbekleidung", "book": "Schulmaterial & Bücher",
    "textbook": "Schulmaterial & Bücher", "notebook": "Schulmaterial & Bücher",
    "pencil": "Schulmaterial & Bücher", "pencil case": "Schulmaterial & Bücher",
    "ruler": "Schulmaterial & Bücher", "calculator": "Schulmaterial & Bücher",
    "key": "Schlüssel & Wertsachen", "keyring": "Schlüssel & Wertsachen",
    "watch": "Schlüssel & Wertsachen", "ring": "Schlüssel & Wertsachen",
    "necklace": "Schlüssel & Wertsachen", "bracelet": "Schlüssel & Wertsachen",
}


def _softmax(values):
    values = values - np.max(values)
    exp = np.exp(values)
    return exp / np.sum(exp)


def analyze_image_ai(pil_image: Image.Image):
    """Erkennt einen Gegenstand mit MobileNetV2/ONNX und fällt sicher zurück.

    Wichtig: ImageNet ist kein speziell trainiertes Fundbüro-Modell. Das Ergebnis
    ist deshalb bewusst nur ein Vorschlag; das Formular lässt die Kategorie ändern.
    """
    vision = load_vision_model()
    if vision is not None:
        try:
            session, labels = vision
            image = ImageOps.fit(pil_image.convert("RGB"), (224, 224), Image.Resampling.LANCZOS)
            arr = np.asarray(image, dtype=np.float32) / 255.0
            arr = (arr - np.array([.485, .456, .406], dtype=np.float32)) / np.array([.229, .224, .225], dtype=np.float32)
            arr = np.transpose(arr, (2, 0, 1))[None, ...]
            output = session.run(None, {session.get_inputs()[0].name: arr})[0][0]
            probs = _softmax(output)
            ranked = np.argsort(probs)[::-1]

            # Nicht die erstbeste beliebige ImageNet-Klasse nehmen, sondern die
            # stärkste passende Objektklasse aus den Top-50.
            candidates = []
            for rank, index in enumerate(ranked[:50]):
                label = str(labels[int(index)]).lower().replace("_", " ")
                category = VISION_CLASS_TO_CATEGORY.get(label)
                if category:
                    candidates.append((category, float(probs[index]), label, rank))

            if candidates:
                category, probability, label, rank = max(candidates, key=lambda x: x[1])
                # Die ImageNet-Wahrscheinlichkeit ist bei Fotos oft klein; sie
                # dient nur als Signal. Ein niedriger Wert bleibt sichtbar als
                # Warnung, die Kategorie wird aber trotzdem sinnvoll vorgeschlagen.
                confidence = max(0.35, min(0.88, 0.35 + float(probability) * 3.0))
                return category, confidence, f"MobileNetV2 ONNX · {label}"
        except Exception:
            pass

    # Konservativer Fallback: niemals aus Seitenverhältnis allein eine falsche
    # konkrete Kategorie behaupten.
    rgb_img = pil_image.convert("RGB")
    w, h = rgb_img.size
    aspect_ratio = w / float(h)
    small = rgb_img.resize((64, 64))
    arr = np.asarray(small, dtype=np.float32)
    avg_color = arr.mean(axis=(0, 1))
    std_color = arr.std(axis=(0, 1))
    r, g, b = avg_color

    if std_color.mean() < 18 and r < 80 and g < 80 and b < 80:
        return "Elektronik & Kabel", 0.50, "Bildmerkmale · unsicherer Vorschlag"
    if aspect_ratio < 0.62 or aspect_ratio > 1.7:
        return "Trinkflaschen & Brotdosen", 0.50, "Bildmerkmale · unsicherer Vorschlag"
    return "Sonstiges", 0.35, "Kein zuverlässiges Modell verfügbar"

# =============================================================================
# 4. HILFSFUNKTIONEN FÜR DIE OBERFLÄCHE
# =============================================================================

ROLES = ["Schüler:in", "Lehrkraft", "Hausmeister / Admin"]


def nav_to(target: str):
    """Wird als Button-Callback genutzt: springt direkt in den gewünschten Bereich."""
    st.session_state["nav"] = target


def request_claim(item_id: int):
    """Callback: öffnet den Anspruchsbereich mit bereits gewähltem Fundstück."""
    st.session_state["claim_target"] = item_id
    st.session_state["nav"] = "Beanspruchen"


def ticket_html(item: dict, is_new: bool) -> str:
    """Rendert ein Fundstück als gedruckten Beleg (Rasteransicht)."""
    status = item.get("status", "Offen")
    item_id = item.get("id")
    titel = html.escape(str(item.get("titel", "")))
    kategorie = html.escape(str(item.get("kategorie", "")))
    fundort = html.escape(str(item.get("fundort", "")))
    lagerort = html.escape(str(item.get("abgabeort", "")))
    beschreibung = html.escape(str(item.get("beschreibung", "")))
    frist = html.escape(str(item.get("datum_ablauf", "")))
    datum = html.escape(str(item.get("datum_fund", "")))

    loaded = load_item_image(item.get("image_file"))
    if loaded is not None:
        photo = f'<div class="ticket-photo"><img src="{image_to_data_uri(loaded, 460)}" alt="{titel}"></div>'
    else:
        photo = f'<div class="ticket-photo ph">{kategorie}</div>'

    chips = "".join(f'<span class="chip">{html.escape(str(t))}</span>' for t in item.get("tags", []))
    neu = '<span class="newflag">Neu</span>' if is_new else ""

    return f"""
    <div class="ticket">
        <div class="ticket-head">
            <span class="ticket-id">Beleg Nr. #{item_id}</span>
            <span class="stamp s-{status.lower()}">{status}</span>
        </div>
        {photo}
        <div class="ticket-body">
            <div class="ticket-title">{titel}{neu}</div>
            <dl class="tgrid">
                <dt>Fundort</dt><dd>{fundort}</dd>
                <dt>Gefunden</dt><dd>{datum}</dd>
                <dt>Lagerort</dt><dd>{lagerort}</dd>
                <dt>Frist bis</dt><dd>{frist}</dd>
            </dl>
            <div class="tdesc">{beschreibung}</div>
            <div class="tchips">{chips}</div>
        </div>
    </div>
    """


def row_html(item: dict, is_new: bool) -> str:
    """Rendert ein Fundstück als kompakte Listenzeile."""
    status = item.get("status", "Offen")
    titel = html.escape(str(item.get("titel", "")))
    kategorie = html.escape(str(item.get("kategorie", "")))
    beschreibung = html.escape(str(item.get("beschreibung", "")))
    meta = html.escape(f"#{item.get('id')} · {item.get('fundort')} · {item.get('datum_fund')} · {kategorie}")

    loaded = load_item_image(item.get("image_file"))
    if loaded is not None:
        thumb = f'<img class="thumb" src="{image_to_data_uri(loaded, 170)}" alt="{titel}">'
    else:
        thumb = f'<div class="thumb ph">{kategorie}</div>'

    neu = '<span class="newflag">Neu</span>' if is_new else ""

    return f"""
    <div class="row-item">
        {thumb}
        <div class="ri-main">
            <div class="ri-title">{titel}{neu}</div>
            <div class="ri-meta">{meta}</div>
            <div class="ri-desc">{beschreibung}</div>
        </div>
        <span class="stamp s-{status.lower()}">{status}</span>
    </div>
    """


# =============================================================================
# 5. KOPFBEREICH, KENNZAHLEN UND NAVIGATION
# =============================================================================

items_all = st.session_state["fundstuecke_liste"]
heute = datetime.date.today()
neu_grenze = (heute - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

anz_gesamt = len(items_all)
anz_offen = sum(1 for i in items_all if i.get("status") == "Offen")
anz_bean = sum(1 for i in items_all if i.get("status") == "Beansprucht")
anz_abgeholt = sum(1 for i in items_all if i.get("status") == "Abgeholt")
quote = (anz_abgeholt / anz_gesamt * 100) if anz_gesamt else 0.0
anz_offene_pruefung = len([c for c in st.session_state["claims"] if c.get("status") == "In Prüfung"])

col_brand, col_zugang = st.columns([3.6, 1.2])

with col_brand:
    st.markdown(f"""
    <div class="mast">
        <div class="kicker">
            <span>Katharineum zu Lübeck</span>
            <em>Amtliches Fundverzeichnis</em>
            <span>{heute.strftime('%d.%m.%Y')}</span>
        </div>
        <h1>KATH. FUND</h1>
        <div class="sub">Fundstücke <b>melden</b>, <b>durchsuchen</b> und <b>wiedererlangen</b> — ein Vorgang, keine Zettelwirtschaft.</div>
    </div>
    """, unsafe_allow_html=True)

with col_zugang:
    st.markdown('<div class="ctl-lbl">Zugang</div>', unsafe_allow_html=True)
    role = st.selectbox("Rolle", ROLES, label_visibility="collapsed", key="role")
    st.session_state["current_role"] = role

    if role == "Hausmeister / Admin":
        pin = st.text_input("PIN", type="password", placeholder="PIN (Demo: 1234)",
                            label_visibility="collapsed", key="pin")
        st.session_state["is_authenticated"] = (pin == "1234")
        if pin and pin != "1234":
            st.caption("PIN ungültig")
        elif pin == "1234":
            st.caption("Freigeschaltet")
    else:
        st.session_state["is_authenticated"] = True

    st.button("＋ Fundstück erfassen", width="stretch", key="cta_new",
              on_click=nav_to, args=("Erfassen",))

st.markdown(f"""
<div class="kpis">
    <div class="kpi"><span>Im Verzeichnis</span><b>{anz_gesamt}</b></div>
    <div class="kpi"><span>Offen</span><b>{anz_offen}</b></div>
    <div class="kpi"><span>Beansprucht</span><b>{anz_bean}</b></div>
    <div class="kpi"><span>Abgeholt</span><b>{anz_abgeholt}</b></div>
    <div class="kpi"><span>Prüfungen offen</span><b>{anz_offene_pruefung}</b></div>
    <div class="kpi accent"><span>Rückführquote</span><b>{quote:.0f} %</b></div>
</div>
""", unsafe_allow_html=True)

# Hauptnavigation — groß, immer sichtbar, nicht versteckt
if "nav" not in st.session_state:
    st.session_state["nav"] = "Katalog"

with st.container(key="navwrap"):
    nav = st.radio(
        "Bereich",
        ["Katalog", "Erfassen", "Beanspruchen", "Verwaltung"],
        horizontal=True,
        label_visibility="collapsed",
        key="nav",
    )

st.markdown('<div style="border-bottom: 1.5px solid var(--ink); margin-bottom: 6px;"></div>',
            unsafe_allow_html=True)


# =============================================================================
# 6. BEREICH: KATALOG
# =============================================================================

def render_katalog():
    st.markdown("""
    <div class="sec">
        <h2>Fundverzeichnis</h2>
        <span class="tag">Schnellsuche · Register · Raster</span>
    </div>
    """, unsafe_allow_html=True)

    # --- Ansichtsmodus (die drei Einstiege aus dem Papierentwurf) ---
    col_mode, col_layout = st.columns([3, 1])
    with col_mode:
        with st.container(key="modefilter"):
            mode = st.radio(
                "Ansicht",
                ["Alle Stücke", "Diese Woche gefunden", "A–Z Register"],
                horizontal=True,
                label_visibility="collapsed",
                key="mode",
            )
    with col_layout:
        with st.container(key="layoutsel"):
            layout = st.radio(
                "Darstellung",
                ["Raster", "Liste"],
                horizontal=True,
                label_visibility="collapsed",
                key="layout",
            )

    # --- Schnellsuche ---
    col_q, col_ort = st.columns([3.2, 1])
    with col_q:
        with st.container(key="searchwrap"):
            query = st.text_input(
                "Schnellsuche",
                placeholder="Schnellsuche — Jacke, Blau, Nike, AirPods oder #1002 …",
                label_visibility="collapsed",
                key="q",
            )
    with col_ort:
        fundort_filter = st.selectbox("Fundort", ["Alle Fundorte"] + LOCATIONS + ["Unbekannt"],
                                      label_visibility="collapsed", key="loc")

    # --- Kategorien und Status als Klick-Chips ---
    st.markdown('<div class="ctl-lbl">Kategorie</div>', unsafe_allow_html=True)
    kat_filter = st.radio("Kategorie", ["Alle"] + CATEGORIES, horizontal=True,
                          label_visibility="collapsed", key="cat")

    st.markdown('<div class="ctl-lbl">Bearbeitungsstand</div>', unsafe_allow_html=True)
    status_filter = st.radio("Status", ["Alle", "Offen", "Beansprucht", "Abgeholt"],
                             horizontal=True, label_visibility="collapsed", key="status")

    # --- Filtern ---
    visible = list(st.session_state["fundstuecke_liste"])
    q = (query or "").strip().lower()
    if q:
        visible = [
            i for i in visible
            if q in str(i.get("titel", "")).lower()
            or q in str(i.get("beschreibung", "")).lower()
            or q in str(i.get("fundort", "")).lower()
            or q in str(i.get("kategorie", "")).lower()
            or any(q in str(t).lower() for t in i.get("tags", []))
            or q in str(i.get("id", ""))
        ]
    if kat_filter != "Alle":
        visible = [i for i in visible if i.get("kategorie") == kat_filter]
    if fundort_filter != "Alle Fundorte":
        visible = [i for i in visible if i.get("fundort") == fundort_filter]
    if status_filter != "Alle":
        visible = [i for i in visible if i.get("status") == status_filter]
    if mode == "Diese Woche gefunden":
        visible = [i for i in visible if str(i.get("datum_fund", "")) >= neu_grenze]

    if mode == "A–Z Register":
        visible.sort(key=lambda i: str(i.get("titel", "")).lower())
    else:
        visible.sort(key=lambda i: str(i.get("datum_fund", "")), reverse=True)

    if mode == "A–Z Register":
        sort_hint = "alphabetisch"
    elif mode == "Diese Woche gefunden":
        sort_hint = "neu eingegangen"
    else:
        sort_hint = "neueste zuerst"

    st.markdown(f"""
    <div class="sec-note" style="margin-top:14px;">
        <b>{len(visible)}</b> Eintragung(en) · Ansicht: {mode} · Sortierung: {sort_hint}
    </div>
    """, unsafe_allow_html=True)

    if not visible:
        st.markdown("""
        <div class="empty">
            Keine Eintragung passt zu dieser Auswahl<br>
            <span style="text-transform:none; letter-spacing:0;">Suchbegriff ändern oder Kategorie- und Statusfilter zurücksetzen.</span>
        </div>
        """, unsafe_allow_html=True)
        return

    if layout == "Raster":
        for block in range(0, len(visible), 3):
            cols = st.columns(3, gap="medium")
            for slot in range(3):
                pos = block + slot
                if pos >= len(visible):
                    continue
                item = visible[pos]
                with cols[slot]:
                    st.markdown(ticket_html(item, str(item.get("datum_fund", "")) >= neu_grenze),
                                unsafe_allow_html=True)
                    if item.get("status") in ("Offen", "Beansprucht"):
                        st.button("Anspruch prüfen", key=f"claim_btn_{item.get('id')}", width="stretch",
                                  on_click=request_claim, args=(item.get("id"),))
    else:
        for item in visible:
            st.markdown(row_html(item, str(item.get("datum_fund", "")) >= neu_grenze),
                        unsafe_allow_html=True)
            if item.get("status") in ("Offen", "Beansprucht"):
                st.button("Anspruch prüfen", key=f"claim_row_{item.get('id')}",
                          on_click=request_claim, args=(item.get("id"),))


# =============================================================================
# 7. BEREICH: ERFASSEN
# =============================================================================

def render_erfassen():
    st.markdown("""
    <div class="sec">
        <h2>Fundstück aufnehmen</h2>
        <span class="tag">Lichtbild · automatische Zuordnung · Eintrag</span>
    </div>
    <div class="sec-note">Foto aufnehmen oder hochladen — die Zuordnung erfolgt automatisch, Korrektur jederzeit möglich.</div>
    """, unsafe_allow_html=True)

    col_bild, col_form = st.columns([1, 1.1], gap="large")

    uploaded_pil = None
    ai_category = CATEGORIES[0]
    ai_confidence = 0.0
    ai_engine = "Standby"

    with col_bild:
        st.markdown("#### Lichtbild")
        upload_mode = st.radio("Eingabeweg", ["Datei hochladen", "Kamera auslösen"],
                               horizontal=True, key="upload_mode")

        if upload_mode == "Datei hochladen":
            img_file = st.file_uploader("Bild auswählen", type=["jpg", "jpeg", "png", "webp"],
                                        key="file_upload_input")
            if img_file is not None:
                uploaded_pil = Image.open(img_file).convert("RGB")
        else:
            cam_file = st.camera_input("Kamera auslösen", key="cam_input")
            if cam_file is not None:
                uploaded_pil = Image.open(cam_file).convert("RGB")

        if uploaded_pil is not None:
            preview = uploaded_pil.copy()
            preview.thumbnail((900, 470), Image.Resampling.LANCZOS)
            st.image(preview, caption="Aufnahme für den Beleg", width="stretch")
            with st.spinner("Zuordnung läuft"):
                ai_category, ai_confidence, ai_engine = analyze_image_ai(uploaded_pil)

            if ai_category not in CATEGORIES:
                ai_category = "Sonstiges"

            st.markdown(f"""
            <div class="verdict">
                <div class="verdict-stamp">Vorschlag</div>
                <div>
                    <div class="verdict-cat">{html.escape(ai_category)}</div>
                    <div class="verdict-meta">Sicherheit {ai_confidence * 100:.0f} % · {html.escape(ai_engine)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if ai_confidence < 0.60:
                st.markdown("""
                <div class="ai-warn"><b>Unsicherer Vorschlag:</b> Bitte die Kategorie rechts unbedingt prüfen. Ein Bildmodell kann ähnliche Gegenstände verwechseln.</div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty">
                Noch kein Lichtbild<br>
                <span style="text-transform:none; letter-spacing:0;">Ohne Foto lässt sich ein Fundstück trotzdem vollständig erfassen.</span>
            </div>
            """, unsafe_allow_html=True)

    with col_form:
        st.markdown("#### Angaben zum Fundstück")
        with st.form("form_add_item", clear_on_submit=True):
            in_titel = st.text_input("Bezeichnung*", placeholder="z. B. Dunkelblaue Regenjacke, Größe M")

            if ai_category not in CATEGORIES:
                ai_category = "Sonstiges"

            st.markdown(f"""
            <div class="note">
                <b>Modellvorschlag:</b> {html.escape(ai_category)}
                <span>Automatisch aus dem Lichtbild abgeleitet. Bitte unten bestätigen oder ändern.</span>
            </div>
            """, unsafe_allow_html=True)
            in_kategorie = st.selectbox(
                "Kategorie bestätigen*",
                CATEGORIES,
                index=CATEGORIES.index(ai_category) if ai_category in CATEGORIES else len(CATEGORIES) - 1,
            )

            c1, c2 = st.columns(2)
            with c1:
                in_fundort = st.selectbox("Fundort*", LOCATIONS)
            with c2:
                in_abgabeort = st.text_input("Lagerort*", value="Hausmeisterbüro (Raum 001)")

            in_tags = st.text_input("Schlagworte", placeholder="kommagetrennt, z. B. Nike, Blau, Größe L")
            in_beschreibung = st.text_area("Besondere Merkmale", height=110,
                                           placeholder="Kratzer, Initialen, Anhänger, Inhalt …")

            c3, c4 = st.columns(2)
            with c3:
                in_kuerzel = st.text_input("Melder-Kürzel*", placeholder="z. B. MAX-8B")
            with c4:
                in_rolle = st.selectbox("Rolle der findenden Person",
                                        ["Schüler:in", "Lehrkraft", "Hausmeister", "Sonstige"])

            st.caption("Personenbezogene Daten bleiben geschützt im Hausmeisterprotokoll.")

            if st.form_submit_button("Eintrag ins Fundbuch übernehmen", width="stretch"):
                if not in_titel.strip() or not in_kuerzel.strip():
                    st.error("Bezeichnung und Melder-Kürzel sind Pflichtfelder.")
                else:
                    items = st.session_state["fundstuecke_liste"]
                    new_id = max([i["id"] for i in items]) + 1 if items else 1001

                    saved_img_name = save_uploaded_image(uploaded_pil, new_id) if uploaded_pil is not None else None

                    parsed_tags = [t.strip() for t in in_tags.split(",") if t.strip()]
                    if not parsed_tags:
                        parsed_tags = [ai_category.split(" ")[0]]

                    neues_item = {
                        "id": new_id,
                        "titel": in_titel.strip(),
                        "kategorie": in_kategorie,
                        "fundort": in_fundort,
                        "abgabeort": in_abgabeort.strip() or "Hausmeisterbüro (Raum 001)",
                        "kontakt_kuerzel": in_kuerzel.strip().upper(),
                        "finder_rolle": in_rolle,
                        "datum_fund": heute.strftime("%Y-%m-%d"),
                        "datum_ablauf": (heute + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
                        "status": "Offen",
                        "beschreibung": in_beschreibung.strip() or "Keine nähere Beschreibung angegeben.",
                        "image_file": saved_img_name,
                        "tags": parsed_tags,
                    }

                    st.session_state["fundstuecke_liste"].insert(0, neues_item)
                    log_action(in_kuerzel.strip().upper(), f"Fundstück #{new_id} registriert ({in_titel.strip()})")
                    st.toast(f"Beleg #{new_id} angelegt", icon="✅")
                    st.rerun()


# =============================================================================
# 8. BEREICH: BEANSPRUCHEN
# =============================================================================

def render_beanspruchen():
    st.markdown("""
    <div class="sec">
        <h2>Fundstück beanspruchen</h2>
        <span class="tag">Nachweis · Prüfung · Aushändigung</span>
    </div>
    <div class="sec-note">Eigentum wird geprüft: Je genauer der Nachweis, desto schneller die Aushändigung.</div>
    """, unsafe_allow_html=True)

    offene = [i for i in st.session_state["fundstuecke_liste"]
              if i.get("status") in ("Offen", "Beansprucht")]

    if not offene:
        st.markdown("""
        <div class="empty">
            Zurzeit liegt kein beanspruchbares Fundstück vor<br>
            <span style="text-transform:none; letter-spacing:0;">Sobald etwas abgegeben wird, erscheint es hier.</span>
        </div>
        """, unsafe_allow_html=True)
        return

    labels = {f"#{i['id']} — {i['titel']} ({i['fundort']})": i["id"] for i in offene}
    optionen = list(labels.keys())

    # Vorauswahl, falls aus dem Katalog heraus "Anspruch prüfen" gedrückt wurde
    ziel = st.session_state.pop("claim_target", None)
    default_index = 0
    if ziel is not None:
        for pos, label in enumerate(optionen):
            if labels[label] == ziel:
                default_index = pos
                break
        st.session_state.pop("claim_item", None)

    col_info, col_nachweis = st.columns([1, 1], gap="large")

    with col_info:
        st.markdown("#### Beleg wählen")
        gewaehlt = st.selectbox("Fundstück", optionen, index=default_index,
                                label_visibility="collapsed", key="claim_item")
        ziel_item = next(i for i in st.session_state["fundstuecke_liste"] if i["id"] == labels[gewaehlt])

        st.markdown(ticket_html(ziel_item, False), unsafe_allow_html=True)

    with col_nachweis:
        st.markdown("#### Eigentumsnachweis")
        with st.form("form_claim"):
            c_name = st.text_input("Name und Klasse*", placeholder="z. B. Julia Koch (9b)")
            c_proof = st.text_area(
                "Nachweis*",
                height=150,
                placeholder="Merkmale, die nur die rechtmäßige Besitzerin oder der Besitzer kennt: Inhalt, Gravur, Sperrbildschirm, Initialen …",
            )
            if st.form_submit_button("Anspruch zur Prüfung einreichen", width="stretch"):
                if not c_name.strip() or not c_proof.strip():
                    st.error("Name und Nachweis sind Pflichtfelder.")
                else:
                    claims = st.session_state["claims"]
                    new_claim_id = max([c["claim_id"] for c in claims]) + 1 if claims else 501
                    claims.insert(0, {
                        "claim_id": new_claim_id,
                        "item_id": ziel_item["id"],
                        "name": c_name.strip(),
                        "proof": c_proof.strip(),
                        "datum": heute.strftime("%Y-%m-%d"),
                        "status": "In Prüfung",
                    })
                    ziel_item["status"] = "Beansprucht"
                    log_action(c_name.strip(), f"Anspruch #{new_claim_id} auf Beleg #{ziel_item['id']} eingereicht")
                    st.toast("Anspruch eingereicht", icon="✅")
                    st.rerun()


# =============================================================================
# 9. BEREICH: VERWALTUNG
# =============================================================================

def render_verwaltung():
    st.markdown("""
    <div class="sec">
        <h2>Verwaltung</h2>
        <span class="tag">Ansprüche · Kennzahlen · Register · Protokoll</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state["current_role"] != "Hausmeister / Admin":
        st.info("Dieser Bereich gehört zum Hausmeisterbüro. Rolle im Kopfbereich auf „Hausmeister / Admin“ stellen.")
        return

    if not st.session_state["is_authenticated"]:
        st.warning("PIN erforderlich. Bitte im Kopfbereich unter „Zugang“ eingeben (Demo: 1234).")
        return

    tab_claims, tab_kpi, tab_register, tab_log = st.tabs(
        ["Ansprüche", "Kennzahlen", "Register", "Protokoll & Export"]
    )

    with tab_claims:
        claims = st.session_state["claims"]
        if not claims:
            st.markdown('<div class="empty">Keine Ansprüche im Eingang</div>', unsafe_allow_html=True)
        for c in claims:
            rel = next((i for i in st.session_state["fundstuecke_liste"] if i["id"] == c["item_id"]), None)
            titel = rel["titel"] if rel else "Gelöschtes Fundstück"
            status_slug = "abgeholt" if c["status"] == "Genehmigt" else ("entsorgt" if c["status"] == "Abgelehnt" else "beansprucht")

            with st.expander(f"Anspruch #{c['claim_id']} · Beleg #{c['item_id']} · {titel}"):
                st.markdown(f"""
                <div class="note">
                    <b>{html.escape(str(c['name']))}</b>
                    <span>Eingereicht am {c['datum']} · Status {c['status']}</span>
                </div>
                <div class="tdesc" style="border-top:none;">{html.escape(str(c['proof']))}</div>
                <div style="margin-bottom:10px;"><span class="stamp s-{status_slug}">{c['status']}</span></div>
                """, unsafe_allow_html=True)

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Genehmigen & Aushändigung vermerken", key=f"app_{c['claim_id']}",
                                 width="stretch"):
                        c["status"] = "Genehmigt"
                        if rel:
                            rel["status"] = "Abgeholt"
                        log_action("ADMIN", f"Anspruch #{c['claim_id']} genehmigt (Beleg #{c['item_id']} ausgehändigt)")
                        sync_storage()
                        st.rerun()
                with b2:
                    if st.button("Anspruch abweisen", key=f"rej_{c['claim_id']}", width="stretch"):
                        c["status"] = "Abgelehnt"
                        if rel and rel["status"] == "Beansprucht":
                            rel["status"] = "Offen"
                        log_action("ADMIN", f"Anspruch #{c['claim_id']} abgewiesen")
                        sync_storage()
                        st.rerun()

    with tab_kpi:
        df = pd.DataFrame(st.session_state["fundstuecke_liste"])
        if df.empty:
            st.markdown('<div class="empty">Keine Daten</div>', unsafe_allow_html=True)
            return

        st.markdown(f"""
        <div class="kpis">
            <div class="kpi"><span>Registriert</span><b>{anz_gesamt}</b></div>
            <div class="kpi"><span>Ausgehändigt</span><b>{anz_abgeholt}</b></div>
            <div class="kpi"><span>Rückführquote</span><b>{quote:.0f} %</b></div>
            <div class="kpi"><span>Offene Prüfungen</span><b>{anz_offene_pruefung}</b></div>
            <div class="kpi"><span>Kategorien</span><b>{df['kategorie'].nunique()}</b></div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Verteilung nach Kategorien")
            st.bar_chart(df["kategorie"].value_counts(), color="#B23A2A")
        with c2:
            st.markdown("##### Verteilung nach Fundorten")
            st.bar_chart(df["fundort"].value_counts(), color="#2B4C7E")

    with tab_register:
        df = pd.DataFrame(st.session_state["fundstuecke_liste"])
        spalten = [c for c in ["id", "titel", "kategorie", "fundort", "status", "datum_fund", "datum_ablauf"] if c in df.columns]
        st.dataframe(df[spalten], width="stretch", hide_index=True)

        st.markdown("##### Fristenprüfung")
        faellig = [i for i in st.session_state["fundstuecke_liste"]
                   if str(i.get("datum_ablauf", "")) < heute.strftime("%Y-%m-%d") and i.get("status") == "Offen"]
        if faellig:
            st.warning(f"{len(faellig)} Fundstück(e) haben die 90-Tage-Frist überschritten.")
            if st.button("Frist überschrittene als entsorgt austragen", width="stretch"):
                for i in faellig:
                    i["status"] = "Entsorgt"
                log_action("ADMIN", f"{len(faellig)} Fundstücke als entsorgt markiert")
                sync_storage()
                st.rerun()
        else:
            st.markdown('<div class="empty">Alle Fristen im grünen Bereich</div>', unsafe_allow_html=True)

    with tab_log:
        logs = pd.DataFrame(st.session_state["audit_logs"])
        st.dataframe(logs, width="stretch", hide_index=True)

        export = {
            "items": st.session_state["fundstuecke_liste"],
            "claims": st.session_state["claims"],
            "audit_logs": st.session_state["audit_logs"],
            "export_date": datetime.datetime.now().isoformat(),
        }
        st.download_button(
            "Gesamtes Fundverzeichnis herunterladen (JSON)",
            data=json.dumps(export, ensure_ascii=False, indent=2),
            file_name=f"kath_fund_export_{heute.strftime('%Y%m%d')}.json",
            mime="application/json",
            width="stretch",
        )


# =============================================================================
# 10. AUSGABE
# =============================================================================

if nav == "Katalog":
    render_katalog()
elif nav == "Erfassen":
    render_erfassen()
elif nav == "Beanspruchen":
    render_beanspruchen()
else:
    render_verwaltung()
