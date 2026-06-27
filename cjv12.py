import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import pytz
import time
import requests
import json
import re
import random
import uuid

# ==========================================
# 1. APP CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Cjarvis Omni-Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

ist = pytz.timezone('Asia/Kolkata')

# ==========================================
# 2. STATE MANAGEMENT
# ==========================================
PAGES = [
    "⚡ Home Base",
    "💰 Budget Tracker & Analytics",
    "🏋️ Habit Tracker",
    "📚 Subject Tracker (Academic)",
    "🗺️ Locations Unlocked",
    "🤖 CJ Agent",
    "📋 Activity Log",
    "📖 User Guide",
    "⚙️ Settings"
]

# Default habits
DEFAULT_HABITS = [
    {"id": "1", "name": "Physical Exercise", "emoji": "🏋️", "streak": 0, "last_checkin": None, "active": True},
    {"id": "2", "name": "Reading", "emoji": "📖", "streak": 0, "last_checkin": None, "active": True},
    {"id": "3", "name": "Study Session", "emoji": "📚", "streak": 0, "last_checkin": None, "active": True},
    {"id": "4", "name": "Meditation", "emoji": "🧘", "streak": 0, "last_checkin": None, "active": True},
]

def init_state():
    defaults = {
        'current_page': "⚡ Home Base",
        'dashboard_widgets': ["Balance", "Today's Spending", "Total Expenses", "Habit Streak", "To-Do List", "Daily Digest"],
        'streak': 0,
        'balance': 5000.0,
        'transactions': [],
        'locations': [],
        'subjects': [],
        'modules': {},
        'mood_logs': [],
        'daily_digest': [],
        'digest_generated_date': None,
        'user_name': "Monolith Agent",
        'opening_balance': 5000.0,
        'income_sources': [],
        'monthly_budget': {},
        'current_week': None,
        'last_streak_date': None,
        'deadlines': [],
        'github_token': '',
        'gist_id': '',
        'activity_log': [],
        'custom_banner': None,
        'custom_banner_url': '',
        'todos': [],
        'habits': DEFAULT_HABITS.copy(),
        'theme': 'dark',
        'weekly_history': [None]*7,
    }
    for key, default_val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_val

    # Ensure subjects have modules
    for subj in st.session_state.subjects:
        if subj['name'] not in st.session_state.modules:
            st.session_state.modules[subj['name']] = []

init_state()

# ==========================================
# 3. GITHUB GIST SYNC
# ==========================================
KEYS_TO_SYNC = [
    'streak', 'balance', 'transactions', 'locations',
    'subjects', 'modules', 'mood_logs', 'opening_balance', 'income_sources',
    'monthly_budget', 'deadlines', 'custom_banner_url',
    'dashboard_widgets', 'activity_log', 'user_name', 'todos', 'habits',
    'theme', 'weekly_history', 'last_streak_date', 'current_week'
]

def load_from_gist(token, gist_id):
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        res = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers)
        if res.status_code == 200:
            files = res.json().get('files', {})
            if 'cjarvis_state.json' in files:
                return json.loads(files['cjarvis_state.json']['content'])
    except Exception as e:
        st.sidebar.error(f"Load Error: {e}")
    return None

def save_to_gist(token, gist_id):
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload_data = {k: st.session_state[k] for k in KEYS_TO_SYNC if k in st.session_state}
        payload = {
            "files": {
                "cjarvis_state.json": {
                    "content": json.dumps(payload_data, indent=4)
                }
            }
        }
        res = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload)
        return res.status_code == 200
    except Exception as e:
        st.sidebar.error(f"Save Error: {e}")
        return False

