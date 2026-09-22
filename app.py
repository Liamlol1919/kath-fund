"""kath.fund — Digitales Fundbüro des Katharineums zu Lübeck.

UI komplett auf `streamlit-shadcn-ui` aufgebaut (shadcn-Cards, Badges,
Tabs, Metric-Cards, Charts, Dialoge). Bilderkennung über das
Teachable-Machine-Modell `keras_model.h5` aus TestKI4
(https://github.com/kumma-git/TestKI4) — Input: Foto, Output: Klassen aus
`teachable_labels.txt`. Fallback: ONNX-ImageNet, danach Heuristik.
"""

from __future__ import annotations

import datetime
import io
import json
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit_shadcn_ui as ui
from PIL import Image

from teachable_ai import (
    TEACHABLE_TO_CATEGORY,
    heuristic_guess,
    load_teachable_labels,
    predict_teachable,
)

# =============================================================================
# 1. Seite & Konstanten
# =============================================================================
st.set_page_config(
    page_title="kath.fund — Fundbüro Katharineum",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STORAGE = Path("data")
IMG_DIR = STORAGE / "images"
ITEMS_FILE = STORAGE / "items.json"
CLAIMS_FILE = STORAGE / "claims.json"
STORAGE.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)

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
STATUSES = ["Offen", "Beansprucht", "Abgeholt"]

KAT_EMOJI = {
    "Kleidung & Textilien": "🧥",
    "Trinkflaschen & Brotdosen": "🥤",
    "Rucksäcke & Taschen": "🎒",
    "Elektronik & Kabel": "🎧",
    "Schlüssel & Wertsachen": "🔑",
    "Schulmaterial & Bücher": "📚",
    "Sportbekleidung": "👟",
    "Sonstiges": "📦",
}

STATUS_VARIANT = {
    "Offen": "destructive",
    "Beansprucht": "secondary",
    "Abgeholt": "outline",
    "Entsorgt": "outline",
}

TABS = ["Entdecken", "Verzeichnis", "Fund melden", "Dashboard"]

# =============================================================================
# 2. Storage
# =============================================================================
DEFAULT_ITEMS = [
    {
        "id": 1001, "titel": "Dunkelblaue Regenjacke",
        "kategorie": "Kleidung & Textilien", "fundort": "Pausenhof",
        "abgabeort": "Hausmeisterbüro (Raum 001)",
        "datum_fund": "2026-09-01", "datum_ablauf": "2026-12-01",
        "status": "Offen",
        "beschreibung": "Größe M, gelber Reißverschluss.",
        "image_file": None, "tags": ["Jacke", "Blau"],
    },
    {
        "id": 1002, "titel": "Edelstahl-Trinkflasche 1L",
        "kategorie": "Trinkflaschen & Brotdosen", "fundort": "Sporthalle",
        "abgabeort": "Sporthalle Regallager",
        "datum_fund": "2026-08-28", "datum_ablauf": "2026-11-28",
        "status": "Offen",
        "beschreibung": "Mattgrün, mit Sport-Aufklebern.",
        "image_file": None, "tags": ["Flasche", "Grün"],
    },
]


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


for key, path, default in (
    ("items", ITEMS_FILE, DEFAULT_ITEMS),
    ("claims", CLAIMS_FILE, []),
):
    if key not in st.session_state:
        st.session_state[key] = load_json(path, default)

st.session_state.setdefault("tab", TABS[0])
st.session_state.setdefault("selected_id", None)
st.session_state.setdefault("flash", None)  # (kind, title, text)
st.session_state.setdefault("rep_bytes", None)
st.session_state.setdefault("rep_ai", None)
st.session_state.setdefault("rep_titel_ai", "")
st.session_state.setdefault("rep_kat_ai", None)
st.session_state.setdefault("show_done_dialog", False)
st.session_state.setdefault("uploader_nonce", 0)

items: list = st.session_state["items"]
claims: list = st.session_state["claims"]
heute = datetime.date.today().isoformat()


def save_all() -> None:
    save_json(ITEMS_FILE, items)
    save_json(CLAIMS_FILE, claims)


def flash(kind: str, title: str, text: str = "") -> None:
    st.session_state["flash"] = (kind, title, text)


def show_flash() -> None:
    msg = st.session_state.get("flash")
    if not msg:
        return
    kind, title, text = msg
    ui.alert(title, text or None, variant="destructive" if kind == "error" else "default")
    st.session_state["flash"] = None


