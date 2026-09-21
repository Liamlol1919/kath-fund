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


def file_uri(path_str, max_dim=1400):
    p = Path(path_str)
    if not p.exists():
        return ""
    img = Image.open(p)
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


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
    <div class="report-wrap">
    <button onclick="window.parent.location.search=''"
      style="border:1px solid #D6D5D1;background:#fff;border-radius:10px;padding:6px 12px;font-size:.85rem;cursor:pointer;">← Zurück zur App</button>
    <div class="rp-title">📷 Fund melden</div>
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
ipad_frame = file_uri("assets/ipad.png")
logo_main = file_uri("assets/logo_new.png", 900) or logo_top
data_json = json.dumps({"items": items_json, "wordmark": wordmark, "logoTop": logo_top,
                        "categories": CATEGORIES, "claims": len(claims_json)},
                       ensure_ascii=False)

UI = r"""
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css" rel="stylesheet" type="text/css"/>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  :root {
    --bg: #EDECE8; --card: #FFFFFF; --fg: #18181B; --muted: #71717A;
    --line: #D6D5D1; --line-dash: #C9C8C4; --accent: #DC2626; --accent-fg: #FEF2F2;
    --ok: #16A34A; --info: #2563EB; --warn: #D97706;
  }
  * { -webkit-font-smoothing: antialiased; }
  body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg);
         color: var(--fg); margin: 0; padding-top: 0; }
  html, body { margin-top: 0 !important; }
  .app { background: var(--bg); }

  /* ---------- Typo & Basis (shadcn-Vibe) ---------- */
  .lbl { font-size: .68rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
         color: var(--muted); }
  h1 { font-weight: 800; letter-spacing: -.03em; }
  .dots { background-image: radial-gradient(#C9C8C4 1px, transparent 1.2px); background-size: 16px 16px; }
  .icard { background: var(--card); border: 1px solid var(--line); border-radius: .9rem; }
  .icard-hover { transition: all .16s ease; }
  .icard-hover:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(24,24,27,.08);
                       border-color: #C8C8CC; }
  .clamp2 { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
  .scroller { display:flex; gap:.75rem; overflow-x:auto; padding:.25rem .15rem .85rem;
              scroll-snap-type:x proximity; scrollbar-width: thin; }
  .scroller > * { flex:0 0 200px; scroll-snap-align:start; }
  .scroller::-webkit-scrollbar { height: 5px; }
  .scroller::-webkit-scrollbar-thumb { background:#D4D4D8; border-radius: 3px; }
  dialog::backdrop { background: rgba(24,24,27,.5); backdrop-filter: blur(2px); }
  .btn-accent { background: var(--accent); color: #fff; border: none; }
  .btn-accent:hover { background: #B91C1C; color:#fff; }
  .chip { border:1px solid var(--line); background:#fff; color:var(--fg); border-radius:999px;
          padding: .3rem .8rem; font-size:.78rem; font-weight:500; }
  .chip.on { background: var(--fg); color:#fff; border-color: var(--fg); }
  svg.lucide { width: 1.15em; height: 1.15em; vertical-align: -0.2em; }
</style>
</head>
<body>
<div class="app">

  <!-- floating sidebar-button + FAB -->
  <button class="fixed top-3 left-3 z-40 w-10 h-10 rounded-xl bg-white border border-[var(--line)] shadow-sm flex items-center justify-center"
          onclick="drawer.open()" aria-label="Menü">
    <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
  </button>
  <button class="fixed bottom-4 right-4 z-40 h-12 px-4 rounded-full btn-accent shadow-lg text-sm font-semibold flex items-center gap-2"
          onclick="openReport('camera')">
    <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg> Melden
  </button>

  <!-- flash -->
  <div id="flash" class="hidden px-4 pt-3">
    <div class="icard px-4 py-3 flex items-center gap-2 text-sm border-[var(--ok)]/40 bg-[#F0FDF4]">
      <svg class="lucide text-[var(--ok)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M20 6 9 17l-5-5"/></svg>
      <span id="flashText"></span>
    </div>
  </div>

  <!-- ============ HOME ============ -->
  <div id="view-home" class="max-w-6xl mx-auto px-4 pb-10">
    <div class="dots rounded-2xl -mx-4 px-4 pt-7 pb-5 text-center">
      <img src="__LOGO__" class="w-52 md:w-60 mx-auto" alt="kath.fund">
    </div>

    <form class="join w-full mt-4" onsubmit="doSearch(event)">
      <input id="homeQ" class="input input-bordered join-item w-full bg-white" style="border-radius:.65rem 0 0 .65rem"
             placeholder="Was suchst du? Jacke, AirPods, #1002 …">
      <button class="btn join-item" style="border-radius:0 .65rem .65rem 0">
        <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      </button>
    </form>

    <!-- Zwei Wege -->
    <div class="grid grid-cols-2 gap-3 mt-4">
      <div class="icard icard-hover p-4 cursor-pointer" onclick="openReport('camera')">
        <div class="w-10 h-10 rounded-xl bg-[var(--accent-fg)] flex items-center justify-center text-[var(--accent)]">
          <svg class="lucide" style="width:1.4em;height:1.4em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z"/><circle cx="12" cy="13" r="3.2"/></svg>
        </div>
        <b class="block mt-2 text-sm">Etwas gefunden?</b>
        <span class="text-xs text-[var(--muted)]">Foto → automatisch eintragen</span>
      </div>
      <div class="icard icard-hover p-4 cursor-pointer" onclick="goSearchAll()">
        <div class="w-10 h-10 rounded-xl bg-[#EFF6FF] flex items-center justify-center text-[var(--info)]">
          <svg class="lucide" style="width:1.4em;height:1.4em" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/><path d="M8.5 11h5"/></svg>
        </div>
        <b class="block mt-2 text-sm">Etwas verloren?</b>
        <span class="text-xs text-[var(--muted)]">Verzeichnis durchsuchen</span>
      </div>
    </div>

    <!-- Kategorien -->
    <p class="lbl mt-6 mb-2">Kategorien</p>
    <div class="scroller" id="scrollerCats"></div>

    <!-- Neu -->
    <p class="lbl mt-3 mb-2">Neu im Fundbüro</p>
    <div class="scroller" id="scrollerNew"></div>

    <!-- Alle Bereiche -->
    <p class="lbl mt-3 mb-2">Alle Bereiche</p>
    <div class="grid grid-cols-1 gap-2" id="catList"></div>
  </div>

  <!-- ============ SEARCH ============ -->
  <div id="view-search" class="max-w-6xl mx-auto px-4 pb-10 hidden">
    <button class="btn btn-ghost btn-sm mt-3 -ml-2" onclick="show('home')">
      <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="m15 18-6-6 6-6"/></svg> Start
    </button>
    <h1 class="text-xl mt-1" id="searchTitle">Alle Fundstücke</h1>
    <form class="join w-full mt-3" onsubmit="doSearchFromView(event)">
      <input id="searchQ" class="input input-bordered join-item w-full bg-white" style="border-radius:.65rem 0 0 .65rem" placeholder="Suchen oder #Belegnummer …">
      <button class="btn join-item" style="border-radius:0 .65rem .65rem 0">
        <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      </button>
    </form>
    <div class="flex flex-wrap gap-1.5 mt-3" id="catChips"></div>
    <div class="flex flex-wrap gap-1.5 mt-2" id="statusChips"></div>
    <p class="text-xs text-[var(--muted)] mt-4" id="resultCount"></p>
    <div class="grid grid-cols-2 gap-3 mt-2" id="searchGrid"></div>
  </div>

  <!-- ============ ITEM ============ -->
  <div id="view-item" class="max-w-3xl mx-auto px-4 pb-24 hidden">
    <button class="btn btn-ghost btn-sm mt-3 -ml-2" onclick="backFromItem()">
      <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="m15 18-6-6 6-6"/></svg> Zurück
    </button>
    <div id="itemDetail" class="mt-2"></div>
  </div>

  </div><!-- /app -->

<!-- ============ DRAWER ============ -->
<dialog id="drawer" class="modal modal-start">
  <div class="modal-box max-w-xs p-0 rounded-r-2xl rounded-l-none overflow-hidden">
    <div class="p-4 border-b border-[var(--line)]">
      <img src="__LOGO__" class="w-32" alt="kath.fund">
      <p class="text-xs text-[var(--muted)] mt-2">Katharineum zu Lübeck</p>
    </div>
    <div class="p-3 space-y-0.5">
      <button class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 hover:bg-[#E9E8E4] text-sm font-medium" onclick="drawer.close();show('home')">
        <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1Z"/></svg> Start</button>
      <button class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 hover:bg-[#E9E8E4] text-sm font-medium" onclick="drawer.close();goSearchAll()">
        <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg> Alle Fundstücke</button>
      <button class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 hover:bg-[#E9E8E4] text-sm font-medium" onclick="drawer.close();openReport('camera')">
        <svg class="lucide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z"/><circle cx="12" cy="13" r="3.2"/></svg> Fund melden</button>
    </div>
    <div class="px-4 pt-2 pb-1 lbl">Kategorien</div>
    <div class="px-3 pb-2 max-h-56 overflow-y-auto" id="drawerCats"></div>
    <div class="px-4 pt-2 pb-1 lbl">Kennzahlen</div>
    <div class="px-4 pb-4 grid grid-cols-2 gap-2" id="statDrawer"></div>
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>

<!-- ============ CLAIM MODAL ============ -->
<dialog id="claimModal" class="modal">
  <div class="modal-box max-w-md p-5">
    <h3 class="font-bold text-lg">Das ist meins</h3>
    <p class="text-sm text-[var(--muted)] mt-0.5" id="claimItemLabel"></p>
    <div class="pt-3 space-y-3">
      <input id="claimName" class="input input-bordered w-full bg-white" placeholder="Name und Klasse* (z. B. Julia Koch, 9b)">
      <textarea id="claimProof" class="textarea textarea-bordered w-full h-24 bg-white"
        placeholder="Nachweis*: Was weiß nur die Besitzerin / der Besitzer? Inhalt, Gravur, Initialen …"></textarea>
    </div>
    <div class="modal-action">
      <button class="btn btn-ghost btn-sm" onclick="claimModal.close()">Abbrechen</button>
      <button class="btn btn-accent btn-sm" onclick="submitClaim()">Anspruch einreichen</button>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>

<script>
const DATA = __DATA__;
const items = DATA.items;
let currentView = 'home', lastGrid = null, filterCat = 'Alle', filterStatus = 'Alle';

const $ = (s) => document.querySelector(s);
const esc = (s) => { const d = document.createElement('div'); d.textContent = s ?? ''; return d.innerHTML; };
const KAT_ICON = {
  "Kleidung & Textilien": '<path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23Z"/>',
  "Trinkflaschen & Brotdosen": '<path d="M15 2h2a2 2 0 0 1 2 2v18a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h2"/><path d="M10 2v20"/><path d="M7 8h3M7 12h3M7 16h3"/>',
  "Rucksäcke & Taschen": '<path d="M4 10a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><path d="M8 21v-5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v5"/>',
  "Elektronik & Kabel": '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-5Zm18 0h-3a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-5Z"/><path d="M3 14v-3a9 9 0 0 1 18 0v3"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"/>',
  "Schlüssel & Wertsachen": '<circle cx="7.5" cy="15.5" r="4.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
  "Schulmaterial & Bücher": '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
  "Sportbekleidung": '<path d="m8 3 4 8 5-5 5 15H2L8 3Z"/>',
  "Sonstiges": '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
};
const katSvg = (kat, cls='lucide') =>
  `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${KAT_ICON[kat]||KAT_ICON['Sonstiges']}</svg>`;

function showFlash(t) { if (!t) return;
  $('#flashText').textContent = t; $('#flash').classList.remove('hidden'); }
function show(v) { currentView = v;
  ['home','search','item'].forEach(x => $('#view-'+x).classList.toggle('hidden', x !== v));
  window.scrollTo(0,0); fitHeight(); }
function fitHeight() {
  try {
    const f = window.frameElement;
    if (f) f.style.height = Math.max(document.documentElement.scrollHeight, 600) + 'px';
  } catch (e) {}
}
window.addEventListener('load', fitHeight);
window.addEventListener('resize', fitHeight);
setInterval(fitHeight, 500);
function openReport(mode) { window.top.location.search = '?view=report' + (mode === 'camera' ? '&mode=camera' : ''); }
function submitClaim() {
  const name = $('#claimName').value.trim(), proof = $('#claimProof').value.trim();
  const iid = claimModal.dataset.item;
  if (!name || !proof) { $('#claimName').classList.toggle('input-error', !name);
                         $('#claimProof').classList.toggle('textarea-error', !proof); return; }
  window.top.location.search = `?action=claim&item=${iid}&name=${encodeURIComponent(name)}&proof=${encodeURIComponent(proof)}`;
}

function statusBadge(s) {
  const map = { 'Offen':'bg-[#FEF3C7] text-[#92400E]', 'Beansprucht':'bg-[#DBEAFE] text-[#1E40AF]',
                'Abgeholt':'bg-[#DCFCE7] text-[#166534]', 'Entsorgt':'bg-[#FEE2E2] text-[#991B1B]' };
  return `<span class="text-[.62rem] font-semibold uppercase tracking-wide rounded-full px-2 py-0.5 ${map[s]||'bg-[#E9E8E4] text-[var(--muted)]'}">${esc(s)}</span>`;
}

function card(i) {
  const fig = i.img
    ? `<figure class="h-32 overflow-hidden"><img src="${i.img}" class="w-full h-full object-cover" alt=""></figure>`
    : `<figure class="h-32 dots flex items-center justify-center text-[var(--muted)]">${katSvg(i.kategorie,'lucide')}<span style="width:2em;height:2em"></span></figure>`;
  const neu = i.neu ? `<span class="text-[.62rem] font-semibold uppercase rounded-full px-2 py-0.5 bg-[var(--accent)] text-white">Neu</span>` : '';
  return `
  <div class="icard icard-hover cursor-pointer overflow-hidden" onclick="openItem(${i.id},'grid')">
    ${fig}
    <div class="p-3">
      <b class="block text-[.88rem] leading-snug clamp2">${esc(i.titel)}</b>
      <p class="text-[.68rem] text-[var(--muted)] mt-1">${esc(i.fundort)}</p>
      <div class="flex flex-wrap gap-1 mt-2">${statusBadge(i.status)}${neu}</div>
    </div>
  </div>`;
}

function openItem(id, ctx) {
  lastGrid = ctx;
  const i = items.find(x => x.id === id); if (!i) return;
  const claimable = i.status === 'Offen' || i.status === 'Beansprucht';
  const fig = i.img
    ? `<img src="${i.img}" class="w-full rounded-xl border border-[var(--line)] object-cover">`
    : `<div class="rounded-xl border border-dashed border-[var(--line-dash)] h-56 dots flex items-center justify-center text-[var(--muted)]">${katSvg(i.kategorie,'lucide')}<span style="width:3.2em;height:3.2em"></span></div>`;
  const tags = (i.tags||[]).map(t=>`<span class="text-[.68rem] rounded-full border border-[var(--line)] px-2 py-0.5">${esc(t)}</span>`).join('');
  $('#itemDetail').innerHTML = `
  <div class="flex items-center gap-2 flex-wrap mt-1">
    <h1 class="text-lg md:text-xl">${esc(i.titel)}</h1>
    ${statusBadge(i.status)}${i.neu?'<span class="text-[.62rem] font-semibold uppercase rounded-full px-2 py-0.5 bg-[var(--accent)] text-white">Neu</span>':''}
  </div>
  <div class="mt-3 space-y-3">
    ${fig}
    ${tags?`<div class="flex flex-wrap gap-1.5">${tags}</div>`:''}
    <div class="icard p-4 space-y-2.5 text-sm">
      <div class="flex justify-between"><span class="text-[var(--muted)]">Kategorie</span><b>${esc(i.kategorie)}</b></div>
      <div class="flex justify-between"><span class="text-[var(--muted)]">Fundort</span><b>${esc(i.fundort)}</b></div>
      <div class="flex justify-between"><span class="text-[var(--muted)]">Gefunden</span><b>${esc(i.datum_fund)}</b></div>
      <div class="flex justify-between"><span class="text-[var(--muted)]">Lagerort</span><b>${esc(i.abgabeort)}</b></div>
      <div class="flex justify-between"><span class="text-[var(--muted)]">Abholen bis</span><b>${esc(i.datum_ablauf)}</b></div>
      <p class="text-xs text-[var(--muted)] border-t border-[var(--line)] pt-2.5 leading-relaxed">${esc(i.beschreibung)}</p>
    </div>
    ${claimable
      ? `<button class="btn btn-accent w-full" onclick="openClaim(${i.id})">Das ist meins — Anspruch melden</button>`
      : `<p class="text-center text-xs text-[var(--muted)]">Bereits abgeholt.</p>`}
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
  const hay = [i.titel, i.beschreibung, i.fundort, i.kategorie, ('#'+i.id), ...(i.tags||[])].join(' ').toLowerCase();
  return hay.includes(q);
}
function renderSearch() {
  const list = items.filter(matches).sort((a,b)=> b.datum_fund.localeCompare(a.datum_fund));
  $('#resultCount').innerHTML = `<b>${list.length}</b> Treffer${filterCat!=='Alle'?' · '+esc(filterCat):''}`;
  $('#searchGrid').innerHTML = list.length
    ? list.map(i => card(i)).join('')
    : `<div class="col-span-full icard border-dashed py-10 text-center text-sm text-[var(--muted)]">
         Keine Treffer — anderen Suchbegriff probieren.</div>`;
  fitHeight();
}
function renderChips() {
  const j = (s) => s.replace(/'/g, "\\'");
  $('#catChips').innerHTML = ['Alle', ...DATA.categories]
    .map(c => `<button class="chip ${filterCat===c?'on':''}" onclick="setCat('${j(c)}')">${esc(c)}</button>`).join('');
  $('#statusChips').innerHTML = ['Alle','Offen','Beansprucht','Abgeholt']
    .map(s => `<button class="chip ${filterStatus===s?'on':''}" onclick="setStatus('${s}')">${s}</button>`).join('');
}
function setCat(c) { filterCat = c; renderChips(); renderSearch(); }
function setStatus(s) { filterStatus = s; renderChips(); renderSearch(); }
function goSearchAll() { $('#searchQ').value=''; filterCat='Alle'; filterStatus='Alle';
  renderChips(); renderSearch(); $('#searchTitle').textContent='Alle Fundstücke'; show('search'); }
function goSearchCat(cat) { $('#searchQ').value=''; filterCat=cat; filterStatus='Alle';
  renderChips(); renderSearch(); $('#searchTitle').textContent=cat; show('search'); }
function doSearch(e) { e.preventDefault(); $('#searchQ').value = $('#homeQ').value;
  filterCat='Alle'; filterStatus='Alle'; renderChips(); renderSearch();
  $('#searchTitle').textContent='Suchergebnisse'; show('search'); }
function doSearchFromView(e) { e.preventDefault(); renderSearch(); }

function init() {
  showFlash('__FLASH__');
  const open = items.filter(i=>i.status==='Offen');

  $('#scrollerCats').innerHTML = DATA.categories.map(cat => {
    const n = items.filter(i=>i.kategorie===cat).length;
    return `<div>
      <div class="icard icard-hover p-3.5 cursor-pointer h-full" onclick="goSearchCat('${cat.replace(/'/g,"\\'")}')">
        <div class="w-9 h-9 rounded-lg bg-[#E9E8E4] flex items-center justify-center">${katSvg(cat)}</div>
        <b class="block text-[.8rem] leading-tight mt-2 clamp2">${esc(cat)}</b>
        <span class="text-[.66rem] text-[var(--muted)]">${n}</span>
      </div></div>`;
  }).join('');

  const neu = [...items].filter(i=>i.status!=='Entsorgt')
    .sort((a,b)=>b.datum_fund.localeCompare(a.datum_fund)).slice(0,10);
  $('#scrollerNew').innerHTML = neu.map(i=>`<div>${card(i)}</div>`).join('');

  $('#catList').innerHTML = DATA.categories.map(cat => {
    const n = items.filter(i=>i.kategorie===cat).length;
    return `<div class="icard flex items-center gap-3 px-3.5 py-2.5">
      <div class="w-8 h-8 rounded-lg bg-[#E9E8E4] flex items-center justify-center">${katSvg(cat)}</div>
      <div class="flex-1 min-w-0"><b class="block text-[.82rem] truncate">${esc(cat)}</b>
        <span class="text-[.66rem] text-[var(--muted)]">${n} Fundstück(e)</span></div>
      <button class="btn btn-ghost btn-xs" onclick="goSearchCat('${cat.replace(/'/g,"\\'")}')">→</button>
    </div>`;
  }).join('');

  const j = (s) => s.replace(/'/g, "\\'");
  $('#drawerCats').innerHTML = DATA.categories.map(c =>
    `<button class="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 hover:bg-[#E9E8E4] text-[.82rem]" onclick="drawer.close();goSearchCat('${j(c)}')">
      <span class="text-[var(--muted)]">${katSvg(c)}</span><span class="truncate">${esc(c)}</span>
      <span class="ml-auto text-[.66rem] text-[var(--muted)]">${items.filter(i=>i.kategorie===c).length}</span></button>`).join('');

  $('#statDrawer').innerHTML = `
    <div class="icard p-2.5"><p class="lbl">Offen</p><p class="text-lg font-extrabold">${open.length}</p></div>
    <div class="icard p-2.5"><p class="lbl">Neu</p><p class="text-lg font-extrabold">${items.filter(i=>i.neu).length}</p></div>
    <div class="icard p-2.5"><p class="lbl">Abgeholt</p><p class="text-lg font-extrabold text-[var(--ok)]">${items.filter(i=>i.status==='Abgeholt').length}</p></div>
    <div class="icard p-2.5"><p class="lbl">Gesamt</p><p class="text-lg font-extrabold">${items.length}</p></div>`;
  renderChips();
  fitHeight();
}
init();

</script>
</body>
</html>
"""