# ==========================================
# 4. THEME ENGINE (with gradients)
# ==========================================
def get_theme_css(theme_name):
    themes = {
        'dark': {
            'bg': '#0E0E0E',
            'bg_grad': 'linear-gradient(135deg, #0E0E0E, #1A1A2E)',
            'card': '#1A1A1A',
            'border': '#2C2C2C',
            'text': '#E8E8E8',
            'heading': '#FFFFFF',
            'label': '#A8A8A8',
            'accent': '#6C63FF',
            'accent2': '#FF6584',
            'success': '#4ECDC4',
            'warning': '#FFD93D',
            'danger': '#FF6584',
        },
        'light': {
            'bg': '#F5F5F5',
            'bg_grad': 'linear-gradient(135deg, #F5F5F5, #E8E8F0)',
            'card': '#FFFFFF',
            'border': '#DDDDDD',
            'text': '#222222',
            'heading': '#111111',
            'label': '#666666',
            'accent': '#6C63FF',
            'accent2': '#FF6584',
            'success': '#2E7D32',
            'warning': '#F9A825',
            'danger': '#C62828',
        },
        'blue': {
            'bg': '#0A192F',
            'bg_grad': 'linear-gradient(135deg, #0A192F, #1A365D)',
            'card': '#112240',
            'border': '#233554',
            'text': '#E6F1FF',
            'heading': '#64FFDA',
            'label': '#8892B0',
            'accent': '#64FFDA',
            'accent2': '#FF6B6B',
            'success': '#4ECDC4',
            'warning': '#FFD93D',
            'danger': '#FF6B6B',
        },
        'purple': {
            'bg': '#1A0A2E',
            'bg_grad': 'linear-gradient(135deg, #1A0A2E, #3A1A5E)',
            'card': '#2A1A3E',
            'border': '#3A2A4E',
            'text': '#E8E0F0',
            'heading': '#D4BFFF',
            'label': '#B09CC0',
            'accent': '#B388FF',
            'accent2': '#FF80AB',
            'success': '#69DB7C',
            'warning': '#FFD93D',
            'danger': '#FF80AB',
        },
        'gradient': {
            'bg': '#0F0C29',
            'bg_grad': 'linear-gradient(135deg, #0F0C29, #302B63, #24243E)',
            'card': 'rgba(255,255,255,0.08)',
            'border': 'rgba(255,255,255,0.15)',
            'text': '#F0F0FF',
            'heading': '#FFFFFF',
            'label': '#C0C0E0',
            'accent': '#6C63FF',
            'accent2': '#FF6584',
            'success': '#69DB7C',
            'warning': '#FFD93D',
            'danger': '#FF6584',
        }
    }
    t = themes.get(theme_name, themes['dark'])
    # Convert hex to RGB for alpha
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    accent_rgb = hex_to_rgb(t['accent'])
    accent2_rgb = hex_to_rgb(t['accent2'])
    
    css = f"""
    <style>
        :root {{
            --bg: {t['bg']};
            --bg-grad: {t['bg_grad']};
            --card-bg: {t['card']};
            --border: {t['border']};
            --text: {t['text']};
            --heading: {t['heading']};
            --label: {t['label']};
            --accent: {t['accent']};
            --accent2: {t['accent2']};
            --success: {t['success']};
            --warning: {t['warning']};
            --danger: {t['danger']};
            --accent-rgb: {accent_rgb[0]},{accent_rgb[1]},{accent_rgb[2]};
            --accent2-rgb: {accent2_rgb[0]},{accent2_rgb[1]},{accent2_rgb[2]};
        }}

        /* HIDE DEPLOY BUTTON */
        .stDeployButton {{
            display: none !important;
        }}
        .stAppDeployButton {{
            display: none !important;
        }}
        [data-testid="stToolbar"] {{
            display: none !important;
        }}

        /* MAIN BACKGROUND */
        .stApp {{
            background: var(--bg-grad) !important;
            color: var(--text) !important;
        }}
        .stApp .block-container {{
            background: transparent;
            padding-top: 5rem !important;
            padding-bottom: 2rem;
            max-width: 1450px !important;
        }}
        [data-testid="stHeader"] {{
            background: var(--bg) !important;
            border-bottom: 1px solid var(--border) !important;
            height: 60px !important;
        }}
        section.main {{
            padding-top: 0rem !important;
        }}

        /* METRICS */
        div[data-testid="metric-container"] {{
            background: var(--card-bg) !important;
            border: 1px solid var(--border) !important;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            transition: border 0.2s ease;
        }}
        div[data-testid="metric-container"]:hover {{
            border-color: var(--accent) !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: var(--heading) !important;
            font-weight: 700;
        }}
        div[data-testid="stMetricLabel"] {{
            color: var(--label) !important;
            font-weight: 600;
        }}

        /* CARDS */
        .cjarvis-card {{
            background: var(--card-bg) !important;
            border: 1px solid var(--border) !important;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
            min-height: 140px;
            transition: all 0.25s ease;
            cursor: default;
        }}
        .cjarvis-card:hover {{
            transform: translateY(-3px);
            border-color: var(--accent) !important;
        }}
        .card-icon {{
            background: rgba(var(--accent-rgb), 0.08) !important;
            border: 1px solid rgba(var(--accent-rgb), 0.15) !important;
            color: var(--accent) !important;
            width: 45px;
            height: 45px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            margin-bottom: 15px;
        }}
        .card-title {{
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--heading) !important;
            margin-bottom: 10px;
        }}
        .card-text {{
            font-size: 0.9rem;
            color: var(--label) !important;
            line-height: 1.5;
        }}

        /* STREAK BADGE */
        .duo-streak {{
            background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
            color: white !important;
            padding: 8px 28px;
            border-radius: 40px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
            font-size: 18px;
            display: block;
            width: fit-content;
            margin: 0 auto 12px auto;
            box-shadow: 0 4px 20px rgba(var(--accent-rgb), 0.25);
            text-align: center;
        }}

        /* WEEK CONTAINER */
        .week-container {{
            display: flex;
            justify-content: center;
            gap: 18px;
            margin-bottom: 30px;
            background: rgba(var(--accent-rgb), 0.03);
            padding: 16px 20px;
            border-radius: 16px;
            border: 1px solid rgba(var(--accent-rgb), 0.08);
        }}
        .day-node {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }}
        .circle {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 16px;
            font-family: 'JetBrains Mono', monospace;
            transition: all 0.2s ease;
        }}
        .circle.done {{
            background: rgba(var(--accent-rgb), 0.15);
            color: var(--accent);
            border: 1px solid var(--accent);
            box-shadow: 0 0 15px rgba(var(--accent-rgb), 0.15);
        }}
        .circle.missed {{
            background: rgba(var(--accent2-rgb), 0.12);
            color: var(--accent2);
            border: 1px solid var(--accent2);
            box-shadow: 0 0 15px rgba(var(--accent2-rgb), 0.12);
        }}
        .circle.future {{
            background: var(--card-bg);
            color: #555;
            border: 1px solid var(--border);
        }}
        .day-label {{
            font-size: 12px;
            font-weight: 700;
            color: var(--label);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* MODULE ROWS */
        .module-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }}
        .module-done {{
            color: var(--accent);
            font-weight: 700;
        }}
        .module-pending {{
            color: #666;
        }}

        /* DIGEST */
        .digest-item {{
            background: var(--card-bg);
            border-left: 3px solid var(--accent);
            padding: 12px 18px;
            border-radius: 8px;
            margin-bottom: 10px;
            color: var(--text);
            font-size: 14px;
            font-family: 'JetBrains Mono', monospace;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}

        /* DATE */
        .live-date {{
            font-size: 1.1rem;
            color: var(--label);
            text-align: center;
            margin-bottom: 25px;
            text-transform: uppercase;
            letter-spacing: 3px;
            font-weight: 600;
        }}

        /* HERO */
        .hero-title {{
            color: var(--heading);
            font-weight: 800;
            font-size: 3.8rem;
            margin-bottom: 0px;
            text-align: center;
            text-shadow: 0 2px 20px rgba(var(--accent-rgb), 0.15);
            letter-spacing: -1px;
        }}
        .hero-subtitle {{
            color: var(--accent);
            font-size: 1.2rem;
            font-weight: 600;
            margin-top: -5px;
            margin-bottom: 25px;
            text-align: center;
            letter-spacing: 2px;
            opacity: 0.8;
        }}

        /* ATTENDANCE BADGES */
        .att-safe {{ color: var(--success); font-weight: 700; }}
        .att-warning {{ color: var(--warning); font-weight: 700; }}
        .att-danger {{ color: var(--danger); font-weight: 700; }}
        .exam-soon {{ color: var(--danger); font-weight: 700; font-size: 12px; }}
        .exam-ok {{ color: var(--success); font-weight: 700; font-size: 12px; }}

        /* MOOD */
        .mood-score-high {{ color: var(--success); font-weight: 800; font-size: 18px; font-family: 'JetBrains Mono', monospace; }}
        .mood-score-mid {{ color: var(--warning); font-weight: 800; font-size: 18px; font-family: 'JetBrains Mono', monospace; }}
        .mood-score-low {{ color: var(--danger); font-weight: 800; font-size: 18px; font-family: 'JetBrains Mono', monospace; }}

        /* BUTTONS */
        .stButton button {{
            background: var(--accent) !important;
            color: white !important;
            border: none !important;
            border-radius: 40px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }}
        .stButton button:hover {{
            background: var(--accent2) !important;
            box-shadow: 0 4px 20px rgba(var(--accent-rgb), 0.3) !important;
            transform: scale(1.01) !important;
        }}
        .stButton button:focus {{
            box-shadow: 0 0 0 2px rgba(var(--accent-rgb), 0.3) !important;
        }}
        .stButton button[data-baseweb="button"]:nth-child(2) {{
            background: var(--card-bg) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
        }}
        .stButton button[data-baseweb="button"]:nth-child(2):hover {{
            background: #333 !important;
            border-color: var(--accent) !important;
        }}

        /* SIDEBAR */
        section[data-testid="stSidebar"] {{
            background: var(--bg) !important;
            border-right: 1px solid var(--border) !important;
        }}
        section[data-testid="stSidebar"] .css-1d391kg {{
            background: var(--bg) !important;
        }}
        section[data-testid="stSidebar"] .stRadio label {{
            color: var(--label) !important;
            font-weight: 500 !important;
        }}
        section[data-testid="stSidebar"] .stRadio label:hover {{
            color: var(--text) !important;
        }}
        section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] input:checked ~ div {{
            border-color: var(--accent) !important;
        }}
        .stMultiSelect [data-baseweb="tag"] {{
            background: var(--card-bg) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
        }}

        /* TABS */
        .stTabs [data-baseweb="tab-list"] button {{
            color: var(--label) !important;
            font-weight: 600;
            border-bottom: 2px solid transparent;
        }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            color: var(--accent) !important;
            border-bottom-color: var(--accent) !important;
        }}

        /* EXPANDER */
        .streamlit-expanderHeader {{
            color: var(--text) !important;
            background: var(--card-bg) !important;
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
        }}
        .streamlit-expanderHeader:hover {{
            border-color: var(--accent) !important;
        }}

        /* PROGRESS */
        .stProgress > div > div {{
            background: var(--accent) !important;
        }}

        /* DATAFRAME */
        .stDataFrame {{
            background: var(--card-bg) !important;
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
        }}
        .stDataFrame thead tr th {{
            color: var(--label) !important;
            font-weight: 600 !important;
        }}
        .stDataFrame tbody tr td {{
            color: var(--text) !important;
        }}

        /* ALERTS */
        .stAlert {{
            border-radius: 12px !important;
            border-left: 4px solid var(--accent) !important;
            background: var(--card-bg) !important;
        }}
        .stAlert[data-baseweb="notification"] {{
            background: var(--card-bg) !important;
        }}

        /* CODE */
        .stCodeBlock {{
            background: var(--card-bg) !important;
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
        }}

        img {{
            border-radius: 12px;
        }}

        /* TODO */
        .todo-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }}
        .todo-item .task-done {{
            text-decoration: line-through;
            color: var(--label);
        }}
        .todo-item .task-pending {{
            color: var(--text);
        }}

        /* RESPONSIVE */
        @media (max-width: 640px) {{
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}
            .hero-title {{
                font-size: 2.5rem !important;
            }}
            .live-date {{
                font-size: 0.9rem !important;
            }}
        }}
    </style>
    """
    return css

