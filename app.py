"""
kath.fund — Fundbüro · Katharineum zu Lübeck
Architektur: Streamlit = Backend only. Die gesamte UI läuft als ein HTML-Dokument
(Tailwind + daisyUI) in einem iframe (components.html). Kein Streamlit-DOM-Kampf.

Kommunikation:
  Python -> iframe:  items/claims als JSON eingebettet
  iframe  -> Python: window.parent.location.search = ?action=...  (löst Rerun aus)
Suche/Filter/Navigation laufen komplett im iframe (JS) — instant, ohne Server.
"""

import json
import datetime
import io
import base64
import html as html_mod
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import streamlit.components.v1 as components

# =============================================================================
# 1. PAGE + DATA
# =============================================================================

st.set_page_config(page_title="kath.fund — Fundbüro", page_icon="🎒",
                   layout="wide", initial_sidebar_state="collapsed")

STORAGE = Path("data")
STORAGE.mkdir(exist_ok=True)
IMG_DIR = STORAGE / "images"
IMG_DIR.mkdir(exist_ok=True)
ITEMS_FILE = STORAGE / "items.json"
CLAIMS_FILE = STORAGE / "claims.json"

CATEGORIES = [
    "Kleidung & Textilien", "Trinkflaschen & Brotdosen", "Rucksäcke & Taschen",
    "Elektronik & Kabel", "Schlüssel & Wertsachen", "Schulmaterial & Bücher",
    "Sportbekleidung", "Sonstiges",
]
LOCATIONS = ["Hauptgebäude - Foyer", "Pausenhof", "Sporthalle", "Mensa / Cafeteria",
             "Bibliothek", "Fachräume / MINT", "Musiksaal", "Unbekannt"]

KAT_ICON = {
    "Kleidung & Textilien": "🧥", "Trinkflaschen & Brotdosen": "🥤",
    "Rucksäcke & Taschen": "🎒", "Elektronik & Kabel": "🎧",
    "Schlüssel & Wertsachen": "🔑", "Schulmaterial & Bücher": "📚",
    "Sportbekleidung": "👟", "Sonstiges": "📦",
}