# =============================================================================
# 3. Bilder & KI
# =============================================================================
def save_uploaded_image(pil_img: Image.Image, item_id: int) -> str:
    name = f"item_{item_id}_{int(datetime.datetime.now().timestamp())}.jpg"
    if pil_img.mode in ("RGBA", "P"):
        pil_img = pil_img.convert("RGB")
    pil_img.save(IMG_DIR / name, format="JPEG", quality=85)
    return name


def load_item_image(filename: str | None) -> Image.Image | None:
    if not filename:
        return None
    p = IMG_DIR / filename
    if p.exists():
        try:
            return Image.open(p)
        except Exception:
            return None
    return None


@st.cache_resource(show_spinner="🧠 KI-Modell wird geladen …")
def _onnx_session():
    """ONNX-Fallback (ImageNet) — nur falls Teachable/TF fehlt."""
    try:
        import onnxruntime as ort
        import urllib.request

        rel = "https://github.com/Liamlol1919/kath-fund/releases/download/models"
        for fname in ("mobilenetv2.onnx",):
            p = Path(fname)
            if not (p.exists() and p.stat().st_size > 1000):
                try:
                    urllib.request.urlretrieve(f"{rel}/{fname}", p)
                except Exception:
                    continue
            if p.exists() and p.stat().st_size > 1000:
                labels = load_json(Path("imagenet_labels.json"), [])
                if labels:
                    sess = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
                    return sess, labels
    except Exception:
        pass
    return None


_ONNX_TO_KAT = {
    "backpack": "Rucksäcke & Taschen", "purse": "Rucksäcke & Taschen",
    "handbag": "Rucksäcke & Taschen", "wallet": "Schlüssel & Wertsachen",
    "water bottle": "Trinkflaschen & Brotdosen", "bottle": "Trinkflaschen & Brotdosen",
    "coffee mug": "Trinkflaschen & Brotdosen", "cup": "Trinkflaschen & Brotdosen",
    "t-shirt": "Kleidung & Textilien", "jersey": "Kleidung & Textilien",
    "jacket": "Kleidung & Textilien", "running shoe": "Sportbekleidung",
    "pencil box": "Schulmaterial & Bücher", "calculator": "Schulmaterial & Bücher",
    "headphone": "Elektronik & Kabel", "laptop computer": "Elektronik & Kabel",
    "mobile phone": "Elektronik & Kabel", "padlock": "Schlüssel & Wertsachen",
}


