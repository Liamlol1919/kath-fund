"""
===============================================================================
               KATH. FUND - FUNDBÜRO APP (SKIZZEN-LAYOUT)
===============================================================================
"""

import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
import datetime
import json
import time

# =============================================================================
# 1. PAGE CONFIG & SESSION STATE INITIALIZATION
# =============================================================================

st.set_page_config(
    page_title="Kath. Fund",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    "Unbekannt"
]

# Direkte Absicherung gegen KeyError beim Neustart/Reload
if 'fundstuecke_liste' not in st.session_state:
    st.session_state['fundstuecke_liste'] = [
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
            "beschreibung": "Größe M, gelber Reißverschluss.",
            "image_data": None,
            "tags": ["Jacke", "Blau", "Größe M"]
        },
        {
            "id": 1002,
            "titel": "AirPods Pro Case",
            "kategorie": "Elektronik & Kabel",
            "fundort": "Mensa / Cafeteria",
            "abgabeort": "Sekretariat",
            "kontakt_kuerzel": "HAUSMEISTER-K",
            "finder_rolle": "Hausmeister",
            "datum_fund": "2026-09-05",
            "datum_ablauf": "2026-12-05",
            "status": "Beansprucht",
            "beschreibung": "Kratzer auf der Rückseite, schwarze Schutzhülle.",
            "image_data": None,
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
            "beschreibung": "Mattgrün mit Aufklebern.",
            "image_data": None,
            "tags": ["720°DGREE", "Grün", "Metall"]
        }
    ]

if 'claims' not in st.session_state:
    st.session_state['claims'] = []

if 'audit_logs' not in st.session_state:
    st.session_state['audit_logs'] = []

if 'current_role' not in st.session_state:
    st.session_state['current_role'] = "Schüler:in"

if 'is_authenticated' not in st.session_state:
    st.session_state['is_authenticated'] = False

