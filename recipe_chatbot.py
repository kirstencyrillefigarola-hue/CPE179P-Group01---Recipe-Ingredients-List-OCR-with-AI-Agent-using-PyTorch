import streamlit as st
import easyocr
import os
import numpy as np
from PIL import Image
from google import genai
from dotenv import load_dotenv

# --- 1. Configuration ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Recipe Agent", page_icon="🍳", layout="wide")

# --- 2. Load Models (Cached) ---
@st.cache_resource
def load_ocr():
    # Loads once and stays in memory
    print("Loading EasyOCR...")
    return easyocr.Reader(['en'], gpu=False)

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=API_KEY)

# --- 3. Chat Logic ---
def query_gemini(chat_history):
    """
    Sends the conversation to Gemini for translation/modification.
    """
    client = get_gemini_client()
    
    # Build a simple prompt history
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

# --- 4. Main Interface ---
st.title("🍳 Recipe Agent: Scan, Clean & Translate")
st.markdown("Upload a recipe image to see the raw text, the cleaned version, and then translate it!")

# Initialize Chat History if empty
if "messages" not in st.session_state:
    st.session_state.messages = []

# File Uploader
uploaded_file = st.file_uploader("Upload Recipe Image", type=["png", "jpg", "jpeg", "webp"])

# --- Step 1: Processing (Only runs if a file is uploaded) ---
if uploaded_file:
    # Use a unique key for the file to prevent re-running on every interaction
    file_key = f"proc_{uploaded_file.name}"
    
    # Create 2 columns for the Top Section
    col1, col2 = st.columns([1, 1])

    # --- Display 1: The Image ---
    with col1:
        st.subheader("1. Original Image")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

    # --- Run OCR & Generation (Only if new file) ---
    if file_key not in st.session_state:
        with st.spinner("👀 Reading text with EasyOCR..."):
            reader = load_ocr()
            image_np = np.array(image)
            raw_text_result = reader.readtext(image_np, detail=0)
            raw_text = " ".join(raw_text_result)
            
            # Save raw text to session state
            st.session_state[f"raw_{file_key}"] = raw_text

        with st.spinner("✨ Formatting with Gemini..."):
            initial_prompt = (
                f"Here is the raw text from a recipe image: '{raw_text}'. "
                "Please format this into a clean, structured recipe with a Title, Ingredients, and Instructions."
            )
            
            client = get_gemini_client()
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=initial_prompt
            )
            recipe_text = response.text
            
            # Save recipe to session state
            st.session_state[f"recipe_{file_key}"] = recipe_text
            
            # Reset Chat and add the recipe as the starting point
            st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": initial_prompt})
            st.session_state.messages.append({"role": "assistant", "content": recipe_text})
            
            # Mark file as processed
            st.session_state[file_key] = True

    # --- Display 2: Raw OCR Text ---
    with col2:
        st.subheader("2. Extracted Text (EasyOCR)")
        # Retrieve the text from session state
        saved_raw_text = st.session_state.get(f"raw_{file_key}", "Processing...")
        st.text_area("Raw Output", saved_raw_text, height=300)

    # --- Display 3: The Cleaned Recipe (Chat View) ---
    st.divider()
    st.subheader("3. Final Recipe & Translation")

    # Display the conversation history (starts with the Recipe)
    for i, message in enumerate(st.session_state.messages):
        # Hide the system prompt (the raw text prompt) from the chat view for cleanliness
        if "Here is the raw text" in message["content"]:
            continue
            
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Step 4: Chat Input (For Translation) ---
    if prompt := st.chat_input("Ask me to translate this (e.g., 'Translate to Spanish')"):
        
        # Add user message to state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_text = query_gemini(st.session_state.messages)
                st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})