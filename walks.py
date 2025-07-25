import datetime
import json
import os
from typing import List

import pandas as pd
import requests
import streamlit as st

# --- CONFIG ---
ROUTE_FILE = "route.json"
CURRENT_LOCATION_FILE = "current_location.json"
HOST_ID = "admin"
HOST_PASS = "123"
GEMINI_API_KEY = "AIzaSyDiOmJlfCz3i6TBYln0_EqkM1p_VFVrMyI"  # Replace with your Gemini API key
HF_TOKEN = "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"  # Replace with your Hugging Face token
GROQ_API_KEY = "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"  # Replace with your Groq API key
TOGETHER_API_KEY = "tgp_v1_PMi3Pvc3z0vlW-lM5eStXtXvO26VOHO31TOSO0xq3YRaU"  # Replace with your Together API key
UNSPLASH_ACCESS_KEY = "wTQeL98lH4lohWZkTw9Jdg4_ACKbZf7EVr_3pMvXvmk"  # Replace with your Unsplash Access Key

# --- MODEL CHOICE ---
MODEL_OPTIONS = ["Gemini (Google)", "Groq (Llama-3)", "Together (Mixtral-8x7B)"]

# --- INITIAL ROUTE DATA ---
DEFAULT_ROUTE = [
    "Swaminarayan Temple, Kalupur",
    "Kavi Dalpatram Chowk",
    "Lambeshwar Ni Pol",
    "Calico Dome",
    "Kala Ramji Mandir",
    "Shantinathji Mandir, Haja Patel Ni Pol",
    "Kuvavala Khancha, Doshivada Ni Pol",
    "Secret Passage, Shantinath Ni Pol",
    "Zaveri Vad",
    "Sambhavnath Ni Khadki",
    "Chaumukhji Ni Pol",
    "Astapadji Derasar",
    "Harkunvar Shethani Ni Haveli",
    "Dodiya Haveli",
    "Fernandez Bridge (Gandhi Road)",
    "Chandla Ol",
    "Muharat Pol",
    "Ahmedabad Stock Exchange",
    "Manek Chowk",
    "Rani-no-Haziro",
    "Badshah-no-Haziro",
    "Jami Masjid"
]

# --- HELPERS ---
def load_route() -> List[str]:
    if not os.path.exists(ROUTE_FILE):
        with open(ROUTE_FILE, "w") as f:
            json.dump(DEFAULT_ROUTE, f)
    with open(ROUTE_FILE, "r") as f:
        return json.load(f)

def save_route(route: List[str]):
    with open(ROUTE_FILE, "w") as f:
        json.dump(route, f)

def load_current_location() -> str:
    if not os.path.exists(CURRENT_LOCATION_FILE):
        with open(CURRENT_LOCATION_FILE, "w") as f:
            json.dump("", f)
    with open(CURRENT_LOCATION_FILE, "r") as f:
        return json.load(f)

def save_current_location(location: str):
    with open(CURRENT_LOCATION_FILE, "w") as f:
        json.dump(location, f)

def load_previous_location() -> str:
    if os.path.exists("previous_location.json"):
        with open("previous_location.json", "r") as f:
            return json.load(f)
    return ""

def save_previous_location(location: str):
    with open("previous_location.json", "w") as f:
        json.dump(location, f)

def load_previous_locations() -> list:
    if os.path.exists("previous_locations.json"):
        with open("previous_locations.json", "r") as f:
            return json.load(f)
    return []

def save_previous_locations(locations: list):
    with open("previous_locations.json", "w") as f:
        json.dump(locations, f)