def apply_theme():
    theme = st.session_state.get('theme', 'dark')
    css = get_theme_css(theme)
    st.markdown(css, unsafe_allow_html=True)

apply_theme()

# ==========================================
# 5. CORE ENGINE FUNCTIONS
# ==========================================
def log_action(action):
    timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.activity_log.insert(0, {
        'timestamp': timestamp,
        'action': action
    })

def process_transaction(txn_type, amount, category, note):
    if txn_type == "Expense":
        if st.session_state.balance < amount:
            st.error("Transaction Failed: Insufficient funds.")
            return False
        st.session_state.balance -= amount
    elif txn_type == "Income":
        st.session_state.balance += amount
    else:
        return False
    
    txn_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M")
    st.session_state.transactions.insert(0, {
        "Date": txn_time, "Type": txn_type, "Category": category,
        "Amount (₹)": amount, "Note": note
    })
    log_action(f"{txn_type} ₹{amount} - {category} ({note})")
    return True

def get_attendance_status(total, attended):
    if total == 0:
        return 0, 0, "No Data", "att-warning"
    pct = (attended / total) * 100
    safe_skips = max(0, int((attended - 0.75 * total) / 0.75))
    if pct >= 85: return pct, safe_skips, "Safe", "att-safe"
    elif pct >= 75: return pct, safe_skips, "On Edge", "att-warning"
    else:
        t, a, needed = total, attended, 0
        while a / t < 0.75 and needed < 100:
            t += 1; a += 1; needed += 1
        return pct, -needed, "Danger", "att-danger"

def days_until(date_str_iso):
    try:
        target = datetime.strptime(date_str_iso, "%Y-%m-%d").date()
        return (target - date.today()).days
    except:
        return None

def generate_digest():
    digest = []
    for subj in st.session_state.subjects:
        pct, safe, label, _ = get_attendance_status(subj["total"], subj["attended"])
        if label == "Danger": digest.append(f"🚨 {subj['name']}: Critical at {pct:.0f}%. Attend immediately.")
        elif label == "On Edge": digest.append(f"⚠️ {subj['name']}: {pct:.0f}% — {safe} skips left.")
    
    total_spent = sum(t["Amount (₹)"] for t in st.session_state.transactions if t["Type"] == "Expense")
    if total_spent > 0:
        digest.append(f"💸 ₹{total_spent:,.0f} spent. Remaining: ₹{st.session_state.balance:,.0f}.")
    digest.append(f"🔥 Habit Streak: {st.session_state.streak} days. Keep it up!")
    return digest

# ==========================================
# 6. HABIT FUNCTIONS
# ==========================================
def check_weekly_reset():
    today = date.today()
    week_num = today.isocalendar()[1]
    if st.session_state.current_week != week_num:
        st.session_state.weekly_history = [None] * 7
        st.session_state.current_week = week_num
        log_action("Weekly history reset")
    return (today.weekday() + 1) % 7

# ==========================================
# 7. SIDEBAR & NAVIGATION
# ==========================================
with st.sidebar:
    user_name = st.session_state.get('user_name', 'Monolith Agent')
    st.markdown(f"<h2 style='color:var(--accent); font-family: JetBrains Mono; font-weight:800;'>CJARVIS_OS</h2>", unsafe_allow_html=True)
    st.caption(f"👤 User: {user_name}")

    st.markdown("---")
    with st.expander("🔐 Sync with GitHub", expanded=False):
        token = st.text_input("GitHub Token", type="password", value=st.session_state.github_token or "")
        gist_id = st.text_input("Gist ID", value=st.session_state.gist_id or "")
        if st.button("Save Credentials & Load", use_container_width=True):
            if token and gist_id:
                st.session_state.github_token = token
                st.session_state.gist_id = gist_id
                with st.spinner("Loading from Gist..."):
                    remote = load_from_gist(token, gist_id)
                    if remote:
                        for k, v in remote.items():
                            if k in st.session_state:
                                st.session_state[k] = v
                        st.success("State loaded from Gist!")
                        log_action("Loaded state from Gist")
                    else:
                        st.error("Load failed. Check token/gist ID.")
            else:
                st.warning("Enter both token and Gist ID.")
        if st.button("Push to Gist", use_container_width=True):
            if st.session_state.github_token and st.session_state.gist_id:
                with st.spinner("Pushing..."):
                    if save_to_gist(st.session_state.github_token, st.session_state.gist_id):
                        st.success("State saved to Gist!")
                        log_action("Pushed state to Gist")
                    else:
                        st.error("Push failed.")
            else:
                st.warning("No credentials stored.")

    st.markdown("---")
    st.metric("Wallet Balance", f"₹{st.session_state.balance:,.2f}")
    total_budget = sum(st.session_state.monthly_budget.values())
    st.metric("Monthly Budget", f"₹{total_budget:,.2f}")
    
    st.markdown("---")
    # Full page list (including Settings, Guide, Log) in one radio
    try:
        rad_idx = PAGES.index(st.session_state.current_page)
    except ValueError:
        rad_idx = 0
    selected_page = st.radio("System Modules", PAGES, index=rad_idx)
    st.session_state.current_page = selected_page

    # Dashboard widgets (only on Home Base)
    if st.session_state.current_page == "⚡ Home Base":
        st.markdown("---")
        widget_options = ["Balance", "Today's Spending", "Total Expenses", "Habit Streak", "To-Do List", "Daily Digest", "Recent Transactions", "Upcoming Deadlines", "Attendance Summary", "Mood"]
        widgets = st.multiselect(
            "Dashboard Layout",
            options=widget_options,
            default=[w for w in st.session_state.dashboard_widgets if w in widget_options]
        )
        st.session_state.dashboard_widgets = widgets

# ==========================================
# 8. MAIN VIEWS
# ==========================================
now_time = datetime.now(ist)
today_str = now_time.strftime("%B %d, %Y")
day_index = check_weekly_reset()

# Quote
QUOTES = [
    "The only easy day was yesterday.",
    "Success is not for the lazy.",
    "Discipline equals freedom.",
    "Stay hard.",
    "You are your only limit.",
    "It’s not about being the best, it’s about being better than you were yesterday.",
    "The pain of discipline is less than the pain of regret.",
    "Every champion was once a contender that refused to give up.",
    "Your habits shape your future.",
    "Be the 8%.",
]
quote = random.choice(QUOTES)

