from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key="AIzaSyDpuFnENGEafI_3XkrGMKPJ9Yp8m3FtktM")  # Replace with your Gemini API key
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI(title="AI Tutor from Handwritten Image")

# --- Extract content from image ---
def extract_text_from_image(image_bytes: bytes):
    try:
        response = model.generate_content([
            "Extract all visible content from this image (text, formulas, notes, etc.) as clearly as possible.",
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        return response.text.strip()
    except Exception as e:
        return f"❌ Error extracting: {str(e)}"

# --- Validate and explain content ---
def validate_information(extracted_text: str):
    prompt = f"""
You are an expert tutor.

Review the following extracted content from a handwritten image:

\"\"\"{extracted_text}\"\"\"

Your task:
- Identify any incorrect facts or formulas.
- Correct them.
- Explain the correct concept clearly as a tutor would to a student.

Use a friendly tone, and keep your explanations simple and clear.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error validating: {str(e)}"

# --- Follow-up question based on image text ---
def answer_followup_question(image_text: str, question: str):
    prompt = f"""
Based on this content extracted from an image:

\"\"\"{image_text}\"\"\"

Answer this follow-up question in a helpful, clear way:

\"{question}\"
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error answering question: {str(e)}"

# --- API endpoint to analyze image ---
@app.post("/analyze/")
async def analyze_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    extracted = extract_text_from_image(image_bytes)
    validation = validate_information(extracted)

    return JSONResponse({
        "extracted_content": extracted,
        "validation_explanation": validation
    })

# --- API endpoint to answer follow-up question ---
@app.post("/question/")
async def follow_up_question(image_text: str = Form(...), question: str = Form(...)):
    response = answer_followup_question(image_text, question)
    return JSONResponse({"answer": response})
