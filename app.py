"""
===============================================================================
          kath.fund — Digitales Fundbüro · Katharineum zu Lübeck
===============================================================================
Mobile-first (Handy & iPad zuerst). Hero → Suche → Fund melden → Neu → Kategorien.
Filter & Verwaltung liegen aufgeräumt in der Sidebar.
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
from PIL import Image, ImageOps
import numpy as np

# =============================================================================
# 1. CONFIG & STYLING
# =============================================================================

st.set_page_config(
    page_title="kath.fund — Fundbüro",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="expanded",
)

EMBLEM_PATH = Path("assets/emblem.png")
WORDMARK_PATH = Path("assets/wordmark.png")


def file_data_uri(path: Path, max_dim: int = 320) -> str:
    if not path.exists():
        return ""
    try:
        img = Image.open(path)
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


EMBLEM_URI = file_data_uri(EMBLEM_PATH, 200)
WORDMARK_URI = file_data_uri(WORDMARK_PATH, 700)

CSS_PATH = Path("assets/style.css")
_css = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""
_css += f"""
[data-testid='stSidebarCollapsedControl'] {{
    background-image: url('{EMBLEM_URI}') !important;
}}
"""
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

# =============================================================================
# 2. DATA PERSISTENCE
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
    "Sonstiges",
]

LOCATIONS = [
    "Hauptgebäude - Foyer",
    "Pausenhof",
    "Sporthalle",
    "Mensa / Cafeteria",
    "Bibliothek",
    "Fachräume / MINT",
    "Musiksaal",
    "Unbekannt",
]

DEFAULT_ITEMS = [
    {
        "id": 1001,
        "titel": "Derbe Regenjacke Dunkelblau",
        "kategorie": "Kleidung & Textilien",
        "fundort": "Pausenhof",
        "abgabeort": "Hausmeisterbüro (Raum 001)",
        "datum_fund": "2026-09-01",
        "datum_ablauf": "2026-12-01",
        "status": "Offen",
        "beschreibung": "Größe M, gelber Reißverschluss, Name im Etikett leicht verwischt.",
        "image_file": None,
        "tags": ["Jacke", "Blau", "Größe M"],
    },
    {
        "id": 1002,
        "titel": "AirPods Pro Case",
        "kategorie": "Elektronik & Kabel",
        "fundort": "Mensa / Cafeteria",
        "abgabeort": "Sekretariat (Tresor)",
        "datum_fund": "2026-09-05",
        "datum_ablauf": "2026-12-05",
        "status": "Beansprucht",
        "beschreibung": "Kratzer auf der Rückseite, schwarze Silikon-Schutzhülle.",
        "image_file": None,
        "tags": ["Apple", "Audio", "Schwarz"],
    },
    {
        "id": 1003,
        "titel": "Edelstahl Trinkflasche 1L",
        "kategorie": "Trinkflaschen & Brotdosen",
        "fundort": "Sporthalle",
        "abgabeort": "Sporthalle Regallager",
        "datum_fund": "2026-08-28",
        "datum_ablauf": "2026-11-28",
        "status": "Abgeholt",
        "beschreibung": "Marke 720°DGREE, mattgrün mit Sport-Aufklebern.",
        "image_file": None,
        "tags": ["720°DGREE", "Grün", "Metall"],
    },
    {
        "id": 1004,
        "titel": "Federmappe mit Filzstiften",
        "kategorie": "Schulmaterial & Bücher",
        "fundort": "Fachräume / MINT",
        "abgabeort": "Hausmeisterbüro (Raum 001)",
        "datum_fund": datetime.date.today().strftime("%Y-%m-%d"),
        "datum_ablauf": (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
        "status": "Offen",
        "beschreibung": "Rot kariert, ca. 30 Filzstifte, Initialen „J.K.“ auf dem Etikett.",
        "image_file": None,
        "tags": ["Federmappe", "Filzstifte"],
    },
    {
        "id": 1005,
        "titel": "Bundesliga-Sportschuh links",
        "kategorie": "Sportbekleidung",
        "fundort": "Sporthalle",
        "abgabeort": "Sporthalle Regallager",
        "datum_fund": datetime.date.today().strftime("%Y-%m-%d"),
        "datum_ablauf": (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
        "status": "Offen",
        "beschreibung": "Größe 43, schwarz-weiß, Schnürsenkel gemacht.",
        "image_file": None,
        "tags": ["Schuh", "Größe 43"],
    },
    {
        "id": 1006,
        "titel": "Stadtbibliothek Schlüsselbund",
        "kategorie": "Schlüssel & Wertsachen",
        "fundort": "Bibliothek",
        "abgabeort": "Sekretariat (Tresor)",
        "datum_fund": "2026-09-08",
        "datum_ablauf": "2026-12-08",
        "status": "Offen",
        "beschreibung": "Drei Schlüssel, blauer Bibliotheks-Anhänger.",
        "image_file": None,
        "tags": ["Schlüssel", "Anhänger"],
    },
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
            "status": "In Prüfung",
        }
    ])
if "audit_logs" not in st.session_state:
    st.session_state["audit_logs"] = load_json_file(LOGS_FILE, [
        {"timestamp": "2026-09-01 08:30:00", "user": "SYSTEM", "action": "Datenbank gestartet"},
    ])
if "current_role" not in st.session_state:
    st.session_state["current_role"] = "Schüler:in"
if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False
if "view" not in st.session_state:
    st.session_state["view"] = "home"


def sync_storage():
    save_json_file(ITEMS_FILE, st.session_state["fundstuecke_liste"])
    save_json_file(CLAIMS_FILE, st.session_state["claims"])
    save_json_file(LOGS_FILE, st.session_state["audit_logs"])


def log_action(user: str, action: str):
    st.session_state["audit_logs"].insert(0, {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
    })
    sync_storage()


def save_uploaded_image(pil_img: Image.Image, item_id: int) -> str:
    filename = f"item_{item_id}_{int(datetime.datetime.now().timestamp())}.jpg"
    pil_img.save(IMG_DIR / filename, format="JPEG", quality=85)
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
    img = pil_img.copy()
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


# =============================================================================
# 3. AI VISION ENGINE (MOBILENETV2 ONNX, SONST HEURISTIK)
# =============================================================================

VISION_CLASS_TO_CATEGORY = {
    "mobile phone": "Elektronik & Kabel", "cellular telephone": "Elektronik & Kabel",
    "hand-held computer": "Elektronik & Kabel", "laptop computer": "Elektronik & Kabel",
    "notebook computer": "Elektronik & Kabel", "desktop computer": "Elektronik & Kabel",
    "computer keyboard": "Elektronik & Kabel", "computer mouse": "Elektronik & Kabel",
    "remote control": "Elektronik & Kabel", "digital clock": "Elektronik & Kabel",
    "microphone": "Elektronik & Kabel", "digital camera": "Elektronik & Kabel",
    "headphone": "Elektronik & Kabel", "radio": "Elektronik & Kabel",
    "iPod": "Elektronik & Kabel", "cell": "Elektronik & Kabel",
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
    "sombrero": "Kleidung & Textilien", "cowboy hat": "Kleidung & Textilien",
    "running shoe": "Sportbekleidung", "tennis ball": "Sportbekleidung",
    "volleyball": "Sportbekleidung", "basketball": "Sportbekleidung",
    "soccer ball": "Sportbekleidung", "football helmet": "Sportbekleidung",
    "book jacket": "Schulmaterial & Bücher", "comic book": "Schulmaterial & Bücher",
    "notebook": "Schulmaterial & Bücher", "pencil box": "Schulmaterial & Bücher",
    "rubber eraser": "Schulmaterial & Bücher", "rule": "Schulmaterial & Bücher",
    "calculator": "Schulmaterial & Bücher",
    "padlock": "Schlüssel & Wertsachen", "combination lock": "Schlüssel & Wertsachen",
    "analog clock": "Schlüssel & Wertsachen", "digital watch": "Schlüssel & Wertsachen",
    "necklace": "Schlüssel & Wertsachen", "bracelet": "Schlüssel & Wertsachen",
    "sunglasses": "Sonstiges", "umbrella": "Sonstiges",
}


@st.cache_resource(show_spinner=False)
def load_vision_model():
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


def _softmax(values):
    values = values - np.max(values)
    exp = np.exp(values)
    return exp / np.sum(exp)


def analyze_image_ai(pil_image: Image.Image):
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
            candidates = []
            for index in ranked[:50]:
                label = str(labels[int(index)]).lower().replace("_", " ")
                category = VISION_CLASS_TO_CATEGORY.get(label) or VISION_CLASS_TO_CATEGORY.get(label.split(",")[0].strip())
                if category:
                    candidates.append((category, float(probs[index]), label))
            if candidates:
                category, probability, label = max(candidates, key=lambda x: x[1])
                confidence = max(0.35, min(0.88, 0.35 + float(probability) * 3.0))
                return category, confidence, f"MobileNetV2 · {label}"
        except Exception:
            pass

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
# 4. NAVIGATION HELFER
# =============================================================================

def go(view: str):
    st.session_state["view"] = view


def open_item(item_id: int):
    st.session_state["item_id"] = item_id
    st.session_state["view"] = "item"


def request_claim(item_id: int):
    st.session_state["claim_target"] = item_id
    st.session_state["view"] = "claim"


# =============================================================================
# 5. RENDER-BAUSTEINE
# =============================================================================

heute = datetime.date.today()
neu_grenze = (heute - datetime.timedelta(days=7)).strftime("%Y-%m-%d")


def is_new(item) -> bool:
    return str(item.get("datum_fund", "")) >= neu_grenze


STATUS_BADGE = {
    "Offen": "badge-warning",
    "Beansprucht": "badge-info",
    "Abgeholt": "badge-success",
    "Entsorgt": "badge-error",
}


KAT_ICON = {
    "Kleidung & Textilien": "🧥",
    "Trinkflaschen & Brotdosen": "🥤",
    "Rucksäcke & Taschen": "🎒",
    "Elektronik & Kabel": "🎧",
    "Schlüssel & Wertsachen": "🔑",
    "Schulmaterial & Bücher": "📚",
    "Sportbekleidung": "👟",
    "Sonstiges": "📦",
}

STATUS_BADGE_CLASS = {"Offen": "b-warn", "Beansprucht": "b-info",
                      "Abgeholt": "b-ok", "Entsorgt": "b-err"}


def badge_html(item: dict, extra: str = "") -> str:
    status = item.get("status", "Offen")
    bcls = STATUS_BADGE_CLASS.get(status, "")
    out = f'<span class="badge {bcls}">{html.escape(status)}</span>'
    if is_new(item):
        out += '<span class="badge b-new">Neu</span>'
    return out + extra


def card_html(item: dict) -> str:
    """Fundkarte: Bild oder Kategorie-Icon, Titel, Meta, Status-Badges."""
    titel = html.escape(str(item.get("titel", "")))
    meta = html.escape(f"📍 {item.get('fundort')} · {item.get('datum_fund')}")
    kat = html.escape(item.get("kategorie", ""))
    loaded = load_item_image(item.get("image_file"))
    if loaded is not None:
        figure = f'<figure><img src="{image_to_data_uri(loaded, 420)}" alt="{titel}"></figure>'
    else:
        icon = KAT_ICON.get(item.get("kategorie", ""), "📦")
        figure = f'<figure class="ph"><span>{icon}</span><small>{kat}</small></figure>'
    return f"""
    <div class="fund-card">
        {figure}
        <div class="fc-body">
            <div class="fc-title">{titel}</div>
            <div class="fc-meta">{meta}</div>
            <div class="fc-badges">{badge_html(item)}</div>
        </div>
    </div>
    """


def scroller(items: list, key_prefix: str):
    """Karten in horizontal scrollbarer Zeile; Klick öffnet die Detailseite."""
    if not items:
        return
    html_cards = "".join(f'<div class="sc-cell">{card_html(i)}</div>' for i in items)
    st.markdown(f'<div class="scroller">{html_cards}</div>', unsafe_allow_html=True)
    for idx, item in enumerate(items):
        st.button("Ansehen", key=f"{key_prefix}_{item['id']}",
                  on_click=open_item, args=(item["id"],))


def section_head(title: str, count=None):
    c = f'<span class="count">{count}</span>' if count else ""
    st.markdown(f'<div class="sec"><h2>{html.escape(title)}</h2>{c}</div>',
                unsafe_allow_html=True)


def apply_filters(items, query="", kat="Alle", status="Alle", ort="Alle Fundorte"):
    q = (query or "").strip().lower()
    out = list(items)
    if q:
        out = [
            i for i in out
            if q in str(i.get("titel", "")).lower()
            or q in str(i.get("beschreibung", "")).lower()
            or q in str(i.get("fundort", "")).lower()
            or q in str(i.get("kategorie", "")).lower()
            or any(q in str(t).lower() for t in i.get("tags", []))
            or q in str(i.get("id", ""))
        ]
    if kat != "Alle":
        out = [i for i in out if i.get("kategorie") == kat]
    if status != "Alle":
        out = [i for i in out if i.get("status") == status]
    if ort != "Alle Fundorte":
        out = [i for i in out if i.get("fundort") == ort]
    return out


# =============================================================================
# 6. SIDEBAR
# =============================================================================

items_all = st.session_state["fundstuecke_liste"]

with st.sidebar:
    st.markdown(
        f'<div style="text-align:center;padding:2px 0 4px;">'
        f'<img src="{WORDMARK_URI}" style="width:150px;height:auto;" alt="kath.fund">'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sblbl">Bereich</div>', unsafe_allow_html=True)
    nav_labels = {"home": "Start", "search": "Alle Fundstücke", "erfassen": "Fund melden",
                  "claim": "Fund beanspruchen", "admin": "Büro (Admin)"}
    current = st.session_state["view"]
    current_label = nav_labels.get(current, "Start") if current != "item" else "Alle Fundstücke"
    chosen = st.radio("Bereich", list(nav_labels.values()),
                      index=list(nav_labels.values()).index(current_label),
                      label_visibility="collapsed", key="sidenav")
    if nav_labels.get(st.session_state["view"]) != chosen:
        for k, v in nav_labels.items():
            if v == chosen:
                st.session_state["view"] = k

    st.markdown('<div class="sblbl">Filter</div>', unsafe_allow_html=True)
    kat_filter = st.radio("Kategorie", ["Alle"] + CATEGORIES, key="f_kat",
                          label_visibility="collapsed")
    status_filter = st.radio("Status", ["Alle", "Offen", "Beansprucht", "Abgeholt"],
                             key="f_status", label_visibility="collapsed")
    ort_filter = st.selectbox("Fundort", ["Alle Fundorte"] + LOCATIONS,
                              key="f_ort", label_visibility="collapsed")

    st.markdown('<div class="sblbl">Zugang</div>', unsafe_allow_html=True)
    role = st.selectbox("Rolle", ["Schüler:in", "Lehrkraft", "Hausmeister / Admin"],
                        key="f_role", label_visibility="collapsed")
    st.session_state["current_role"] = role
    if role == "Hausmeister / Admin":
        pin = st.text_input("PIN", type="password", placeholder="PIN (Demo: 1234)",
                            key="f_pin", label_visibility="collapsed")
        st.session_state["is_authenticated"] = (pin == "1234")
        if pin and pin != "1234":
            st.caption("PIN ungültig")
        elif pin == "1234":
            st.caption("Freigeschaltet")
    else:
        st.session_state["is_authenticated"] = True

    offen = sum(1 for i in items_all if i.get("status") == "Offen")
    st.caption(f"{offen} Fundstück(e) offen · {heute.strftime('%d.%m.%Y')}")


# =============================================================================
# 7. ANSICHT: START (HERO)
# =============================================================================

def view_home():
    st.markdown(f"""
    <div class="hero">
        <img src="{WORDMARK_URI}" alt="kath.fund">
        <div class="kicker">Katharineum zu Lübeck · <b>Amtliches Fundverzeichnis</b></div>
    </div>
    """, unsafe_allow_html=True)

    c_q, c_go = st.columns([3.4, 1])
    with c_q:
        with st.container(key="heroq"):
            query = st.text_input("Suche", placeholder="🔍 Jacke, AirPods, Schlüsselbund, #1002 …",
                                  label_visibility="collapsed", key="q_home")
    with c_go:
        with st.container(key="herogo"):
            st.button("Suchen", width="stretch", key="go_home", type="primary",
                      on_click=go, args=("search",))

    # --- Fund melden: kompakter CTA-Banner ---
    up1, up2 = st.columns([2.2, 1])
    with up1:
        st.markdown("""
        <div class="report-cta">
            <div><div class="t">Etwas gefunden? 📷</div>
            <div class="s">Foto hochladen, Kategorie wird automatisch vorgeschlagen.</div></div>
        </div>
        """, unsafe_allow_html=True)
        uploaded = st.file_uploader("Foto des Fundstücks", type=["jpg", "jpeg", "png", "webp"],
                                    key="home_upload", label_visibility="collapsed")
    with up2:
        st.write("")
        if st.button("＋ Fund jetzt melden", key="reportbtn", width="stretch", type="primary"):
            if uploaded is not None:
                st.session_state["pending_photo"] = uploaded.getvalue()
            go("erfassen")
            st.rerun()

    # --- Neu ---
    neue = sorted([i for i in items_all if i.get("status") in ("Offen", "Beansprucht")],
                  key=lambda i: str(i.get("datum_fund", "")), reverse=True)[:8]
    section_head("Neu im Fundbüro", f"{len(neue)} Stück(e)")
    if neue:
        scroller(neue, "new")
    else:
        st.markdown('<div class="empty">Noch keine Fundstücke</div>', unsafe_allow_html=True)

    # --- Kategorien ---
    for kat in CATEGORIES[:4]:
        kat_items = sorted([i for i in items_all if i.get("kategorie") == kat],
                           key=lambda i: str(i.get("datum_fund", "")), reverse=True)
        if not kat_items:
            continue
        section_head(kat, f"{len(kat_items)} Stück(e)")
        scroller(kat_items[:8], f"kat{CATEGORIES.index(kat)}")


# =============================================================================
# 8. ANSICHT: SUCHE / KATALOG
# =============================================================================

def view_search():
    query = st.text_input("Suche", placeholder="Suchbegriff oder Belegnummer …",
                          key="q_search", label_visibility="collapsed")
    visible = apply_filters(items_all, query,
                            st.session_state.get("f_kat", "Alle"),
                            st.session_state.get("f_status", "Alle"),
                            st.session_state.get("f_ort", "Alle Fundorte"))
    visible.sort(key=lambda i: str(i.get("datum_fund", "")), reverse=True)

    n = len(visible)
    st.markdown(f'<div class="sec-note"><b>{n}</b> Treffer · Filter liegen in der Sidebar (Wappen oben links)</div>',
                unsafe_allow_html=True)

    if not visible:
        st.markdown("""<div class="empty">Keine Treffer<br>
        <span style="text-transform:none;letter-spacing:0;">Anderen Suchbegriff probieren oder Filter zurücksetzen.</span></div>""",
                    unsafe_allow_html=True)
        return

    # Handy: 1 Spalte, iPad: 2, Desktop: 3
    per_row = 3
    for block in range(0, n, per_row):
        cols = st.columns(per_row, gap="medium")
        for slot in range(per_row):
            pos = block + slot
            if pos >= n:
                continue
            item = visible[pos]
            with cols[slot]:
                st.markdown(card_html(item), unsafe_allow_html=True)
                if item.get("status") in ("Offen", "Beansprucht"):
                    st.button("Ansehen & beanspruchen", key=f"sq_{item['id']}",
                              on_click=open_item, args=(item["id"],), width="stretch")
                else:
                    st.button("Ansehen", key=f"sq_{item['id']}",
                              on_click=open_item, args=(item["id"],), width="stretch")


# =============================================================================
# 9. ANSICHT: DETAIL
# =============================================================================

def view_item():
    item_id = st.session_state.get("item_id")
    item = next((i for i in items_all if i["id"] == item_id), None)
    if item is None:
        st.warning("Fundstück nicht gefunden.")
        st.button("← Zurück", on_click=go, args=("search",))
        return

    st.button("← Zurück", key="back_item", on_click=go, args=("search",))
    titel = html.escape(str(item.get("titel", "")))

    st.markdown(f"""
    <div class="detail-head"><h2>{titel}</h2>{badge_html(item)}</div>
    """, unsafe_allow_html=True)

    img_col, info_col = st.columns([1, 1], gap="large")
    with img_col:
        loaded = load_item_image(item.get("image_file"))
        if loaded is not None:
            preview = loaded.copy()
            preview.thumbnail((900, 900), Image.Resampling.LANCZOS)
            st.image(preview, width="stretch")
        else:
            icon = KAT_ICON.get(item.get("kategorie", ""), "📦")
            st.markdown(f'<div class="fund-card"><figure class="ph" style="height:240px;font-size:3rem;">'
                        f'<span>{icon}</span></figure></div>', unsafe_allow_html=True)
        tags = "".join(f'<span class="badge">{html.escape(str(t))}</span> '
                       for t in item.get("tags", []))
        if tags:
            st.markdown(f'<div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">{tags}</div>',
                        unsafe_allow_html=True)

    with info_col:
        st.markdown(f"""
        <div class="panel">
            <dl class="dgrid">
                <dt>Kategorie</dt><dd>{html.escape(item.get('kategorie', ''))}</dd>
                <dt>Fundort</dt><dd>{html.escape(item.get('fundort', ''))}</dd>
                <dt>Gefunden am</dt><dd>{html.escape(item.get('datum_fund', ''))}</dd>
                <dt>Lagerort</dt><dd>{html.escape(item.get('abgabeort', ''))}</dd>
                <dt>Abholen bis</dt><dd>{html.escape(item.get('datum_ablauf', ''))}</dd>
            </dl>
            <div class="note"><b>Beschreibung</b><span>{html.escape(item.get('beschreibung', ''))}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if item.get("status") in ("Offen", "Beansprucht"):
            st.button("Das ist meins — Anspruch melden", key="claim_detail", width="stretch",
                      on_click=request_claim, args=(item["id"],))
        else:
            st.caption("Dieses Fundstück wurde bereits abgeholt oder ist nicht mehr verfügbar.")


