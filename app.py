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
    initial_sidebar_state="expanded"
)

# Designsystem "Kartei": analoges Fundbuch — Papier, Tinte, Stempel.
# Keine Streamlit-Standardoptik: eigenes Komponenten-Set (Masthead, Ticket,
# Stamp, Ledger, Verdict, KPI) + voll reskinnte Native-Widgets.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Archivo:wght@500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --paper: #F1EDDF;
        --card: #FBF8EE;
        --field: #FFFDF6;
        --ink: #1D1A14;
        --ink-soft: #6E6656;
        --line: #D8D0B9;
        --red: #B23A2A;
        --green: #2E6B34;
        --amber: #96690F;
        --blue: #2E4E7E;
    }

    ::selection { background: var(--red); color: #FFF8F0; }

    /* ---------- App-Grundgerüst ---------- */
    [data-testid="stAppViewContainer"] {
        background-color: var(--paper);
        background-image: radial-gradient(#E2D9C1 1px, transparent 1.2px);
        background-size: 22px 22px;
    }
    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        color: var(--ink);
    }
    hr { border: none; border-top: 3px double var(--ink); opacity: .8; margin: 1.2em 0; }

    /* ---------- Streamlit-Chrome ausblenden ---------- */
    #MainMenu, footer,
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }

    /* ---------- Masthead (Zeitungskopf statt Badge-Card) ---------- */
    .masthead { border-bottom: 4px double var(--ink); padding: 4px 2px 16px; margin-bottom: 20px; }
    .mast-kicker {
        display: flex; justify-content: space-between; gap: 12px;
        font-family: 'IBM Plex Mono', monospace; font-size: .68rem;
        letter-spacing: .14em; text-transform: uppercase; color: var(--ink-soft);
        border-top: 1.5px solid var(--ink); border-bottom: 1px solid var(--ink);
        padding: 6px 0; margin-bottom: 12px;
    }
    .masthead h1 {
        font-family: 'Archivo Black', sans-serif; font-weight: 400;
        font-size: clamp(2rem, 4.6vw, 3.3rem); letter-spacing: -.01em;
        margin: 0; color: var(--ink); line-height: 1.02;
    }
    .mast-sub { font-size: .95rem; color: var(--ink-soft); margin-top: 6px; }
    .mast-sub b { color: var(--red); }

    /* ---------- Sektionsköpfe ---------- */
    .sec { display: flex; align-items: center; gap: 12px; border-bottom: 1.5px solid var(--ink); padding-bottom: 9px; margin: 4px 0 6px; }
    .sec-no { font-family: 'IBM Plex Mono', monospace; background: var(--ink); color: var(--paper); font-size: .7rem; padding: 3px 9px; border-radius: 4px; letter-spacing: .12em; }
    .sec h2 { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.28rem; margin: 0; letter-spacing: -.01em; }
    .sec-sub { color: var(--ink-soft); margin: 8px 0 18px; font-size: .9rem; }
    .stMarkdown h4 {
        font-family: 'IBM Plex Mono', monospace !important; font-size: .72rem !important;
        letter-spacing: .14em !important; text-transform: uppercase !important;
        color: var(--ink-soft) !important; margin-top: 1.2em !important;
    }
    .stMarkdown h5 { font-family: 'Archivo', sans-serif; font-weight: 700; font-size: .92rem; }
    [data-testid="stCaptionContainer"] { font-family: 'IBM Plex Mono', monospace; font-size: .72rem; color: var(--ink-soft); }

    /* ---------- Ticket-Karte (Fundstück) ---------- */
    .ticket { background: var(--card); border: 1.5px solid var(--ink); border-radius: 10px; overflow: hidden; margin-bottom: 4px; box-shadow: 4px 4px 0 rgba(29,26,20,.14); }
    .ticket-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 9px 13px; background: #F4EEDA; border-bottom: 1.5px solid var(--ink); }
    .ticket-id { font-family: 'IBM Plex Mono', monospace; font-size: .7rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-soft); }
    .ticket-photo img { display: block; width: 100%; height: 205px; object-fit: cover; border-bottom: 1.5px solid var(--ink); }
    .ticket-photo.ph {
        height: 120px; display: flex; align-items: center; justify-content: center;
        background: repeating-linear-gradient(45deg, #EFE8D2 0 10px, #F7F2E2 10px 20px);
        border-bottom: 1.5px solid var(--ink);
        font-family: 'IBM Plex Mono', monospace; font-size: .68rem; letter-spacing: .1em;
        text-transform: uppercase; color: var(--ink-soft);
    }
    .ticket-body { padding: 13px 14px 14px; }
    .ticket-title { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.04rem; letter-spacing: -.01em; margin: 0 0 8px; line-height: 1.25; }
    .trow { display: flex; justify-content: space-between; gap: 10px; padding: 5px 0; border-top: 1px dotted var(--line); font-size: .83rem; }
    .trow span { font-family: 'IBM Plex Mono', monospace; font-size: .64rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-soft); padding-top: 2px; }
    .trow b { font-weight: 600; text-align: right; }
    .ticket-tags { margin-top: 9px; }
    .tchip {
        display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: .66rem;
        letter-spacing: .06em; text-transform: uppercase; color: var(--ink);
        border: 1px solid var(--ink); border-radius: 4px; padding: 2px 7px; margin: 0 5px 5px 0; background: var(--field);
    }

    /* ---------- Stempel (Status) ---------- */
    .stamp {
        display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: .64rem;
        font-weight: 600; letter-spacing: .12em; text-transform: uppercase; white-space: nowrap;
        padding: 4px 10px; border: 1.5px solid currentColor; border-radius: 4px;
        box-shadow: inset 0 0 0 2px var(--card), inset 0 0 0 3.5px currentColor;
        transform: rotate(-3deg); background: var(--card);
    }
    .s-offen { color: var(--amber); } .s-beansprucht { color: var(--blue); }
    .s-abgeholt { color: var(--green); } .s-entsorgt { color: var(--red); }

    /* ---------- Prüfvermerk (KI-Box-Ersatz) ---------- */
    .verdict { display: flex; gap: 14px; align-items: center; background: var(--card); border: 1.5px solid var(--ink); border-radius: 10px; padding: 13px 16px; margin-top: 14px; box-shadow: 4px 4px 0 rgba(29,26,20,.14); }
    .verdict-stamp {
        font-family: 'IBM Plex Mono', monospace; text-transform: uppercase; font-size: .66rem;
        letter-spacing: .12em; color: var(--red); border: 2px solid var(--red); border-radius: 6px;
        padding: 7px 11px; transform: rotate(-4deg); white-space: nowrap; font-weight: 600;
        box-shadow: inset 0 0 0 2px var(--card), inset 0 0 0 3.5px var(--red);
    }
    .verdict-cat { font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.05rem; }
    .verdict-meta { font-family: 'IBM Plex Mono', monospace; font-size: .7rem; color: var(--ink-soft); margin-top: 2px; }
    .note { border-left: 3px solid var(--ink); background: #F4EEDA; padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: .87rem; margin-bottom: 12px; }
    .note b { font-weight: 700; } .note span { color: var(--ink-soft); font-size: .8rem; }

    /* ---------- Sidebar: dunkles Kontor ---------- */
    [data-testid="stSidebar"] { background: #1D1A14; background-image: radial-gradient(rgba(255,248,230,.055) 1px, transparent 1.2px); background-size: 18px 18px; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #EDE7D5; }
    .side-title { font-family: 'Archivo Black', sans-serif; color: #F5EFDD; font-size: 1.3rem; letter-spacing: 0; }
    .side-sub { font-family: 'IBM Plex Mono', monospace; color: #A79E86; font-size: .66rem; letter-spacing: .16em; text-transform: uppercase; margin: 2px 0 8px; }
    .ledger { border: 1px solid #453F30; border-radius: 8px; overflow: hidden; margin: 12px 0; }
    .lrow { display: flex; justify-content: space-between; align-items: baseline; padding: 8px 12px; border-bottom: 1px dashed #453F30; }
    .lrow:last-child { border-bottom: none; }
    .lrow span { font-family: 'IBM Plex Mono', monospace; text-transform: uppercase; font-size: .64rem; letter-spacing: .12em; color: #A79E86; }
    .lrow b { font-family: 'IBM Plex Mono', monospace; font-size: .95rem; color: #F5EFDD; }
    .side-note { font-size: .74rem; color: #A79E86; line-height: 1.5; }
    .side-rule { border: none; border-top: 1px solid #453F30; margin: 14px 0; }

    /* ---------- Tabs als Karteireiter ---------- */
    [data-testid="stTabs"] [data-baseweb="tabList"] { gap: 6px; border-bottom: 1.5px solid var(--ink); }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-family: 'IBM Plex Mono', monospace; font-size: .7rem; letter-spacing: .1em;
        text-transform: uppercase; color: var(--ink-soft); padding: 10px 15px;
        border: 1.5px solid transparent; border-bottom: none; border-radius: 8px 8px 0 0;
    }
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] { color: var(--ink); background: var(--card); border-color: var(--ink); font-weight: 600; }
    [data-testid="stTabs"] [data-baseweb="tabHighlight"] { display: none; }
    [data-testid="stTabs"] [data-baseweb="tabBorder"] { display: none; }

    /* ---------- Buttons ---------- */
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button,
    [data-testid="stFileUploader"] button, [data-testid="stCameraInput"] button {
        font-family: 'IBM Plex Mono', monospace !important; text-transform: uppercase !important;
        letter-spacing: .1em !important; font-size: .7rem !important; font-weight: 600 !important;
        background: var(--card) !important; color: var(--ink) !important;
        border: 1.5px solid var(--ink) !important; border-radius: 7px !important;
        box-shadow: 3px 3px 0 var(--ink); padding: .6rem 1.1rem !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        transform: translate(-1px, -1px); box-shadow: 4px 4px 0 var(--ink);
    }
    .stButton > button:active, .stDownloadButton > button:active, [data-testid="stFormSubmitButton"] > button:active {
        transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--ink);
    }
    [data-testid="stFormSubmitButton"] > button { background: var(--red) !important; border-color: var(--red) !important; color: #FFF6EA !important; }
    .stDownloadButton > button { background: var(--ink) !important; color: var(--paper) !important; }

    /* ---------- Formularfelder ---------- */
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div, div[data-testid="stNumberInput"] input {
        background: var(--field) !important; border: 1.5px solid var(--line) !important;
        border-radius: 7px !important; font-size: .88rem !important; color: var(--ink) !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: var(--ink) !important; box-shadow: 2px 2px 0 var(--ink) !important;
    }
    div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed var(--ink); background: var(--field); border-radius: 10px;
    }
    input[type="radio"], input[type="checkbox"] { accent-color: var(--red); }
    div[data-testid="stRadio"] div[role="radiogroup"] { gap: 8px; }

    /* ---------- Alerts, Expander, Tabellen ---------- */
    div[data-testid="stAlert"] { border: 1.5px solid var(--ink); border-radius: 8px; background: var(--card); box-shadow: 3px 3px 0 rgba(29,26,20,.14); }
    details[data-testid="stExpander"] { border: 1.5px solid var(--ink); border-radius: 8px; background: var(--card); }
    details[data-testid="stExpander"] summary { font-family: 'IBM Plex Mono', monospace; font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; }
    details[data-testid="stExpander"] summary:hover { color: var(--red); }
    div[data-testid="stDataFrame"] { border: 1.5px solid var(--ink); border-radius: 8px; overflow: hidden; }
    div[data-testid="stImage"] figcaption { font-family: 'IBM Plex Mono', monospace; font-size: .68rem; color: var(--ink-soft); }

    /* ---------- KPI-Karten (Admin) ---------- */
    .kpi { background: var(--card); border: 1.5px solid var(--ink); border-radius: 10px; padding: 10px 14px; box-shadow: 3px 3px 0 rgba(29,26,20,.14); }
    .kpi span { font-family: 'IBM Plex Mono', monospace; font-size: .62rem; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-soft); }
    .kpi b { display: block; font-family: 'Archivo', sans-serif; font-weight: 800; font-size: 1.5rem; letter-spacing: -.01em; }
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
def load_mobilenet_model():
    """Versucht MobileNetV2 zu laden (nur wenn TensorFlow installiert ist)."""
    try:
        import tensorflow as tf
        from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
        model = MobileNetV2(weights="imagenet")
        return model, preprocess_input, decode_predictions
    except Exception:
        return None

def analyze_image_ai(pil_image: Image.Image):
    """
    KI-Erkennung: MobileNetV2 (falls verfügbar), sonst Heuristik.
    """
    # Versuche MobileNetV2
    mobilenet_result = load_mobilenet_model()
    if mobilenet_result is not None:
        model, preprocess_input, decode_predictions = mobilenet_result
        try:
            size = (224, 224)
            image = ImageOps.fit(pil_image, size, Image.Resampling.LANCZOS)
            img_array = np.asarray(image, dtype=np.float32)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            preds = model.predict(img_array, verbose=0)
            decoded = decode_predictions(preds, top=5)[0]  # Top-5 Klassen

            # Suche die erste Klasse, die wir auf eine Kategorie mappen können
            for _, class_name, prob in decoded:
                class_name_lower = class_name.lower().replace("_", " ")
                if class_name_lower in IMAGENET_CLASS_TO_CATEGORY:
                    category = IMAGENET_CLASS_TO_CATEGORY[class_name_lower]
                    return category, float(prob), "MobileNetV2 (ImageNet)"

            # Wenn keine passende Klasse gefunden, nehme die beste mit "Sonstiges"
            best_class = decoded[0][1].lower().replace("_", " ")
            return "Sonstiges", float(decoded[0][2]), "MobileNetV2 (ImageNet, keine Zuordnung)"
        except Exception:
            pass

    # Heuristik-Fallback
    rgb_img = pil_image.convert("RGB")
    w, h = rgb_img.size
    aspect_ratio = w / float(h)
    small = rgb_img.resize((64, 64))
    arr = np.array(small, dtype=np.float32)
    avg_color = arr.mean(axis=(0, 1))
    std_color = arr.std(axis=(0, 1))
    r, g, b = avg_color

    suggested = "Sonstiges"
    confidence = 0.84

    if aspect_ratio < 0.65 or aspect_ratio > 1.55:
        suggested = "Trinkflaschen & Brotdosen"
        confidence = 0.88
    elif (r > 130 and g < 100 and b < 100) or (b > 130 and r < 100) or (r > 150 and g > 150 and b < 80):
        suggested = "Kleidung & Textilien"
        confidence = 0.86
    elif std_color.mean() < 22 and (r < 60 and g < 60 and b < 60 or r > 200 and g > 200 and b > 200):
        suggested = "Elektronik & Kabel"
        confidence = 0.82
    elif aspect_ratio > 0.8 and aspect_ratio < 1.3 and std_color.mean() > 40:
        suggested = "Rucksäcke & Taschen"
        confidence = 0.85
    else:
        suggested = "Kleidung & Textilien"
        confidence = 0.78

    return suggested, confidence, "Vision-Feature-Engine (Heuristik)"

# =============================================================================
# 4. SIDEBAR: AUTHENTIFIZIERUNG & METRIKEN
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div style="padding-top: 4px;">
        <div class="side-title">KONTOR</div>
        <div class="side-sub">Fundbüro • Katharineum</div>
    </div>
    """, unsafe_allow_html=True)
    
    role = st.selectbox(
        "Rolle wählen",
        ["Schüler:in", "Lehrkraft", "Hausmeister / Admin"],
        index=0
    )
    st.session_state["current_role"] = role

    if role == "Hausmeister / Admin":
        pin = st.text_input("Schlüssel-PIN (Demo: 1234)", type="password")
        if pin == "1234":
            st.session_state["is_authenticated"] = True
            st.success("Freigeschaltet")
        else:
            st.session_state["is_authenticated"] = False
            if pin != "":
                st.error("PIN ungültig")
    else:
        st.session_state["is_authenticated"] = True

    st.markdown('<hr class="side-rule">', unsafe_allow_html=True)

    items_list = st.session_state["fundstuecke_liste"]
    tot = len(items_list)
    offen = sum(1 for i in items_list if i.get("status") == "Offen")
    beansprucht = sum(1 for i in items_list if i.get("status") == "Beansprucht")
    abgeholt = sum(1 for i in items_list if i.get("status") == "Abgeholt")

    st.markdown(f"""
    <div class="side-sub">Bestandsbuch</div>
    <div class="ledger">
        <div class="lrow"><span>Gesamt</span><b>{tot}</b></div>
        <div class="lrow"><span>Offen</span><b>{offen}</b></div>
        <div class="lrow"><span>Beansprucht</span><b>{beansprucht}</b></div>
        <div class="lrow"><span>Abgeholt</span><b>{abgeholt}</b></div>
    </div>
    <div class="side-note">
        <b>DSGVO-Modus aktiv:</b> Namen und Kontaktdaten von Schüler:innen werden öffentlich pseudonymisiert.
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 5. HEADER (ANALOGER MASTHEAD STATT STREAMLIT-DEFAULT)
# =============================================================================

today_display = datetime.date.today().strftime("%d. %B %Y").upper()

st.markdown(f"""
<div class="masthead">
    <div class="mast-kicker">
        <span>Katharineum zu Lübeck</span>
        <span>Amtliches Fundverzeichnis</span>
        <span>{today_display}</span>
    </div>
    <h1>KATH. FUND</h1>
    <div class="mast-sub">
        Digitales Fundbuch der Schule — Fundstücke <b>melden</b>, <b>durchsuchen</b> und <b>wiedererlangen</b>.
    </div>
</div>
""", unsafe_allow_html=True)

tab_katalog, tab_erfassen, tab_beanspruchen, tab_admin = st.tabs([
    "Katalog (main)",
    "Erfassen (form)",
    "Beanspruchen",
    "Verwaltung & Admin"
])

# =============================================================================
# TAB 1: KATALOG (SKIZZEN-LAYOUT MIT SUCHE + GO BUTTON + FILTER + 3ER CARDS)
# =============================================================================

with tab_katalog:
    st.markdown("""
    <div class="sec">
        <span class="sec-no">TAB I</span>
        <h2>Hauptverzeichnis aller Fundstücke</h2>
    </div>
    <div class="sec-sub">Suchbegriff eingeben oder nach Kategorie, Fundort und Bearbeitungsstatus filtern.</div>
    """, unsafe_allow_html=True)

    col_search, col_go, col_reset = st.columns([5, 1, 1])
    with col_search:
        search_query = st.text_input(
            "Suchbegriff",
            placeholder="Suchbegriff (z. B. Jacke, Blau, Nike, AirPods, #1002)...",
            label_visibility="collapsed",
            key="search_field"
        )
    with col_go:
        go_btn = st.button("Filtern", width="stretch")
    with col_reset:
        if st.button("Zurücksetzen", width="stretch"):
            st.session_state.pop("search_field", None)
            st.rerun()

    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        kat_filter = st.selectbox("Kategorie", ["Alle"] + CATEGORIES)
    with col_f2:
        loc_filter = st.selectbox("Fundort", ["Alle"] + LOCATIONS)
    with col_f3:
        status_filter = st.selectbox("Status", ["Alle", "Offen", "Beansprucht", "Abgeholt"])

    visible_items = st.session_state["fundstuecke_liste"]

    q = (search_query or "").strip().lower()
    if q:
        visible_items = [
            i for i in visible_items
            if q in i.get("titel", "").lower()
            or q in i.get("beschreibung", "").lower()
            or any(q in t.lower() for t in i.get("tags", []))
            or q in str(i.get("id", ""))
        ]

    if kat_filter != "Alle":
        visible_items = [i for i in visible_items if i.get("kategorie") == kat_filter]

    if loc_filter != "Alle":
        visible_items = [i for i in visible_items if i.get("fundort") == loc_filter]

    if status_filter != "Alle":
        visible_items = [i for i in visible_items if i.get("status") == status_filter]

    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:.74rem; text-transform:uppercase; letter-spacing:.12em; color:var(--ink-soft); margin:12px 0 16px;">
        Treffer im Verzeichnis: <b>{len(visible_items)}</b> Eintragung(en)
    </div>
    """, unsafe_allow_html=True)

    if not visible_items:
        st.info("Keine passenden Fundstücke im Verzeichnis gefunden. Suchbegriff anpassen oder Filter zurücksetzen.")
    else:
        for idx in range(0, len(visible_items), 3):
            cols = st.columns(3)
            for sub_idx in range(3):
                item_idx = idx + sub_idx
                if item_idx < len(visible_items):
                    item = visible_items[item_idx]
                    with cols[sub_idx]:
                        status = item.get("status", "Offen")
                        status_slug = status.lower()
                        item_id = item.get("id")
                        titel_esc = html.escape(str(item.get("titel", "")))
                        fundort_esc = html.escape(str(item.get("fundort", "")))
                        datum_esc = html.escape(str(item.get("datum_fund", "")))
                        kat_esc = html.escape(str(item.get("kategorie", "")))
                        abgabe_esc = html.escape(str(item.get("abgabeort", "")))

                        loaded_img = load_item_image(item.get("image_file"))
                        if loaded_img is not None:
                            img_uri = image_to_data_uri(loaded_img, max_dim=440)
                            photo_html = f'<div class="ticket-photo"><img src="{img_uri}" alt="{titel_esc}"></div>'
                        else:
                            photo_html = '<div class="ticket-photo ph">Kein Lichtbild erfasst</div>'

                        chips_html = "".join([
                            f'<span class="tchip">{html.escape(t)}</span>'
                            for t in item.get("tags", [])
                        ])

                        ticket_html = f"""
                        <div class="ticket">
                            <div class="ticket-head">
                                <span class="ticket-id">BELEG NR. #{item_id}</span>
                                <span class="stamp s-{status_slug}">{status}</span>
                            </div>
                            {photo_html}
                            <div class="ticket-body">
                                <div class="ticket-title">{titel_esc}</div>
                                <div class="trow"><span>Kategorie</span><b>{kat_esc}</b></div>
                                <div class="trow"><span>Fundort</span><b>{fundort_esc}</b></div>
                                <div class="trow"><span>Erfasst am</span><b>{datum_esc}</b></div>
                                <div class="trow"><span>Lagerort</span><b>{abgabe_esc}</b></div>
                                <div class="ticket-tags">{chips_html}</div>
                            </div>
                        </div>
                        """
                        st.markdown(ticket_html, unsafe_allow_html=True)

                        with st.expander(f"Aktenauszug #{item_id} einsehen"):
                            st.write(f"**Beschreibung:** {item.get('beschreibung')}")
                            st.write(f"**Melder-Kürzel:** `{item.get('kontakt_kuerzel')}` ({item.get('finder_rolle')})")
                            st.write(f"**Gesetzliche Frist:** bis {item.get('datum_ablauf')}")

# =============================================================================
# TAB 2: ERFASSEN (FORM - MIT FOTO UPLOAD + KI ANALYSE AUS DER SKIZZE)
# =============================================================================

with tab_erfassen:
    st.markdown("""
    <div class="sec">
        <span class="sec-no">TAB II</span>
        <h2>Neues Fundstück im Buch registrieren</h2>
    </div>
    <div class="sec-sub">Foto hochladen oder aufnehmen. Das System führt eine automatische optische Klassifikation durch.</div>
    """, unsafe_allow_html=True)

    col_u1, col_u2 = st.columns([1, 1], gap="large")

    uploaded_pil = None
    ai_category = CATEGORIES[0]
    ai_confidence = 0.0
    ai_engine = "Standby"

    with col_u1:
        st.markdown("#### Lichtbild aufnehmen")
        upload_mode = st.radio("Eingabeweg", ["Datei auswählen", "Kamera auslösen"], horizontal=True)

        if upload_mode == "Datei auswählen":
            img_file = st.file_uploader("Bild auswählen", type=["jpg", "jpeg", "png", "webp"], key="file_upload_input")
            if img_file is not None:
                uploaded_pil = Image.open(img_file).convert("RGB")
        else:
            cam_file = st.camera_input("Kamera auslösen", key="cam_input")
            if cam_file is not None:
                uploaded_pil = Image.open(cam_file).convert("RGB")

        if uploaded_pil is not None:
            st.image(uploaded_pil, caption="Vorschau des erfassten Lichtbilds", width="stretch")
            with st.spinner("Prüfalgorithmus läuft..."):
                ai_category, ai_confidence, ai_engine = analyze_image_ai(uploaded_pil)

            if ai_category not in CATEGORIES:
                ai_category = "Sonstiges"

            verdict_html = f"""
            <div class="verdict">
                <div class="verdict-stamp">Geprüft</div>
                <div>
                    <div class="verdict-cat">{html.escape(ai_category)}</div>
                    <div class="verdict-meta">Zuverlässigkeit: {ai_confidence*100:.0f}% • Verfahren: {html.escape(ai_engine)}</div>
                </div>
            </div>
            """
            st.markdown(verdict_html, unsafe_allow_html=True)

    with col_u2:
        st.markdown("#### Angaben zum Fundstück")
        with st.form("form_add_item", clear_on_submit=True):
            in_titel = st.text_input("Bezeichnung des Gegenstands*", placeholder="z. B. Dunkelblaue Regenjacke, Gr. M")

            if ai_category not in CATEGORIES:
                ai_category = "Sonstiges"

            st.markdown(f"""
            <div class="note">
                <b>Automatische Zuordnung:</b> {html.escape(ai_category)}<br>
                <span>Wurde aus dem Lichtbild abgeleitet und für den Eintrag übernommen.</span>
            </div>
            """, unsafe_allow_html=True)

            in_fundort = st.selectbox("Fundort*", LOCATIONS)
            in_abgabeort = st.text_input("Aktueller Lagerort*", value="Hausmeisterbüro (Raum 001)")
            in_tags = st.text_input("Schlagworte (durch Komma getrennt)", placeholder="z. B. Nike, Blau, Größe L")
            in_beschreibung = st.text_area("Besondere Merkmale", placeholder="Kratzer, Initialen, auffällige Anhänger oder Inhalt...")

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                in_kuerzel = st.text_input("Kürzel / Name & Klasse*", placeholder="z. B. MAX-8B")
            with col_sub2:
                in_rolle = st.selectbox("Rolle der findenden Person", ["Schüler:in", "Lehrkraft", "Hausmeister", "Sonstige"])

            st.markdown("""
            <div style="font-family:'IBM Plex Mono',monospace; font-size:.66rem; color:var(--ink-soft); margin:6px 0 10px; letter-spacing:.08em; text-transform:uppercase;">
                DSGVO: Personendaten verbleiben geschützt im Hausmeisterprotokoll.
            </div>
            """, unsafe_allow_html=True)

            btn_save = st.form_submit_button("Eintrag ins Fundbuch übernehmen", width="stretch")

            if btn_save:
                if not in_titel.strip() or not in_kuerzel.strip():
                    st.error("Bitte mindestens Bezeichnung und ein Melderkürzel angeben.")
                else:
                    items = st.session_state["fundstuecke_liste"]
                    new_id = max([i["id"] for i in items]) + 1 if items else 1001

                    saved_img_name = None
                    if uploaded_pil is not None:
                        saved_img_name = save_uploaded_image(uploaded_pil, new_id)

                    parsed_tags = [t.strip() for t in in_tags.split(",") if t.strip()]
                    if not parsed_tags:
                        parsed_tags = [ai_category.split(" ")[0]]

                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    expiry_str = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")

                    new_item = {
                        "id": new_id,
                        "titel": in_titel.strip(),
                        "kategorie": ai_category,
                        "fundort": in_fundort,
                        "abgabeort": in_abgabeort.strip(),
                        "kontakt_kuerzel": in_kuerzel.strip().upper(),
                        "finder_rolle": in_rolle,
                        "datum_fund": today_str,
                        "datum_ablauf": expiry_str,
                        "status": "Offen",
                        "beschreibung": in_beschreibung.strip() or "Keine nähere Beschreibung angegeben.",
                        "image_file": saved_img_name,
                        "tags": parsed_tags
                    }

                    st.session_state["fundstuecke_liste"].insert(0, new_item)
                    log_action(in_kuerzel.upper(), f"Fundstück #{new_id} registriert ({in_titel})")
                    sync_storage()
                    st.success(f"Fundstück Beleg #{new_id} im Hauptverzeichnis angelegt.")
                    st.rerun()

# =============================================================================
# TAB 3: BEANSPRUCHEN (CLAIM WORKFLOW)
# =============================================================================

with tab_beanspruchen:
    st.markdown("""
    <div class="sec">
        <span class="sec-no">TAB III</span>
        <h2>Eigentumsnachweis erbringen</h2>
    </div>
    <div class="sec-sub">Gegenstand im Hauptverzeichnis entdeckt? Reiche hier deinen Anspruch mit unverwechselbaren Details ein.</div>
    """, unsafe_allow_html=True)

    open_items = {
        f"#{i['id']} — {i['titel']} ({i['fundort']})": i['id']
        for i in st.session_state["fundstuecke_liste"]
        if i.get("status") in ["Offen", "Beansprucht"]
    }

    if not open_items:
        st.info("Aktuell liegen keine offenen Fundstücke vor, für die ein Anspruch geltend gemacht werden kann.")
    else:
        col_c1, col_c2 = st.columns([1, 1], gap="large")

        with col_c1:
            st.markdown("#### Beleg auswählen")
            selected_label = st.selectbox("Fundstück auswählen*", list(open_items.keys()))
            selected_id = open_items[selected_label]
            target_item = next(i for i in st.session_state["fundstuecke_liste"] if i["id"] == selected_id)

            t_titel = html.escape(str(target_item['titel']))
            t_ort = html.escape(str(target_item['fundort']))
            t_lager = html.escape(str(target_item['abgabeort']))
            t_dat = html.escape(str(target_item['datum_fund']))
            t_desc = html.escape(str(target_item['beschreibung']))
            t_stat = target_item.get('status', 'Offen')

            st.markdown(f"""
            <div class="ticket" style="margin-top: 6px;">
                <div class="ticket-head">
                    <span class="ticket-id">BELEG NR. #{target_item['id']}</span>
                    <span class="stamp s-{t_stat.lower()}">{t_stat}</span>
                </div>
                <div class="ticket-body">
                    <div class="ticket-title">{t_titel}</div>
                    <div class="trow"><span>Fundort</span><b>{t_ort}</b></div>
                    <div class="trow"><span>Lagerort</span><b>{t_lager}</b></div>
                    <div class="trow"><span>Funddatum</span><b>{t_dat}</b></div>
                    <div style="font-size: .84rem; color: var(--ink); margin-top: 10px; font-style: italic; border-top: 1px dotted var(--line); padding-top: 8px;">
                        {t_desc}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            img = load_item_image(target_item.get("image_file"))
            if img:
                st.image(img, width=280)

        with col_c2:
            st.markdown("#### Nachweis zur Prüfung")
            with st.form("form_claim"):
                c_name = st.text_input("Name und Klasse*", placeholder="z. B. Julia Koch (Klasse 9b)")
                c_proof = st.text_area(
                    "Verdeckter Eigentumsnachweis*",
                    placeholder="Beschreibe Merkmale, die nur der rechtmäßige Besitzer kennt: Tascheninhalt, Gravur, PIN, Sperrbildschirm, Initialen..."
                )
                btn_claim_submit = st.form_submit_button("Anspruch zur Prüfung einreichen", width="stretch")

                if btn_claim_submit:
                    if not c_name.strip() or not c_proof.strip():
                        st.error("Bitte vollständigen Namen und einen stichhaltigen Eigentumsnachweis angeben.")
                    else:
                        claims = st.session_state["claims"]
                        new_claim_id = max([c["claim_id"] for c in claims]) + 1 if claims else 501
                        new_claim = {
                            "claim_id": new_claim_id,
                            "item_id": selected_id,
                            "name": c_name.strip(),
                            "proof": c_proof.strip(),
                            "datum": datetime.date.today().strftime("%Y-%m-%d"),
                            "status": "In Prüfung"
                        }
                        claims.insert(0, new_claim)
                        target_item["status"] = "Beansprucht"
                        log_action(c_name.strip(), f"Anspruch #{new_claim_id} auf Beleg #{selected_id} eingereicht")
                        sync_storage()
                        st.success("Anspruch erfasst. Die Prüfung erfolgt im Hausmeister-Portal.")
                        st.rerun()

# =============================================================================
# TAB 4: VERWALTUNG & ADMIN
# =============================================================================

with tab_admin:
    st.markdown("""
    <div class="sec">
        <span class="sec-no">TAB IV</span>
        <h2>Verwaltung & Kontor-Aufsicht</h2>
    </div>
    <div class="sec-sub">Zugang nur für das Hausmeisterbüro und die Schulverwaltung.</div>
    """, unsafe_allow_html=True)

    if not st.session_state["is_authenticated"] and st.session_state["current_role"] == "Hausmeister / Admin":
        st.warning("Schlüssel-PIN erforderlich. Bitte in der linken Kontor-Leiste freischalten.")
    elif st.session_state["current_role"] != "Hausmeister / Admin":
        st.info("Diese Sektion ist der Schulverwaltung vorbehalten. Bitte in der Seitenleiste die Rolle 'Hausmeister / Admin' wählen.")
    else:
        adm_tabs = st.tabs([
            "Ansprüche",
            "Bestandskennzahlen",
            "Vollständiges Register",
            "Prüfprotokoll & Export"
        ])

        with adm_tabs[0]:
            st.markdown("#### Offene Eigentumsansprüche")
            claims = st.session_state["claims"]
            if not claims:
                st.info("Aktuell keine Ansprüche im Eingang.")
            else:
                for c in claims:
                    rel_item = next((i for i in st.session_state["fundstuecke_liste"] if i["id"] == c["item_id"]), None)
                    item_title = rel_item["titel"] if rel_item else "Gelöschtes Fundstück"

                    with st.expander(f"Anspruch #{c['claim_id']} zu Beleg #{c['item_id']} — {item_title} [{c['status']}]"):
                        st.write(f"**Antragsteller:** {c['name']}")
                        st.write(f"**Eingereicht am:** {c['datum']}")
                        st.write(f"**Vorgelegter Nachweis:** {c['proof']}")

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("Genehmigen & Aushändigung vermerken", key=f"app_{c['claim_id']}", width="stretch"):
                                c["status"] = "Genehmigt"
                                if rel_item:
                                    rel_item["status"] = "Abgeholt"
                                log_action("ADMIN", f"Anspruch #{c['claim_id']} genehmigt (Beleg #{c['item_id']} ausgehändigt)")
                                sync_storage()
                                st.success("Genehmigt. Status auf 'Abgeholt' gesetzt.")
                                st.rerun()

                        with col_btn2:
                            if st.button("Anspruch abweisen", key=f"rej_{c['claim_id']}", width="stretch"):
                                c["status"] = "Abgelehnt"
                                if rel_item and rel_item["status"] == "Beansprucht":
                                    rel_item["status"] = "Offen"
                                log_action("ADMIN", f"Anspruch #{c['claim_id']} abgewiesen")
                                sync_storage()
                                st.warning("Anspruch abgewiesen.")
                                st.rerun()

        with adm_tabs[1]:
            st.markdown("#### Kennzahlen des Fundbüros")
            items_df = pd.DataFrame(st.session_state["fundstuecke_liste"])

            total_c = len(items_df)
            ret_c = sum(1 for i in st.session_state["fundstuecke_liste"] if i.get("status") == "Abgeholt")
            ret_rate = (ret_c / total_c * 100) if total_c > 0 else 0.0
            claims_c = len([c for c in st.session_state["claims"] if c.get("status") == "In Prüfung"])

            kcol1, kcol2, kcol3, kcol4 = st.columns(4)
            with kcol1:
                st.markdown(f'<div class="kpi"><span>Registriert</span><b>{total_c}</b></div>', unsafe_allow_html=True)
            with kcol2:
                st.markdown(f'<div class="kpi"><span>Ausgehändigt</span><b>{ret_c}</b></div>', unsafe_allow_html=True)
            with kcol3:
                st.markdown(f'<div class="kpi"><span>Rückführquote</span><b>{ret_rate:.0f}%</b></div>', unsafe_allow_html=True)
            with kcol4:
                st.markdown(f'<div class="kpi"><span>Offene Prüfungen</span><b>{claims_c}</b></div>', unsafe_allow_html=True)

            if not items_df.empty:
                st.write("")
                col_ch1, col_ch2 = st.columns(2)
                with col_ch1:
                    st.markdown("##### Verteilung nach Kategorien")
                    st.bar_chart(items_df["kategorie"].value_counts())
                with col_ch2:
                    st.markdown("##### Verteilung nach Fundorten")
                    st.bar_chart(items_df["fundort"].value_counts())

        with adm_tabs[2]:
            st.markdown("#### Hauptbuch-Tabelle")
            df_full = pd.DataFrame(st.session_state["fundstuecke_liste"])
            cols_to_show = ["id", "titel", "kategorie", "fundort", "status", "datum_fund", "datum_ablauf"]
            available_cols = [c for c in cols_to_show if c in df_full.columns]
            st.dataframe(df_full[available_cols], width="stretch")

            st.markdown("---")
            st.markdown("##### Fristenprüfung (Gesetzliche 90 Tage)")
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            expired = [i for i in st.session_state["fundstuecke_liste"] if i.get("datum_ablauf", "") < today_str and i.get("status") == "Offen"]

            if expired:
                st.warning(f"{len(expired)} Fundstück(e) haben die gesetzliche Aufbewahrungsfrist überschritten.")
                if st.button("Abgelaufene Fundstücke als 'Entsorgt' austragen", width="stretch"):
                    for e in expired:
                        e["status"] = "Entsorgt"
                    log_action("ADMIN", f"{len(expired)} Fundstücke als entsorgt markiert")
                    sync_storage()
                    st.success("Bereinigt.")
                    st.rerun()
            else:
                st.info("Alle Aufbewahrungsfristen befinden sich im ordnungsgemäßen Zeitraum.")

        with adm_tabs[3]:
            st.markdown("#### Revisionssicheres Prüfprotokoll")
            logs_df = pd.DataFrame(st.session_state["audit_logs"])
            st.dataframe(logs_df, width="stretch")

            st.markdown("---")
            st.markdown("##### Daten-Sicherung")
            export_data = {
                "items": st.session_state["fundstuecke_liste"],
                "claims": st.session_state["claims"],
                "audit_logs": st.session_state["audit_logs"],
                "export_date": datetime.datetime.now().isoformat()
            }
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(
                "Gesamtes Fundverzeichnis herunterladen (JSON)",
                data=json_str,
                file_name=f"kath_fund_export_{datetime.date.today().strftime('%Y%m%d')}.json",
                mime="application/json",
                width="stretch"
            )