UI = (UI
      .replace("__WORDMARK__", wordmark)
      .replace("__LOGOTOP__", logo_top)
      .replace("__LOGO__", logo_main)
      .replace("__DATA__", data_json)
      .replace("__FLASH__", flash.replace("'", "\\'")))

st.markdown("""
<style>
  header[data-testid="stHeader"] { display: none !important; }
  [data-testid="stAppViewContainer"] > section.main,
  section.main { padding: 0 !important; }
  .block-container, [data-testid="stMainBlockContainer"] {
    padding: 0 !important; max-width: 100% !important; margin-top: 0 !important;
  }
  [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"],
  section.stMain > div { background: #EDECE8 !important; }
  [data-testid="stVerticalBlock"] { gap: 0 !important; }
  section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ÃuÃeres iframe: eigene Sandbox, damit Modal/Top-Navigation funktionieren
OUTER = """<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#EDECE8;overflow:hidden}
iframe{width:100%;border:0;display:block}</style></head><body>
<iframe id="app" srcdoc="__SRCDOC__"
  sandbox="allow-scripts allow-same-origin allow-top-navigation allow-forms allow-modals"
  style="width:100%;height:1200px"></iframe>
<script>
const f = document.getElementById('app');
function sync() {
  try {
    const h = f.contentDocument.documentElement.scrollHeight;
    if (h > 200) f.style.height = h + 'px';
  } catch (e) {}
  try {
    const of = window.frameElement;
    if (of) {
      const hh = parseInt(f.style.height) || 1200;
      of.style.height = hh + 'px';
      let p = of.parentElement;
      if (p) p.style.height = hh + 'px';
      if (p && p.parentElement) p.parentElement.style.height = 'auto';
    }
  } catch (e) {}
}
setInterval(sync, 400);
window.addEventListener('message', sync);
</script></body></html>"""

outer = OUTER.replace("__SRCDOC__", html_mod.escape(UI, quote=True))
components.html(outer, height=1200, scrolling=False)
