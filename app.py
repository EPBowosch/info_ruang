import csv
import io
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta
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

# ------------------------------------------------------------------ CSS Kustom (Tema ATMI)
st.markdown("""
<style>
    .stApp {
        background-color: #f4f7fa;
    }
    .header-box {
        background: linear-gradient(135deg, #082250 0%, #0f4592 65%, #2f9be8 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(8, 34, 80, 0.15);
    }
    .header-title {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
    }
    .header-sub {
        font-size: 0.95rem;
        color: #bce0fd;
        margin-top: 0.2rem;
    }
    .status-card {
        padding: 1.8rem;
        border-radius: 14px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .status-free {
        background-color: #e4f5ea;
        border-left: 8px solid #2fa866;
        color: #17293a;
    }
    .status-busy {
        background-color: #fdeceb;
        border-left: 8px solid #c0392b;
        color: #17293a;
    }
    .info-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        height: 100%;
    }
    .badge {
        display: inline-block;
        background-color: #eef3f6;
        color: #17293a;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 3px 4px 3px 0;
        border: 1px solid #d7e0e6;
    }
    .agenda-item {
        background: white;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #2f9be8;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .agenda-active {
        border-left: 5px solid #b9770e;
        background: #fff8eb;
    }
    .agenda-past {
        border-left: 5px solid #95a5a6;
        opacity: 0.7;
    }
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

# Header Banner
st.markdown(f"""
<div class="header-box">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div>
            <p class="header-title">🏢 Sistem Informasi & Peminjaman Ruang</p>
            <p class="header-sub">Politeknik ATMI Surakarta &nbsp;•&nbsp; {HARI[now.weekday()]}, {now.day} {BLN[now.month-1]} {now.year} ({now.strftime('%H.%M')} WIB)</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Kontrol Pilihan Ruangan & Refresh
col_sel, col_ref = st.columns([4, 1])
with col_sel:
    room_keys = list(ROOMS.keys())
    selected_key = st.selectbox(
        "Pilih Ruangan:",
        options=room_keys,
        format_func=lambda k: f"{ROOMS[k]['label']} ({ROOMS[k]['loc']})",
        label_visibility="collapsed",
    )
with col_ref:
    if st.button("🔄 Segarkan Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

ruang = ROOMS[selected_key]
events, err = load_events()

if err:
    st.error(f"Gagal memuat data dari Google Sheet: {err}")

acara_7hari = filter_ruang(events, selected_key, today)
hari_ini = sorted([a for d, a in acara_7hari if d == 0], key=lambda a: a["s"])
cur = next((a for a in hari_ini if a["s"] <= nh < a["e"]), None)
nxt = next((a for a in hari_ini if a["s"] > nh), None)

# Navigasi Tab
tab1, tab2, tab3, tab4 = st.tabs([
    "🟢 Status Saat Ini",
    "📅 Agenda Hari Ini",
    "🗓️ Jadwal 7 Hari",
    "✍️ Cara & Form Pinjam"
])

# ---------------- TAB 1: STATUS ----------------
with tab1:
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        if cur:
            sisa = max(0, round((cur["e"] - nh) * 60))
            st.markdown(f"""
            <div class="status-card status-busy">
                <span style="background:#c0392b; color:white; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:600;">SEDANG DIGUNAKAN</span>
                <h2 style="margin: 12px 0 4px 0; font-size:1.8rem;">{ruang['label']}</h2>
                <p style="color:#5a6d7b; margin-bottom:20px;">{ruang['loc']}</p>
                <div style="background:white; padding:16px; border-radius:10px; border-left:4px solid #c0392b;">
                    <small style="color:#5a6d7b;">Agenda berlangsung:</small>
                    <h4 style="margin:4px 0; color:#17293a;">{cur['title']}</h4>
                    <p style="margin:0; font-weight:600; color:#c0392b;">{hm(cur['s'])} – {hm(cur['e'])} WIB (Selesai {sisa} menit lagi)</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            info_next = (
                f"Agenda berikutnya: <b>{nxt['title']}</b> pukul <b>{hm(nxt['s'])} WIB</b>."
                if nxt else "Tidak ada agenda terjadwal lagi untuk hari ini."
            )
            st.markdown(f"""
            <div class="status-card status-free">
                <span style="background:#2a8a4f; color:white; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:600;">TERSEDIA SEKARANG</span>
                <h2 style="margin: 12px 0 4px 0; font-size:1.8rem;">{ruang['label']}</h2>
                <p style="color:#5a6d7b; margin-bottom:20px;">{ruang['loc']}</p>
                <p style="font-size:1.05rem; margin-bottom:8px;">{info_next}</p>
                <p style="color:#2a8a4f; font-weight:600; margin:0;">✓ Ruangan kosong dan siap digunakan.</p>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        badges = "".join([f'<span class="badge">{f}</span>' for f in ruang["fac"]])
        st.markdown(f"""
        <div class="info-card">
            <h4 style="color:#0a2a5c; margin-top:0;">ℹ️ Informasi Ruangan</h4>
            <p style="margin-bottom:8px;"><b>Jenis:</b><br>{ruang['type']}</p>
            <p style="margin-bottom:8px;"><b>Lokasi:</b><br>{ruang['loc']}</p>
            <p style="margin-bottom:12px;"><b>Kapasitas:</b><br>{ruang['cap']}</p>
            <p style="margin-bottom:6px;"><b>Fasilitas:</b></p>
            <div>{badges}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------- TAB 2: HARI INI ----------------
with tab2:
    st.subheader(f"Agenda Hari Ini — {ruang['label']}")
    if not hari_ini:
        st.info("Belum ada agenda peminjaman untuk ruangan ini hari ini.")
    else:
        for a in hari_ini:
            is_cur = (a is cur)
            is_past = (nh >= a["e"])
            cls = "agenda-item agenda-active" if is_cur else ("agenda-item agenda-past" if is_past else "agenda-item")
            tag = " • SEDANG BERLANGSUNG" if is_cur else (" • SELESAI" if is_past else "")
            st.markdown(f"""
            <div class="{cls}">
                <div style="font-weight:700; color:#0a2a5c; font-size:0.95rem;">{hm(a['s'])} – {hm(a['e'])} WIB <span style="color:#b9770e;">{tag}</span></div>
                <div style="font-size:1.15rem; font-weight:600; color:#17293a; margin-top:4px;">{a['title']}</div>
                <div style="font-size:0.9rem; color:#5a6d7b; margin-top:2px;">{a['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

# ---------------- TAB 3: 7 HARI ----------------
with tab3:
    st.subheader(f"Jadwal 7 Hari ke Depan — {ruang['label']}")
    cols = st.columns(7)
    for i in range(7):
        d = date.fromordinal(today.toordinal() + i)
        nama_hari = "Hari Ini" if i == 0 else HARI[d.weekday()]
        lst = sorted([a for k, a in acara_7hari if k == i], key=lambda a: a["s"])
        with cols[i]:
            border = "2px solid #2fa866" if i == 0 else "1px solid #d7e0e6"
            st.markdown(f"""
            <div style="background:white; border:{border}; border-radius:10px; padding:10px; min-height:220px;">
                <div style="font-weight:700; color:#0a2a5c;">{nama_hari}</div>
                <div style="font-size:0.85rem; color:#5a6d7b; margin-bottom:10px;">{d.day} {BLN[d.month-1]}</div>
            """, unsafe_allow_html=True)
            if not lst:
                st.caption("Kosong")
            else:
                for a in lst:
                    st.markdown(f"""
                    <div style="background:#e8eefb; padding:6px 8px; border-radius:6px; margin-bottom:6px; font-size:0.82rem;">
                        <b>{hm(a['s'])}–{hm(a['e'])}</b><br>{a['title']}
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ---------------- TAB 4: PINJAM ----------------
with tab4:
    c_form, c_guide = st.columns([3, 2], gap="large")
    with c_form:
        st.subheader("Buat Permintaan Peminjaman")
        with st.form("form_pinjam"):
            judul_acara = st.text_input("Nama Kegiatan / Rapat", placeholder="Contoh: Rapat Koordinasi Prodi")
            tgl_acara = st.date_input("Tanggal", value=today, min_value=today)
            c_t1, c_t2 = st.columns(2)
            jam_mulai = c_t1.time_input("Jam Mulai", value=time(8, 0))
            jam_selesai = c_t2.time_input("Jam Selesai", value=time(10, 0))
            deskripsi = st.text_area("Keterangan / Peminjam", placeholder="Nama peminjam & unit kerja")
            submit = st.form_submit_button("Lanjutkan ke Google Calendar", type="primary")

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
                st.success("Tautan undangan kalender siap! Klik tombol di bawah untuk menyimpan ke Google Calendar Anda:")
                st.link_button("📅 Buka & Simpan di Google Calendar", gcal_url, type="primary")

    with c_guide:
        st.markdown(f"""
        <div class="info-card">
            <h4 style="color:#0a2a5c; margin-top:0;">📌 Alur Peminjaman Ruang</h4>
            <ol style="padding-left:1.2rem; line-height:1.7; color:#17293a;">
                <li>Isi formulir di samping dengan lengkap.</li>
                <li>Klik tombol <b>Lanjutkan ke Google Calendar</b>.</li>
                <li>Pastikan email kalender ruang (<code>{ruang['mail']}</code>) sudah tercantum di daftar tamu (Guests).</li>
                <li>Klik <b>Save / Simpan</b> pada halaman Google Calendar.</li>
                <li>Jadwal akan otomatis muncul di dasbor ini dalam ±30 detik setelah disinkronkan ke Sheet.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
