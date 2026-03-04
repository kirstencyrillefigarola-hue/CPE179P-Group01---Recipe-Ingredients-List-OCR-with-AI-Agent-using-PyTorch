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

st.set_page_config(page_title="Recipe Agent", page_icon="🤖")

# --- 2. Load Models (Cached) ---
@st.cache_resource
def load_ocr():
    print("Loading EasyOCR...")
    return easyocr.Reader(['en'], gpu=False)

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=API_KEY)

# --- 3. Logic: Chat with the Recipe ---
def query_gemini(chat_history):
    """
    Sends the entire conversation history to Gemini so it remembers context.
    """
    client = get_gemini_client()
    # Convert session state history to Gemini format if needed, 
    # but for simple text, concatenating usually works well or using the chat method.
    
    # We will reconstruct the conversation context for the model
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

# --- 4. The UI ---
st.title("🤖 Conversational Recipe Agent")
st.markdown("Upload a recipe, then ask me to **translate** it or modify it!")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# File Uploader
uploaded_file = st.file_uploader("Upload Recipe Image", type=["png", "jpg", "jpeg", "webp"])

# --- Step 1: Process Image (Only if new file uploaded) ---
if uploaded_file:
    # We use a file_key to track if the image changed
    file_key = f"processed_{uploaded_file.name}"
    
    if file_key not in st.session_state:
        # A. Run EasyOCR
        with st.spinner("👀 Reading text with EasyOCR..."):
            reader = load_ocr()
            image = Image.open(uploaded_file)
            image_np = np.array(image)
            raw_text = " ".join(reader.readtext(image_np, detail=0))
        
        # B. Initial Prompt for Gemini
        initial_prompt = (
            f"Here is the raw text from a recipe image: '{raw_text}'. "
            "Please format this into a clean, readable recipe."
        )

        # C. Get Initial Recipe
        with st.spinner("🍳 Generating Recipe..."):
            client = get_gemini_client()
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=initial_prompt
            )
            recipe_text = response.text

        # D. Save to Chat History
        # We save the 'context' (raw text) invisibly or just start the chat with the result
        st.session_state.messages = [] # Clear old chat on new upload
        st.session_state.messages.append({"role": "user", "content": initial_prompt})
        st.session_state.messages.append({"role": "assistant", "content": recipe_text})
        
        # Mark as processed so we don't re-run on every click
        st.session_state[file_key] = True

# --- Step 2: Display Chat Interface ---
for message in st.session_state.messages:
    # Skip the raw OCR prompt in the display to keep it clean
    if "Here is the raw text" in message["content"]:
        continue
        
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Step 3: Handle User Inputs (Translation, etc.) ---
if prompt := st.chat_input("Ex: 'Translate to Spanish' or 'Convert to Metric'"):
    
    # 1. Show User Message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = query_gemini(st.session_state.messages)
            st.markdown(response_text)
            
    st.session_state.messages.append({"role": "assistant", "content": response_text})