DEFAULT_ITEMS = [
    {"id": 1001, "titel": "Derbe Regenjacke Dunkelblau", "kategorie": "Kleidung & Textilien",
     "fundort": "Pausenhof", "abgabeort": "Hausmeisterbüro (Raum 001)",
     "datum_fund": "2026-09-01", "datum_ablauf": "2026-12-01", "status": "Offen",
     "beschreibung": "Größe M, gelber Reißverschluss, Name im Etikett leicht verwischt.",
     "image_file": None, "tags": ["Jacke", "Blau", "Größe M"]},
    {"id": 1002, "titel": "AirPods Pro Case", "kategorie": "Elektronik & Kabel",
     "fundort": "Mensa / Cafeteria", "abgabeort": "Sekretariat (Tresor)",
     "datum_fund": "2026-09-05", "datum_ablauf": "2026-12-05", "status": "Beansprucht",
     "beschreibung": "Kratzer auf der Rückseite, schwarze Silikon-Schutzhülle.",
     "image_file": None, "tags": ["Apple", "Audio", "Schwarz"]},
    {"id": 1003, "titel": "Edelstahl Trinkflasche 1L", "kategorie": "Trinkflaschen & Brotdosen",
     "fundort": "Sporthalle", "abgabeort": "Sporthalle Regallager",
     "datum_fund": "2026-08-28", "datum_ablauf": "2026-11-28", "status": "Abgeholt",
     "beschreibung": "Marke 720°DGREE, mattgrün mit Sport-Aufklebern.",
     "image_file": None, "tags": ["720°DGREE", "Grün", "Metall"]},
    {"id": 1004, "titel": "Federmappe mit Filzstiften", "kategorie": "Schulmaterial & Bücher",
     "fundort": "Fachräume / MINT", "abgabeort": "Hausmeisterbüro (Raum 001)",
     "datum_fund": datetime.date.today().strftime("%Y-%m-%d"),
     "datum_ablauf": (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
     "status": "Offen", "beschreibung": "Rot kariert, ca. 30 Filzstifte, Initialen „J.K.“.",
     "image_file": None, "tags": ["Federmappe", "Filzstifte"]},
    {"id": 1005, "titel": "Sportschuh links Größe 43", "kategorie": "Sportbekleidung",
     "fundort": "Sporthalle", "abgabeort": "Sporthalle Regallager",
     "datum_fund": datetime.date.today().strftime("%Y-%m-%d"),
     "datum_ablauf": (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
     "status": "Offen", "beschreibung": "Schwarz-weiß, sauber gebunden.",
     "image_file": None, "tags": ["Schuh", "43"]},
    {"id": 1006, "titel": "Schlüsselbund mit Bibliotheks-Anhänger", "kategorie": "Schlüssel & Wertsachen",
     "fundort": "Bibliothek", "abgabeort": "Sekretariat (Tresor)",
     "datum_fund": "2026-09-08", "datum_ablauf": "2026-12-08", "status": "Offen",
     "beschreibung": "Drei Schlüssel, blauer Anhänger der Stadtbibliothek.",
     "image_file": None, "tags": ["Schlüssel", "Blau"]},
]


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if "items" not in st.session_state:
    st.session_state["items"] = load_json(ITEMS_FILE, DEFAULT_ITEMS)
if "claims" not in st.session_state:
    st.session_state["claims"] = load_json(CLAIMS_FILE, [
        {"claim_id": 501, "item_id": 1002, "name": "Lukas M. (9b)",
         "proof": "Seriennummer auf OVP vorhanden.", "datum": "2026-09-06", "status": "In Prüfung"}])
if "flash" not in st.session_state:
    st.session_state["flash"] = ""

# =============================================================================
# 2. BILDER
# =============================================================================


def save_uploaded_image(pil_img, item_id):
    name = f"item_{item_id}_{int(datetime.datetime.now().timestamp())}.jpg"
    pil_img.save(IMG_DIR / name, format="JPEG", quality=85)
    return name


def load_item_image(filename):
    if not filename:
        return None
    p = IMG_DIR / filename
    if p.exists():
        try:
            return Image.open(p)
        except Exception:
            return None
    return None


def img_uri(filename, max_dim=420):
    img = load_item_image(filename)
    if img is None:
        return None
    img = img.copy()
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def logo_top_uri():
    p = Path("assets/logo_top.png")
    if not p.exists():
        return ""
    img = Image.open(p)
    img.thumbnail((640, 640), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def wordmark_uri():
    p = Path("assets/wordmark.png")
    if not p.exists():
        return ""
    img = Image.open(p)
    img.thumbnail((640, 640), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# =============================================================================
# 3. KI (MobileNetV2 ONNX, Fallback-Heuristik)
# =============================================================================

VISION_CLASS_TO_CATEGORY = {
    "mobile phone": "Elektronik & Kabel", "cellular telephone": "Elektronik & Kabel",
    "laptop computer": "Elektronik & Kabel", "notebook computer": "Elektronik & Kabel",
    "computer keyboard": "Elektronik & Kabel", "computer mouse": "Elektronik & Kabel",
    "remote control": "Elektronik & Kabel", "iPod": "Elektronik & Kabel",
    "digital clock": "Elektronik & Kabel", "microphone": "Elektronik & Kabel",
    "digital camera": "Elektronik & Kabel", "headphone": "Elektronik & Kabel",
    "backpack": "Rucksäcke & Taschen", "purse": "Rucksäcke & Taschen",
    "handbag": "Rucksäcke & Taschen", "wallet": "Rucksäcke & Taschen",
    "briefcase": "Rucksäcke & Taschen", "suitcase": "Rucksäcke & Taschen",
    "water bottle": "Trinkflaschen & Brotdosen", "bottle": "Trinkflaschen & Brotdosen",
    "beer bottle": "Trinkflaschen & Brotdosen", "coffee mug": "Trinkflaschen & Brotdosen",
    "cup": "Trinkflaschen & Brotdosen", "pitcher": "Trinkflaschen & Brotdosen",
    "t-shirt": "Kleidung & Textilien", "jersey": "Kleidung & Textilien",
    "sweatshirt": "Kleidung & Textilien", "pullover": "Kleidung & Textilien",
    "cardigan": "Kleidung & Textilien", "sweater": "Kleidung & Textilien",
    "jacket": "Kleidung & Textilien", "coat": "Kleidung & Textilien",
    "jean": "Kleidung & Textilien", "trousers": "Kleidung & Textilien",
    "dress": "Kleidung & Textilien", "scarf": "Kleidung & Textilien",
    "running shoe": "Sportbekleidung", "tennis ball": "Sportbekleidung",
    "volleyball": "Sportbekleidung", "basketball": "Sportbekleidung",
    "soccer ball": "Sportbekleidung", "book jacket": "Schulmaterial & Bücher",
    "comic book": "Schulmaterial & Bücher", "pencil box": "Schulmaterial & Bücher",
    "rubber eraser": "Schulmaterial & Bücher", "calculator": "Schulmaterial & Bücher",
    "padlock": "Schlüssel & Wertsachen", "combination lock": "Schlüssel & Wertsachen",
    "digital watch": "Schlüssel & Wertsachen", "necklace": "Schlüssel & Wertsachen",
    "bracelet": "Schlüssel & Wertsachen",
}


@st.cache_resource(show_spinner=False)
def load_vision_model():
    try:
        import onnxruntime as ort
        mp, lp = Path("mobilenetv2.onnx"), Path("imagenet_labels.json")
        if not mp.exists() or not lp.exists():
            return None
        session = ort.InferenceSession(str(mp), providers=["CPUExecutionProvider"])
        return session, json.loads(lp.read_text(encoding="utf-8"))
    except Exception:
        return None


def _softmax(v):
    v = v - np.max(v)
    e = np.exp(v)
    return e / np.sum(e)


def analyze_image_ai(pil_image):
    vision = load_vision_model()
    if vision is not None:
        try:
            session, labels = vision
            image = ImageOps.fit(pil_image.convert("RGB"), (224, 224), Image.Resampling.LANCZOS)
            arr = np.asarray(image, dtype=np.float32) / 255.0
            arr = (arr - np.array([.485, .456, .406], dtype=np.float32)) / np.array([.229, .224, .225], dtype=np.float32)
            arr = np.transpose(arr, (2, 0, 1))[None, ...]
            out = session.run(None, {session.get_inputs()[0].name: arr})[0][0]
            probs = _softmax(out)
            ranked = np.argsort(probs)[::-1]
            cands = []
            for idx in ranked[:50]:
                label = str(labels[int(idx)]).lower().replace("_", " ")
                cat = VISION_CLASS_TO_CATEGORY.get(label)
                if cat:
                    cands.append((cat, float(probs[idx]), label))
            if cands:
                cat, p, label = max(cands, key=lambda x: x[1])
                conf = max(0.35, min(0.88, 0.35 + p * 3.0))
                return cat, conf, f"MobileNetV2 · {label}"
        except Exception:
            pass
    rgb = pil_image.convert("RGB")
    w, h = rgb.size
    arr = np.asarray(rgb.resize((64, 64)), dtype=np.float32)
    std = arr.std(axis=(0, 1)).mean()
    r, g, b = arr.mean(axis=(0, 1))
    if std < 18 and r < 80 and g < 80 and b < 80:
        return "Elektronik & Kabel", 0.5, "Bildmerkmale · unsicher"
    if w / float(h) < 0.62 or w / float(h) > 1.7:
        return "Trinkflaschen & Brotdosen", 0.5, "Bildmerkmale · unsicher"
    return "Sonstiges", 0.35, "Kein Modell verfügbar"


# =============================================================================
# 4. AKTIONEN (aus dem iframe via Query-Params)
# =============================================================================

qp = st.query_params
items = st.session_state["items"]
claims = st.session_state["claims"]
heute = datetime.date.today().isoformat()


def parent_refresh(msg=""):
    st.session_state["flash"] = msg
    for k in list(qp.keys()):
        del qp[k]
    st.rerun()


action = qp.get("action", "")

if action == "claim":
    iid = int(qp.get("item", 0))
    name = qp.get("name", "").strip()
    proof = qp.get("proof", "").strip()
    if name and proof:
        item = next((i for i in items if i["id"] == iid), None)
        if item and item["status"] in ("Offen", "Beansprucht"):
            new_id = max([c["claim_id"] for c in claims], default=500) + 1
            claims.insert(0, {"claim_id": new_id, "item_id": iid, "name": name,
                              "proof": proof, "datum": heute, "status": "In Prüfung"})
            item["status"] = "Beansprucht"
            save_json(ITEMS_FILE, items)
            save_json(CLAIMS_FILE, claims)
            parent_refresh(f"Anspruch auf „{item['titel']}“ eingereicht — wir melden uns.")
    parent_refresh("Bitte Name und Nachweis ausfüllen.")

elif action == "report_done":
    parent_refresh("")

# =============================================================================
# 5. REPORT-ANSICHT (nativ, wegen Datei-Upload)
# =============================================================================

if qp.get("view") == "report":
    st.markdown("""
    <style>
      .stApp { background: #F7F5F0; }
      .report-wrap { max-width: 760px; margin: 0 auto; padding: 1rem 1rem 3rem; }
      .rp-title { font-size: 1.6rem; font-weight: 800; }
      .rp-sub { color: #6E6862; margin-bottom: 1rem; }
      .vcard { background: #fff; border: 1px solid #E4E0D8; border-radius: 12px;
               box-shadow: 0 1px 2px rgba(0,0,0,.05); padding: 16px 18px; margin-top: 10px;
               display:flex; gap:14px; align-items:center; }
      .vstamp { background:#F6DEDA; color:#B23A2A; font-weight:700; font-size:.72rem;
                padding:6px 10px; border-radius:8px; white-space:nowrap; }
    </style>
    <div class="report-wrap"><div class="rp-title">📷 Fund melden</div>
    <div class="rp-sub">Foto aufnehmen oder hochladen — Kategorie wird automatisch vorgeschlagen.
    Nach dem Eintrag landet das Fundstück direkt im Verzeichnis.</div></div>
    """, unsafe_allow_html=True)

    uploaded_pil = None
    up_mode = st.radio("Quelle", ["Kamera", "Datei hochladen"], horizontal=True,
                       index=0 if qp.get("mode") == "camera" else 1)
    if up_mode == "Datei hochladen":
        f = st.file_uploader("Foto", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    else:
        f = st.camera_input("Kamera", label_visibility="collapsed")
    if f is not None:
        uploaded_pil = Image.open(f).convert("RGB")

    ai_cat, ai_conf, ai_engine = "Sonstiges", 0.0, "Standby"
    if uploaded_pil is not None:
        prev = uploaded_pil.copy()
        prev.thumbnail((760, 760), Image.Resampling.LANCZOS)
        st.image(prev, width="stretch")
        with st.spinner("Kategorie wird erkannt …"):
            ai_cat, ai_conf, ai_engine = analyze_image_ai(uploaded_pil)
        st.markdown(f"""
        <div class="vcard"><span class="vstamp">Vorschlag</span>
        <div><b style="font-size:1.05rem">{html_mod.escape(ai_cat)}</b>
        <div style="font-size:.75rem;color:#6E6862">Sicherheit {ai_conf*100:.0f} % · {html_mod.escape(ai_engine)}</div>
        </div></div>""", unsafe_allow_html=True)
        if ai_conf < 0.6:
            st.info("Unsicherer Vorschlag — bitte Kategorie unten prüfen.")

    with st.form("report_form"):
        t = st.text_input("Bezeichnung*", placeholder="z. B. Dunkelblaue Regenjacke, Größe M")
        kat = st.selectbox("Kategorie*", CATEGORIES,
                           index=CATEGORIES.index(ai_cat) if ai_cat in CATEGORIES else len(CATEGORIES) - 1)
        c1, c2 = st.columns(2)
        ort = c1.selectbox("Fundort*", LOCATIONS)
        lager = c2.text_input("Lagerort*", value="Hausmeisterbüro (Raum 001)")
        tags = st.text_input("Schlagworte", placeholder="kommagetrennt: Nike, Blau, Größe L")
        desc = st.text_area("Besondere Merkmale", placeholder="Kratzer, Initialen, Inhalt …")
        if st.form_submit_button("Ins Fundbuch eintragen", type="primary", use_container_width=True):
            if not t.strip():
                st.error("Bitte eine Bezeichnung angeben.")
            else:
                new_id = max([i["id"] for i in items], default=1000) + 1
                img_name = save_uploaded_image(uploaded_pil, new_id) if uploaded_pil is not None else None
                parsed = [x.strip() for x in tags.split(",") if x.strip()] or [ai_cat.split(" ")[0]]
                items.insert(0, {
                    "id": new_id, "titel": t.strip(), "kategorie": kat, "fundort": ort,
                    "abgabeort": lager.strip() or "Hausmeisterbüro (Raum 001)",
                    "datum_fund": heute,
                    "datum_ablauf": (datetime.date.today() + datetime.timedelta(days=90)).isoformat(),
                    "status": "Offen", "beschreibung": desc.strip() or "Keine nähere Beschreibung.",
                    "image_file": img_name, "tags": parsed})
                save_json(ITEMS_FILE, items)
                qp_view = "report_saved"
                st.session_state["flash"] = f"Fundstück „{t.strip()}“ wurde eingetragen 🎉"
                for k in list(qp.keys()):
                    del qp[k]
                st.rerun()
    st.stop()

# =============================================================================
# 6. UI (ein HTML-Dokument mit daisyUI im iframe)
# =============================================================================

neu_grenze = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
items_json = []
for it in items:
    it2 = dict(it)
    it2["img"] = img_uri(it.get("image_file"))
    it2["icon"] = KAT_ICON.get(it.get("kategorie", ""), "📦")
    it2["neu"] = str(it.get("datum_fund", "")) >= neu_grenze
    items_json.append(it2)

claims_json = st.session_state["claims"]
flash = st.session_state["flash"]
st.session_state["flash"] = ""

wordmark = wordmark_uri()
logo_top = logo_top_uri()
data_json = json.dumps({"items": items_json, "wordmark": wordmark, "logoTop": logo_top,
                        "categories": CATEGORIES, "claims": len(claims_json)},
                       ensure_ascii=False)

UI = r"""
<!doctype html>
<html lang="de" data-theme="kfund">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css" rel="stylesheet" type="text/css"/>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  [data-theme="kfund"] {
    --p: 43% 0.16 25;  --pc: 96% 0.03 25;
    --b1: 97% 0.01 90; --b2: 100% 0 0; --bc: 22% 0.02 70;
    --r: 45% 0.09 150; --rc: 96% 0.02 150;
  }
  body { font-family: 'Inter', system-ui, sans-serif; background: #F7F5F0; }
  .mono { font-family: ui-monospace, 'IBM Plex Mono', monospace; }
  .card-hover { transition: transform .15s ease, box-shadow .15s ease; }
  .card-hover:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(0,0,0,.10); }
  .clamp2 { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
  .scroller { display:flex; gap:1rem; overflow-x:auto; padding:.4rem .2rem 1rem; scroll-snap-type:x proximity; }
  .scroller > div { flex:0 0 240px; scroll-snap-align:start; }
  .scroller::-webkit-scrollbar { height:6px; }
  .scroller::-webkit-scrollbar-thumb { background:#D6D1C6; border-radius:3px; }
  dialog::backdrop { background: rgba(20,17,12,.45); }
</style>
</head>
<body class="min-h-screen">

<!-- ============ DRAWER (Sidebar) ============ -->
<div class="drawer">
  <input id="drawerToggle" type="checkbox" class="drawer-toggle"/>
  <div class="drawer-content">

    <!-- ============ TOPBAR ============ -->
    <div class="navbar bg-base-100 border-b border-base-300 sticky top-0 z-40 shadow-sm px-2 md:px-6">
      <div class="flex-none">
        <label for="drawerToggle" class="btn btn-ghost btn-square" aria-label="Menü">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </label>
      </div>
      <div class="flex-1 flex justify-center">
        <img src="__WORDMARK__" class="h-8 md:h-10 w-auto" alt="kath.fund">
      </div>
      <div class="flex-none flex items-center gap-2">
        <span class="badge badge-outline hidden sm:inline-flex mono" id="openCount"></span>
        <a class="btn btn-primary btn-sm md:btn" onclick="openReport()">📷 Fund melden</a>
      </div>
    </div>

    <!-- ============ FLASH ============ -->
    <div id="flash" class="hidden max-w-5xl mx-auto px-4 pt-4">
      <div class="alert alert-success shadow"><span id="flashText"></span></div>
    </div>

    <!-- ============ VIEW: HOME ============ -->
    <div id="view-home" class="max-w-5xl mx-auto px-4 pb-16">
      <div class="text-center pt-6 md:pt-8 pb-2">
        <img src="__LOGOTOP__" class="w-64 md:w-80 mx-auto" alt="kath.fund">
      </div>

      <!-- Suche -->
      <form class="join w-full mt-4" onsubmit="doSearch(event)">
        <input id="homeQ" class="input input-bordered join-item input-lg w-full bg-base-100"
               placeholder="🔍 Jacke, AirPods, Schlüsselbund, #1002 …">
        <button class="btn btn-neutral join-item input-lg">Suchen</button>
      </form>

      <!-- CTA: Etwas gefunden? -->
      <div class="card bg-base-100 shadow-lg border border-base-200 mt-6 overflow-hidden">
        <div class="card-body p-6 md:p-10 items-center text-center gap-3">
          <div class="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
            <span class="text-4xl">🎒</span>
          </div>
          <h2 class="card-title text-2xl md:text-3xl justify-center">Etwas gefunden?</h2>
          <p class="text-base-content/60 max-w-md">Mach ein Foto oder lade eins hoch — die Kategorie wird
          automatisch erkannt und du kannst das Fundstück direkt eintragen.</p>
          <div class="flex flex-col sm:flex-row gap-3 mt-2 w-full sm:w-auto">
            <a class="btn btn-primary btn-lg" onclick="openReport('camera')">📷 Foto aufnehmen</a>
            <a class="btn btn-outline btn-lg" onclick="openReport('upload')">📄 Datei hochladen</a>
          </div>
        </div>
      </div>

      <!-- Kategorie-Scroller -->
      <h2 class="text-xl font-bold mt-8 mb-1">Kategorien</h2>
      <p class="text-sm text-base-content/50 mb-2">Von Elektronik bis Klamotten — tippen zum Filtern</p>
      <div class="scroller" id="scrollerCats"></div>

      <!-- Neu -->
      <h2 class="text-xl font-bold mt-8 mb-1">Neu im Fundbüro</h2>
      <p class="text-sm text-base-content/50 mb-2">Zuletzt eingegegangene Fundstücke</p>
      <div class="scroller" id="scrollerNew"></div>

      <!-- Kategorien-Liste -->
      <h2 class="text-xl font-bold mt-8 mb-1">Alle Bereiche</h2>
      <p class="text-sm text-base-content/50 mb-3">Direkt zum gefilterten Verzeichnis</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3" id="catList"></div>
    </div>

    <!-- ============ VIEW: SEARCH ============ -->
    <div id="view-search" class="max-w-5xl mx-auto px-4 pb-16 hidden">
      <button class="btn btn-ghost btn-sm mt-4 -ml-3" onclick="show('home')">← Start</button>
      <h1 class="text-2xl font-bold mt-2" id="searchTitle">Alle Fundstücke</h1>
      <form class="join w-full mt-3" onsubmit="doSearchFromView(event)">
        <input id="searchQ" class="input input-bordered join-item w-full bg-base-100"
               placeholder="🔍 Suchen oder #Belegnummer …">
        <button class="btn btn-neutral join-item">Los</button>
      </form>
      <div class="flex flex-wrap gap-2 mt-4" id="catChips"></div>
      <div class="flex flex-wrap gap-2 mt-2" id="statusChips"></div>
      <p class="text-sm text-base-content/50 mt-4" id="resultCount"></p>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4" id="searchGrid"></div>
    </div>

    <!-- ============ VIEW: DETAIL ============ -->
    <div id="view-item" class="max-w-4xl mx-auto px-4 pb-16 hidden">
      <button class="btn btn-ghost btn-sm mt-4 -ml-3" onclick="backFromItem()">← Zurück</button>
      <div id="itemDetail" class="mt-3"></div>
    </div>
  </div>

  <!-- ============ DRAWER-SIDEBAR ============ -->
  <div class="drawer-side z-50">
    <label for="drawerToggle" class="drawer-overlay" aria-label="Schließen"></label>
    <aside class="bg-base-100 min-h-full w-72 p-4 border-r border-base-300">
      <img src="__LOGOTOP__" class="w-40 mx-auto mb-4" alt="kath.fund">
      <ul class="menu w-full gap-1">
        <li><a onclick="closeDrawer();show('home')"><b>🏠 Start</b></a></li>
        <li><a onclick="closeDrawer();goSearchAll()"><b>🔍 Alle Fundstücke</b></a></li>
        <li><a onclick="closeDrawer();openReport()">📷 Fund melden</a></li>
      </ul>
      <div class="divider my-2">Kategorien</div>
      <ul class="menu w-full gap-0.5" id="drawerCats"></ul>
      <div class="divider my-2">Status</div>
      <ul class="menu w-full gap-0.5" id="drawerStatus"></ul>
      <div class="divider my-2">Kennzahlen</div>
      <div id="statDrawer"></div>
      <p class="text-xs text-base-content/40 mt-4 text-center">Katharineum zu Lübeck · Fundbüro</p>
    </aside>
  </div>
</div>

<!-- ============ MODAL: BEANSPRUCHEN ============ -->
<dialog id="claimModal" class="modal">
  <div class="modal-box max-w-lg">
    <h3 class="font-bold text-lg">Das ist meins — Anspruch melden</h3>
    <p class="text-sm text-base-content/60 mt-1" id="claimItemLabel"></p>
    <div class="py-3 space-y-3">
      <input id="claimName" class="input input-bordered w-full" placeholder="Name und Klasse* (z. B. Julia Koch, 9b)">
      <textarea id="claimProof" class="textarea textarea-bordered w-full h-28"
        placeholder="Nachweis*: Was weiß nur die rechtmäßige Besitzerin / der Besitzer? Inhalt, Gravur, Initialen, Sperrbildschirm …"></textarea>
    </div>
    <div class="modal-action">
      <button class="btn btn-ghost" onclick="claimModal.close()">Abbrechen</button>
      <button class="btn btn-primary" onclick="submitClaim()">Anspruch einreichen</button>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>

<script>
const DATA = __DATA__;
const items = DATA.items;
let currentView = 'home';
let lastGrid = null;
let filterCat = 'Alle';
let filterStatus = 'Alle';

const $ = (s) => document.querySelector(s);
const esc = (s) => { const d = document.createElement('div'); d.textContent = s ?? ''; return d.innerHTML; };
const KAT_ICON = {
  "Kleidung & Textilien": "🧥", "Trinkflaschen & Brotdosen": "🥤",
  "Rucksäcke & Taschen": "🎒", "Elektronik & Kabel": "🎧",
  "Schlüssel & Wertsachen": "🔑", "Schulmaterial & Bücher": "📚",
  "Sportbekleidung": "👟", "Sonstiges": "📦",
};

function showFlash(t) {
  if (!t) return;
  $('#flashText').textContent = t;
  $('#flash').classList.remove('hidden');
}
function show(v) {
  currentView = v;
  ['home','search','item'].forEach(x => $('#view-'+x).classList.toggle('hidden', x !== v));
  window.scrollTo(0,0);
}
function closeDrawer() { $('#drawerToggle').checked = false; }
function openReport(mode) { window.parent.location.search = '?view=report' + (mode === 'camera' ? '&mode=camera' : ''); }

function submitClaim() {
  const name = $('#claimName').value.trim();
  const proof = $('#claimProof').value.trim();
  const iid = claimModal.dataset.item;
  if (!name || !proof) { $('#claimName').classList.toggle('input-error', !name);
                         $('#claimProof').classList.toggle('textarea-error', !proof); return; }
  window.parent.location.search = `?action=claim&item=${iid}&name=${encodeURIComponent(name)}&proof=${encodeURIComponent(proof)}`;
}

function statusBadge(s) {
  const map = { 'Offen':'badge-warning', 'Beansprucht':'badge-info',
                'Abgeholt':'badge-success', 'Entsorgt':'badge-error' };
  return `<span class="badge badge-sm ${map[s]||'badge-ghost'}">${esc(s)}</span>`;
}
function card(i) {
  const fig = i.img
    ? `<figure><img src="${i.img}" class="h-40 w-full object-cover" alt="${esc(i.titel)}"></figure>`
    : `<figure class="h-40 w-full bg-base-200 flex flex-col items-center justify-center gap-1">
         <span class="text-4xl">${i.icon}</span>
         <span class="text-xs text-base-content/50">${esc(i.kategorie)}</span></figure>`;
  const neu = i.neu ? `<span class="badge badge-sm badge-primary">Neu</span>` : '';
  return `
  <div class="card bg-base-100 shadow card-hover cursor-pointer" onclick="openItem(${i.id}, 'grid')">
    ${fig}
    <div class="card-body p-4 gap-1.5">
      <h3 class="card-title text-base leading-snug clamp2">${esc(i.titel)}</h3>
      <p class="text-xs text-base-content/50">📍 ${esc(i.fundort)} · ${esc(i.datum_fund)}</p>
      <div class="flex flex-wrap gap-1.5 mt-1">${statusBadge(i.status)}${neu}</div>
    </div>
  </div>`;
}

function openItem(id, ctx) {
  lastGrid = ctx;
  const i = items.find(x => x.id === id);
  if (!i) return;
  const claimable = i.status === 'Offen' || i.status === 'Beansprucht';
  const fig = i.img
    ? `<img src="${i.img}" class="w-full rounded-box border border-base-300 object-cover">`
    : `<div class="rounded-box bg-base-200 h-64 flex flex-col items-center justify-center gap-2">
         <span class="text-6xl">${i.icon}</span><span class="text-sm text-base-content/50">${esc(i.kategorie)}</span></div>`;
  const tags = (i.tags||[]).map(t=>`<span class="badge badge-ghost badge-sm">${esc(t)}</span>`).join('');
  $('#itemDetail').innerHTML = `
  <div class="flex items-center gap-3 flex-wrap">
    <h1 class="text-2xl md:text-3xl font-bold">${esc(i.titel)}</h1>
    ${statusBadge(i.status)}${i.neu?'<span class="badge badge-primary badge-sm">Neu</span>':''}
  </div>
  <div class="grid md:grid-cols-2 gap-6 mt-4">
    <div>${fig}
      ${tags?`<div class="flex flex-wrap gap-1.5 mt-3">${tags}</div>`:''}
    </div>
    <div class="bg-base-100 border border-base-300 rounded-box shadow-sm p-5">
      <dl class="grid grid-cols-[auto_1fr] gap-x-5 gap-y-2.5 text-sm">
        <dt class="text-base-content/50 uppercase text-[.68rem] tracking-wider pt-1">Kategorie</dt><dd class="font-semibold">${esc(i.kategorie)}</dd>
        <dt class="text-base-content/50 uppercase text-[.68rem] tracking-wider pt-1">Fundort</dt><dd class="font-semibold">${esc(i.fundort)}</dd>
        <dt class="text-base-content/50 uppercase text-[.68rem] tracking-wider pt-1">Gefunden</dt><dd class="font-semibold">${esc(i.datum_fund)}</dd>
        <dt class="text-base-content/50 uppercase text-[.68rem] tracking-wider pt-1">Lagerort</dt><dd class="font-semibold">${esc(i.abgabeort)}</dd>
        <dt class="text-base-content/50 uppercase text-[.68rem] tracking-wider pt-1">Abholen bis</dt><dd class="font-semibold">${esc(i.datum_ablauf)}</dd>
      </dl>
      <div class="mt-4 border-t border-base-200 pt-3">
        <p class="text-[.68rem] uppercase tracking-wider text-base-content/50 mb-1">Beschreibung</p>
        <p class="text-sm">${esc(i.beschreibung)}</p>
      </div>
      ${claimable
        ? `<button class="btn btn-primary w-full mt-5" onclick="openClaim(${i.id})">Das ist meins — Anspruch melden</button>`
        : `<p class="text-sm text-base-content/40 mt-5">Dieses Fundstück wurde bereits abgeholt.</p>`}
    </div>
  </div>`;
  show('item');
}
function backFromItem() { show(lastGrid === 'search' ? 'search' : 'home'); }

function openClaim(id) {
  const i = items.find(x => x.id === id);
  claimModal.dataset.item = id;
  $('#claimItemLabel').textContent = `#${i.id} — ${i.titel} (${i.fundort})`;
  $('#claimName').value = ''; $('#claimProof').value = '';
  claimModal.showModal();
}

function matches(i) {
  const q = $('#searchQ').value.trim().toLowerCase();
  if (filterCat !== 'Alle' && i.kategorie !== filterCat) return false;
  if (filterStatus !== 'Alle' && i.status !== filterStatus) return false;
  if (!q) return true;
  const hay = [i.titel, i.beschreibung, i.fundort, i.kategorie, ('#'+i.id),
               ...(i.tags||[])].join(' ').toLowerCase();
  return hay.includes(q);
}
function renderSearch() {
  const list = items.filter(matches).sort((a,b)=> b.datum_fund.localeCompare(a.datum_fund));
  $('#resultCount').innerHTML = `<b>${list.length}</b> Treffer`;
  $('#searchGrid').innerHTML = list.length
    ? list.map(i => card(i)).join('')
    : `<div class="col-span-full text-center border border-dashed border-base-300 rounded-box py-10 text-base-content/50">
         Keine Treffer — anderen Suchbegriff probieren.</div>`;
}
function chip(label, active, onclick) {
  return `<button class="btn btn-sm rounded-full ${active?'btn-neutral':'btn-outline btn-ghost'}" onclick="${onclick}">${label}</button>`;
}
function renderChips() {
  const j = (s) => s.replace(/'/g, "\\'");
  $('#catChips').innerHTML = ['Alle', ...DATA.categories]
    .map(c => chip(c + (c==='Alle'?'':` (${items.filter(i=>i.kategorie===c).length})`),
                   filterCat===c, `setCat('${j(c)}')`)).join('');
  $('#statusChips').innerHTML = ['Alle','Offen','Beansprucht','Abgeholt']
    .map(s => chip(s, filterStatus===s, `setStatus('${s}')`)).join('');
}
function setCat(c) { filterCat = c; renderChips(); renderSearch(); }
function setStatus(s) { filterStatus = s; renderChips(); renderSearch(); }
function goSearchAll() {
  $('#searchQ').value = ''; filterCat='Alle'; filterStatus='Alle';
  renderChips(); renderSearch();
  $('#searchTitle').textContent = 'Alle Fundstücke'; show('search');
}
function goSearchCat(cat) {
  $('#searchQ').value = ''; filterCat=cat; filterStatus='Alle';
  renderChips(); renderSearch();
  $('#searchTitle').textContent = cat; show('search');
}
function doSearch(e) { e.preventDefault();
  $('#searchQ').value = $('#homeQ').value;
  filterCat='Alle'; filterStatus='Alle'; renderChips(); renderSearch();
  $('#searchTitle').textContent = 'Suchergebnisse'; show('search'); }
function doSearchFromView(e) { e.preventDefault(); renderSearch(); }

function katCard(cat) {
  const icon = KAT_ICON[cat] || '📦';
  const n = items.filter(i=>i.kategorie===cat).length;
  return `<div>
    <div class="card bg-base-100 shadow card-hover cursor-pointer h-full" onclick="goSearchCat('${cat.replace(/'/g,"\\'")}')">
      <div class="card-body p-4 items-center text-center gap-1">
        <span class="text-4xl">${icon}</span>
        <h3 class="card-title text-sm justify-center">${esc(cat)}</h3>
        <span class="text-xs text-base-content/50">${n} Stück(e)</span>
      </div>
    </div>
  </div>`;
}

function init() {
  showFlash('__FLASH__');
  const open = items.filter(i=>i.status==='Offen');
  $('#openCount').textContent = `${open.length} offen`;
  $('#statDrawer').innerHTML = `
    <div class="stats stats-vertical w-full bg-base-200/40">
      <div class="stat py-2"><div class="stat-title text-xs">Offen</div>
        <div class="stat-value text-primary text-xl">${open.length}</div></div>
      <div class="stat py-2"><div class="stat-title text-xs">Diese Woche</div>
        <div class="stat-value text-xl">${items.filter(i=>i.neu).length}</div></div>
      <div class="stat py-2"><div class="stat-title text-xs">Zurückgeführt</div>
        <div class="stat-value text-success text-xl">${items.filter(i=>i.status==='Abgeholt').length}</div></div>
      <div class="stat py-2"><div class="stat-title text-xs">Gesamt</div>
        <div class="stat-value text-xl">${items.length}</div></div>
    </div>`;

  // Kategorie-Scroller
  $('#scrollerCats').innerHTML = DATA.categories.map(katCard).join('');

  // Neu
  const neu = [...items].filter(i=>i.status!=='Entsorgt')
    .sort((a,b)=>b.datum_fund.localeCompare(a.datum_fund)).slice(0,10);
  $('#scrollerNew').innerHTML = neu.map(i=>`<div>${card(i)}</div>`).join('');

  // Kategorien-Liste mit Buttons
  $('#catList').innerHTML = DATA.categories.map(cat => {
    const icon = KAT_ICON[cat] || '📦';
    const n = items.filter(i=>i.kategorie===cat).length;
    return `<div class="flex items-center gap-3 bg-base-100 border border-base-200 rounded-box px-4 py-3 shadow-sm">
      <span class="text-2xl">${icon}</span>
      <div class="flex-1"><b class="text-sm">${esc(cat)}</b>
        <div class="text-xs text-base-content/50">${n} Fundstück(e)</div></div>
      <button class="btn btn-sm btn-outline" onclick="goSearchCat('${cat.replace(/'/g,"\\'")}')">Ansehen →</button>
    </div>`;
  }).join('');

  // Drawer-Menüs
  const j = (s) => s.replace(/'/g, "\\'");
  $('#drawerCats').innerHTML = DATA.categories.map(c =>
    `<li><a class="text-sm" onclick="closeDrawer();goSearchCat('${j(c)}')">${KAT_ICON[c]||'📦'} ${esc(c)}
      <span class="badge badge-ghost badge-xs ml-auto">${items.filter(i=>i.kategorie===c).length}</span></a></li>`).join('');
  $('#drawerStatus').innerHTML = ['Alle','Offen','Beansprucht','Abgeholt'].map(s =>
    `<li><a class="text-sm" onclick="closeDrawer();goSearchStatus('${s}')">${s}</a></li>`).join('');

  renderChips();
}
function goSearchStatus(s) {
  $('#searchQ').value = ''; filterCat='Alle'; filterStatus=s;
  renderChips(); renderSearch();
  $('#searchTitle').textContent = 'Fundstücke · ' + s; show('search');
}
init();
</script>
</body>
</html>
"""

UI = (UI
      .replace("__WORDMARK__", wordmark)
      .replace("__LOGOTOP__", logo_top)
      .replace("__DATA__", data_json)
      .replace("__FLASH__", flash.replace("'", "\\'")))

components.html(UI, height=1400, scrolling=True)
