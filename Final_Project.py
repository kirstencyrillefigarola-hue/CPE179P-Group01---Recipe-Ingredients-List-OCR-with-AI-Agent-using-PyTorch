import streamlit as st
import easyocr
import os
import numpy as np
import json
import uuid
import sqlite3
import io
import speech_recognition as sr
from gtts import gTTS
from langdetect import detect 
from PIL import Image
from google import genai
from dotenv import load_dotenv

# --- 1. Configuration & DB Setup ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Recipe Agent Pro", page_icon="🍳", layout="wide")

# --- NEW: Fixed CSS for Perfect Alignment & Sizing ---
hide_st_style = """
            <style>
            /* Hides the top right menu and Deploy button */
            [data-testid="stToolbar"] {visibility: hidden !important;}
            /* Hides the default Streamlit footer */
            footer {visibility: hidden !important;}
            
            /* --- Force exact same height for all 3 inputs --- */
            
            /* 1. Target the actual gray background box of the text input */
            div[data-testid="stTextInput"] div[data-baseweb="input"] {
                height: 46px !important;
                border-radius: 8px !important;
            }
            
            /* Ensure the text is centered vertically inside the new taller box */
            div[data-testid="stTextInput"] input {
                line-height: 46px !important;
            }
            
            /* 2. Lock the Audio widget height */
            div[data-testid="stAudioInput"] {
                height: 46px !important;
            }
            
            /* 3. Make the Submit button match the exact same height */
            div[data-testid="stFormSubmitButton"] button {
                height: 46px !important;
                border-radius: 8px !important;
                padding-top: 0px !important;
                padding-bottom: 0px !important;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect("recipe_agent.db")
    c = conn.cursor()
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    # Create Chat History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipe_chats (
            session_id TEXT PRIMARY KEY,
            username TEXT,
            title TEXT,
            messages TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Run this once when the script loads
init_db()

# Helper to get a fresh DB connection per operation
def get_db_connection():
    return sqlite3.connect("recipe_agent.db")

# --- 2. Load Models (Cached) ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=API_KEY)

# --- 3. Helper Functions ---
def query_gemini(chat_history):
    client = get_gemini_client()
    full_prompt = "You are a helpful Recipe Assistant. \n\n"
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "Model"
        full_prompt += f"{role}: {msg['content']}\n"
    full_prompt += "Model: "

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

def save_chat_to_db():
    """Saves the current session state messages to SQLite ONLY if logged in."""
    if st.session_state.get("username") and st.session_state.get("session_id") and st.session_state.get("messages"):
        chat_json = json.dumps(st.session_state.messages)
        title = st.session_state.get("chat_title", "New Recipe Chat")
        
        conn = get_db_connection()
        c = conn.cursor()
        # Insert new chat or update existing one based on session_id
        c.execute('''
            INSERT INTO recipe_chats (session_id, username, title, messages)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET 
                messages=excluded.messages,
                title=excluded.title
        ''', (st.session_state.session_id, st.session_state.username, title, chat_json))
        
        conn.commit()
        conn.close()

# --- 4. Pop-up Dialogs (Modals) ---
@st.dialog("Log in")
def show_login_dialog():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Submit"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        
        if result:
            if result[0] == password:
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Incorrect password.")
        else:
            st.error("User not found.")

@st.dialog("Sign up")
def show_signup_dialog():
    st.write("Create an account to save your recipes.")
    username = st.text_input("Choose Username")
    password = st.text_input("Choose Password", type="password")
    if st.button("Create Account"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            st.error("Username already exists. Please choose another.")
            conn.close()
        else:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            st.session_state.username = username
            st.success("Account created successfully!")
            st.rerun()

# --- 5. Session Initialization ---
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_title" not in st.session_state:
    st.session_state.chat_title = "New Recipe Chat"

# --- 6. Top Bar (Login / Signup Buttons) ---
if not st.session_state.username:
    col1, col2, col3 = st.columns([8, 1, 1])
    with col2:
        if st.button("Log in", width="stretch"):
            show_login_dialog()
    with col3:
        if st.button("Sign up", width="stretch"):
            show_signup_dialog()
else:
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("Sign out", width="stretch"):
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()

# --- 7. Sidebar (History vs Guest Prompt) ---
if not st.session_state.username:
    st.sidebar.title("Recipe Agent")
    st.sidebar.markdown("### Get responses tailored to you")
    st.sidebar.markdown("Log in to get answers based on saved chats, plus save your translated recipes.")
    if st.sidebar.button("Log in", key="sidebar_login", width="stretch"):
        show_login_dialog()
    if st.sidebar.button("Sign up", key="sidebar_signup", width="stretch"):
        show_signup_dialog()
else:
    st.sidebar.title(f"Hi {st.session_state.username} ✨")
    if st.sidebar.button("➕ New Recipe Chat", width="stretch"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_title = "New Recipe Chat"
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Your Saved Recipes")
    
    # Fetch user's chat history from SQLite
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT session_id, title, messages FROM recipe_chats WHERE username = ?", (st.session_state.username,))
    saved_chats = c.fetchall()
    conn.close()

    if saved_chats:
        for chat_id, title, messages_json in saved_chats:
            if st.sidebar.button(f"💬 {title}", key=f"btn_{chat_id}", width="stretch"):
                st.session_state.session_id = chat_id
                st.session_state.chat_title = title
                st.session_state.messages = json.loads(messages_json)
                st.rerun()

# --- 8. Main Interface ---
st.title("🍳 Recipe Agent: Scan, Clean & Translate")

# Just the file uploader at the top
uploaded_file = st.file_uploader("Upload Recipe Image", type=["png", "jpg", "jpeg", "webp"])

# Process Uploaded Image
if uploaded_file:
    file_key = f"proc_{uploaded_file.name}_{st.session_state.session_id}"
    col_img, col_text = st.columns([1, 1])

    with col_img:
        st.subheader("1. Original Image")
        image = Image.open(uploaded_file)
        st.image(image, width="stretch")

    if file_key not in st.session_state:
        with st.spinner("👀 Reading text with EasyOCR..."):
            reader = load_ocr()
            image_np = np.array(image)
            raw_text_result = reader.readtext(image_np, detail=0)
            raw_text = " ".join(raw_text_result)
            st.session_state[f"raw_{file_key}"] = raw_text

        with st.spinner("✨ Formatting with Gemini..."):
            initial_prompt = (
                f"Here is the raw text from a recipe image: '{raw_text}'. "
                "Please format this into a clean, structured recipe with a Title, Ingredients, and Instructions. "
                "IMPORTANT: Do not include any introductory text or conversational filler. Start the very first line with the recipe Title."
            )
            
            client = get_gemini_client()
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=initial_prompt
            )
            recipe_text = response.text
            
            # Extract the actual recipe name from Gemini's response smartly
            lines = [line.strip() for line in recipe_text.split('\n') if line.strip()]
            actual_title = "Unknown Recipe"
            
            for line in lines:
                clean_line = line.replace('#', '').replace('*', '').strip()
                if "here is" in clean_line.lower() or "formatted" in clean_line.lower() or "sure" in clean_line.lower():
                    continue
                if clean_line:
                    actual_title = clean_line
                    break 
            
            if len(actual_title) > 30:
                actual_title = actual_title[:27] + "..."
            
            st.session_state.chat_title = actual_title
            st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": initial_prompt})
            st.session_state.messages.append({"role": "assistant", "content": recipe_text})
            
            save_chat_to_db()
            st.session_state[file_key] = True

    with col_text:
        st.subheader("2. Extracted Text (EasyOCR)")
        saved_raw_text = st.session_state.get(f"raw_{file_key}", "Processing...")
        st.text_area("Raw Output", saved_raw_text, height=300)

# --- 9. Chat & Output Interface ---
if uploaded_file or len(st.session_state.messages) > 0:
    st.divider()
    st.subheader("3. Final Recipe & Translation")

    # We use a container here so that new messages appear ABOVE the form input
    chat_container = st.container()

    # Render existing chat history in the container
    with chat_container:
        for message in st.session_state.messages:
            if "Here is the raw text" in message["content"]:
                continue
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    st.write("---")
    
    # --- Custom Input Area (Form) ---
    with st.form("chat_input_form", clear_on_submit=True, border=False):
        # vertical_alignment is "center" to keep them aligned
        col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment="center")
        
        with col1:
            text_prompt = st.text_input("Ask Recipe Agent:", label_visibility="collapsed", placeholder="Ask Recipe Agent...")
        
        with col2:
            audio_value = st.audio_input("Voice", label_visibility="collapsed")
            
        with col3:
            submit_btn = st.form_submit_button("Send 🚀", width="stretch")

    # Handle the submission ONLY when the Send button is clicked
    if submit_btn:
        prompt = None 
        
        # Check if they recorded audio first
        if audio_value is not None:
            with chat_container: 
                with st.spinner("Listening to audio..."):
                    r = sr.Recognizer()
                    with sr.AudioFile(audio_value) as source:
                        audio_data = r.record(source)
                        try:
                            prompt = r.recognize_google(audio_data)
                        except sr.UnknownValueError:
                            st.error("Sorry, I couldn't catch that.")
                        except sr.RequestError:
                            st.error("Speech recognition error.")
        # If no audio, grab the text
        elif text_prompt:
            prompt = text_prompt

        # Process the prompt
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response_text = query_gemini(st.session_state.messages)
                        st.markdown(response_text)
                        
                        # --- Language Detection & Text-to-Speech Output ---
                        try:
                            try:
                                detected_lang = detect(response_text)
                            except Exception:
                                detected_lang = 'en'
                                
                            tts = gTTS(text=response_text, lang=detected_lang) 
                            audio_fp = io.BytesIO()
                            tts.write_to_fp(audio_fp)
                            audio_fp.seek(0)
                            
                            st.audio(audio_fp, format='audio/mp3', autoplay=True)
                        except Exception as e:
                            st.error(f"Could not generate audio: {e}")
            
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            save_chat_to_db()