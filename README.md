# CPE179P-Group01---Recipe-Ingredients-List-OCR-with-AI-Agent-using-PyTorch
# 🍳 Recipe Agent Pro: Scan, Clean & Translate
### Using Streamlit, EasyOCR, and Google Gemini AI

## 📘 Overview
This project is a **multimodal AI web application** designed to digitize, format, and translate physical recipe cards and cookbook pages. 
It uses **EasyOCR (PyTorch)** to extract raw text from uploaded images, **Google Gemini 2.5 Flash Lite** to structure and translate that text into a clean recipe format, and **Streamlit** for an interactive, voice-enabled user interface.

---

## ⚙️ Setup Instructions

### 1. Install Dependencies
Ensure Python is installed on your system, then install the required libraries by running the following command in your terminal:

```bash
pip install streamlit easyocr torch torchvision numpy python-dotenv google-genai SpeechRecognition gTTS langdetect pillow
```
### 2. Configure Your API Key
  This application requires a Google Gemini API key to function.
    
    1. Create a file named .env in the exact same folder as your Python script.
    2. Open the .env file in a text editor and add your API key like this:
      
      GEMINI_API_KEY=your_actual_api_key_here

## 🖥️ Running the Application
### 1. Open Terminal
  Open a new terminal window or command prompt on your computer.
### 2. Navigate to the Project Folder
  Go to the folder where your Final_Project.py file is located:

```bash
cd path/to/your/project/folder
```
### 3. Launch Streamlit
Execute the application by running:
```bash
streamlit run Final_Project.py
```

## 🖼️ Using the Application
Once the web interface loads, you can interact with the Recipe Agent as follows:

## 1. Log In / Sign Up (Optional but Recommended)
  - Use the top-right buttons to create an account.
  - Logging in allows the app to save your recipe chats to a local SQLite database so you can access them later from the sidebar.

## 2. Upload a Recipe Image
  - Click the Browse files button at the top of the page.
  - Select a recipe image in one of the supported formats: .png, .jpg, .jpeg, or .webp.
  - The app will display the original image, use EasyOCR to extract the raw text, and instantly use Gemini to format it into a clean, structured recipe.

## 3. Interact & Translate (Voice or Text)
  - Scroll down to the bottom input bar.
  - Voice Command: Click the Microphone icon, record a prompt (e.g., "Translate this recipe to Tagalog" or "Can you substitute the butter?"), and click Send.
  - Text Command: Alternatively, type your request into the text box and click Send.

## 4. Listen to the AI
  - The AI will display its translated or modified recipe.
  - The app will automatically detect the language the AI responded in and use Text-to-Speech to read the response out loud with the correct accent.

### 📝 Notes
    1. API Limits: If using a free-tier Gemini API key, you may hit a rate limit if you send too many requests too quickly. If the app throws a quota error, simply wait 60 seconds and try again.
    2. First Run: The very first time you upload an image, EasyOCR will need a moment to download its language detection models.
    3. Hardware Warnings: If you see a PyTorch warning in your terminal about using the "CPU" instead of a GPU, this is completely normal for standard laptops and will not break the app.
    4. Microphone Permissions: Ensure you have granted your web browser permission to access your microphone so the voice commands can function.

### 👨‍💻 Developers
1. Cortez, Jethro P.
2. Figarola, Kirsten Cyrille M.
3. Laureano, Rupert Jay C.

**Course:** CPE179P/B1
**University:** Mapúa University
