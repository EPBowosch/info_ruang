import csv
import io
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import streamlit as st

# ------------------------------------------------------------------ konfigurasi halaman
st.set_page_config(
    page_title="Dasbor Ruang - Politeknik ATMI Surakarta",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SHEET_ID = "10_RQ33nnqwmAsO1UHVXyUmRBenivdj1M1v234OdrdW4"
SHEET_GID = "0"
SHEET_NAME = "Sheet1"
TZ = ZoneInfo("Asia/Jakarta")

ROOMS = {
    "edukasi": {
        "label": "Ruang Meeting Edukasi",
        "type": "Ruang Rapat",
        "loc": "Kampus 1, Area Edukasi",
        "cap": "25 orang",
        "fac": ["Proyektor", "AC", "Whiteboard", "Wi-Fi"],
        "mail": "ruang@atmi.ac.id",
    },
    "gonzaga": {
        "label": "Ruang Meeting Gonzaga",
        "type": "Ruang Rapat",
        "loc": "Kampus 2, Area Gonzaga",
        "cap": "20 orang",
        "fac": ["TV Display", "AC", "Wi-Fi"],
        "mail": "ruang@atmi.ac.id",
    },
    "aula Kampus1": {
        "label": "Aula Politeknik ATMI",
        "type": "Aula Utama",
        "loc": "Kampus 1, Area Lantai 2",
        "cap": "400 orang",
        "fac": ["Sound System", "Panggung", "Proyektor", "AC"],
        "mail": "ruang@atmi.ac.id",
    },
    "aula Kampus2": {
        "label": "Aula Gedung Gonzaga",
        "type": "Aula",
        "loc": "Kampus 2, Area Lantai 2",
        "cap": "200 orang",
        "fac": ["Sound System", "Proyektor", "AC"],
        "mail": "ruang@atmi.ac.id",
    },
}

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BLN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
BULAN = [
    "januari", "februari", "maret", "april", "mei", "juni",
    "juli", "agustus", "september", "oktober", "november", "desember"
]

# State untuk navigasi 4 menu utama
if "active_menu" not in st.session_state:
    st.session_state.active_menu = 0

# ------------------------------------------------------------------ CSS & Tema ATMI Surakarta
# Latar belakang gradasi biru khas ATMI + ilustrasi SVG teknis (Roda Gigi, Jangka Sorong, Lengan Robot)
BG_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' width='1440' height='900' viewBox='0 0 1440 900'>
  <defs>
    <linearGradient id='atmiGrad' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' stop-color='#061b42'/>
      <stop offset='50%' stop-color='#0d3b82'/>
      <stop offset='100%' stop-color='#1d68c4'/>
    </linearGradient>
    <pattern id='grid' width='40' height='40' patternUnits='userSpaceOnUse'>
      <path d='M 40 0 L 0 0 0 40' fill='none' stroke='#ffffff' stroke-opacity='0.04' stroke-width='1'/>
    </pattern>
  </defs>
  <rect width='1440' height='900' fill='url(#atmiGrad)'/>
  <rect width='1440' height='900' fill='url(#grid)'/>
  
  <!-- Ornamen Roda Gigi Besar Kanan Atas -->
  <g transform='translate(1320, 140)' stroke='#7fc8ff' stroke-opacity='0.12' stroke-width='4' fill='none'>
    <circle cx='0' cy='0' r='170'/>
    <circle cx='0' cy='0' r='130'/>
    <circle cx='0' cy='0' r='55'/>
    <path d='M-15,-190 L15,-190 L22,-168 L-22,-168 Z M-15,190 L15,190 L22,168 L-22,168 Z M-190,-15 L-190,15 L-168,22 L-168,-22 Z M190,-15 L190,15 L168,22 L168,-22 Z'/>
    <path transform='rotate(45)' d='M-15,-190 L15,-190 L22,-168 L-22,-168 Z M-15,190 L15,190 L22,168 L-22,168 Z M-190,-15 L-190,15 L-168,22 L-168,-22 Z M190,-15 L190,15 L168,22 L168,-22 Z'/>
  </g>

  <!-- Ornamen Jangka Sorong (Vernier Caliper) Kiri Bawah -->
  <g transform='translate(60, 740) rotate(-8)' stroke='#7fc8ff' stroke-opacity='0.14' stroke-width='3' fill='none'>
    <rect x='0' y='0' width='420' height='26' rx='3'/>
    <path d='M0,0 L0,-45 L26,-45 L32,0 M0,26 L0,85 L26,85 L34,26'/>
    <rect x='130' y='-10' width='85' height='46' rx='4'/>
    <circle cx='185' cy='-42' r='34'/>
    <circle cx='185' cy='-42' r='25'/>
    <line x1='185' y1='-42' x2='202' y2='-58'/>
  </g>

  <!-- Ornamen Lengan Robot Industri Kanan Bawah -->
  <g transform='translate(1150, 620)' stroke='#7fc8ff' stroke-opacity='0.14' stroke-width='3.5' fill='none'>
    <rect x='20' y='210' width='160' height='22' rx='4'/>
    <path d='M50,210 L65,175 L135,175 L150,210 Z'/>
    <circle cx='100' cy='165' r='18'/>
    <line x1='100' y1='165' x2='160' y2='75' stroke-width='14' stroke-linecap='round'/>
    <circle cx='160' cy='75' r='15'/>
    <line x1='160' y1='75' x2='255' y2='95' stroke-width='12' stroke-linecap='round'/>
    <circle cx='255' cy='95' r='10'/>
    <path d='M265,85 L285,75 M265,105 L285,115'/>
  </g>
</svg>
""".strip()

BG_DATA_URI = "data:image/svg+xml;utf8," + urllib.parse.quote(BG_SVG)

st.markdown(f"""
<style>
    /* Latar Belakang Utama Tema ATMI */
    .stApp {{
        background-image: url("{BG_DATA_URI}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Header Banner */
    .header-box {{
        background: rgba(6, 24, 58, 0.88);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(127, 200, 255, 0.3);
        border-bottom: 4px solid #2f9be8;
        padding: 1.4rem 1.8rem;
        border-radius: 16px;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}
    .header-title {{
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0;
        letter-spacing: 0.3px;
    }}
    .header-sub {{
        font-size: 1rem;
        color: #93d0ff !important;
        margin-top: 0.3rem;
        font-weight: 500;
    }}

    /* Label & Selectbox Kontras Tinggi */
    .control-label {{
        color: #ffffff !important;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }}
    div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 2px solid #2f9be8 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    div[data-baseweb="select"] span {{
        color: #0f172a !important;
    }}

    /* 4 TOMBOL MENU UTAMA BESAR & MENCOLOK */
    div.stButton > button {{
        width: 100%;
        min-height: 74px;
        border-radius: 14px !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.3px;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }}
    /* Menu Tidak Aktif (Secondary) -> Putih Bersih Teks Biru Tua */
    div.stButton > button[kind="secondary"] {{
        background-color: #ffffff !important;
        color: #0a2a5c !important;
        border: 2px solid #cbd5e1 !important;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        background-color: #e0f2fe !important;
        border-color: #2f9be8 !important;
        transform: translateY(-2px);
    }}
    div.stButton > button[kind="secondary"] p {{
        color: #0a2a5c !important;
        font-size: 1.12rem !important;
        font-weight: 800 !important;
    }}

    /* Menu Aktif (Primary) -> Biru Cerah ATMI Teks Putih Menyala */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #2f9be8 0%, #0284c7 100%) !important;
        color: #ffffff !important;
        border: 3px solid #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(47, 155, 232, 0.55) !important;
    }}
    div.stButton > button[kind="primary"] p {{
        color: #ffffff !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
    }}

    /* Kartu Konten Putih Solid (Kontras Tinggi Anti-Tabrakan) */
    .solid-card {{
        background-color: #ffffff !important;
        color: #111827 !important;
        padding: 1.8rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
    }}
    .solid-card h2, .solid-card h3, .solid-card h4 {{
        color: #0a2a5c !important;
    }}
    .solid-card p, .solid-card li, .solid-card div {{
        color: #1f2937 !important;
    }}

    /* Kartu Status Ruangan */
    .status-free {{
        background-color: #ecfdf5 !important;
        border: 2px solid #10b981;
        border-left: 12px solid #059669;
    }}
    .status-busy {{
        background-color: #fef2f2 !important;
        border: 2px solid #ef4444;
        border-left: 12px solid #dc2626;
    }}

    /* Badge Fasilitas */
    .badge {{
        display: inline-block;
        background-color: #e0f2fe !important;
        color: #0369a1 !important;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.9rem;
        margin: 4px 6px 4px 0;
        border: 1px solid #bae6fd;
    }}

    /* Judul Seksi di Atas Latar Biru */
    .section-heading {{
        color: #ffffff !important;
        font-size: 1.45rem;
        font-weight: 800;
        margin: 0.5rem 0 1rem 0;
        text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }}

    /* Item Agenda */
    .agenda-item {{
        background-color: #ffffff !important;
        padding: 1.1rem 1.4rem;
        border-radius: 12px;
        border-left: 8px solid #2f9be8;
        margin-bottom: 0.85rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .agenda-active {{
        background-color: #fffbeb !important;
        border-left: 8px solid #d97706;
    }}
    .agenda-past {{
        background-color: #f1f5f9 !important;
        border-left: 8px solid #64748b;
    }}

    /* Form Peminjaman Putih Bersih */
    [data-testid="stForm"] {{
        background-color: #ffffff !important;
        padding: 1.8rem !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important;
    }}
    [data-testid="stForm"] label p {{
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ fungsi pengolahan data
def hm(h: float) -> str:
    m = round(h * 60)
    return f"{m // 60:02d}.{m % 60:02d}"

def jam(teks: str) -> float:
    m = re.search(r"(\d+)[.:](\d+)", teks or "")
    return int(m.group(1)) + int(m.group(2)) / 60 if m else 0.0

def tanggal(teks: str):
    m = re.search(r"(\d+)\s+([A-Za-z]+)\s+(\d{4})", teks or "")
    if not m or m.group(2).lower() not in BULAN:
        return None
    return date(int(m.group(3)), BULAN.index(m.group(2).lower()) + 1, int(m.group(1)))

@st.cache_data(ttl=30, show_spinner=False)
def load_events():
    galat = []
    urls = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}",
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
        + urllib.parse.quote(SHEET_NAME),
    )
    teks = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dasbor-ruang-web/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read().decode("utf-8-sig")
            if raw.lstrip().lower().startswith(("<!doctype", "<html")):
                raise ValueError("Sheet belum dibagikan publik (Viewer)")
            teks = raw
            break
        except Exception as e:
            galat.append(str(e))

    if teks is None:
        return [], "; ".join(galat)

    baris = list(csv.reader(io.StringIO(teks)))
    if not baris:
        return [], "Data kosong"

    kep = [h.strip().lower() for h in baris[0]]
    idx = {
        k: (kep.index(k) if k in kep else -1)
        for k in ("judul", "waktu mulai", "waktu selesai", "lokasi", "deskripsi", "hari")
    }
    if idx["judul"] < 0 or idx["hari"] < 0:
        return [], "Kolom Judul / Hari tidak ditemukan di Sheet"

    def ambil(r, k):
        return r[idx[k]].strip() if 0 <= idx[k] < len(r) else ""

    out = []
    for r in baris[1:]:
        j, d = ambil(r, "judul"), tanggal(ambil(r, "hari"))
        s, e = jam(ambil(r, "waktu mulai")), jam(ambil(r, "waktu selesai"))
        if j and d and e > s:
            out.append({
                "title": j,
                "date": d,
                "s": s,
                "e": e,
                "loc": ambil(r, "lokasi").lower(),
                "desc": ambil(r, "deskripsi"),
            })
    out.sort(key=lambda a: (a["date"], a["s"]))
    return out, ""

def filter_ruang(events, room_key, today):
    ruang = ROOMS[room_key]
    penanda = (room_key.casefold(), ruang["label"].casefold(), ruang["loc"].casefold())
    out = []
    for a in events:
        d = (a["date"] - today).days
        if 0 <= d < 7 and any(p in a["loc"] for p in penanda):
            out.append((d, a))
    return out

# ------------------------------------------------------------------ tampilan utama
now = datetime.now(TZ)
today = now.date()
nh = now.hour + now.minute / 60

# Header Banner ATMI
st.markdown(f"""
<div class="header-box">
    <p class="header-title">⚙️ SISTEM INFORMASI & PEMINJAMAN RUANG</p>
    <p class="header-sub">Politeknik ATMI Surakarta &nbsp;•&nbsp; {HARI[now.weekday()]}, {now.day} {BLN[now.month-1]} {now.year} &nbsp;•&nbsp; Pukul {now.strftime('%H.%M')} WIB</p>
</div>
""", unsafe_allow_html=True)

# Baris Pemilih Ruangan & Tombol Refresh
col_sel, col_ref = st.columns([4, 1], gap="medium")
with col_sel:
    st.markdown('<div class="control-label">📍 PILIH RUANGAN YANG DIPANTAU:</div>', unsafe_allow_html=True)
    selected_key = st.selectbox(
        "Pilih Ruangan",
        options=list(ROOMS.keys()),
        format_func=lambda k: f"{ROOMS[k]['label']} — {ROOMS[k]['loc']}",
        label_visibility="collapsed",
    )
with col_ref:
    st.markdown('<div class="control-label">&nbsp;</div>', unsafe_allow_html=True)
    if st.button("🔄 Segarkan", key="btn_refresh", type="secondary"):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------ 4 MENU UTAMA BESAR & MENCOLOK
MENUS = [
    ("🟢 STATUS RUANG", 0),
    ("📋 AGENDA HARI INI", 1),
    ("🗓️ JADWAL 7 HARI", 2),
    ("✍️ PINJAM RUANG", 3),
]

m_cols = st.columns(4, gap="medium")
for label, idx in MENUS:
    with m_cols[idx]:
        btn_type = "primary" if st.session_state.active_menu == idx else "secondary"
        if st.button(label, key=f"nav_menu_{idx}", type=btn_type, use_container_width=True):
            st.session_state.active_menu = idx
            st.rerun()

st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 1.2rem 0;'>", unsafe_allow_html=True)

# Muat & Filter Data
ruang = ROOMS[selected_key]
events, err = load_events()

if err:
    st.error(f"Gagal memuat data dari Google Sheet: {err}")

acara_7hari = filter_ruang(events, selected_key, today)
hari_ini = sorted([a for d, a in acara_7hari if d == 0], key=lambda a: a["s"])
cur = next((a for a in hari_ini if a["s"] <= nh < a["e"]), None)
nxt = next((a for a in hari_ini if a["s"] > nh), None)

# ------------------------------------------------------------------ KONTEN HALAMAN AKTIF
menu = st.session_state.active_menu

# ============== MENU 0: STATUS RUANG ==============
if menu == 0:
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        if cur:
            sisa = max(0, round((cur["e"] - nh) * 60))
            st.markdown(f"""
            <div class="solid-card status-busy">
                <span style="background:#dc2626; color:#ffffff !important; padding:6px 16px; border-radius:20px; font-size:0.9rem; font-weight:800;">● SEDANG DIGUNAKAN</span>
                <h2 style="margin: 16px 0 4px 0; font-size:2rem; color:#7f1d1d !important;">{ruang['label']}</h2>
                <p style="color:#4b5563 !important; font-weight:600; margin-bottom:22px;">{ruang['loc']}</p>
                <div style="background:#ffffff; padding:18px; border-radius:12px; border:1px solid #fecaca; border-left:6px solid #dc2626;">
                    <div style="font-size:0.85rem; color:#6b7280 !important; font-weight:700;">KEGIATAN BERLANGSUNG:</div>
                    <div style="font-size:1.3rem; font-weight:800; color:#111827 !important; margin:4px 0;">{cur['title']}</div>
                    <div style="font-size:1rem; font-weight:700; color:#dc2626 !important;">Pukul {hm(cur['s'])} – {hm(cur['e'])} WIB (Selesai {sisa} menit lagi)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            info_next = (
                f"Agenda berikutnya: <b style='color:#0a2a5c;'>{nxt['title']}</b> pukul <b style='color:#0a2a5c;'>{hm(nxt['s'])} WIB</b>."
                if nxt else "Tidak ada agenda terjadwal lagi untuk hari ini."
            )
            st.markdown(f"""
            <div class="solid-card status-free">
                <span style="background:#059669; color:#ffffff !important; padding:6px 16px; border-radius:20px; font-size:0.9rem; font-weight:800;">✓ TERSEDIA SEKARANG</span>
                <h2 style="margin: 16px 0 4px 0; font-size:2rem; color:#064e3b !important;">{ruang['label']}</h2>
                <p style="color:#374151 !important; font-weight:600; margin-bottom:22px;">{ruang['loc']}</p>
                <div style="background:#ffffff; padding:18px; border-radius:12px; border:1px solid #a7f3d0;">
                    <p style="font-size:1.1rem; color:#111827 !important; margin-bottom:8px;">{info_next}</p>
                    <p style="color:#059669 !important; font-weight:800; font-size:1rem; margin:0;">Ruangan kosong dan siap digunakan untuk kegiatan.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        badges = "".join([f'<span class="badge">{f}</span>' for f in ruang["fac"]])
        st.markdown(f"""
        <div class="solid-card">
            <h3 style="margin-top:0; border-bottom:2px solid #e2e8f0; padding-bottom:10px;">ℹ️ Spesifikasi Ruangan</h3>
            <p style="margin-bottom:10px;"><b style="color:#0a2a5c;">Jenis Ruangan:</b><br><span style="font-size:1.05rem;">{ruang['type']}</span></p>
            <p style="margin-bottom:10px;"><b style="color:#0a2a5c;">Lokasi Gedung:</b><br><span style="font-size:1.05rem;">{ruang['loc']}</span></p>
            <p style="margin-bottom:14px;"><b style="color:#0a2a5c;">Kapasitas Maksimal:</b><br><span style="font-size:1.05rem;">{ruang['cap']}</span></p>
            <p style="margin-bottom:8px;"><b style="color:#0a2a5c;">Fasilitas Tersedia:</b></p>
            <div>{badges}</div>
        </div>
        """, unsafe_allow_html=True)

# ============== MENU 1: AGENDA HARI INI ==============
elif menu == 1:
    st.markdown(f'<div class="section-heading">📋 Daftar Agenda Hari Ini — {ruang["label"]}</div>', unsafe_allow_html=True)
    if not hari_ini:
        st.markdown("""
        <div class="solid-card" style="text-align:center; padding:2.5rem;">
            <h3 style="margin-bottom:8px;">Tidak Ada Agenda Hari Ini</h3>
            <p style="font-size:1.05rem;">Ruangan belum memiliki jadwal peminjaman hari ini. Silakan klik menu <b>✍️ PINJAM RUANG</b> untuk membuat jadwal baru.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for a in hari_ini:
            is_cur = (a is cur)
            is_past = (nh >= a["e"])
            cls = "agenda-item agenda-active" if is_cur else ("agenda-item agenda-past" if is_past else "agenda-item")
            badge_status = (
                '<span style="background:#d97706; color:#ffffff; padding:3px 10px; border-radius:12px; font-size:0.8rem; margin-left:8px;">SEDANG BERLANGSUNG</span>'
                if is_cur else (
                    '<span style="background:#64748b; color:#ffffff; padding:3px 10px; border-radius:12px; font-size:0.8rem; margin-left:8px;">SELESAI</span>'
                    if is_past else
                    '<span style="background:#0284c7; color:#ffffff; padding:3px 10px; border-radius:12px; font-size:0.8rem; margin-left:8px;">TERJADWAL</span>'
                )
            )
            desc_html = f'<div style="font-size:0.95rem; color:#475569 !important; margin-top:4px;">{a["desc"]}</div>' if a["desc"] else ""
            st.markdown(f"""
            <div class="{cls}">
                <div style="font-weight:800; color:#0a2a5c !important; font-size:1rem;">
                    🕒 {hm(a['s'])} – {hm(a['e'])} WIB {badge_status}
                </div>
                <div style="font-size:1.25rem; font-weight:800; color:#0f172a !important; margin-top:6px;">{a['title']}</div>
                {desc_html}
            </div>
            """, unsafe_allow_html=True)

# ============== MENU 2: JADWAL 7 HARI ==============
elif menu == 2:
    st.markdown(f'<div class="section-heading">🗓️ Jadwal 7 Hari ke Depan — {ruang["label"]}</div>', unsafe_allow_html=True)
    cols = st.columns(7, gap="small")
    for i in range(7):
        d = date.fromordinal(today.toordinal() + i)
        nama_hari = "HARI INI" if i == 0 else HARI[d.weekday()].upper()
        lst = sorted([a for k, a in acara_7hari if k == i], key=lambda a: a["s"])
        with cols[i]:
            top_bar = "#10b981" if i == 0 else "#0a2a5c"
            items_html = ""
            if not lst:
                items_html = '<div style="color:#64748b !important; font-style:italic; font-size:0.9rem; padding-top:8px;">Kosong</div>'
            else:
                for a in lst:
                    items_html += f"""
                    <div style="background:#e0f2fe; border-left:4px solid #0284c7; padding:8px; border-radius:8px; margin-bottom:8px;">
                        <div style="font-weight:800; color:#0369a1 !important; font-size:0.85rem;">{hm(a['s'])}–{hm(a['e'])}</div>
                        <div style="font-weight:700; color:#0f172a !important; font-size:0.9rem; margin-top:2px;">{a['title']}</div>
                    </div>
                    """
            st.markdown(f"""
            <div style="background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.18); min-height:260px;">
                <div style="background:{top_bar}; padding:10px; text-align:center;">
                    <div style="color:#ffffff !important; font-weight:800; font-size:0.9rem;">{nama_hari}</div>
                    <div style="color:#e2e8f0 !important; font-size:0.85rem; font-weight:600;">{d.day} {BLN[d.month-1]} {d.year}</div>
                </div>
                <div style="padding:10px;">
                    {items_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============== MENU 3: PINJAM RUANG ==============
elif menu == 3:
    st.markdown(f'<div class="section-heading">✍️ Formulir Peminjaman — {ruang["label"]}</div>', unsafe_allow_html=True)
    c_form, c_guide = st.columns([3, 2], gap="large")
    with c_form:
        with st.form("form_pinjam"):
            judul_acara = st.text_input("Nama Kegiatan / Rapat", placeholder="Contoh: Rapat Koordinasi Prodi Mekatronika")
            tgl_acara = st.date_input("Tanggal Pelaksanaan", value=today, min_value=today)
            c_t1, c_t2 = st.columns(2)
            jam_mulai = c_t1.time_input("Jam Mulai", value=time(8, 0))
            jam_selesai = c_t2.time_input("Jam Selesai", value=time(10, 0))
            deskripsi = st.text_area("Nama Peminjam & Unit / Keterangan", placeholder="Contoh: Bpk. Budi - Unit Produksi")
            submit = st.form_submit_button("📅 Buat Undangan Google Calendar", type="primary", use_container_width=True)

        if submit:
            if not judul_acara.strip():
                st.warning("Mohon isi nama kegiatan terlebih dahulu.")
            elif jam_selesai <= jam_mulai:
                st.warning("Jam selesai harus lebih akhir dari jam mulai.")
            else:
                dt_start = datetime.combine(tgl_acara, jam_mulai).strftime("%Y%m%dT%H%M00")
                dt_end = datetime.combine(tgl_acara, jam_selesai).strftime("%Y%m%dT%H%M00")
                params = urllib.parse.urlencode({
                    "action": "TEMPLATE",
                    "text": judul_acara.strip(),
                    "dates": f"{dt_start}/{dt_end}",
                    "location": f"{ruang['label']} ({ruang['loc']})",
                    "details": deskripsi.strip(),
                    "add": ruang["mail"],
                })
                gcal_url = f"https://calendar.google.com/calendar/render?{params}"
                st.success("Tautan Google Calendar berhasil dibuat! Klik tombol di bawah untuk menyimpan jadwal:")
                st.link_button("🚀 Buka & Simpan di Google Calendar Sekarang", gcal_url, type="primary", use_container_width=True)

    with c_guide:
        st.markdown(f"""
        <div class="solid-card">
            <h3 style="margin-top:0; border-bottom:2px solid #e2e8f0; padding-bottom:10px;">📌 Panduan Peminjaman</h3>
            <ol style="padding-left:1.3rem; line-height:1.8; font-size:1rem;">
                <li>Pastikan ruangan yang dipilih pada bagian atas sudah sesuai.</li>
                <li>Isi nama kegiatan, tanggal, dan jam peminjaman pada formulir di samping.</li>
                <li>Klik tombol <b>Buat Undangan Google Calendar</b>.</li>
                <li>Pada tab Google Calendar yang terbuka, pastikan email <code style="background:#f1f5f9; color:#0f172a; padding:2px 6px; border-radius:4px;">{ruang['mail']}</code> sudah masuk di daftar tamu.</li>
                <li>Klik <b>Save / Simpan</b>. Jadwal akan tampil otomatis di dasbor ini dalam ±30 detik.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