def analyze(pil_image: Image.Image) -> dict:
    """Einheitliche Analyse: Teachable-h5 → ONNX → Heuristik."""
    res = predict_teachable(pil_image)
    if res is not None:
        return res
    sess = _onnx_session()
    if sess is not None:
        try:
            session, labels = sess
            from PIL import ImageOps

            img = ImageOps.fit(pil_image.convert("RGB"), (224, 224), Image.Resampling.LANCZOS)
            a = np.asarray(img, dtype=np.float32) / 255.0
            a = (a - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array(
                [0.229, 0.224, 0.225], dtype=np.float32
            )
            arr = np.transpose(a, (2, 0, 1))[None, ...]
            out = session.run(None, {session.get_inputs()[0].name: arr})[0][0]
            out = out - out.max()
            probs = np.exp(out) / np.exp(out).sum()
            ranked = np.argsort(probs)[::-1][:60]
            for i in ranked:
                name = str(labels[int(i)]).lower().replace("_", " ")
                if name in _ONNX_TO_KAT:
                    return {
                        "label": name.title(),
                        "confidence": float(np.clip(probs[int(i)] * 2.2, 0.4, 0.9)),
                        "category": _ONNX_TO_KAT[name],
                        "top3": [],
                        "engine": "MobileNetV2-ImageNet (Fallback)",
                    }
        except Exception:
            pass
    out = heuristic_guess(pil_image)
    return out


# =============================================================================
# 4. Theme & Header (shadcn)
# =============================================================================
st.markdown(
    """
    <style>
      .stApp { background: #F7F5F0; }
      header[data-testid="stHeader"] { background: rgba(247,245,240,.85); }
      section[data-testid="stSidebar"] { display: none; }
      h1.kath-title { font-weight: 800; letter-spacing: -.03em; margin: 0;
                      font-size: clamp(1.7rem, 4vw, 2.6rem); }
      p.kath-sub { color: #71717A; margin: .15rem 0 0; }
      .kath-hero { background: linear-gradient(135deg, #B23A2A, #7C2418);
                   color: #fff; border-radius: 1.1rem; padding: 1.6rem 1.8rem;
                   box-shadow: 0 12px 32px rgba(178,58,42,.25); }
      .kath-hero h2 { margin: 0; font-size: 1.5rem; letter-spacing: -.02em; }
      .kath-hero p { margin: .35rem 0 0; opacity: .9; }
    </style>
    """,
    unsafe_allow_html=True,
)

head_l, head_r = st.columns([1, 5])
with head_l:
    logo = Path("assets/logo_new.png")
    if logo.exists():
        st.image(str(logo), width=110)
    else:
        ui.avatar(fallback="K", size="large")
with head_r:
    st.markdown('<h1 class="kath-title">kath.fund 🎒</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="kath-sub">Digitales Fundbüro · Katharineum zu Lübeck · '
        "Foto hochladen, KI erkennt's, abholen.</p>",
        unsafe_allow_html=True,
    )
    ui.badges(
        [
            ("Katharineum zu Lübeck", "default"),
            ("Hausmeisterbüro · Raum 001", "secondary"),
            ("KI-Bilderkennung aktiv", "outline"),
        ]
    )
ui.separator()

# =============================================================================
# 5. Tabs (gesteuert → Karten können per Klick springen)
# =============================================================================
tab = ui.tabs(TABS, value=st.session_state.get("tab", TABS[0]), key="main_tabs")
st.session_state["tab"] = tab
show_flash()


def goto(view: str, category: str | None = None) -> None:
    st.session_state["tab"] = view
    if category is not None:
        st.session_state["fkat"] = category
    st.session_state["selected_id"] = None
    st.rerun()


def item_by_id(item_id: int) -> dict | None:
    return next((i for i in items if i.get("id") == item_id), None)


def status_badge(status: str) -> None:
    ui.badge(status, variant=STATUS_VARIANT.get(status, "secondary"))


def thumb(item: dict, width: int = 400) -> None:
    img = load_item_image(item.get("image_file"))
    if img is not None:
        st.image(img, use_container_width=True)
    else:
        st.markdown(
            f"<div style='font-size:3rem;text-align:center;padding:1rem;'>"
            f"{KAT_EMOJI.get(item.get('kategorie', ''), '📦')}</div>",
            unsafe_allow_html=True,
        )


def open_items():
    return [i for i in items if i.get("status") == "Offen"]


# =============================================================================
# 6. TAB: Entdecken
# =============================================================================
if tab == "Entdecken":
    st.markdown(
        "<div class='kath-hero'><h2>Verloren? Gefunden? Ein Foto genügt. 📷</h2>"
        "<p>Unsere KI erkennt Trinkflaschen, Schlüssel, Kopfhörer & Co. "
        "automatisch — du meldest den Fund in unter einer Minute.</p></div>",
        unsafe_allow_html=True,
    )
    st.write("")

    n_offen = len(open_items())
    neu_grenze = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    n_neu = len([i for i in items if str(i.get("datum_fund", "")) >= neu_grenze])
    n_abgeholt = len([i for i in items if i.get("status") == "Abgeholt"])

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        ui.metric_card("Offene Funde", n_offen, description="warten auf Abholung")
    with m2:
        ui.metric_card("Neu (7 Tage)", n_neu, description="frisch im Fundbüro")
    with m3:
        ui.metric_card("Bereits abgeholt", n_abgeholt, description="erfolgreich vermittelt 🎉")
    with m4:
        ui.metric_card("Kategorien", len(CATEGORIES), description="von Jacke bis Taschenrechner")

    st.write("")
    ui.card(
        title="Zwei Wege zum Ziel",
        description="Wähle, was zu dir passt — alles andere übernimmt die App.",
    )
    c1, c2 = st.columns(2)
    with c1:
        ui.card(
            title="📷 Etwas gefunden?",
            content="Foto hochladen → KI schlägt Kategorie vor → eintragen. Fertig.",
            footer="Dauert ca. 1 Minute.",
        )
        if ui.button("Fund melden", key="hero_report"):
            goto("Fund melden")
    with c2:
        ui.card(
            title="🔎 Etwas verloren?",
            content="Verzeichnis durchsuchen, Fundstück wiedererkennen, Anspruch melden.",
            footer=f"Aktuell {n_offen} offene Funde.",
        )
        if ui.button("Verzeichnis öffnen", key="hero_search", variant="secondary"):
            goto("Verzeichnis")

    st.write("")
    st.subheader("Kategorien")
    cols = st.columns(4)
    for idx, kat in enumerate(CATEGORIES):
        count = len([i for i in items if i.get("kategorie") == kat])
        with cols[idx % 4]:
            ui.card(
                title=f"{KAT_EMOJI.get(kat, '📦')} {kat}",
                description=f"{count} Fundstück(e)",
            )
            if ui.button("Ansehen", key=f"kat_{idx}", variant="outline"):
                goto("Verzeichnis", category=kat)

    st.write("")
    st.subheader("Neu im Fundbüro")
    fresh = sorted(items, key=lambda i: str(i.get("datum_fund", "")), reverse=True)[:4]
    if not fresh:
        ui.alert("Noch ganz leer hier", "Melde den ersten Fund über „Fund melden“.")
    else:
        cols = st.columns(4)
        for idx, it in enumerate(fresh):
            with cols[idx % 4]:
                thumb(it)
                st.markdown(f"**{it.get('titel', 'Fundstück')}**")
                st.caption(f"#{it.get('id')} · {it.get('fundort', '')}")
                status_badge(it.get("status", "Offen"))
                if ui.button("Details", key=f"new_{it.get('id')}", variant="secondary"):
                    st.session_state["selected_id"] = it.get("id")
                    goto("Verzeichnis")

# =============================================================================
# 7. TAB: Verzeichnis (Suche + Detail + Anspruch)
# =============================================================================
elif tab == "Verzeichnis":
    sel = st.session_state.get("selected_id")

    if sel is not None and (detail := item_by_id(sel)) is not None:
        # ---------------- Detailansicht ----------------
        if ui.button("← Zurück zum Verzeichnis", key="back", variant="ghost"):
            st.session_state["selected_id"] = None
            st.rerun()

        st.markdown(f"## {detail.get('titel', 'Fundstück')}")
        ui.badges(
            [
                (f"#{detail.get('id')}", "secondary"),
                (detail.get("kategorie", ""), "default"),
                (detail.get("status", ""), STATUS_VARIANT.get(detail.get("status", ""), "secondary")),
            ]
        )
        st.write("")
        d1, d2 = st.columns([3, 2])
        with d1:
            img = load_item_image(detail.get("image_file"))
            if img is not None:
                st.image(img, use_container_width=True)
            else:
                st.markdown(
                    f"<div style='font-size:5rem;text-align:center;padding:2rem;'>"
                    f"{KAT_EMOJI.get(detail.get('kategorie', ''), '📦')}</div>",
                    unsafe_allow_html=True,
                )
            tags = detail.get("tags", []) or []
            if tags:
                ui.badges([(t, "outline") for t in tags])
        with d2:
            ui.card(
                title="Funddaten",
                content=(
                    f"Kategorie: {detail.get('kategorie', '')}\n"
                    f"Fundort: {detail.get('fundort', '')}\n"
                    f"Gefunden: {detail.get('datum_fund', '')}\n"
                    f"Lagerort: {detail.get('abgabeort', '')}\n"
                    f"Abholen bis: {detail.get('datum_ablauf', '')}"
                ),
                description=detail.get("beschreibung", ""),
            )
            st.write("")
            if detail.get("status") in ("Offen", "Beansprucht"):
                ui.card(
                    title="Das ist meins 🙋",
                    description="Name + Nachweis angeben — das Sekretariat prüft den Anspruch.",
                )
                ui.input("Name und Klasse", key="claim_name", placeholder="z. B. Julia K., 9b")
                ui.textarea(
                    "Nachweis",
                    key="claim_proof",
                    placeholder="Was weiß nur der Besitzer? Inhalt, Gravur, Initialen …",
                    rows=3,
                )
                if ui.button("Anspruch einreichen", key="claim_go"):
                    name = (st.session_state.get("claim_name") or "").strip()
                    proof = (st.session_state.get("claim_proof") or "").strip()
                    if not name or not proof:
                        flash("error", "Fast geschafft", "Bitte Name und Nachweis ausfüllen.")
                        st.rerun()
                    new_id = max([c.get("claim_id", 500) for c in claims], default=500) + 1
                    claims.insert(
                        0,
                        {
                            "claim_id": new_id, "item_id": detail["id"],
                            "name": name, "proof": proof,
                            "datum": heute, "status": "In Prüfung",
                        },
                    )
                    detail["status"] = "Beansprucht"
                    save_all()
                    for k in ("claim_name", "claim_proof"):
                        st.session_state.pop(k, None)
                    flash("ok", "Anspruch eingereicht ✅", "Wir melden uns — bitte Ausweis mitbringen.")
                    st.rerun()
            else:
                ui.alert("Bereits abgeholt", "Dieses Fundstück wurde schon vermittelt. 🎉")
    else:
        # ---------------- Such- & Listenansicht ----------------
        st.subheader("Verzeichnis durchsuchen")
        q = ui.input(
            "Suche", value="", key="q", placeholder="Jacke, AirPods, #1002 …", type="search"
        )
        f1, f2, f3 = st.columns([2, 2, 1])
        with f1:
            fkat = ui.select("Kategorie", ["Alle", *CATEGORIES], key="fkat")
        with f2:
            fstat = ui.select("Status", ["Alle", *STATUSES], key="fstat")
        with f3:
            st.write("")
            if ui.button("Zurücksetzen", key="reset", variant="ghost"):
                for k in ("q", "fkat", "fstat"):
                    st.session_state.pop(k, None)
                st.rerun()

        def matches(it: dict) -> bool:
            if fkat != "Alle" and it.get("kategorie") != fkat:
                return False
            if fstat != "Alle" and it.get("status") != fstat:
                return False
            if (qq := (q or "").strip().lower()):
                hay = " ".join(
                    [
                        str(it.get("titel", "")), str(it.get("beschreibung", "")),
                        str(it.get("fundort", "")), str(it.get("kategorie", "")),
                        f"#{it.get('id')}", " ".join(it.get("tags", []) or []),
                    ]
                ).lower()
                return all(w in hay for w in qq.split())
            return True

        hits = sorted(
            [i for i in items if matches(i)],
            key=lambda i: str(i.get("datum_fund", "")),
            reverse=True,
        )
        st.caption(f"**{len(hits)}** Treffer" + (f" in „{fkat}“" if fkat != "Alle" else ""))

        if not hits:
            ui.alert(
                "Keine Treffer",
                "Anderen Suchbegriff versuchen — oder direkt einen Fund melden.",
            )
            if ui.button("Zum Meldeformular", key="nohit", variant="secondary"):
                goto("Fund melden")
        else:
            for row in range(0, len(hits), 3):
                cols = st.columns(3)
                for k, it in enumerate(hits[row : row + 3]):
                    with cols[k]:
                        thumb(it)
                        st.markdown(f"**{it.get('titel', 'Fundstück')}**")
                        st.caption(f"#{it.get('id')} · {it.get('fundort', '')}")
                        status_badge(it.get("status", "Offen"))
                        if ui.button("Ansehen", key=f"view_{it.get('id')}", variant="outline"):
                            st.session_state["selected_id"] = it.get("id")
                            st.rerun()

# =============================================================================
# 8. TAB: Fund melden (Foto → KI → Formular)
# =============================================================================
elif tab == "Fund melden":
    st.subheader("Fund melden 📷")
    ui.card(
        title="So geht's",
        description="1) Foto hochladen   2) KI-Erkennung starten   3) Vorschlag prüfen & eintragen.",
    )

    src = st.radio("Quelle", ["Datei hochladen", "Kamera"], horizontal=True, key="rep_src")
    if src == "Datei hochladen":
        up = st.file_uploader(
            "Foto", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed",
            key=f"up_{st.session_state['uploader_nonce']}",
        )
    else:
        up = st.camera_input("Kamera", label_visibility="collapsed",
                             key=f"cam_{st.session_state['uploader_nonce']}")
    if up is not None:
        st.session_state["rep_bytes"] = up.getvalue()

    if st.session_state.get("rep_bytes"):
        pil = Image.open(io.BytesIO(st.session_state["rep_bytes"])).convert("RGB")
        p1, p2 = st.columns([2, 3])
        with p1:
            st.image(pil, caption="Vorschau", use_container_width=True)
        with p2:
            if ui.button("🔎 Jetzt per KI erkennen", key="ai_go"):
                with st.spinner("KI analysiert das Foto … (erster Start lädt das Modell)"):
                    st.session_state["rep_ai"] = analyze(pil)
                ai = st.session_state["rep_ai"]
                st.session_state["rep_titel_ai"] = ai["label"].capitalize()
                st.session_state["rep_kat_ai"] = ai.get("category", "Sonstiges")
                if ai.get("category") in CATEGORIES:
                    st.session_state["rep_kat"] = ai["category"]
                st.rerun()

            ai = st.session_state.get("rep_ai")
            if ai:
                ui.card(
                    title=f"Vorschlag: {ai['label'].capitalize()}",
                    description=f"{ai['engine']} · Kategorie „{ai['category']}“",
                )
                ui.progress(
                    min(100.0, max(0.0, ai["confidence"] * 100.0)),
                    label="Sicherheit", show_value=True,
                )
                if ai.get("top3"):
                    st.caption("Top-3 der KI:")
                    for lab, prob in ai["top3"]:
                        st.write(f"{lab.capitalize()} — {prob * 100:.0f} %")
                        ui.progress(prob * 100.0, show_value=False)
                if ai["confidence"] < 0.5:
                    ui.alert(
                        "Unsicherer Vorschlag",
                        "Bitte Kategorie und Titel unten von Hand prüfen.",
                    )
        st.write("")
        ui.separator()
        st.subheader("Eintragen")
        ai = st.session_state.get("rep_ai") or {}
        titel = ui.input(
            "Bezeichnung", value=st.session_state.get("rep_titel_ai", ""),
            key="rep_titel", placeholder="z. B. Blaue Trinkflasche, 0,75 L",
        )
        kat_opts = CATEGORIES
        kat_default = st.session_state.get("rep_kat_ai")
        kat = ui.select(
            "Kategorie", kat_opts,
            index=kat_opts.index(kat_default) if kat_default in kat_opts else len(kat_opts) - 1,
            key="rep_kat",
        )
        r1, r2 = st.columns(2)
        with r1:
            ort = ui.select("Fundort", LOCATIONS, key="rep_ort")
        with r2:
            lager = ui.input("Lagerort", value="Hausmeisterbüro (Raum 001)", key="rep_lager")
        tags_raw = ui.input("Schlagworte (kommagetrennt)", key="rep_tags",
                            placeholder="Nike, Blau, Größe L")
        desc = ui.textarea("Besondere Merkmale", key="rep_desc",
                           placeholder="Kratzer, Initialen, Inhalt …", rows=3)

        if ui.button("Ins Fundbuch eintragen ✅", key="rep_save"):
            if not (titel or "").strip():
                flash("error", "Titel fehlt", "Bitte eine Bezeichnung angeben.")
                st.rerun()
            new_id = max([i.get("id", 1000) for i in items], default=1000) + 1
            img_name = save_uploaded_image(pil, new_id)
            parsed = [x.strip() for x in (tags_raw or "").split(",") if x.strip()] or [
                (ai.get("label") or kat).capitalize()
            ]
            items.insert(
                0,
                {
                    "id": new_id, "titel": titel.strip(), "kategorie": kat,
                    "fundort": ort, "abgabeort": (lager or "").strip() or "Hausmeisterbüro (Raum 001)",
                    "datum_fund": heute,
                    "datum_ablauf": (datetime.date.today() + datetime.timedelta(days=90)).isoformat(),
                    "status": "Offen",
                    "beschreibung": (desc or "").strip() or "Keine nähere Beschreibung.",
                    "image_file": img_name, "tags": parsed,
                },
            )
            save_all()
            st.session_state["rep_bytes"] = None
            st.session_state["rep_ai"] = None
            st.session_state["rep_titel_ai"] = ""
            st.session_state["rep_kat_ai"] = None
            for k in ("rep_titel", "rep_kat", "rep_ort", "rep_lager", "rep_tags", "rep_desc"):
                st.session_state.pop(k, None)
            st.session_state["uploader_nonce"] += 1
            st.session_state["last_id"] = new_id
            st.session_state["show_done_dialog"] = True
            st.rerun()
    else:
        ui.alert(
            "Noch kein Foto",
            "Lade oben ein Foto hoch oder nutze die Kamera — danach startet die KI.",
        )
        with st.expander("Fototipps 💡"):
            st.markdown(
                "- Gute Belichtung, ruhiger Hintergrund\n"
                "- Gegenstand vollständig & formatfüllend\n"
                "- Keine Personen auf dem Foto"
            )

    if st.session_state.get("show_done_dialog"):
        lid = st.session_state.get("last_id")
        choice = ui.alert_dialog(
            True,
            "Eingetragen! 🎉",
            f"Fundstück #{lid} ist jetzt im Verzeichnis. Wie geht's weiter?",
            confirm_label="Weiteren Fund melden",
            cancel_label="Zum Verzeichnis",
            key="done_dialog",
        )
        if choice is True:
            st.session_state["show_done_dialog"] = False
            st.rerun()
        elif choice is False:
            st.session_state["show_done_dialog"] = False
            goto("Verzeichnis")

# =============================================================================
# 9. TAB: Dashboard
# =============================================================================
elif tab == "Dashboard":
    st.subheader("Dashboard 📊")
    counts_kat = [
        {"Kategorie": k, "Anzahl": len([i for i in items if i.get("kategorie") == k])}
        for k in CATEGORIES
    ]
    counts_stat: dict[str, int] = {}
    for i in items:
        s = i.get("status", "Offen")
        counts_stat[s] = counts_stat.get(s, 0) + 1

    d1, d2 = st.columns(2)
    with d1:
        ui.metric_card(
            "Vermittlungsquote",
            f"{(counts_stat.get('Abgeholt', 0) / max(1, len(items)) * 100):.0f} %",
            description=f"{counts_stat.get('Abgeholt', 0)} von {len(items)} abgeholt",
        )
    with d2:
        ui.metric_card(
            "Offene Ansprüche",
            len([c for c in claims if c.get("status") == "In Prüfung"]),
            description="warten auf Prüfung im Sekretariat",
        )

    st.write("")
    import pandas as pd

    c1, c2 = st.columns(2)
    with c1:
        df_kat = pd.DataFrame([r for r in counts_kat if r["Anzahl"] > 0]) or pd.DataFrame(
            [{"Kategorie": "–", "Anzahl": 0}]
        )
        ui.bar_chart(df_kat, x="Kategorie", y="Anzahl", title="Funde je Kategorie")
    with c2:
        stat_rows = [
            {"Status": s, "Anzahl": n} for s, n in counts_stat.items() if n > 0
        ][:5] or [{"Status": "–", "Anzahl": 0}]
        df_stat = pd.DataFrame(stat_rows)
        ui.pie_chart(df_stat, names="Status", values="Anzahl", title="Statusverteilung", donut=True)

    st.write("")
    st.subheader("Zuletzt eingetragen")
    recent = sorted(items, key=lambda i: str(i.get("datum_fund", "")), reverse=True)[:8]
    if recent:
        ui.table(
            [
                {
                    "#": r.get("id"), "Titel": r.get("titel"),
                    "Kategorie": r.get("kategorie"), "Fundort": r.get("fundort"),
                    "Status": r.get("status"),
                }
                for r in recent
            ],
            caption="Die 8 neuesten Einträge",
        )
    else:
        ui.alert("Keine Einträge", "Noch ist das Fundbuch leer.")

    st.write("")
    st.subheader("Gut zu wissen")
    ui.accordion(
        [
            {
                "value": "abholen",
                "label": "Wie hole ich etwas ab?",
                "content": "Fundstück im Verzeichnis finden, Anspruch mit Nachweis melden, "
                "dann mit Schülerausweis im Hausmeisterbüro (Raum 001) oder im Sekretariat abholen.",
            },
            {
                "value": "fristen",
                "label": "Wie lange wird aufbewahrt?",
                "content": "Fundsachen werden 90 Tage aufbewahrt. Danach werden sie gespendet oder entsorgt.",
            },
            {
                "value": "ki",
                "label": "Was erkennt die KI?",
                "content": "Das Teachable-Machine-Modell (TestKI4) unterscheidet 11 Klassen: "
                + ", ".join(load_teachable_labels())
                + ". Die Kategorie lässt sich immer von Hand korrigieren.",
            },
        ]
    )

# =============================================================================
# 10. Footer
# =============================================================================
st.write("")
ui.separator()
st.caption("kath.fund · Katharineum zu Lübeck · Fundbüro: Hausmeisterbüro (Raum 001) · "
           "KI: Teachable Machine (TestKI4, keras_model.h5) · UI: streamlit-shadcn-ui")