if st.session_state.current_page == "⚡ Home Base":
    
    st.markdown(f"<div class='duo-streak'>HABIT STREAK: {st.session_state.streak}</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>CJARVIS</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='hero-subtitle' style='color:var(--accent2);'>{quote}</h3>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='live-date'>{now_time.strftime('%A • %d %B %Y')}</div>", unsafe_allow_html=True)

    # Banner
    if st.session_state.custom_banner is not None:
        st.image(st.session_state.custom_banner, use_container_width=True)
    elif st.session_state.custom_banner_url:
        st.image(st.session_state.custom_banner_url, use_container_width=True)
    else:
        st.image("https://placehold.co/1200x260/1A1A1A/6C63FF?text=Upload+a+banner+in+Settings", use_container_width=True)

    # Weekly Grid
    days_labels = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
    html_nodes = ""
    for i, status in enumerate(st.session_state.weekly_history):
        cls = "done" if status is True else "missed" if status is False else "future"
        icon = "✓" if status is True else "✗" if status is False else "·"
        html_nodes += f"<div class='day-node'><div class='circle {cls}'>{icon}</div><div class='day-label'>{days_labels[i]}</div></div>"
    st.markdown(f"<div class='week-container'>{html_nodes}</div>", unsafe_allow_html=True)

    # Dashboard
    st.subheader("⚡ System Dashboard")
    widgets = st.session_state.dashboard_widgets
    if widgets:
        # Separate metric widgets from expandable ones
        expandable = ["Daily Digest", "Recent Transactions", "Upcoming Deadlines", "Attendance Summary", "Mood"]
        metric_widgets = [w for w in widgets if w not in expandable and w != "To-Do List"]
        cols = st.columns(len(metric_widgets) if metric_widgets else 1)
        col_idx = 0

        # Metric widgets
        if "Balance" in widgets:
            with cols[col_idx]:
                st.metric("Balance", f"₹{st.session_state.balance:,.0f}")
            col_idx += 1
        if "Today's Spending" in widgets:
            today_spent = sum(t["Amount (₹)"] for t in st.session_state.transactions if t["Type"] == "Expense" and t["Date"].startswith(date.today().isoformat()))
            with cols[col_idx]:
                st.metric("Today's Spending", f"₹{today_spent:,.0f}")
            col_idx += 1
        if "Total Expenses" in widgets:
            total_spent = sum(t["Amount (₹)"] for t in st.session_state.transactions if t["Type"] == "Expense")
            with cols[col_idx]:
                st.metric("Total Expenses", f"₹{total_spent:,.0f}")
            col_idx += 1
        if "Habit Streak" in widgets:
            with cols[col_idx]:
                st.metric("Habit Streak", f"{st.session_state.streak} days", delta="🔥 Keep going!" if st.session_state.streak > 0 else "Start today!")
            col_idx += 1

        # To-Do List (always visible)
        if "To-Do List" in widgets:
            st.markdown("### 📝 To-Do List")
            with st.container():
                col1, col2, col3, col4 = st.columns([2,1,1,0.5])
                with col1:
                    new_task = st.text_input("Task", key="home_todo_task", placeholder="Write a task...")
                with col2:
                    new_time = st.time_input("Time", key="home_todo_time", value=datetime.now(ist).time())
                with col3:
                    new_date = st.date_input("Date", key="home_todo_date", value=date.today())
                with col4:
                    if st.button("➕", key="home_todo_add"):
                        if new_task:
                            st.session_state.todos.append({
                                "task": new_task,
                                "done": False,
                                "created_date": date.today().isoformat(),
                                "description": "",
                                "time": new_time.strftime("%H:%M"),
                                "due_date": new_date.isoformat()
                            })
                            log_action(f"Added todo: {new_task}")
                            st.rerun()
            if st.session_state.todos:
                for i, todo in enumerate(st.session_state.todos):
                    col1, col2, col3, col4 = st.columns([0.6, 0.15, 0.15, 0.1])
                    with col1:
                        if todo["done"]:
                            st.markdown(f"<div class='todo-item'><span class='task-done'>✅ {todo['task']}</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='todo-item'><span class='task-pending'>⬜ {todo['task']}</span></div>", unsafe_allow_html=True)
                        st.caption(f"Due: {todo.get('due_date', '')} at {todo.get('time', '')}")
                    with col2:
                        if st.button("Done", key=f"home_todo_done_{i}"):
                            st.session_state.todos[i]["done"] = not todo["done"]
                            log_action(f"Toggled todo: {todo['task']}")
                            st.rerun()
                    with col3:
                        if st.button("✏️", key=f"home_todo_edit_{i}"):
                            new_task_name = st.text_input("Edit task", value=todo['task'], key=f"edit_{i}")
                            if new_task_name:
                                st.session_state.todos[i]['task'] = new_task_name
                                log_action(f"Edited todo to: {new_task_name}")
                                st.rerun()
                    with col4:
                        if st.button("❌", key=f"home_todo_del_{i}"):
                            st.session_state.todos.pop(i)
                            log_action(f"Deleted todo: {todo['task']}")
                            st.rerun()
            else:
                st.caption("No tasks yet. Add one above!")

        # Expandable widgets
        if "Daily Digest" in widgets:
            with st.expander("📋 Daily Digest", expanded=False):
                if st.session_state.digest_generated_date != today_str:
                    st.session_state.daily_digest = generate_digest()
                    st.session_state.digest_generated_date = today_str
                    log_action("Auto-generated daily digest")
                if st.button("🔄 Regenerate Digest", use_container_width=True):
                    st.session_state.daily_digest = generate_digest()
                    st.session_state.digest_generated_date = today_str
                    log_action("Manual digest regeneration")
                    st.rerun()
                if st.session_state.daily_digest:
                    for item in st.session_state.daily_digest:
                        st.markdown(f"<div class='digest-item'>{item}</div>", unsafe_allow_html=True)
                else:
                    st.info("System awaiting protocol scan.")

        if "Recent Transactions" in widgets:
            with st.expander("🔄 Recent Transactions", expanded=False):
                if st.session_state.transactions:
                    df = pd.DataFrame(st.session_state.transactions[:5])
                    st.dataframe(df[['Date', 'Type', 'Category', 'Amount (₹)']], use_container_width=True, hide_index=True)
                else:
                    st.caption("No transactions yet.")

        if "Upcoming Deadlines" in widgets:
            with st.expander("⏳ Upcoming Deadlines", expanded=False):
                if st.session_state.deadlines:
                    for d in st.session_state.deadlines:
                        days = days_until(d['date'])
                        if days is not None and days >= 0:
                            st.markdown(f"- **{d['name']}** – {days} days left")
                        else:
                            st.markdown(f"- **{d['name']}** – EXPIRED")
                else:
                    st.caption("No deadlines set.")

        if "Attendance Summary" in widgets:
            with st.expander("📊 Attendance Summary", expanded=False):
                if st.session_state.subjects:
                    total_pct = sum(get_attendance_status(s['total'], s['attended'])[0] for s in st.session_state.subjects) / len(st.session_state.subjects)
                    st.metric("Overall Attendance", f"{total_pct:.1f}%")
                    for s in st.session_state.subjects:
                        pct, _, label, _ = get_attendance_status(s['total'], s['attended'])
                        st.caption(f"{s['name']}: {pct:.0f}% ({label})")
                else:
                    st.caption("No subjects added.")

        if "Mood" in widgets:
            with st.expander("😶 Mood", expanded=False):
                mood_today = next((m for m in reversed(st.session_state.mood_logs) if m["date"] == today_str), None)
                if mood_today:
                    score = mood_today["score"]
                    st.metric("Today's Mood", f"{score}/10")
                    st.caption(f"Note: {mood_today.get('note', '—')}")
                else:
                    st.caption("Mood not logged today.")

    st.markdown("---")
    
    # Deadlines (shown as cards)
    st.subheader("⏳ Deadline Countdown")
    if st.session_state.deadlines:
        cd_cols = st.columns(min(len(st.session_state.deadlines), 4))
        for idx, item in enumerate(st.session_state.deadlines):
            with cd_cols[idx % len(cd_cols)]:
                d = days_until(item["date"])
                if d is not None and d >= 0:
                    st.markdown(f"""
                    <div class="cjarvis-card">
                        <h4>{item['name']}</h4>
                        <h2 style="color:var(--accent); font-weight:800;">{d} Days</h2>
                        <p>{max(0, d*24)} Hours Remaining</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="cjarvis-card" style="border-color:var(--danger);">
                        <h4>{item['name']}</h4>
                        <h2 style="color:var(--danger); font-weight:800;">EXPIRED</h2>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No deadlines set. Add them in Settings.")

    st.markdown("---")

    # Quick-Nav Cards
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="cjarvis-card"><div class="card-icon">💰</div><div class="card-title">FINANCIAL LEDGER</div>
        <div class="card-text">Monitor strict capital outflows.</div></div>""", unsafe_allow_html=True)
        if st.button("ACCESS LEDGER →", key="nav_budget", use_container_width=True):
            st.session_state.current_page = "💰 Budget Tracker & Analytics"
            st.rerun()

        st.markdown("""<div class="cjarvis-card"><div class="card-icon">📚</div><div class="card-title">ACADEMIC VAULT</div>
        <div class="card-text">Track attendance and syllabus modules.</div></div>""", unsafe_allow_html=True)
        if st.button("ACCESS ACADEMICS →", key="nav_subject", use_container_width=True):
            st.session_state.current_page = "📚 Subject Tracker (Academic)"
            st.rerun()
    
    with c2:
        st.markdown("""<div class="cjarvis-card"><div class="card-icon">🏋️</div><div class="card-title">HABIT TRACKER</div>
        <div class="card-text">Track your daily habits and streaks.</div></div>""", unsafe_allow_html=True)
        if st.button("ACCESS HABITS →", key="nav_habit", use_container_width=True):
            st.session_state.current_page = "🏋️ Habit Tracker"
            st.rerun()

        st.markdown("""<div class="cjarvis-card"><div class="card-icon">🤖</div><div class="card-title">CJ AGENT</div>
        <div class="card-text">Log expenses in Tamil/English/Tanglish with intelligent parsing.</div></div>""", unsafe_allow_html=True)
        if st.button("ACCESS CJ AGENT →", key="nav_ai", use_container_width=True):
            st.session_state.current_page = "🤖 CJ Agent"
            st.rerun()
        
        if st.session_state.custom_banner is None and st.session_state.custom_banner_url:
            st.image(st.session_state.custom_banner_url, use_container_width=True)