# =============================================================================
# 10. ANSICHT: FUND MELDEN
# =============================================================================

def view_erfassen():
    st.button("← Zurück", key="back_add", on_click=go, args=("home",))
    section_head("Fund melden", "Foto · Vorschlag · Eintrag")
    st.markdown('<div class="sec-note">Foto aufnehmen oder hochladen — die Zuordnung erfolgt automatisch, Korrektur jederzeit möglich.</div>',
                unsafe_allow_html=True)

    col_bild, col_form = st.columns([1, 1.1], gap="large")
    uploaded_pil = None
    ai_category = CATEGORIES[0]
    ai_confidence = 0.0
    ai_engine = "Standby"

    with col_bild:
        pending = st.session_state.get("pending_photo")
        if pending is not None and "pending_consumed" not in st.session_state:
            uploaded_pil = Image.open(io.BytesIO(pending)).convert("RGB")
        else:
            upload_mode = st.radio("Eingabeweg", ["Datei hochladen", "Kamera auslösen"],
                                   horizontal=True, key="upload_mode")
            if upload_mode == "Datei hochladen":
                img_file = st.file_uploader("Bild auswählen", type=["jpg", "jpeg", "png", "webp"],
                                            key="file_upload_input", label_visibility="collapsed")
            else:
                img_file = st.camera_input("Kamera auslösen", key="cam_input",
                                           label_visibility="collapsed")
            if img_file is not None:
                uploaded_pil = Image.open(img_file).convert("RGB")

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
                <div class="v-stamp">Vorschlag</div>
                <div>
                    <div class="v-cat">{html.escape(ai_category)}</div>
                    <div class="v-meta">Sicherheit {ai_confidence * 100:.0f} % · {html.escape(ai_engine)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if ai_confidence < 0.60:
                st.markdown("""<div class="ai-warn"><b>Unsicherer Vorschlag:</b> Bitte die Kategorie
                rechts unbedingt prüfen. Ein Bildmodell kann ähnliche Gegenstände verwechseln.</div>""",
                            unsafe_allow_html=True)
        else:
            st.markdown("""<div class="empty">Noch kein Lichtbild<br>
            <span style="text-transform:none;letter-spacing:0;">Ohne Foto lässt sich ein Fundstück trotzdem erfassen.</span></div>""",
                        unsafe_allow_html=True)

    with col_form:
        with st.form("form_add_item", clear_on_submit=True):
            in_titel = st.text_input("Bezeichnung*", placeholder="z. B. Dunkelblaue Regenjacke, Größe M")
            st.markdown(f"""
            <div class="note"><b>Modellvorschlag:</b> {html.escape(ai_category)}
            <span>Automatisch aus dem Lichtbild abgeleitet. Bitte unten bestätigen oder ändern.</span></div>
            """, unsafe_allow_html=True)
            in_kategorie = st.selectbox(
                "Kategorie bestätigen*", CATEGORIES,
                index=CATEGORIES.index(ai_category) if ai_category in CATEGORIES else len(CATEGORIES) - 1,
            )
            c1, c2 = st.columns(2)
            with c1:
                in_fundort = st.selectbox("Fundort*", LOCATIONS)
            with c2:
                in_abgabeort = st.text_input("Lagerort*", value="Hausmeisterbüro (Raum 001)")
            in_tags = st.text_input("Schlagworte", placeholder="kommagetrennt, z. B. Nike, Blau, Größe L")
            in_beschreibung = st.text_area("Besondere Merkmale", height=100,
                                           placeholder="Kratzer, Initialen, Anhänger, Inhalt …")

            if st.form_submit_button("Eintrag ins Fundbuch übernehmen", width="stretch"):
                if not in_titel.strip():
                    st.error("Bitte eine Bezeichnung angeben.")
                else:
                    items = st.session_state["fundstuecke_liste"]
                    new_id = max([i["id"] for i in items]) + 1 if items else 1001
                    saved_img_name = save_uploaded_image(uploaded_pil, new_id) if uploaded_pil is not None else None
                    parsed_tags = [t.strip() for t in in_tags.split(",") if t.strip()] or [ai_category.split(" ")[0]]
                    neues_item = {
                        "id": new_id,
                        "titel": in_titel.strip(),
                        "kategorie": in_kategorie,
                        "fundort": in_fundort,
                        "abgabeort": in_abgabeort.strip() or "Hausmeisterbüro (Raum 001)",
                        "datum_fund": heute.strftime("%Y-%m-%d"),
                        "datum_ablauf": (heute + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
                        "status": "Offen",
                        "beschreibung": in_beschreibung.strip() or "Keine nähere Beschreibung angegeben.",
                        "image_file": saved_img_name,
                        "tags": parsed_tags,
                    }
                    items.insert(0, neues_item)
                    log_action("FUND-MELDUNG", f"Fundstück #{new_id} registriert ({in_titel.strip()})")
                    st.session_state["pending_photo"] = None
                    st.session_state["item_id"] = new_id
                    st.session_state["view"] = "item"
                    st.toast(f"Beleg #{new_id} angelegt", icon="✅")
                    st.rerun()


# =============================================================================
# 11. ANSICHT: BEANSPRUCHEN
# =============================================================================

def view_claim():
    st.button("← Zurück", key="back_claim", on_click=go, args=("search",))
    section_head("Fundstück beanspruchen", "Nachweis · Prüfung · Aushändigung")
    st.markdown('<div class="sec-note">Eigentum wird geprüft: Je genauer der Nachweis, desto schneller die Aushändigung.</div>',
                unsafe_allow_html=True)

    offene = [i for i in items_all if i.get("status") in ("Offen", "Beansprucht")]
    if not offene:
        st.markdown("""<div class="empty">Zurzeit liegt kein beanspruchbares Fundstück vor</div>""",
                    unsafe_allow_html=True)
        return

    labels = {f"#{i['id']} — {i['titel']} ({i['fundort']})": i["id"] for i in offene}
    optionen = list(labels.keys())

    ziel = st.session_state.pop("claim_target", None)
    default_index = 0
    if ziel is not None:
        for pos, label in enumerate(optionen):
            if labels[label] == ziel:
                default_index = pos
                break

    col_info, col_nachweis = st.columns([1, 1], gap="large")
    with col_info:
        st.markdown("#### Beleg wählen")
        gewaehlt = st.selectbox("Fundstück", optionen, index=default_index,
                                label_visibility="collapsed", key="claim_item")
        ziel_item = next(i for i in items_all if i["id"] == labels[gewaehlt])
        st.markdown(card_html(ziel_item), unsafe_allow_html=True)

    with col_nachweis:
        st.markdown("#### Eigentumsnachweis")
        with st.form("form_claim"):
            c_name = st.text_input("Name und Klasse*", placeholder="z. B. Julia Koch (9b)")
            c_proof = st.text_area("Nachweis*", height=140,
                                   placeholder="Merkmale, die nur die rechtmäßige Besitzerin oder der Besitzer kennt: Inhalt, Gravur, Sperrbildschirm, Initialen …")
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
# 12. ANSICHT: ADMIN
# =============================================================================

def view_admin():
    st.button("← Zurück", key="back_admin", on_click=go, args=("home",))
    section_head("Büro", "Ansprüche · Register · Protokoll")

    if st.session_state["current_role"] != "Hausmeister / Admin":
        st.info("Dieser Bereich gehört zum Hausmeisterbüro. Rolle in der Sidebar auf „Hausmeister / Admin“ stellen.")
        return
    if not st.session_state["is_authenticated"]:
        st.warning("PIN erforderlich. Bitte in der Sidebar unter „Zugang“ eingeben (Demo: 1234).")
        return

    tab_claims, tab_register, tab_log = st.tabs(["Ansprüche", "Register", "Protokoll & Export"])

    with tab_claims:
        claims = st.session_state["claims"]
        if not claims:
            st.markdown('<div class="empty">Keine Ansprüche im Eingang</div>', unsafe_allow_html=True)
        for c in claims:
            rel = next((i for i in items_all if i["id"] == c["item_id"]), None)
            titel = rel["titel"] if rel else "Gelöschtes Fundstück"
            badge_cls = {"Genehmigt": "b-ok", "Abgelehnt": "b-err", "In Prüfung": "b-info"}.get(c["status"], "")
            with st.expander(f"Anspruch #{c['claim_id']} · Beleg #{c['item_id']} · {titel}"):
                st.markdown(f"""
                <div class="note"><b>{html.escape(str(c['name']))}</b>
                <span>Eingereicht am {c['datum']} · Status {c['status']}</span></div>
                <div style="margin:6px 0 10px;">{html.escape(str(c['proof']))}</div>
                <div style="margin-bottom:10px;"><span class="badge {badge_cls}">{c['status']}</span></div>
                """, unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Genehmigen & aushändigen", key=f"app_{c['claim_id']}", width="stretch"):
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

    with tab_register:
        faellig = [i for i in items_all
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
        for item in items_all:
            st.markdown(card_html(item), unsafe_allow_html=True)

    with tab_log:
        for entry in st.session_state["audit_logs"][:40]:
            st.caption(f"{entry['timestamp']} · {entry['user']} · {entry['action']}")
        export = {
            "items": items_all,
            "claims": st.session_state["claims"],
            "audit_logs": st.session_state["audit_logs"],
            "export_date": datetime.datetime.now().isoformat(),
        }
        st.download_button(
            "Gesamtes Fundverzeichnis herunterladen (JSON)",
            data=json.dumps(export, ensure_ascii=False, indent=2),
            file_name=f"kath_fund_export_{heute.strftime('%Y%m%d')}.json",
            mime="application/json", width="stretch",
        )


# =============================================================================
# 13. ROUTER
# =============================================================================

view = st.session_state["view"]
if view == "home":
    view_home()
elif view == "search":
    view_search()
elif view == "item":
    view_item()
elif view == "erfassen":
    view_erfassen()
elif view == "claim":
    view_claim()
elif view == "admin":
    view_admin()
else:
    view_home()