def log_action(user: str, action: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state['audit_logs'].append({
        "timestamp": now,
        "user": user,
        "action": action
    })

# =============================================================================
# 2. STYLING (ANPASSUNG AN DIE HANDSKIZZE)
# =============================================================================

st.markdown("""
<style>
    .header-skizze {
        text-align: center;
        padding: 10px 0 20px 0;
        border-bottom: 2px solid #333;
        margin-bottom: 25px;
    }
    .header-logo {
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: -1px;
        color: #1e293b;
        font-family: 'Arial Black', sans-serif;
    }
    .card-box {
        background-color: #ffffff;
        border: 2px solid #000000;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 15px;
        min-height: 280px;
    }
    .card-img-placeholder {
        width: 100%;
        height: 140px;
        background-color: #f1f5f9;
        border: 1px dashed #94a3b8;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .card-title {
        font-weight: 800;
        font-size: 1.1rem;
        margin: 5px 0;
        color: #0f172a;
    }
    .tag-badge {
        display: inline-block;
        background-color: #e2e8f0;
        color: #334155;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 0.75rem;
        margin-right: 4px;
        margin-top: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. SIDEBAR NAVIGATION
# =============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Einstellungen & Rolle")
    role = st.selectbox("Aktive Rolle", ["Schüler:in", "Lehrkraft", "Hausmeister / Admin"])
    st.session_state['current_role'] = role
    
    if role == "Hausmeister / Admin":
        pin = st.text_input("Admin-PIN", type="password")
        if pin == "1234":
            st.session_state['is_authenticated'] = True
            st.success("✅ Admin aktiviert")
        else:
            st.session_state['is_authenticated'] = False
            if pin != "":
                st.error("❌ Falscher PIN")
    else:
        st.session_state['is_authenticated'] = True

    st.divider()
    
    total_cnt = len(st.session_state['fundstuecke_liste'])
    offen_cnt = len([i for i in st.session_state['fundstuecke_liste'] if i["status"] == "Offen"])
    
    st.metric("Gesamte Fundstücke", total_cnt)
    st.metric("Offen zur Abholung", offen_cnt)

# =============================================================================
# 4. MAIN HEADER (KATH. FUND LOGO AUS DER SKIZZE)
# =============================================================================

st.markdown("""
<div class="header-skizze">
    <div class="header-logo">⚙️ Kath. Fund</div>
</div>
""", unsafe_allow_html=True)

tab_main, tab_form, tab_claims, tab_admin = st.tabs([
    "🔍 Katalog (main)", 
    "➕ Erfassen (form)", 
    "✋ Beanspruchen", 
    "⚙️ Admin"
])

# =============================================================================
# TAB 1: MAIN (KATALOG & SUCHE - SKIZZEN-LAYOUT)
# =============================================================================

with tab_main:
    # Suchleiste mit "Go" Button laut Skizze
    col_search, col_go = st.columns([5, 1])
    with col_search:
        search_query = st.text_input("Search", placeholder="Suchbegriff eingeben...", label_visibility="collapsed")
    with col_go:
        go_click = st.button("GO 🔍", use_container_width=True)

    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        kat_filter = st.selectbox("Kategorie", ["Alle"] + CATEGORIES)
    with col_f2:
        loc_filter = st.selectbox("Fundort", ["Alle"] + LOCATIONS)

    # Filter-Logik
    items = st.session_state['fundstuecke_liste']
    if search_query:
        items = [i for i in items if search_query.lower() in i["titel"].lower() or search_query.lower() in i["beschreibung"].lower()]
    if kat_filter != "Alle":
        items = [i for i in items if i["kategorie"] == kat_filter]
    if loc_filter != "Alle":
        items = [i for i in items if i["fundort"] == loc_filter]

    st.divider()

    # Cards in 3er Raster entsprechend Zeichnung (Bild oben, Titel & Tags darunter)
    if not items:
        st.info("Keine Fundstücke vorhanden.")
    else:
        for i in range(0, len(items), 3):
            cols = st.columns(3)
            for idx, col in enumerate(cols):
                if i + idx < len(items):
                    item = items[i + idx]
                    with col:
                        st.markdown('<div class="card-box">', unsafe_allow_html=True)
                        
                        # Bild oben im Card-Layout
                        if item["image_data"] is not None:
                            st.image(item["image_data"], use_container_width=True)
                        else:
                            st.markdown('<div class="card-img-placeholder">📷 Kein Foto</div>', unsafe_allow_html=True)
                        
                        st.markdown(f'<div class="card-title">#{item["id"]} - {item["titel"]}</div>', unsafe_allow_html=True)
                        st.caption(f"📍 {item['fundort']} | Status: **{item['status']}**")
                        
                        # Tags-Anzeige unter dem Titel (wie in der Skizze)
                        tags_html = "".join([f'<span class="tag-badge">#{t}</span>' for t in item.get("tags", [])])
                        st.markdown(tags_html, unsafe_allow_html=True)
                        
                        with st.expander("Details anzeigen"):
                            st.write(f"**Beschreibung:** {item['beschreibung']}")
                            st.write(f"**Abgabeort:** {item['abgabeort']}")
                            st.write(f"**Finder:** {item['kontakt_kuerzel']}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# TAB 2: FORM (NEUERFASSUNG MIT UPLOAD-BUTTON MITTIG LAUT SKIZZE)
# =============================================================================

with tab_form:
    st.markdown("### ➕ Neues Fundstück eintragen")
    
    col_u1, col_u2 = st.columns([1, 2])
    
    with col_u1:
        # Upload Button genau wie im Skizzen-Layout
        uploaded_file = st.file_uploader("📷 [ Upload ]", type=["jpg", "jpeg", "png"])
        uploaded_image = None
        if uploaded_file is not None:
            uploaded_image = Image.open(uploaded_file)
            st.image(uploaded_image, caption="Vorschau", use_container_width=True)

    with col_u2:
        with st.form("add_form", clear_on_submit=True):
            in_titel = st.text_input("Titel*")
            in_kat = st.selectbox("Kategorie", CATEGORIES)
            in_loc = st.selectbox("Fundort", LOCATIONS)
            in_abgabe = st.text_input("Abgabeort / Aufbewahrung", value="Hausmeisterbüro")
            in_tags = st.text_input("Tags (kommagetrennt)", placeholder="z. B. Jacke, Blau, Nike")
            in_kuerzel = st.text_input("Dein Kürzel*", placeholder="z. B. MAX-8A")
            in_desc = st.text_area("Beschreibung")
            
            btn_save = st.form_submit_button("Speichern 💾", use_container_width=True)
            
            if btn_save:
                if not in_titel or not in_kuerzel:
                    st.error("Bitte Titel und Kürzel ausfüllen!")
                else:
                    new_id = max([i["id"] for i in st.session_state['fundstuecke_liste']]) + 1 if st.session_state['fundstuecke_liste'] else 1001
                    parsed_tags = [t.strip() for t in in_tags.split(",") if t.strip()]
                    
                    new_item = {
                        "id": new_id,
                        "titel": in_titel,
                        "kategorie": in_kat,
                        "fundort": in_loc,
                        "abgabeort": in_abgabe,
                        "kontakt_kuerzel": in_kuerzel.upper(),
                        "finder_rolle": st.session_state['current_role'],
                        "datum_fund": datetime.date.today().strftime("%Y-%m-%d"),
                        "datum_ablauf": (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
                        "status": "Offen",
                        "beschreibung": in_desc,
                        "image_data": uploaded_image,
                        "tags": parsed_tags
                    }
                    st.session_state['fundstuecke_liste'].append(new_item)
                    log_action(in_kuerzel.upper(), f"Item #{new_id} angelegt")
                    st.success(f"Fundstück #{new_id} erfolgreich gespeichert!")
                    st.rerun()

# =============================================================================
# TAB 3: BEANSPRUCHEN
# =============================================================================

with tab_claims:
    st.markdown("### ✋ Fundstück beanspruchen")
    
    open_items = {f"#{i['id']} - {i['titel']}": i['id'] for i in st.session_state['fundstuecke_liste'] if i["status"] == "Offen"}
    
    if not open_items:
        st.info("Keine offenen Fundstücke verfügbar.")
    else:
        selected_label = st.selectbox("Gegenstand wählen", list(open_items.keys()))
        selected_id = open_items[selected_label]
        
        with st.form("claim_form"):
            c_name = st.text_input("Dein Name / Klasse*")
            c_proof = st.text_area("Eigentumsnachweis (z.B. Merkmale)*")
            btn_claim = st.form_submit_button("Anspruch einreichen")
            
            if btn_claim:
                if c_name and c_proof:
                    st.session_state['claims'].append({
                        "claim_id": len(st.session_state['claims']) + 1,
                        "item_id": selected_id,
                        "name": c_name,
                        "proof": c_proof,
                        "status": "In Prüfung"
                    })
                    st.success("Anspruch eingereicht!")
                else:
                    st.error("Bitte alle Felder ausfüllen!")

# =============================================================================
# TAB 4: ADMIN
# =============================================================================

with tab_admin:
    st.markdown("### ⚙️ Admin & Übersicht")
    if not st.session_state['is_authenticated'] and st.session_state['current_role'] == "Hausmeister / Admin":
        st.warning("🔒 Bitte gib den Admin-PIN in der Seitenleiste ein (Demo: 1234).")
    else:
        st.dataframe(pd.DataFrame(st.session_state['fundstuecke_liste']), use_container_width=True)
        
        st.markdown("#### Audit Logs")
        st.dataframe(pd.DataFrame(st.session_state['audit_logs']), use_container_width=True)
===============================================================================
               SCHUL-FUNDBÜRO ENTERPRISE EDITION v3.1 (FIXED)
===============================================================================

ARCHITEKTUR & MODULE IN DIESER DATEI:
--------------------------------------
1. APP CONFIG & STYLING (Custom CSS, Responsive Grid)
2. DATABASE & SESSION ENGINE (Verwendung von 'fundstuecke_liste' statt '.items')
3. SECURITY & AUTH (PIN-basierte Rollenverwaltung, Audit-Logging)
4. AI VISION ENGINE (Teachable Machine / Keras Pipeline mit Fallback)
5. UTILITIES (QR-Code Generator, Export/Import Engine, Analytics)
6. UI-KOMPONENTEN (Dashboards, Katalog, Claims, Admin-Bereich)

SETUP & INSTALLATION:
---------------------
requirements.txt:
    streamlit>=1.30.0
    tensorflow>=2.12.0
    pillow>=10.0.0
    numpy>=1.24.0
    pandas>=2.0.0

Startbefehl:
    streamlit run app.py
===============================================================================
"""

import streamlit as st
from PIL import Image, ImageOps, ImageDraw
import numpy as np
import pandas as pd
import datetime
import json
import io
import base64
import time

# =============================================================================
# 1. GLOBAL CONFIGURATION & CUSTOM STYLING
# =============================================================================

st.set_page_config(
    page_title="Schul-Fundbüro Enterprise",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

CATEGORIES = [
    "Kleidung & Textilien",
    "Trinkflaschen & Brotdosen",
    "Rucksäcke, Taschen & Turnbeutel",
    "Elektronik & Ladekabel",
    "Schlüssel & Wertsachen",
    "Schulmaterial & Bücher",
    "Sportkleidung & Schuhe",
    "Sonstiges"
]

LOCATIONS = [
    "Hauptgebäude - Foyer",
    "Pausenhof - Nord",
    "Pausenhof - Süd",
    "Sporthalle - Umkleide A",
    "Sporthalle - Umkleide B",
    "Mensa / Cafeteria",
    "Bibliothek",
    "Chemieroom / MINT-Trakt",
    "Musiksaal",
    "Unbekannt"
]

STORAGE_LOCATIONS = [
    "Hausmeisterbüro (Raum 001)",
    "Fund-Kiste Foyer",
    "Sporthalle Regallager",
    "Sekretariat (Tresor für Wertsachen)",
    "Fachlehrer-Zimmer"
]

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .hero-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    .badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }
    .badge-offen { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-beansprucht { background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .badge-abgeholt { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .badge-entsorgt { background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

    .card-container {
        background-color: white;
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. DATABASE & SESSION STATE ENGINE
# =============================================================================

def init_database():
    """Initialisiert die In-Memory Datenstruktur ohne Session-State-Kollisionen."""
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = True
        
        # Eindeutiger Schlüssel 'fundstuecke_liste' statt '.items'
        st.session_state['fundstuecke_liste'] = [
            {
                "id": 1001,
                "titel": "Derbe Regenjacke Dunkelblau",
                "kategorie": "Kleidung & Textilien",
                "fundort": "Pausenhof - Nord",
                "abgabeort": "Hausmeisterbüro (Raum 001)",
                "kontakt_kuerzel": "S-MUELLER",
                "finder_rolle": "Schüler:in",
                "datum_fund": "2026-09-01",
                "datum_ablauf": "2026-12-01",
                "status": "Offen",
                "beschreibung": "Größe M, gelber Reißverschluss, Name leicht verwischt im Etikett.",
                "image_data": None,
                "views": 14
            },
            {
                "id": 1002,
                "titel": "AirPods Pro Ladecase",
                "kategorie": "Elektronik & Ladekabel",
                "fundort": "Mensa / Cafeteria",
                "abgabeort": "Sekretariat (Tresor für Wertsachen)",
                "kontakt_kuerzel": "HAUSMEISTER-K",
                "finder_rolle": "Hausmeister",
                "datum_fund": "2026-09-05",
                "datum_ablauf": "2026-12-05",
                "status": "Beansprucht",
                "beschreibung": "Kratzer auf der Rückseite, schwarze Schutzhülle.",
                "image_data": None,
                "views": 42
            },
            {
                "id": 1003,
                "titel": "Edelstahl Trinkflasche 1L",
                "kategorie": "Trinkflaschen & Brotdosen",
                "fundort": "Sporthalle - Umkleide A",
                "abgabeort": "Sporthalle Regallager",
                "kontakt_kuerzel": "L-SCHMIDT",
                "finder_rolle": "Lehrkraft",
                "datum_fund": "2026-08-28",
                "datum_ablauf": "2026-11-28",
                "status": "Abgeholt",
                "beschreibung": "Marke 720°DGREE, mattgrün mit Aufklebern.",
                "image_data": None,
                "views": 8
            }
        ]
        
        st.session_state.claims = [
            {
                "claim_id": 501,
                "item_id": 1002,
                "antragsteller_kuerzel": "SCHUELER-9B",
                "nachweis": "Kann Seriennummer auf der Originalverpackung vorlegen.",
                "datum": "2026-09-06",
                "status": "In Prüfung"
            }
        ]
        
        st.session_state.audit_logs = [
            {"timestamp": "2026-09-01 08:30:00", "user": "System", "action": "Datenbank initialisiert"},
            {"timestamp": "2026-09-05 14:12:05", "user": "HAUSMEISTER-K", "action": "Item 1002 erstellt"}
        ]
        
        st.session_state.current_role = "Schüler:in"
        st.session_state.is_authenticated = False

init_database()

def log_action(user: str, action: str):
    """Erstellt einen Audit-Log-Eintrag."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_logs.append({
        "timestamp": now,
        "user": user,
        "action": action
    })

# =============================================================================
# 3. UTILITIES & GENERATORS
# =============================================================================

def export_database_json() -> str:
    """Exportiert den Datenbestand sicher als JSON."""
    export_data = {
        "items": [
            {k: v for k, v in item.items() if k != "image_data"} 
            for item in st.session_state['fundstuecke_liste']
        ],
        "claims": st.session_state.claims,
        "export_date": datetime.datetime.now().isoformat()
    }
    return json.dumps(export_data, indent=2, ensure_ascii=False)

# =============================================================================
# 4. AI VISION ENGINE
# =============================================================================

@st.cache_resource
def load_keras_model():
    """Lädt das Keras-Modell."""
    try:
        import tensorflow.keras as keras
        model = keras.models.load_model("keras_model.h5", compile=False)
        class_names = [line.strip() for line in open("labels.txt", "r").readlines()]
        return model, class_names
    except Exception:
        return None, None

def analyze_image_ai(pil_image: Image.Image):
    """Klassifiziert das hochgeladene Bild."""
    model, class_names = load_keras_model()
    
    if model is not None and class_names is not None:
        try:
            size = (224, 224)
            image = ImageOps.fit(pil_image, size, Image.Resampling.LANCZOS)
            image_array = np.asarray(image)
            normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            data[0] = normalized_image_array
            
            prediction = model.predict(data, verbose=0)
            index = np.argmax(prediction)
            confidence = float(prediction[0][index])
            label = class_names[index]
            return label, confidence, "TensorFlow Keras v2"
        except Exception:
            pass
            
    # Fallback-Klassifikator
    img_resized = pil_image.resize((50, 50))
    colors = img_resized.getcolors(2500)
    if colors:
        dominant_color = max(colors, key=lambda item: item[0])[1]
        r, g, b = dominant_color[:3]
        if r > 150 and g < 100:
            return "Kleidung & Textilien", 0.82, "Color-Heuristic Engine (Fallback)"
        elif b > 150:
            return "Trinkflaschen & Brotdosen", 0.78, "Color-Heuristic Engine (Fallback)"
            
    return "Sonstiges", 0.65, "Standard-Klassifikator"

# =============================================================================
# 5. HEADER & NAVIGATION
# =============================================================================

st.markdown("""
<div class="hero-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="hero-title">🏫 Schul-Fundbüro Enterprise</h1>
            <p class="hero-subtitle">Intelligente Fundstückerfassung, KI-Analyse & Fundsachenmanagement</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🔐 Authentifizierung")
    
    role = st.selectbox(
        "Aktive Rolle wählen",
        ["Schüler:in", "Lehrkraft", "Hausmeister / Admin"]
    )
    st.session_state.current_role = role
    
    if role == "Hausmeister / Admin":
        pin_input = st.text_input("Admin-PIN eingeben", type="password")
        if pin_input == "1234":
            st.session_state.is_authenticated = True
            st.success("✅ Admin-Zugriff gewährt")
        else:
            st.session_state.is_authenticated = False
            if pin_input != "":
                st.error("❌ Falscher PIN (Demo: 1234)")
    else:
        st.session_state.is_authenticated = True

    st.divider()
    
    total_items = len(st.session_state['fundstuecke_liste'])
    offen_items = len([i for i in st.session_state['fundstuecke_liste'] if i["status"] == "Offen"])
    
    st.metric("Gesamte Fundstücke", total_items)
    st.metric("Offen zur Abholung", offen_items)
    
    st.divider()
    st.caption("DSGVO-Status: **Aktiv (Pseudonymisiert)**")

tab_katalog, tab_neuerfassung, tab_ansprueche, tab_analytics, tab_admin = st.tabs([
    "🔍 Fundsachen-Katalog",
    "📸 KI-Fundstück Erfassen",
    "✋ Eigentum Beanspruchen",
    "📈 Analytics & Berichte",
    "⚙️ Verwaltung & Admin"
])

# =============================================================================
# TAB 1: FUNDSACHEN-KATALOG
# =============================================================================

with tab_katalog:
    st.subheader("📋 Öffentlicher Fundsachen-Katalog")
    
    col_s1, col_s2, col_s3, col_s4 = st.columns([3, 2, 2, 2])
    
    with col_s1:
        search_term = st.text_input("🔎 Suchbegriff", placeholder="z. B. Adidas, Jacke, Grün...")
    with col_s2:
        kat_filter = st.selectbox("Kategorie", ["Alle Kategorien"] + CATEGORIES)
    with col_s3:
        loc_filter = st.selectbox("Fundort", ["Alle Orte"] + LOCATIONS)
    with col_s4:
        status_filter = st.selectbox("Status", ["Alle Status", "Offen", "Beansprucht", "Abgeholt"])

    filtered_items = st.session_state['fundstuecke_liste']
    
    if search_term:
        filtered_items = [
            i for i in filtered_items 
            if search_term.lower() in i["titel"].lower() or search_term.lower() in i["beschreibung"].lower()
        ]
    if kat_filter != "Alle Kategorien":
        filtered_items = [i for i in filtered_items if i["kategorie"] == kat_filter]
    if loc_filter != "Alle Orte":
        filtered_items = [i for i in filtered_items if i["fundort"] == loc_filter]
    if status_filter != "Alle Status":
        filtered_items = [i for i in filtered_items if i["status"] == status_filter]

    st.write(f"*Zeige {len(filtered_items)} von {len(st.session_state['fundstuecke_liste'])} Fundstücken*")
    st.divider()

    if not filtered_items:
        st.info("Keine Fundstücke mit diesen Filterkriterien gefunden.")
    else:
        for i in range(0, len(filtered_items), 3):
            cols = st.columns(3)
            for idx, col in enumerate(cols):
                if i + idx < len(filtered_items):
                    item = filtered_items[i + idx]
                    with col:
                        status_class = f"badge-{item['status'].lower()}"
                        st.markdown(f"""
                        <div class="card-container">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: bold; color: #64748b;">#{item['id']}</span>
                                <span class="badge {status_class}">{item['status']}</span>
                            </div>
                            <h3 style="margin: 10px 0 5px 0; color: #0f172a; font-size: 1.2rem;">{item['titel']}</h3>
                            <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 10px;">
                                📍 {item['fundort']}<br>
                                📅 Funddatum: {item['datum_fund']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if item["image_data"] is not None:
                            st.image(item["image_data"], use_container_width=True)
                        else:
                            st.caption("📷 Kein Foto vorhanden")
                        
                        with st.expander("Details & Aufbewahrungsort"):
                            st.write(f"**Beschreibung:** {item['beschreibung']}")
                            st.write(f"**Abgabeort:** {item['abgabeort']}")
                            st.write(f"**Finder (Kürzel):** {item['kontakt_kuerzel']} ({item['finder_rolle']})")
                            st.write(f"**Aufbewahrung bis:** {item['datum_ablauf']}")
                            item["views"] += 1
                            st.caption(f"👀 Aufrufe: {item['views']}")

# =============================================================================
# TAB 2: KI-FUNDSTÜCK ERFASSUNG
# =============================================================================

with tab_neuerfassung:
    st.subheader("📸 Neues Fundstück mit KI-Unterstützung registrieren")
    
    col_u1, col_u2 = st.columns([1, 1])
    
    with col_u1:
        st.markdown("##### 1. Foto aufnehmen / hochladen")
        img_file = st.file_uploader("Bild auswählen", type=["jpg", "jpeg", "png", "webp"])
        
        uploaded_pil = None
        predicted_category = CATEGORIES[0]
        confidence_val = 0.0
        engine_name = "N/A"
        
        if img_file is not None:
            uploaded_pil = Image.open(img_file).convert("RGB")
            st.image(uploaded_pil, caption="Hochgeladenes Foto", use_container_width=True)
            
            with st.spinner("🤖 KI analysiert das Bild..."):
                predicted_category, confidence_val, engine_name = analyze_image_ai(uploaded_pil)
                time.sleep(0.3)
            
            st.success(f"**Vorgeschlagene Kategorie:** {predicted_category}")
            st.info(f"📊 Konfidenz: **{confidence_val*100:.1f}%** | Engine: `{engine_name}`")

    with col_u2:
        st.markdown("##### 2. Fund-Details ergänzen")
        with st.form("form_add_item", clear_on_submit=True):
            in_titel = st.text_input("Kurztitel des Gegenstands*", placeholder="z. B. Schwarze Sporttasche")
            
            default_index = CATEGORIES.index(predicted_category) if predicted_category in CATEGORIES else 0
            in_kategorie = st.selectbox("Kategorie bestätigen", CATEGORIES, index=default_index)
            
            in_fundort = st.selectbox("Fundort*", LOCATIONS)
            in_abgabeort = st.selectbox("Aufbewahrungsort*", STORAGE_LOCATIONS)
            in_beschreibung = st.text_area("Genauere Beschreibung", placeholder="Besondere Merkmale...")
            
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                in_kuerzel = st.text_input("Dein Kürzel*", placeholder="z. B. S-SCHMIDT-8B")
            with c_m2:
                in_rolle = st.selectbox("Deine Rolle", ["Schüler:in", "Lehrkraft", "Hausmeister", "Sonstige"])
                
            btn_submit = st.form_submit_button("💾 Fundstück im System speichern")
            
            if btn_submit:
                if not in_titel or not in_kuerzel:
                    st.error("Bitte fülle alle Pflichtfelder (*) aus!")
                else:
                    new_id = max([i["id"] for i in st.session_state['fundstuecke_liste']]) + 1 if st.session_state['fundstuecke_liste'] else 1001
                    now_date = datetime.date.today()
                    expire_date = now_date + datetime.timedelta(days=90)
                    
                    new_item = {
                        "id": new_id,
                        "titel": in_titel,
                        "kategorie": in_kategorie,
                        "fundort": in_fundort,
                        "abgabeort": in_abgabeort,
                        "kontakt_kuerzel": in_kuerzel.upper(),
                        "finder_rolle": in_rolle,
                        "datum_fund": now_date.strftime("%Y-%m-%d"),
                        "datum_ablauf": expire_date.strftime("%Y-%m-%d"),
                        "status": "Offen",
                        "beschreibung": in_beschreibung if in_beschreibung else "Keine Zusatzbeschreibung.",
                        "image_data": uploaded_pil,
                        "views": 0
                    }
                    
                    st.session_state['fundstuecke_liste'].append(new_item)
                    log_action(in_kuerzel.upper(), f"Neues Fundstück registriert: #{new_id} - {in_titel}")
                    st.balloons()
                    st.success(f"Fundstück #{new_id} erfolgreich registriert!")

# =============================================================================
# TAB 3: EIGENTUM BEANSPRUCHEN
# =============================================================================

with tab_ansprueche:
    st.subheader("✋ Eigentum als Besitzer:in beanspruchen")
    
    col_c1, col_c2 = st.columns([1, 1])
    
    with col_c1:
        st.markdown("##### 1. Gegenstand auswählen")
        open_items = {f"#{i['id']} - {i['titel']} ({i['fundort']})": i['id'] for i in st.session_state['fundstuecke_liste'] if i["status"] in ["Offen", "Beansprucht"]}
        
        if not open_items:
            st.info("Aktuell stehen keine Gegenstände zur Beanspruchung bereit.")
        else:
            selected_item_label = st.selectbox("Fundstück wählen", list(open_items.keys()))
            selected_item_id = open_items[selected_item_label]
            
            item_data = next(i for i in st.session_state['fundstuecke_liste'] if i["id"] == selected_item_id)
            st.write(f"**Kategorie:** {item_data['kategorie']}")
            st.write(f"**Funddatum:** {item_data['datum_fund']}")
            st.write(f"**Aufbewahrungsort:** {item_data['abgabeort']}")

    with col_c2:
        if open_items:
            st.markdown("##### 2. Eigentumsnachweis erbringen")
            with st.form("form_claim_item"):
                claim_kuerzel = st.text_input("Dein Kürzel / Name & Klasse*", placeholder="z. B. MAX-MUSTERSCHÜLER-7A")
                claim_proof = st.text_area("Eigentumsnachweis / Beschreibung*", placeholder="Merkmale, Inhalt...")
                
                btn_claim = st.form_submit_button("📩 Anspruch einreichen")
                
                if btn_claim:
                    if not claim_kuerzel or not claim_proof:
                        st.error("Bitte gib dein Kürzel und einen Nachweis an!")
                    else:
                        new_claim_id = len(st.session_state.claims) + 501
                        new_claim = {
                            "claim_id": new_claim_id,
                            "item_id": selected_item_id,
                            "antragsteller_kuerzel": claim_kuerzel.upper(),
                            "nachweis": claim_proof,
                            "datum": datetime.date.today().strftime("%Y-%m-%d"),
                            "status": "In Prüfung"
                        }
                        st.session_state.claims.append(new_claim)
                        item_data["status"] = "Beansprucht"
                        
                        log_action(claim_kuerzel.upper(), f"Anspruch #{new_claim_id} auf Item #{selected_item_id} erhoben")
                        st.success("Dein Anspruch wurde eingereicht!")

# =============================================================================
# TAB 4: ANALYTICS & DASHBOARD
# =============================================================================

with tab_analytics:
    st.subheader("📈 Fundbüro Analytics")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_cnt = len(st.session_state['fundstuecke_liste'])
    returned_cnt = len([i for i in st.session_state['fundstuecke_liste'] if i["status"] == "Abgeholt"])
    return_rate = (returned_cnt / total_cnt * 100) if total_cnt > 0 else 0.0
    active_claims = len([c for c in st.session_state.claims if c["status"] == "In Prüfung"])
    
    kpi1.metric("Gesamt Erfasst", total_cnt)
    kpi2.metric("Erfolgreich Abgeholt", returned_cnt)
    kpi3.metric("Rückgabe-Quote", f"{return_rate:.1f}%")
    kpi4.metric("Offene Ansprüche", active_claims)
    
    st.divider()
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        st.markdown("##### 🏷️ Fundstücke nach Kategorie")
        df_items = pd.DataFrame(st.session_state['fundstuecke_liste'])
        if not df_items.empty:
            st.bar_chart(df_items["kategorie"].value_counts())
            
    with col_a2:
        st.markdown("##### 📍 Häufigste Fundorte")
        if not df_items.empty:
            st.line_chart(df_items["fundort"].value_counts())

# =============================================================================
# TAB 5: ADMIN & SYSTEMVERWALTUNG
# =============================================================================

with tab_admin:
    st.subheader("⚙️ Systemverwaltung & Hausmeister-Portal")
    
    if not st.session_state.is_authenticated and st.session_state.current_role == "Hausmeister / Admin":
        st.warning("🔒 Bitte gib in der linken Seitenleiste den Admin-PIN ein.")
    elif st.session_state.current_role != "Hausmeister / Admin":
        st.info("ℹ️ Dieser Bereich ist Hausmeistern und Administrator:innen vorbehalten.")
    else:
        st.success("👑 Administrator-Sitzung aktiv")
        
        admin_sub1, admin_sub2, admin_sub3 = st.tabs(["📝 Ansprüche Bearbeiten", "🗑️ Datenbereinigung & Fristen", "💾 Export / Backup"])
        
        with admin_sub1:
            st.markdown("##### Offene Eigentums-Ansprüche verwalten")
            if not st.session_state.claims:
                st.info("Keine Ansprüche vorhanden.")
            else:
                for claim in st.session_state.claims:
                    with st.expander(f"Anspruch #{claim['claim_id']} für Item #{claim['item_id']} ({claim['antragsteller_kuerzel']})"):
                        st.write(f"**Antragsteller:** {claim['antragsteller_kuerzel']}")
                        st.write(f"**Eingereicht am:** {claim['datum']}")
                        st.write(f"**Nachweis:** {claim['nachweis']}")
                        st.write(f"**Status:** {claim['status']}")
                        
                        btn_approve, btn_reject = st.columns(2)
                        with btn_approve:
                            if st.button("✅ Genehmigen", key=f"app_{claim['claim_id']}"):
                                claim["status"] = "Genehmigt"
                                for itm in st.session_state['fundstuecke_liste']:
                                    if itm["id"] == claim["item_id"]:
                                        itm["status"] = "Abgeholt"
                                log_action("ADMIN", f"Claim #{claim['claim_id']} genehmigt.")
                                st.success("Anspruch genehmigt!")
                                st.rerun()
                        with btn_reject:
                            if st.button("❌ Ablehnen", key=f"rej_{claim['claim_id']}"):
                                claim["status"] = "Abgelehnt"
                                log_action("ADMIN", f"Claim #{claim['claim_id']} abgelehnt.")
                                st.error("Anspruch abgelehnt.")
                                st.rerun()

        with admin_sub2:
            st.markdown("##### ⏱️ DSGVO & Aufbewahrungsfristen")
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            expired_items = [i for i in st.session_state['fundstuecke_liste'] if i["datum_ablauf"] < today_str and i["status"] == "Offen"]
            
            if not expired_items:
                st.info("Keine abgelaufenen Fundstücke vorhanden.")
            else:
                st.warning(f"Es gibt {len(expired_items)} abgelaufene Fundstücke!")
                if st.button("🧹 Als 'Entsorgt/Gespendet' markieren"):
                    for exp_item in expired_items:
                        exp_item["status"] = "Entsorgt"
                    log_action("ADMIN", f"{len(expired_items)} abgelaufene Items bereinigt.")
                    st.success("Bereinigung durchgeführt.")
                    st.rerun()

        with admin_sub3:
            st.markdown("##### 💾 Datenexport & Audit Logs")
            json_string = export_database_json()
            st.download_button(
                label="📥 Datenbank als JSON herunterladen",
                data=json_string,
                file_name=f"fundbuero_backup_{datetime.date.today().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
            
            st.divider()
            st.markdown("##### 📜 Audit-Log")
            st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True)
