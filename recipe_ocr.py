import os
import time
import easyocr
from google import genai
from google.genai import errors
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Check if key loaded correctly
if not API_KEY:
    print("Error: API Key not found. Check your .env file.")
    exit()

def test_ocr(image_name="download.png"):
    print(f"\n--- 1. Testing EasyOCR (Local) on '{image_name}' ---")
    
    if not os.path.exists(image_name):
        print(f"Error: '{image_name}' not found.")
        return None

    try:
        print("Loading OCR Model...")
        reader = easyocr.Reader(['en'], gpu=False) 
        result = reader.readtext(image_name, detail=0) 
        text = " ".join(result)

        if text:
            # Prints the ENTIRE text found
            print(f"OCR Success! Extracted Full Text:\n\n{text}\n")
            return text
        else:
            print("OCR ran but found no text.")
            return None

    except Exception as e:
        print(f"OCR Failed: {e}")
        return None

def test_gemini(extracted_text):
    print("\n--- 2. Testing Google Gemini (Cloud) ---")
    
    if not extracted_text:
        return

    client = genai.Client(api_key=API_KEY)
    
    prompt = (
        "You are a helpful assistant. "
        "Format this OCR text into a clean recipe:\n\n"
        f"Text: {extracted_text}"
    )

    # UPDATED: Switched back to Gemini 2.5 Flash Lite since 2.0 failed
    model_name = "gemini-2.5-flash-lite" 

    try:
        print(f"Attempting to connect to {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        print(f"Success!\n\n{response.text}")
        
    except errors.ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("\nQUOTA HIT! The Free Tier requires a break.")
            print("   Waiting 60 seconds to reset your limit...")
            
            for i in range(60, 0, -1):
                print(f"   Retrying in {i}s...", end="\r")
                time.sleep(1)
            
            print("\n   Retrying now...")
            
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                print(f"Success on Retry!\n\n{response.text}")
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")

        elif "404" in str(e):
             print(f"Model Name Error: '{model_name}' was not found.")
        else:
            print(f"API Error: {e}")

# --- Main Execution Flow ---
if __name__ == "__main__":
    ocr_text = test_ocr("download.png")
    
    if ocr_text:
        test_gemini(ocr_text)