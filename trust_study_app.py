import streamlit as st
import random
import datetime
from streamlit_autorefresh import st_autorefresh
from hashlib import sha256

# --- Basic Authentication ---
users = {
    "admin": sha256("password123".encode()).hexdigest(),
    "researcher": sha256("truststudy".encode()).hexdigest()
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title(" Login Required")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in users and sha256(password.encode()).hexdigest() == users[username]:
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    st.stop()

# --- Auto Refresh Every 30 Seconds ---
st_autorefresh(interval=30 * 1000, key="auto_refresh")

# --- Page Setup ---
st.set_page_config(page_title="Care Home Simulator", layout="wide")

# --- CSS for Rooms and Flashing Alerts ---
st.markdown("""
    <style>
    .room {
        border: 3px solid #1e88e5;
        border-radius: 12px;
        padding: 12px;
        background-color: #e3f2fd;
        min-height: 150px;
        text-align: center;
        font-size: 16px;
    }
    .alert-room {
        border: 3px solid #e53935 !important;
        background-color: #ffebee !important;
    }
    .room-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Init Session State ---
if "budget" not in st.session_state:
    st.session_state.budget = 50
if "trust" not in st.session_state:
    st.session_state.trust = 75  # percentage
if "logs" not in st.session_state:
    st.session_state.logs = []
if "robots" not in st.session_state:
    st.session_state.robots = {"Room 1": False, "Room 2": True, "Room 3": False, "Kitchen": False, "Hall": True}
if "emergency_room" not in st.session_state:
    st.session_state.emergency_room = None
if "emergency_active" not in st.session_state:
    st.session_state.emergency_active = False

# --- Auto-trigger Emergency Every 30s if None Active ---
if not st.session_state.emergency_active:
    st.session_state.emergency_room = random.choice(list(st.session_state.robots.keys()))
    st.session_state.emergency_active = True

# --- Control Panel ---
with st.sidebar:
    st.title(" Command Center")
    st.metric(" Budget", f"£{st.session_state.budget}")
    st.progress(st.session_state.trust / 100.0, text=f" Trust: {st.session_state.trust}%")

    if st.button("⚠ Trigger Random Emergency"):
        st.session_state.emergency_room = random.choice(list(st.session_state.robots.keys()))
        st.session_state.emergency_active = True

# --- Room Layout ---
st.markdown("### 🏠 Care Home Floorplan")
rooms = ["Room 1", "Room 2", "Room 3", "Kitchen", "Hall", "Command Center"]
cols = st.columns(3)

def render_room(name, col):
    robot_here = st.session_state.robots.get(name, False)
    is_emergency = (st.session_state.emergency_room == name and st.session_state.emergency_active)
    box_class = "room alert-room" if is_emergency else "room"

    col.markdown(f'<div class="{box_class}">', unsafe_allow_html=True)
    col.markdown(f'<div class="room-title">{name}</div>', unsafe_allow_html=True)
    if robot_here:
        col.markdown(" Robot present")
    if name == "Command Center":
        col.button(" Send Report", key="cmd_report")
    else:
        col.button(f"Complete Task in {name}", key=f"task_{name}")
    col.markdown('</div>', unsafe_allow_html=True)

# --- Render Grid ---
for i in range(3):
    render_room(rooms[i], cols[i])
cols2 = st.columns(3)
for i in range(3, 6):
    render_room(rooms[i], cols2[i - 3])

# --- Emergency Response ---
if st.session_state.emergency_active:
    st.markdown(f"###  Emergency in **{st.session_state.emergency_room}**")
    options = [
        "Do nothing",
        f"Send Robot to {st.session_state.emergency_room} (-£2)",
        f"Send Human to {st.session_state.emergency_room} (-£5)",
        f"Check via camera/audio (-£1)"
    ]
    choice = st.radio("Choose your action:", options, key="emergency_radio")
    if st.button("🔍 Respond"):
        cost_map = {
            options[0]: 0,
            options[1]: 2,
            options[2]: 5,
            options[3]: 1
        }
        cost = cost_map[choice]
        st.session_state.budget -= cost
        st.session_state.logs.append({
            "time": datetime.datetime.now().isoformat(),
            "event": f"Emergency in {st.session_state.emergency_room}",
            "response": choice,
            "cost": cost,
            "budget_remaining": st.session_state.budget
        })
        st.session_state.emergency_active = False
        if "Send Robot" in choice:
            st.session_state.trust = max(st.session_state.trust - 3, 0)
        elif "Send Human" in choice:
            st.session_state.trust = min(st.session_state.trust + 2, 100)

# --- Logs ---
st.markdown("### 📋 Action Log")
for log in st.session_state.logs[::-1]:
    st.write(f"{log['time']} — {log['event']} | {log['response']} | Cost: £{log['cost']} | Remaining: £{log['budget_remaining']}")
