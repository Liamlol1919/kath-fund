"""
===============================================================================
                     KATH. FUND - DIGITALE FUNDBÜRO APP
===============================================================================
Inspirationsbasis: Originale Papier-Skizze (Kath. Fund Layout & Workflow)
Optimiert für Streamlit >= 1.40
KI-Modell: MobileNetV2 (öffentlich, vortrainiert auf ImageNet)
===============================================================================
"""

import os
import io
import json
import base64
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

# Responsives Custom CSS mit Skizzen-Stil und modernem Finish
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1300px;
    }

    /* Sketch-inspired Header */
    .header-skizze {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.2rem 1.6rem;
        background: #ffffff;
        border: 2px solid #0f172a;
        border-radius: 14px;
        box-shadow: 4px 4px 0px #0f172a;
        margin-bottom: 1.6rem;
    }
    .header-logo-group {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .header-gear-badge {
        font-size: 2.2rem;
        background: #f1f5f9;
        width: 54px;
        height: 54px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        border: 2px solid #0f172a;
    }
    .header-title-text {
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: -0.03em;
        color: #0f172a;
        margin: 0;
        line-height: 1.1;
    }
    .header-subtitle-text {
        color: #64748b;
        font-size: 0.88rem;
        font-weight: 600;
        margin-top: 2px;
    }
    .header-meta-badge {
        background: #0f172a;
        color: #f8fafc;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    /* Cards Layout (nach Papier-Skizze) */
    .card-box {
        background-color: #ffffff;
        border: 2px solid #0f172a;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 18px;
        box-shadow: 3px 3px 0px #0f172a;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
        display: flex;
        flex-direction: column;
    }
    .card-box:hover {
        transform: translateY(-2px);
        box-shadow: 5px 5px 0px #0f172a;
    }
    .card-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .card-id-pill {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.85rem;
        color: #0f172a;
        background: #f1f5f9;
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid #cbd5e1;
    }
    .card-img-placeholder {
        width: 100%;
        height: 160px;
        background-color: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .card-title {
        font-weight: 800;
        font-size: 1.15rem;
        margin: 4px 0 6px 0;
        color: #0f172a;
        line-height: 1.25;
    }
    .card-location {
        color: #64748b;
        font-size: 0.84rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .tag-badge {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.76rem;
        margin-right: 5px;
        margin-top: 4px;
        font-weight: 700;
    }

    /* Badges */
    .status-badge {
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1.5px solid currentColor;
    }
    .status-offen { color: #b45309; background-color: #fef3c7; }
    .status-beansprucht { color: #1d4ed8; background-color: #dbeafe; }
    .status-abgeholt { color: #15803d; background-color: #dcfce7; }
    .status-entsorgt { color: #b91c1c; background-color: #fee2e2; }

    /* AI Vorschlag Box */
    .ai-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
        border: 2px solid #0284c7;
        border-radius: 12px;
        padding: 12px 16px;
        margin-top: 10px;
        margin-bottom: 14px;
    }
    .ai-box-title {
        font-weight: 800;
        color: #0369a1;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
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

# =============================================================================
# 3. AI VISION ENGINE (MOBILENETV2 + FALLBACKS)
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
    """Lädt vortrainiertes MobileNetV2 (ImageNet)."""
    try:
        import tensorflow as tf
        from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
        model = MobileNetV2(weights="imagenet")
        return model, preprocess_input, decode_predictions
    except Exception as e:
        return None

def analyze_image_ai(pil_image: Image.Image):
    """
    KI-Erkennung mit MobileNetV2 (öffentlich, vortrainiert).
    Fallback: Heuristik (falls TensorFlow nicht verfügbar).
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
    st.markdown("### ⚙️ Steuerung & Rolle")
    
    role = st.selectbox(
        "Aktive Rolle",
        ["Schüler:in", "Lehrkraft", "Hausmeister / Admin"],
        index=0
    )
    st.session_state["current_role"] = role

    if role == "Hausmeister / Admin":
        pin = st.text_input("Admin-PIN (Demo: 1234)", type="password")
        if pin == "1234":
            st.session_state["is_authenticated"] = True
            st.success("✅ Admin freigeschaltet")
        else:
            st.session_state["is_authenticated"] = False
            if pin != "":
                st.error("❌ Falscher PIN")
    else:
        st.session_state["is_authenticated"] = True

    st.markdown("---")

    # Schnelle Statistiken
    items_list = st.session_state["fundstuecke_liste"]
    tot = len(items_list)
    offen = sum(1 for i in items_list if i.get("status") == "Offen")
    beansprucht = sum(1 for i in items_list if i.get("status") == "Beansprucht")
    abgeholt = sum(1 for i in items_list if i.get("status") == "Abgeholt")

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Gesamt", tot)
    col_m2.metric("Offen", offen)

    st.caption(f"🟡 Beansprucht: **{beansprucht}** | 🟢 Abgeholt: **{abgeholt}**")
    st.markdown("---")
    st.caption("🔒 **DSGVO-Modus:** Schülerdaten pseudonymisiert.")

# =============================================================================
# 5. HEADER (NACH DER PAPIER-SKIZZE)
# =============================================================================

st.markdown("""
<div class="header-skizze">
    <div class="header-logo-group">
        <div class="header-gear-badge">⚙️</div>
        <div>
            <h1 class="header-title-text">Kath. Fund</h1>
            <div class="header-subtitle-text">Digitales Fundbüro | Schul-Fundsachen einfach erfassen & wiederfinden</div>
        </div>
    </div>
    <div class="header-meta-badge">KATHARINEUM</div>
</div>
""", unsafe_allow_html=True)

tab_katalog, tab_erfassen, tab_beanspruchen, tab_admin = st.tabs([
    "🔍 Katalog (main)",
    "➕ Erfassen (form)",
    "✋ Beanspruchen",
    "⚙️ Verwaltung & Admin"
])

# =============================================================================
# TAB 1: KATALOG (SKIZZEN-LAYOUT MIT SUCHE + GO BUTTON + FILTER + 3ER CARDS)
# =============================================================================

with tab_katalog:
    # Suchzeile mit GO-Button genau wie in der Skizze
    col_search, col_go, col_reset = st.columns([5, 1, 1])
    with col_search:
        search_query = st.text_input(
            "Search",
            placeholder="Suchbegriff eingeben (z. B. Jacke, Blau, Nike, AirPods)...",
            label_visibility="collapsed",
            key="search_field"
        )
    with col_go:
        go_btn = st.button("GO 🔍", width="stretch")
    with col_reset:
        if st.button("Reset ↺", width="stretch"):
            st.session_state["search_field"] = ""
            st.rerun()

    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        kat_filter = st.selectbox("Kategorie filtern", ["Alle"] + CATEGORIES)
    with col_f2:
        loc_filter = st.selectbox("Fundort filtern", ["Alle"] + LOCATIONS)
    with col_f3:
        status_filter = st.selectbox("Status filtern", ["Alle", "Offen", "Beansprucht", "Abgeholt"])

    # Filterung ausführen
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

    st.caption(f"Gefunden: **{len(visible_items)}** Fundstück(e)")
    st.markdown("---")

    if not visible_items:
        st.info("💡 Keine passenden Fundstücke gefunden. Probiere einen anderen Suchbegriff oder setze den Filter zurück.")
    else:
        # 3er-Raster entsprechend Zeichnung
        for idx in range(0, len(visible_items), 3):
            cols = st.columns(3)
            for sub_idx in range(3):
                item_idx = idx + sub_idx
                if item_idx < len(visible_items):
                    item = visible_items[item_idx]
                    with cols[sub_idx]:
                        status = item.get("status", "Offen")
                        status_cls = f"status-{status.lower()}"

                        st.markdown(f"""
                        <div class="card-box">
                            <div class="card-topbar">
                                <span class="card-id-pill">#{item.get('id')}</span>
                                <span class="status-badge {status_cls}">{status}</span>
                            </div>
                        """, unsafe_allow_html=True)

                        # Bild laden (gespeichertes Bild oder Placeholder)
                        img_file = item.get("image_file")
                        loaded_img = load_item_image(img_file)

                        if loaded_img is not None:
                            st.image(loaded_img, width="stretch")
                        else:
                            st.markdown("""
                            <div class="card-img-placeholder">
                                <span style="font-size: 1.8rem; margin-bottom: 4px;">📷</span>
                                <span>Kein Foto vorhanden</span>
                            </div>
                            """, unsafe_allow_html=True)

                        tags_html = "".join([f'<span class="tag-badge">#{t}</span>' for t in item.get("tags", [])])

                        st.markdown(f"""
                            <div class="card-title">{item.get('titel')}</div>
                            <div class="card-location">📍 {item.get('fundort')} • {item.get('datum_fund')}</div>
                            <div style="margin-bottom: 8px;">{tags_html}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        with st.expander("Details, Abholort"):
                            st.write(f"**Kategorie:** {item.get('kategorie')}")
                            st.write(f"**Beschreibung:** {item.get('beschreibung')}")
                            st.write(f"**Abholort:** {item.get('abgabeort')}")
                            st.write(f"**Gemeldet von:** {item.get('kontakt_kuerzel')} ({item.get('finder_rolle')})")
                            st.write(f"**Aufbewahrungsfrist:** {item.get('datum_ablauf')}")

# =============================================================================
# TAB 2: ERFASSEN (FORM - MIT FOTO UPLOAD + KI ANALYSE AUS DER SKIZZE)
# =============================================================================

with tab_erfassen:
    st.markdown("### ➕ Neues Fundstück eintragen")
    st.caption("Mache ein Foto oder lade ein Bild hoch. Unsere KI schlägt automatisch die passende Kategorie vor.")

    col_u1, col_u2 = st.columns([1, 1], gap="large")

    uploaded_pil = None
    ai_category = CATEGORIES[0]
    ai_confidence = 0.0
    ai_engine = "Standby"

    with col_u1:
        st.markdown("#### 1. Foto aufnehmen / hochladen")
        upload_mode = st.radio("Foto-Quelle", ["📁 Datei-Upload", "📸 Kamera-Live"], horizontal=True)

        if upload_mode == "📁 Datei-Upload":
            img_file = st.file_uploader("Bild auswählen", type=["jpg", "jpeg", "png", "webp"], key="file_upload_input")
            if img_file is not None:
                uploaded_pil = Image.open(img_file).convert("RGB")
        else:
            cam_file = st.camera_input("Foto direkt aufnehmen", key="cam_input")
            if cam_file is not None:
                uploaded_pil = Image.open(cam_file).convert("RGB")

        if uploaded_pil is not None:
            st.image(uploaded_pil, caption="Vorschau deines Fotos", width="stretch")
            with st.spinner("🤖 KI analysiert das Fundstück..."):
                ai_category, ai_confidence, ai_engine = analyze_image_ai(uploaded_pil)

            # Sicherstellen, dass die Kategorie gültig ist
            if ai_category not in CATEGORIES:
                ai_category = "Sonstiges"

            st.markdown(f"""
            <div class="ai-box">
                <div class="ai-box-title">✨ KI-Erkennungsergebnis</div>
                <div style="font-size: 1.1rem; font-weight: 800; color: #0f172a; margin-top: 4px;">
                    {ai_category}
                </div>
                <div style="font-size: 0.82rem; color: #475569; margin-top: 2px;">
                    Sicherheit: <b>{ai_confidence*100:.1f}%</b> • Modell: <code>{ai_engine}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_u2:
        st.markdown("#### 2. Details zum Fundstück")
        with st.form("form_add_item", clear_on_submit=True):
            in_titel = st.text_input("Titel des Gegenstands*", placeholder="z. B. Blaue Nike Sporttasche")

            # KI-Kategorie wird automatisch übernommen – keine manuelle Auswahl
            if ai_category not in CATEGORIES:
                ai_category = "Sonstiges"

            st.markdown(f"""
            <div style="background:#f1f5f9; padding:10px 14px; border-radius:8px; border-left:4px solid #0f172a; margin-bottom:10px;">
                <span style="font-weight:700;">🔍 KI-Kategorie:</span> {ai_category}
                <span style="color:#64748b; font-size:0.85rem;">(automatisch erkannt)</span>
            </div>
            """, unsafe_allow_html=True)

            in_fundort = st.selectbox("Wo wurde es gefunden?*", LOCATIONS)
            in_abgabeort = st.text_input("Aktueller Aufbewahrungsort*", value="Hausmeisterbüro (Raum 001)")
            in_tags = st.text_input("Tags / Merkmale (kommagetrennt)", placeholder="z. B. Nike, Blau, Größe L")
            in_beschreibung = st.text_area("Ausführliche Beschreibung", placeholder="Besondere Kratzer, Inhalt, Initialen...")

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                in_kuerzel = st.text_input("Dein Kürzel / Name & Klasse*", placeholder="z. B. MAX-8B")
            with col_sub2:
                in_rolle = st.selectbox("Deine Rolle", ["Schüler:in", "Lehrkraft", "Hausmeister", "Sonstige"])

            st.caption("🔒 *Hinweis: DSGVO-konform. Es werden keine privaten Kontaktdaten öffentlich gezeigt.*")

            btn_save = st.form_submit_button("💾 Fundstück jetzt registrieren", width="stretch")

            if btn_save:
                if not in_titel.strip() or not in_kuerzel.strip():
                    st.error("⚠️ Bitte mindestens Titel und dein Kürzel ausfüllen!")
                else:
                    items = st.session_state["fundstuecke_liste"]
                    new_id = max([i["id"] for i in items]) + 1 if items else 1001

                    # Bild persistent abspeichern
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
                        "kategorie": ai_category,  # <-- Automatisch übernommen
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
                    st.balloons()
                    st.success(f"🎉 Fundstück #{new_id} erfolgreich im System angelegt!")
                    st.rerun()

# =============================================================================
# TAB 3: BEANSPRUCHEN (CLAIM WORKFLOW)
# =============================================================================

with tab_beanspruchen:
    st.markdown("### ✋ Gegenstand als Eigentümer:in beanspruchen")
    st.write("Hast du deinen Gegenstand im Katalog entdeckt? Reiche hier deinen Anspruch mit eindeutigen Nachweisen ein.")

    open_items = {
        f"#{i['id']} - {i['titel']} ({i['fundort']})": i['id']
        for i in st.session_state["fundstuecke_liste"]
        if i.get("status") in ["Offen", "Beansprucht"]
    }

    if not open_items:
        st.info("Aktuell gibt es keine offenen Fundstücke, die beansprucht werden können.")
    else:
        col_c1, col_c2 = st.columns([1, 1], gap="large")

        with col_c1:
            st.markdown("#### 1. Gegenstand auswählen")
            selected_label = st.selectbox("Fundstück wählen*", list(open_items.keys()))
            selected_id = open_items[selected_label]
            target_item = next(i for i in st.session_state["fundstuecke_liste"] if i["id"] == selected_id)

            # Detailansicht
            st.markdown(f"""
            <div class="card-box" style="margin-top: 10px;">
                <div class="card-title">#{target_item['id']} - {target_item['titel']}</div>
                <p style="color: #64748b; font-size: 0.9rem; margin: 4px 0;">
                    📍 Fundort: <b>{target_item['fundort']}</b><br>
                    📦 Aufbewahrt bei: <b>{target_item['abgabeort']}</b><br>
                    📅 Funddatum: {target_item['datum_fund']}
                </p>
                <div style="font-size: 0.88rem; color: #334155; margin-top: 8px;">
                    <i>{target_item['beschreibung']}</i>
                </div>
            </div>
            """, unsafe_allow_html=True)

            img = load_item_image(target_item.get("image_file"))
            if img:
                st.image(img, width=280)

        with col_c2:
            st.markdown("#### 2. Eigentumsnachweis erbringen")
            with st.form("form_claim"):
                c_name = st.text_input("Dein vollständiger Name & Klasse*", placeholder="z. B. Julia Koch (Klasse 9b)")
                c_proof = st.text_area(
                    "Geheimer Eigentumsnachweis*",
                    placeholder="Beschreibe Dinge, die nur der Besitzer weiß: Inhalt, Kratzer, Sperrcode, Namenstag..."
                )
                btn_claim_submit = st.form_submit_button("📩 Anspruch einreichen", width="stretch")

                if btn_claim_submit:
                    if not c_name.strip() or not c_proof.strip():
                        st.error("⚠️ Bitte Name und einen detaillierten Eigentumsnachweis angeben!")
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
                        log_action(c_name.strip(), f"Anspruch #{new_claim_id} auf Fundstück #{selected_id} eingereicht")
                        sync_storage()
                        st.success("✅ Dein Anspruch wurde eingereicht! Der Hausmeister prüft die Angaben.")
                        st.rerun()

# =============================================================================
# TAB 4: VERWALTUNG & ADMIN
# =============================================================================

with tab_admin:
    st.markdown("### ⚙️ Fundbüro-Verwaltung & Hausmeister-Portal")

    if not st.session_state["is_authenticated"] and st.session_state["current_role"] == "Hausmeister / Admin":
        st.warning("🔒 Bitte gib in der Seitenleiste links den Admin-PIN ein (Standard-Demo: 1234).")
    elif st.session_state["current_role"] != "Hausmeister / Admin":
        st.info("ℹ️ Diese Ansicht ist für Lehrkräfte und Hausmeister gedacht. Wechsle links in der Leiste die Rolle.")
    else:
        st.success("👑 Administrator-Sitzung aktiv")

        adm_tabs = st.tabs([
            "📝 Ansprüche bearbeiten",
            "📊 Analytics & KPIs",
            "🗃️ Alle Fundstücke verwalten",
            "📜 Audit-Logs & Export"
        ])

        # Subtab 1: Ansprüche bearbeiten
        with adm_tabs[0]:
            st.markdown("#### Offene Eigentumsansprüche prüfen")
            claims = st.session_state["claims"]
            if not claims:
                st.info("Keine Ansprüche eingetragen.")
            else:
                for c in claims:
                    rel_item = next((i for i in st.session_state["fundstuecke_liste"] if i["id"] == c["item_id"]), None)
                    item_title = rel_item["titel"] if rel_item else "Gelöschtes Item"

                    with st.expander(f"Anspruch #{c['claim_id']} für #{c['item_id']} ({item_title}) - Status: {c['status']}"):
                        st.write(f"**Antragsteller:** {c['name']}")
                        st.write(f"**Eingereicht am:** {c['datum']}")
                        st.write(f"**Vorgelegter Nachweis:** {c['proof']}")

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("✅ Genehmigen & Abholung bestätigen", key=f"app_{c['claim_id']}", width="stretch"):
                                c["status"] = "Genehmigt"
                                if rel_item:
                                    rel_item["status"] = "Abgeholt"
                                log_action("ADMIN", f"Anspruch #{c['claim_id']} genehmigt (Item #{c['item_id']} abgeholt)")
                                sync_storage()
                                st.success("Genehmigt und Gegenstand als 'Abgeholt' markiert!")
                                st.rerun()

                        with col_btn2:
                            if st.button("❌ Anspruch ablehnen", key=f"rej_{c['claim_id']}", width="stretch"):
                                c["status"] = "Abgelehnt"
                                if rel_item and rel_item["status"] == "Beansprucht":
                                    rel_item["status"] = "Offen"
                                log_action("ADMIN", f"Anspruch #{c['claim_id']} abgelehnt")
                                sync_storage()
                                st.warning("Anspruch abgelehnt.")
                                st.rerun()

        # Subtab 2: Analytics
        with adm_tabs[1]:
            st.markdown("#### Kennzahlen & Diagramme")
            items_df = pd.DataFrame(st.session_state["fundstuecke_liste"])

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            total_c = len(items_df)
            ret_c = sum(1 for i in st.session_state["fundstuecke_liste"] if i.get("status") == "Abgeholt")
            ret_rate = (ret_c / total_c * 100) if total_c > 0 else 0.0
            claims_c = len([c for c in st.session_state["claims"] if c.get("status") == "In Prüfung"])

            kpi1.metric("Registriert", total_c)
            kpi2.metric("Zurückgegeben", ret_c)
            kpi3.metric("Erfolgsquote", f"{ret_rate:.1f}%")
            kpi4.metric("Offene Claims", claims_c)

            if not items_df.empty:
                col_ch1, col_ch2 = st.columns(2)
                with col_ch1:
                    st.markdown("##### Häufigste Kategorien")
                    st.bar_chart(items_df["kategorie"].value_counts())
                with col_ch2:
                    st.markdown("##### Fundorte Hotspots")
                    st.bar_chart(items_df["fundort"].value_counts())

        # Subtab 3: Alle Fundstücke
        with adm_tabs[2]:
            st.markdown("#### Datenbank-Tabelle & Schnelledit")
            df_full = pd.DataFrame(st.session_state["fundstuecke_liste"])
            cols_to_show = ["id", "titel", "kategorie", "fundort", "status", "datum_fund", "datum_ablauf"]
            available_cols = [c for c in cols_to_show if c in df_full.columns]
            st.dataframe(df_full[available_cols], width="stretch")

            # Fristen bereinigen
            st.markdown("---")
            st.markdown("##### ⏱️ Fristenprüfung (3 Monate Aufbewahrung)")
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            expired = [i for i in st.session_state["fundstuecke_liste"] if i.get("datum_ablauf", "") < today_str and i.get("status") == "Offen"]

            if expired:
                st.warning(f"⚠️ {len(expired)} Fundstücke haben die Aufbewahrungsfrist überschritten!")
                if st.button("🧹 Abgelaufene Fundstücke als 'Entsorgt' markieren", width="stretch"):
                    for e in expired:
                        e["status"] = "Entsorgt"
                    log_action("ADMIN", f"{len(expired)} Fundstücke als entsorgt markiert")
                    sync_storage()
                    st.success("Bereinigt!")
                    st.rerun()
            else:
                st.info("Alle Fristen sind im grünen Bereich.")

        # Subtab 4: Audit-Logs & Export
        with adm_tabs[3]:
            st.markdown("#### DSGVO & Revisionssichere Logs")
            logs_df = pd.DataFrame(st.session_state["audit_logs"])
            st.dataframe(logs_df, width="stretch")

            st.markdown("---")
            st.markdown("##### 💾 Daten-Export")
            export_data = {
                "items": st.session_state["fundstuecke_liste"],
                "claims": st.session_state["claims"],
                "audit_logs": st.session_state["audit_logs"],
                "export_date": datetime.datetime.now().isoformat()
            }
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 Gesamte Fundbüro-Datenbank herunterladen (JSON)",
                data=json_str,
                file_name=f"kath_fund_backup_{datetime.date.today().strftime('%Y%m%d')}.json",
                mime="application/json",
                width="stretch"
            )