# ==========================================
# BUDGET TRACKER
# ==========================================
elif st.session_state.current_page == "💰 Budget Tracker & Analytics":
    st.title("💰 Ledger & Analytics")

    with st.expander("⚙️ Wallet Setup & Budget", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            opening = st.number_input("Opening Balance", value=st.session_state.opening_balance, step=100.0)
            if st.button("Update Opening Balance"):
                st.session_state.opening_balance = opening
                st.session_state.balance = opening - sum(t["Amount (₹)"] for t in st.session_state.transactions if t["Type"] == "Expense") + sum(t["Amount (₹)"] for t in st.session_state.transactions if t["Type"] == "Income")
                log_action(f"Set opening balance to ₹{opening}")
                st.success("Opening balance updated!")
                st.rerun()
        with col2:
            st.write("**Income Sources**")
            source = st.text_input("Source name")
            amount = st.number_input("Amount", min_value=0.0, step=100.0)
            if st.button("Add Income Source"):
                if source and amount > 0:
                    st.session_state.income_sources.append({"source": source, "amount": amount, "date": date.today().isoformat()})
                    process_transaction("Income", amount, source, f"Added income source: {source}")
                    log_action(f"Added income source: {source} ₹{amount}")
                    st.success("Income source added!")
                    st.rerun()
            st.write("**Current Sources:**")
            for s in st.session_state.income_sources:
                st.caption(f"- {s['source']}: ₹{s['amount']} ({s['date']})")

        st.markdown("---")
        st.subheader("📊 Monthly Budget by Category")
        categories = ["Food", "Transport", "Groceries", "Shopping", "Stationery", "Personal Care", "Entertainment", "Bills", "Education", "Medical", "Other"]
        for cat in categories:
            col1, col2 = st.columns([2,1])
            with col1:
                budget_val = st.number_input(f"Budget for {cat}", min_value=0.0, step=100.0, key=f"budget_{cat}", value=st.session_state.monthly_budget.get(cat, 0.0))
            with col2:
                spent = sum(t["Amount (₹)"] for t in st.session_state.transactions if t["Category"] == cat and t["Type"] == "Expense")
                st.metric("Spent", f"₹{spent:,.0f}")
            st.session_state.monthly_budget[cat] = budget_val
        if st.button("Save Budget"):
            log_action("Updated monthly budget")
            st.success("Budget saved!")

    tab1, tab2, tab3 = st.tabs(["📒 Ledger", "📊 Analytics", "➕ Log Transaction"])

    with tab1:
        if st.session_state.transactions:
            df = pd.DataFrame(st.session_state.transactions)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No transactions yet. Use the CJ Agent or log one manually below.")

    with tab2:
        if st.session_state.transactions:
            df = pd.DataFrame(st.session_state.transactions)
            expenses_df = df[df["Type"] == "Expense"]
            if not expenses_df.empty:
                cat_summary = expenses_df.groupby("Category")["Amount (₹)"].sum().reset_index()
                st.subheader("Spending by Category")
                st.bar_chart(cat_summary.set_index("Category"))
                daily_copy = expenses_df.copy()
                daily_copy["Day"] = pd.to_datetime(daily_copy["Date"]).dt.date
                daily_sum = daily_copy.groupby("Day")["Amount (₹)"].sum().reset_index()
                st.subheader("Daily Spending Trend")
                st.line_chart(daily_sum.set_index("Day"))

                st.subheader("Budget vs Actual (Monthly)")
                budget_data = []
                for cat, budget in st.session_state.monthly_budget.items():
                    if budget > 0:
                        spent = sum(t["Amount (₹)"] for t in st.session_state.transactions if t["Category"] == cat and t["Type"] == "Expense")
                        budget_data.append({"Category": cat, "Budget": budget, "Spent": spent})
                if budget_data:
                    bdf = pd.DataFrame(budget_data)
                    st.dataframe(bdf, use_container_width=True)
            else:
                st.info("Log some expenses to see charts.")
        else:
            st.info("No data available yet.")

    with tab3:
        st.subheader("Manual Expense Entry")
        c1, c2 = st.columns(2)
        with c1:
            txn_type = st.selectbox("Type", ["Expense", "Income"])
            amount = st.number_input("Amount (₹)", min_value=1.0, step=10.0)
        with c2:
            category = st.selectbox("Category", ["Food", "Transport", "Groceries", "Shopping", "Stationery", "Personal Care", "Entertainment", "Bills", "Education", "Medical", "Other"])
            note = st.text_input("Note")
        if st.button("Log Transaction", type="primary", use_container_width=True):
            if process_transaction(txn_type, amount, category, note):
                st.success(f"✅ ₹{amount} logged as {txn_type}.")
                time.sleep(1); st.rerun()

# ==========================================
# HABIT TRACKER
# ==========================================
elif st.session_state.current_page == "🏋️ Habit Tracker":
    st.title("🏋️ Habit Tracker")
    
    # Update habit streaks daily
    today_str = date.today().strftime("%B %d, %Y")
    for habit in st.session_state.habits:
        if habit['active'] and habit['last_checkin'] != today_str:
            habit['streak'] = 0
    
    all_done = all(h['last_checkin'] == today_str for h in st.session_state.habits if h['active'])
    if all_done and any(h['active'] for h in st.session_state.habits):
        if st.session_state.last_streak_date != today_str:
            st.session_state.streak += 1
            st.session_state.last_streak_date = today_str
            log_action(f"Habit streak increased to {st.session_state.streak}")
    
    st.subheader("📋 Your Habits")
    col1, col2 = st.columns([3,1])
    with col1:
        st.write("Mark each habit as done today.")
    with col2:
        if st.button("➕ Add Habit"):
            st.session_state['show_add_habit'] = True
    
    if st.session_state.get('show_add_habit', False):
        with st.form("add_habit_form"):
            name = st.text_input("Habit name")
            emoji = st.text_input("Emoji (e.g., 🏋️)", value="⭐")
            if st.form_submit_button("Add"):
                if name:
                    new_habit = {
                        "id": str(uuid.uuid4()),
                        "name": name,
                        "emoji": emoji,
                        "streak": 0,
                        "last_checkin": None,
                        "active": True
                    }
                    st.session_state.habits.append(new_habit)
                    log_action(f"Added habit: {name}")
                    st.success("Habit added!")
                    st.session_state['show_add_habit'] = False
                    st.rerun()
                else:
                    st.warning("Name is required.")
    
    for i, habit in enumerate(st.session_state.habits):
        if not habit['active']:
            continue
        with st.container():
            cols = st.columns([0.5, 2, 1, 1, 0.5])
            with cols[0]:
                st.markdown(f"<span style='font-size:2rem;'>{habit['emoji']}</span>", unsafe_allow_html=True)
            with cols[1]:
                st.write(f"**{habit['name']}**")
                if habit['last_checkin'] == today_str:
                    st.caption("✅ Done today")
                else:
                    st.caption("⬜ Not done yet")
            with cols[2]:
                st.metric("Streak", habit['streak'])
            with cols[3]:
                if habit['last_checkin'] != today_str:
                    if st.button("✅", key=f"habit_done_{i}"):
                        habit['last_checkin'] = today_str
                        habit['streak'] += 1
                        all_done_now = all(h['last_checkin'] == today_str for h in st.session_state.habits if h['active'])
                        if all_done_now:
                            st.session_state.streak += 1
                            st.session_state.last_streak_date = today_str
                            log_action(f"All habits done, overall streak increased to {st.session_state.streak}")
                        log_action(f"Habit '{habit['name']}' done, streak {habit['streak']}")
                        st.rerun()
                else:
                    st.button("✅", key=f"habit_done_{i}", disabled=True)
            with cols[4]:
                if st.button("🗑️", key=f"habit_del_{i}"):
                    st.session_state.habits.pop(i)
                    log_action(f"Deleted habit: {habit['name']}")
                    st.rerun()
    
    st.markdown("---")
    st.metric("Overall Habit Streak", f"{st.session_state.streak} days", delta="🔥 Keep going!" if st.session_state.streak > 0 else "Start your streak today!")
    
    # To-Do List
    st.markdown("---")
    st.subheader("📝 To-Do List")
    with st.container():
        col1, col2, col3, col4 = st.columns([2,1,1,0.5])
        with col1:
            new_task = st.text_input("Task", key="habit_todo_task", placeholder="Write a task...")
        with col2:
            new_time = st.time_input("Time", key="habit_todo_time", value=datetime.now(ist).time())
        with col3:
            new_date = st.date_input("Date", key="habit_todo_date", value=date.today())
        with col4:
            if st.button("➕", key="habit_todo_add"):
                if new_task:
                    st.session_state.todos.append({
                        "task": new_task,
                        "done": False,
                        "created_date": date.today().isoformat(),
                        "description": "",
                        "time": new_time.strftime("%H:%M"),
                        "due_date": new_date.isoformat()
                    })
                    log_action(f"Added todo: {new_task}")
                    st.rerun()
    if st.session_state.todos:
        for i, todo in enumerate(st.session_state.todos):
            col1, col2, col3, col4 = st.columns([0.6, 0.15, 0.15, 0.1])
            with col1:
                if todo["done"]:
                    st.markdown(f"<div class='todo-item'><span class='task-done'>✅ {todo['task']}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='todo-item'><span class='task-pending'>⬜ {todo['task']}</span></div>", unsafe_allow_html=True)
                st.caption(f"Due: {todo.get('due_date', '')} at {todo.get('time', '')}")
            with col2:
                if st.button("Done", key=f"habit_todo_done_{i}"):
                    st.session_state.todos[i]["done"] = not todo["done"]
                    log_action(f"Toggled todo: {todo['task']}")
                    st.rerun()
            with col3:
                if st.button("✏️", key=f"habit_todo_edit_{i}"):
                    new_task_name = st.text_input("Edit task", value=todo['task'], key=f"edit_habit_{i}")
                    if new_task_name:
                        st.session_state.todos[i]['task'] = new_task_name
                        log_action(f"Edited todo to: {new_task_name}")
                        st.rerun()
            with col4:
                if st.button("❌", key=f"habit_todo_del_{i}"):
                    st.session_state.todos.pop(i)
                    log_action(f"Deleted todo: {todo['task']}")
                    st.rerun()
    else:
        st.caption("No tasks yet. Add one above!")

# ==========================================
# SUBJECT TRACKER
# ==========================================
elif st.session_state.current_page == "📚 Subject Tracker (Academic)":
    st.title("📚 Academic Command Centre")
    tab1, tab2 = st.tabs(["🏛️ Attendance Vault", "📖 Syllabus Modules"])
    
    with tab1:
        with st.expander("➕ Add/Edit Subjects"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Subject Name")
                new_total = st.number_input("Total Classes", min_value=1, value=30)
                new_attended = st.number_input("Attended", min_value=0, value=20)
                new_exam = st.date_input("Exam Date", value=date.today() + timedelta(days=30))
                if st.button("Add Subject"):
                    if new_name and new_name not in [s['name'] for s in st.session_state.subjects]:
                        st.session_state.subjects.append({"name": new_name, "total": new_total, "attended": new_attended, "exam_date": str(new_exam)})
                        st.session_state.modules[new_name] = []
                        log_action(f"Added subject: {new_name}")
                        st.success(f"Added {new_name}!")
                        st.rerun()
                    else:
                        st.warning("Subject already exists or name missing.")
            with col2:
                subject_names = [s['name'] for s in st.session_state.subjects]
                if subject_names:
                    del_subj = st.selectbox("Select subject to delete", subject_names)
                    if st.button("Delete Subject", type="primary"):
                        st.session_state.subjects = [s for s in st.session_state.subjects if s['name'] != del_subj]
                        if del_subj in st.session_state.modules:
                            del st.session_state.modules[del_subj]
                        log_action(f"Deleted subject: {del_subj}")
                        st.success(f"Deleted {del_subj}")
                        st.rerun()

        for i, subj in enumerate(st.session_state.subjects):
            pct, safe_or_needed, label, css_cls = get_attendance_status(subj["total"], subj["attended"])
            days_left = days_until(subj["exam_date"])
            exam_badge = f" <span class='exam-soon'>Exam in {days_left}d</span>" if days_left and days_left <= 14 else f" <span class='exam-ok'>Exam in {days_left}d</span>" if days_left else ""
            icon = "🔴" if label == "Danger" else "🟡" if label == "On Edge" else "🟢"
            
            with st.expander(f"{icon} {subj['name']} — {pct:.0f}%", expanded=(label != "Safe")):
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("Attendance", f"{subj['attended']}/{subj['total']}")
                with col2:
                    if label == "Danger": st.metric("Classes to Recover", f"{-safe_or_needed}", delta="⚠️ Below 75%", delta_color="inverse")
                    else: st.metric("Safe Skips Left", f"{safe_or_needed}")
                with col3: st.markdown(f"<span class='{css_cls}'>{label}</span>{exam_badge}", unsafe_allow_html=True)
                
                c1, c2, _ = st.columns(3)
                with c1:
                    if st.button("✅ Attended", key=f"att_{i}"):
                        st.session_state.subjects[i]["total"] += 1
                        st.session_state.subjects[i]["attended"] += 1
                        log_action(f"Marked attended for {subj['name']}")
                        st.rerun()
                with c2:
                    if st.button("❌ Missed", key=f"mis_{i}"):
                        st.session_state.subjects[i]["total"] += 1
                        log_action(f"Marked missed for {subj['name']}")
                        st.rerun()

    with tab2:
        subject_names = list(st.session_state.modules.keys())
        if subject_names:
            selected_subj = st.selectbox("Select Subject", subject_names)
            mods = st.session_state.modules[selected_subj]
            with st.expander("➕ Add Module"):
                new_mod = st.text_input("Module Name", key="new_mod_input")
                if st.button("Add Module"):
                    if new_mod:
                        st.session_state.modules[selected_subj].append({"name": new_mod, "done": False})
                        log_action(f"Added module '{new_mod}' to {selected_subj}")
                        st.success(f"Added: {new_mod}")
                        st.rerun()
            for j, mod in enumerate(mods):
                col1, col2 = st.columns([3, 1])
                with col1:
                    icon = "✅" if mod["done"] else "⬜"
                    cls = "module-done" if mod["done"] else "module-pending"
                    st.markdown(f"<div class='module-row'><span class='{cls}'>{icon} {mod['name']}</span></div>", unsafe_allow_html=True)
                with col2:
                    if st.button("Undo" if mod["done"] else "Mark Done", key=f"mod_{selected_subj}_{j}"):
                        st.session_state.modules[selected_subj][j]["done"] = not mod["done"]
                        log_action(f"Toggled module '{mod['name']}' in {selected_subj}")
                        st.rerun()
        else:
            st.info("Add a subject first.")

# ==========================================
# LOCATIONS
# ==========================================
elif st.session_state.current_page == "🗺️ Locations Unlocked":
    st.title("🗺️ Territories Explored")
    for idx, loc in enumerate(st.session_state.locations):
        name = loc.get('name', 'Unknown')
        desc = loc.get('description', '')
        date_added = loc.get('date', 'Unknown date')
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"""<div style="background-color:var(--card-bg);padding:15px;border-radius:12px;margin-bottom:10px;border-left:4px solid var(--accent);">
                <strong style="color:var(--heading);font-size:18px;">📍 {name}</strong>
                <div style="color:var(--label);font-size:12px;">{desc}</div>
                <div style="color:var(--label);font-size:12px;">Added on {date_added}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            if st.button("Delete", key=f"del_loc_{idx}"):
                st.session_state.locations.pop(idx)
                log_action(f"Deleted location: {name}")
                st.rerun()
    new_loc = st.text_input("Location name")
    new_desc = st.text_input("Description (optional)")
    if st.button("Log Discovery"):
        if new_loc and new_loc not in [loc['name'] for loc in st.session_state.locations]:
            st.session_state.locations.append({
                'name': new_loc,
                'description': new_desc,
                'date': date.today().strftime("%B %d, %Y")
            })
            log_action(f"Unlocked location: {new_loc}")
            st.success(f"Location Unlocked: {new_loc} on {date.today().strftime('%B %d, %Y')}!")
            time.sleep(1); st.rerun()
        elif new_loc:
            st.warning("Location already exists.")

# ==========================================
# CJ AGENT
# ==========================================
elif st.session_state.current_page == "🤖 CJ Agent":
    st.title("🤖 CJ Agent – Intelligent Expense Logger")
    st.write("Log expenses in **Tamil, English, or Tanglish**. CJ understands natural language and extracts amount, category, and payment method.")

    user_input = st.text_input(
        "What did you spend on?",
        placeholder="e.g., 'Inniku mess la 80 rupees saaptu cash kuduthen' or 'Spent 200 on cab via GPay'"
    )

    if st.button("Extract & Log", type="primary"):
        if user_input:
            with st.spinner("CJ is thinking..."):
                time.sleep(1.2)
                input_lower = user_input.lower()
                extracted_amt = 0.0
                cat = "Other"
                payment = "Unknown"

                # Amount
                amount_match = re.search(r'(\d+(?:\.\d+)?)', user_input)
                if amount_match:
                    extracted_amt = float(amount_match.group(1))

                # Enhanced category keywords
                categories = {
                    "Food": ["food", "saapadu", "sapadu", "saaptom", "mess", "zomato", "swiggy", "biryani", "dosa", "idly", "idli", "chai", "tea", "lunch", "dinner", "breakfast", "kadai", "hotel", "restaurant", "parotta", "rice", "noodles", "coffee", "juice", "snack", "tiffin", "saap", "soru", "meals", "pizza", "burger", "sandwich", "pasta", "ice cream", "cake", "biscuit", "chocolate"],
                    "Transport": ["cab", "auto", "uber", "ola", "bus", "train", "metro", "petrol", "fuel", "ticket", "travel", "ride", "bike", "poyirundhen", "porom", "station", "share", "van", "flight", "ship", "boat"],
                    "Groceries": ["grocery", "groceries", "vegetables", "fruits", "market", "supermarket", "provision", "milk", "bread", "keerai", "kai", "pazham", "egg", "meat", "chicken", "fish"],
                    "Shopping": ["shopping", "shirt", "dress", "clothes", "amazon", "flipkart", "shoes", "jeans", "bag", "online", "vesham", "pant", "watch", "belt", "hat", "sunglass"],
                    "Stationery": ["pen", "notebook", "book", "stationery", "xerox", "photocopy", "notes", "printout", "paper", "pencil", "eraser", "scale", "sharpener", "file", "folder"],
                    "Personal Care": ["haircut", "salon", "barber", "cream", "soap", "shampoo", "medicine", "tablet", "pharmacy", "health", "aathu", "cut", "shave", "makeup", "perfume", "deodorant"],
                    "Entertainment": ["movie", "cinema", "netflix", "amazon prime", "spotify", "concert", "party", "club", "game", "gaming"],
                    "Bills": ["electricity", "water", "gas", "internet", "phone", "recharge", "mobile", "wifi", "broadband", "rent", "maintenance"],
                    "Education": ["tuition", "coaching", "class", "course", "certification", "workshop", "seminar", "book", "library"],
                    "Medical": ["doctor", "hospital", "clinic", "medicine", "tablet", "syrup", "injection", "checkup", "dentist", "eye", "glasses"]
                }
                for category, keywords in categories.items():
                    if any(w in input_lower for w in keywords):
                        cat = category
                        break

                # Payment
                if any(w in input_lower for w in ["cash", "paisa", "kaiyila", "hand", "notes", "coin"]):
                    payment = "Cash"
                elif any(w in input_lower for w in ["upi", "gpay", "phonepe", "paytm", "online", "card", "neft", "transfer"]):
                    payment = "UPI/Card"

                confidence = 80 if extracted_amt > 0 else 0

                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Amount", f"₹{extracted_amt:,.0f}" if extracted_amt else "Not found")
                with col2:
                    st.metric("🏷️ Category", cat)
                with col3:
                    st.metric("💳 Payment", payment)

                st.progress(confidence/100)
                st.caption(f"Confidence: {confidence}%")

                if extracted_amt > 0:
                    note = f"[AI | {payment}] {user_input}"
                    if process_transaction("Expense", extracted_amt, cat, note):
                        log_action(f"CJ logged expense ₹{extracted_amt} - {cat}")
                        st.success(f"✅ ₹{extracted_amt:,.0f} logged under **{cat}** via {payment}.")
                        st.info("Transaction routed to ledger.")
                else:
                    st.error("⚠️ Could not detect an amount. Include a number like '150 rupees' or '₹200'.")
        else:
            st.warning("Type a sentence first.")

    st.markdown("---")
    st.subheader("📘 Example phrases")
    examples = [
        "Inniku mess la saaptu 80 rupees selavu aachu cash la",
        "Auto ku 60 rs kuduthen",
        "Zomato order 250 rupees GPay panna",
        "Bought notebook for 45 rupees cash",
        "Potheri kadaila groceries 320 rs",
        "Haircut 100 rupees cash",
        "Spent 180 on dinner at hotel",
        "Petrol 200 rupees pochu",
        "food 150",
        "bus ticket 50",
        "new pen 20",
        "electricity bill 500",
        "movie ticket 250",
    ]
    for ex in examples:
        st.code(ex)

# ==========================================
# ACTIVITY LOG
# ==========================================
elif st.session_state.current_page == "📋 Activity Log":
    st.title("📋 Activity Log")
    if not st.session_state.activity_log:
        st.info("No activity logged yet.")
    else:
        df = pd.DataFrame(st.session_state.activity_log)
        search = st.text_input("Search actions", placeholder="Type keyword...")
        if search:
            df = df[df['action'].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True, hide_index=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Log"):
                st.session_state.activity_log = []
                st.rerun()
        with col2:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=f"cjarvis_activity_{date.today()}.csv",
                mime="text/csv"
            )

# ==========================================
# USER GUIDE
# ==========================================
elif st.session_state.current_page == "📖 User Guide":
    st.title("📖 User Guide")
    st.markdown("""
    ### Welcome to Cjarvis Omni-Tracker

    **Cjarvis** is your personal discipline and tracking system. Below is a quick overview of each module.

    ---

    #### ⚡ Home Base
    - **Dashboard** – view wallet stats, habit streak, and a visible to‑do list.
    - **Weekly Grid** – track your daily habit completion. Auto‑resets every Monday.
    - **Daily Digest** – automatically generated each new day; hit "Regenerate" to refresh.
    - **Deadline Countdown** – see days remaining; add/edit in Settings.
    - **Quick‑Nav Cards** – one‑click access to all modules.

    ---

    #### 💰 Budget Tracker & Analytics
    - **Wallet Setup** – set opening balance, add income sources, and define monthly budgets per category.
    - **Ledger** – view all transactions with filters.
    - **Analytics** – spending by category, daily trends, budget vs actual.
    - **Manual Entry** – log expenses or income.

    ---

    #### 🏋️ Habit Tracker
    - **Track your daily habits** – mark each habit as done today.
    - **Streak** – each habit has its own streak; overall streak increases when all active habits are done.
    - **Add/Delete habits** – create your own habits with custom emojis.
    - **To-Do List** – syncs with the Home page to-do list.

    ---

    #### 📚 Subject Tracker (Academic)
    - **Attendance Vault** – track total/attended classes, safe skips, and exam countdown. Add/edit/delete subjects.
    - **Syllabus Modules** – mark topics as done to monitor progress.

    ---

    #### 🗺️ Locations Unlocked
    - Keep a list of places you've explored – each entry stores name, description, and date.

    ---

    #### 🤖 CJ Agent
    - Log expenses using natural language (Tamil, English, or Tanglish). CJ extracts amount, category, and payment method with an expanded keyword list.

    ---

    #### 📋 Activity Log
    - Chronological list of all actions – transactions, habit check‑ins, to‑do changes, etc. Search and export to CSV.

    ---

    #### ⚙️ Settings
    - **User Name** – customise your display name.
    - **Theme** – choose from Dark, Light, Blue, Purple, or Gradient.
    - **Banner** – upload your own image or use a URL.
    - **Dashboard Widgets** – toggle which widgets appear on the Home Base.
    - **Deadlines** – add/remove your own deadlines.
    - **GitHub Sync** – enter your GitHub token and Gist ID to save/load state across devices (see detailed instructions below).
    - **Data Management** – export/import settings (JSON) and reset all data.

    ---

    ### 🔐 How to Sync with GitHub

    1. **Get a GitHub Personal Access Token**  
       - Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens).  
       - Click **Generate new token (classic)**.  
       - Give it a name (e.g., "Cjarvis Sync").  
       - Select the **`gist`** scope.  
       - Click **Generate token** and **copy the token** – you won't see it again.

    2. **Create a Gist**  
       - Go to [Gist](https://gist.github.com/).  
       - Write a description (e.g., "Cjarvis state").  
       - In the filename, type `cjarvis_state.json`.  
       - Put some placeholder content like `{}`.  
       - Choose **Public** or **Secret** (recommended).  
       - Click **Create gist**.  
       - Copy the **Gist ID** from the URL: `https://gist.github.com/yourusername/`**`<GIST_ID>`** .

    3. **Enter Credentials in Cjarvis**  
       - In the sidebar, expand **"Sync with GitHub"**.  
       - Paste your token and Gist ID.  
       - Click **"Save Credentials & Load"** – this will pull any previously saved data.  
       - To push your current data, click **"Push to Gist"**.

    ---

    **Tips:**
    - Use the **Sidebar** to navigate and check your wallet.
    - The **overall habit streak** increments **only once per day** when all active habits are completed.
    - Weekly history auto‑resets every Monday.
    - **No financial penalties** – now it’s about your habits and streaks.
    - The dashboard shows motivational messages based on your streak.

    Stay disciplined. Stay focused. You are the 8%.
    """)

# ==========================================
# SETTINGS
# ==========================================
elif st.session_state.current_page == "⚙️ Settings":
    st.title("⚙️ Settings")

    st.subheader("👤 User Name")
    current_name = st.session_state.get('user_name', 'Monolith Agent')
    new_name = st.text_input("Your display name", value=current_name)
    if new_name != current_name:
        if st.button("Update Name"):
            st.session_state.user_name = new_name
            log_action(f"Updated user name to {new_name}")
            st.success("Name updated!")
            st.rerun()

    st.markdown("---")

    st.subheader("🎨 Theme")
    theme_options = ['dark', 'light', 'blue', 'purple', 'gradient']
    current_theme = st.session_state.get('theme', 'dark')
    selected_theme = st.selectbox("Choose a theme", theme_options, index=theme_options.index(current_theme))
    if selected_theme != current_theme:
        st.session_state.theme = selected_theme
        log_action(f"Theme changed to {selected_theme}")
        st.rerun()

    st.markdown("---")

    st.subheader("🖼️ Banner Image")
    st.write("Upload an image or provide a URL.")
    uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg', 'gif'])
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        st.session_state.custom_banner = bytes_data
        log_action("Uploaded custom banner")
        st.success("Banner uploaded!")
        st.rerun()
    else:
        url = st.text_input("Or enter image URL", value=st.session_state.custom_banner_url)
        if url != st.session_state.custom_banner_url:
            st.session_state.custom_banner_url = url
            st.session_state.custom_banner = None
            log_action(f"Updated banner URL to {url}")
            st.success("Banner URL updated!")
            st.rerun()
        if st.button("Clear Banner"):
            st.session_state.custom_banner = None
            st.session_state.custom_banner_url = ''
            log_action("Cleared banner")
            st.rerun()

    st.markdown("---")

    st.subheader("📊 Dashboard Widgets")
    widget_options = ["Balance", "Today's Spending", "Total Expenses", "Habit Streak", "To-Do List", "Daily Digest", "Recent Transactions", "Upcoming Deadlines", "Attendance Summary", "Mood"]
    current_widgets = st.session_state.dashboard_widgets
    new_widgets = st.multiselect(
        "Select widgets to show on Home Base",
        options=widget_options,
        default=[w for w in current_widgets if w in widget_options]
    )
    if set(new_widgets) != set(current_widgets):
        st.session_state.dashboard_widgets = new_widgets
        log_action(f"Updated dashboard widgets: {new_widgets}")
        st.success("Widgets updated!")
        st.rerun()

    st.markdown("---")

    st.subheader("⏱️ Manage Deadlines")
    deadlines = st.session_state.deadlines
    for i, d in enumerate(deadlines):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_name = st.text_input(f"Name {i+1}", value=d['name'], key=f"dl_name_{i}")
        with col2:
            new_date = st.date_input(f"Date {i+1}", value=datetime.strptime(d['date'], "%Y-%m-%d").date(), key=f"dl_date_{i}")
        with col3:
            if st.button("Delete", key=f"dl_del_{i}"):
                st.session_state.deadlines.pop(i)
                log_action(f"Deleted deadline: {d['name']}")
                st.rerun()
        if new_name != d['name'] or str(new_date) != d['date']:
            st.session_state.deadlines[i]['name'] = new_name
            st.session_state.deadlines[i]['date'] = str(new_date)
            log_action(f"Updated deadline: {new_name}")

    if st.button("Add New Deadline"):
        st.session_state.deadlines.append({"name": "New Deadline", "date": str(date.today() + timedelta(days=30))})
        log_action("Added new deadline")
        st.rerun()

    st.markdown("---")

    st.subheader("🔐 GitHub Sync Credentials")
    st.info("You can set your GitHub token and Gist ID in the sidebar under 'Sync with GitHub'.")
    if st.session_state.get('github_token'):
        st.success("✅ Credentials are set.")
    else:
        st.warning("⚠️ No credentials stored. Enter them in the sidebar.")
    if st.button("Clear Credentials"):
        st.session_state.github_token = ''
        st.session_state.gist_id = ''
        st.success("Credentials cleared.")
        st.rerun()

    st.markdown("---")

    st.subheader("💾 Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Settings (JSON)"):
            export_data = {k: st.session_state[k] for k in KEYS_TO_SYNC if k in st.session_state}
            json_str = json.dumps(export_data, indent=4)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"cjarvis_backup_{date.today()}.json",
                mime="application/json"
            )
    with col2:
        uploaded = st.file_uploader("Import JSON", type=['json'])
        if uploaded is not None:
            try:
                import_data = json.load(uploaded)
                for k, v in import_data.items():
                    if k in st.session_state:
                        st.session_state[k] = v
                log_action("Imported settings from JSON")
                st.success("Settings imported!")
                st.rerun()
            except:
                st.error("Invalid JSON file.")
    
    if st.button("⚠️ Reset All Data (Factory Reset)", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.clear()
        init_state()
        log_action("Factory reset performed")
        st.success("All data reset to default. Please refresh the page.")
        st.rerun()

    st.markdown("---")
    st.caption("All settings are stored locally in your browser session. Use GitHub Sync to persist across devices.")