def gemini_chat(prompt: str) -> str:
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {"key": GEMINI_API_KEY}
    try:
        response = requests.post(url, headers=headers, params=params, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            try:
                error_msg = response.json().get('error', {}).get('message', str(response.text))
            except Exception:
                error_msg = response.text
            return f"Gemini API Error: {error_msg} (Status code: {response.status_code})"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def groq_chat(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Groq API Error: {response.text} (Status code: {response.status_code})"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def together_chat(prompt: str) -> str:
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Together API Error: {response.text} (Status code: {response.status_code})"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def get_ai_response(prompt: str, model_choice: str) -> str:
    if model_choice == "Gemini (Google)":
        return gemini_chat(prompt)
    elif model_choice == "Groq (Llama-3)":
        return groq_chat(prompt)
    else:
        return together_chat(prompt)

@st.cache_data(show_spinner=False)
def get_site_info(site: str, model_choice: str) -> str:
    prompt = f"Give a short, engaging, and informative description (max 80 words) about the heritage site: {site} in Ahmedabad."
    info = get_ai_response(prompt, model_choice)
    if info.startswith("Gemini API Error") or info.startswith("Groq API Error") or info.startswith("Together API Error") or info.startswith("Exception occurred"):
        st.warning(info)
    return info

def get_unsplash_image(query):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": 1
    }
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        if data.get("results"):
            return data["results"][0]["urls"]["regular"]
    except Exception:
        pass
    return "https://placehold.co/400x200?text=No+Image"

# --- DATA FOR IMAGES, AND TRIVIA (STOP_COORDS removed) ---
STOP_IMAGES = {
    stop: f"https://placehold.co/400x200?text={stop.replace(' ', '+')}" for stop in DEFAULT_ROUTE
}
STOP_TRIVIA = {
    "Swaminarayan Temple, Kalupur": ("In which year was the Swaminarayan Temple built?", "1822"),
    "Kavi Dalpatram Chowk": ("Who was Kavi Dalpatram?", "Poet"),
    "Lambeshwar Ni Pol": ("What is a 'Pol' in Ahmedabad?", "Traditional housing cluster"),
    "Calico Dome": ("What was the Calico Dome famous for?", "Textiles"),
    # ... add more trivia for other stops as needed ...
}

# --- TIMER HELPERS ---
START_TIME_FILE = "walk_start_time.json"
def load_start_time():
    if os.path.exists(START_TIME_FILE):
        with open(START_TIME_FILE, "r") as f:
            return json.load(f)
    return None

def save_start_time(start_time):
    with open(START_TIME_FILE, "w") as f:
        json.dump(start_time, f)

# --- MAP (REMOVED) ---
# The render_walk_map function and related imports are removed.

# --- TIMER DISPLAY ---
def display_timer():
    start_time = load_start_time()
    if start_time:
        start_dt = datetime.datetime.fromisoformat(start_time)
        elapsed = datetime.datetime.now() - start_dt
        st.info(f"⏱️ Walk started at {start_dt.strftime('%H:%M:%S')}. Elapsed: {str(elapsed).split('.')[0]}")
    else:
        st.info("⏱️ Walk not started yet.")

# --- MAIN APP ---
st.set_page_config(page_title="Ahmedabad Heritage Walk", layout="wide")
st.markdown("""
    <style>
    .current-location {
        background-color: #ffe082;
        border-radius: 8px;
        padding: 8px;
        font-weight: bold;
        color: #6d4c00;
    }
    .previous-location {
        background-color: #b3e5fc;
        border-radius: 8px;
        padding: 8px;
        font-weight: bold;
        color: #01579b;
    }
    .locked-info {
        color: #bdbdbd;
        font-style: italic;
        font-size: 0.95em;
    }
    .heritage-stop {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 8px;
        padding: 8px;
        background: #fafafa;
    }
    .chat-bubble-user {
        background: #e3f2fd;
        border-radius: 12px;
        padding: 8px 12px;
        margin-bottom: 4px;
        text-align: right;
    }
    .chat-bubble-bot {
        background: #fffde7;
        border-radius: 12px;
        padding: 8px 12px;
        margin-bottom: 8px;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ Ahmedabad Heritage Walk")
st.markdown("---")

# --- LEGEND ---
with st.expander("Legend / Info", expanded=False):
    st.markdown("""
    <span class='current-location'>Current Location</span>  
    <span class='previous-location'>Previous Location</span>  
    <span class='locked-info'>🔒 Info locked until you reach this stop</span>
    """, unsafe_allow_html=True)

# --- SIDEBAR: LOGIN & CURRENT LOCATION ---
st.sidebar.header("Login")
user_type = st.sidebar.radio("I am a...", ["Client", "Host (Admin)"])

# --- SIDEBAR: MODEL CHOICE ---
st.sidebar.markdown("---")
st.sidebar.subheader("AI Model")
model_choice = st.sidebar.selectbox("Choose AI Model", MODEL_OPTIONS, index=0)

current_location = load_current_location()
previous_locations = load_previous_locations()

if user_type == "Host (Admin)":
    host_id = st.sidebar.text_input("Host ID")
    host_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if host_id == HOST_ID and host_pass == HOST_PASS:
            st.session_state["is_admin"] = True
        else:
            st.sidebar.error("Invalid credentials")
    if st.session_state.get("is_admin"):
        st.success("Logged in as Host/Admin")
        st.sidebar.markdown(f"**Current Location:**\n\n<span class='current-location'>{current_location or 'Not set'}</span>", unsafe_allow_html=True)
        st.sidebar.markdown("**Previous Locations:**", unsafe_allow_html=True)
        if previous_locations:
            for loc in previous_locations:
                st.sidebar.markdown(f"<span class='previous-location'>{loc}</span>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown("<span class='previous-location'>None</span>", unsafe_allow_html=True)
        st.subheader("Edit Heritage Walk Route")
        # --- FIX: Changed st.experimental_data_editor to st.data_editor ---
        route = load_route()
        edited_route = st.data_editor(route, num_rows="dynamic", key="route_editor")
        if st.button("Save Route"):
            save_route(edited_route)
            st.success("Route updated! All clients will see the changes.")
        st.write("Current Route:")
        for i, stop in enumerate(route, 1):
            col1, col2 = st.columns([8,2])
            with col1:
                is_current = (stop == current_location)
                is_previous = (stop in previous_locations)
                style = "current-location" if is_current else ("previous-location" if is_previous else "")
                label = " (Current Location)" if is_current else (" (Previous Location)" if is_previous else "")
                st.markdown(f"<span class='{style}'><b>{i}. {stop}</b>{label}</span>" if style else f"{i}. {stop}", unsafe_allow_html=True)
            with col2:
                if st.button("Set as Current", key=f"set_{i}"):
                    if stop != current_location and current_location:
                        prevs = load_previous_locations()
                        if current_location not in prevs:
                            prevs.append(current_location)
                            save_previous_locations(prevs)
                    save_current_location(stop)
                    st.session_state["current_location"] = stop
                    st.rerun()
else:
    st.sidebar.markdown(f"**Current Location:**\n\n<span class='current-location'>{current_location or 'Not set'}</span>", unsafe_allow_html=True)
    st.sidebar.markdown("**Previous Locations:**", unsafe_allow_html=True)
    if previous_locations:
        for loc in previous_locations:
            st.sidebar.markdown(f"<span class='previous-location'>{loc}</span>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<span class='previous-location'>None</span>", unsafe_allow_html=True)
    st.subheader("Heritage Walk Route")
    route = load_route()
    for i, stop in enumerate(route, 1):
        is_current = (stop == current_location)
        is_previous = (stop in previous_locations)
        style = "current-location" if is_current else ("previous-location" if is_previous else "")
        label = " (Current Location)" if is_current else (" (Previous Location)" if is_previous else "")
        with st.container():
            st.markdown(f"<div class='heritage-stop'><span class='{style}'><b>{i}. {stop}</b>{label}</span></div>" if style else f"<div class='heritage-stop'>{i}. <b>{stop}</b></div>", unsafe_allow_html=True)
            if is_current or is_previous:
                with st.expander("Show info about this site"):
                    # Show image
                    unsplash_img = get_unsplash_image(f"{stop} Ahmedabad")
                    st.image(unsplash_img, use_column_width=True)
                    with st.spinner("Fetching info..."):
                        info = get_site_info(stop, model_choice)
                    st.markdown(info)
                    # Trivia/Quiz
                    q_and_a = STOP_TRIVIA.get(stop)
                    if q_and_a:
                        question, correct_answer = q_and_a
                        st.markdown(f"**Trivia:** {question}")
                        user_key = f"trivia_{stop}".replace(" ", "_")
                        user_answer = st.text_input("Your answer:", key=user_key)
                        if st.button("Submit", key=f"submit_{user_key}"):
                            if "trivia_answers" not in st.session_state:
                                st.session_state["trivia_answers"] = {}
                            st.session_state["trivia_answers"][user_key] = user_answer
                        # Show feedback
                        if "trivia_answers" in st.session_state and user_key in st.session_state["trivia_answers"]:
                            given = st.session_state["trivia_answers"][user_key]
                            if given.strip().lower() == correct_answer.strip().lower():
                                st.success("Correct!")
                            else:
                                st.error(f"Wrong! Correct answer: {correct_answer}")
            else:
                st.markdown("<span class='locked-info'>🔒 Info locked until you reach this stop</span>", unsafe_allow_html=True)

    # --- ADMIN: Show all trivia answers ---
    if user_type == "Host (Admin)" and st.session_state.get("is_admin"):
        st.markdown("---")
        st.subheader("Trivia Answers (All Users)")
        if "trivia_answers" in st.session_state:
            for key, ans in st.session_state["trivia_answers"].items():
                stop_name = key.replace("trivia_", "").replace("_", " ")
                q_and_a = STOP_TRIVIA.get(stop_name)
                if q_and_a:
                    _, correct_answer = q_and_a
                    correct = ans.strip().lower() == correct_answer.strip().lower()
                    st.markdown(f"**{stop_name}:** {ans} - {'✅' if correct else '❌'} (Correct: {correct_answer})")
        else:
            st.info("No trivia answers submitted yet.")

    st.markdown("---")
    st.subheader("Ask about the Heritage Walk (Chatbot)")
    st.markdown("<i>Chatbot will answer only about the current or previous location, or general walk info.</i>", unsafe_allow_html=True)
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    user_query = st.text_input("Type your question here", key="chat_input")
    if st.button("Ask", key="ask_btn") and user_query:
        # Add context about the walk and restrict to current/previous location
        context = f"Ahmedabad Heritage Walk route: {', '.join(route)}. "
        if current_location:
            context += f"Current location: {current_location}. "
        if previous_locations:
            context += f"Previous locations: {', '.join(previous_locations)}. "
        prompt = context + "User question: " + user_query
        with st.spinner("Thinking..."):
            answer = get_ai_response(prompt, model_choice)
        st.session_state["chat_history"].append((user_query, answer))
    # Display chat history
    for q, a in st.session_state["chat_history"][-10:]:
        st.markdown(f"<div class='chat-bubble-user'>{q}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bubble-bot'>{a}</div>", unsafe_allow_html=True)

    st.info("You can ask about the current or previous stop, or general info about Ahmedabad's heritage walk.")

display_timer()

# --- HOST: START WALK BUTTON ---
if user_type == "Host (Admin)" and st.session_state.get("is_admin"):
    if not load_start_time():
        if st.button("Start Walk 🏁"):
            now = datetime.datetime.now().isoformat()
            save_start_time(now)
            st.rerun()

st.caption("Made with ❤️ of Team Neev India")
