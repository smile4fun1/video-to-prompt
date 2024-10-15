import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
import tempfile
import base64
import requests
from dotenv import load_dotenv
import hashlib
import json
from pathlib import Path
import asyncio
from typing import List
from fpdf import FPDF
import markdown

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React app's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Predefined analysis types
ANALYSIS_TYPES = {
    "general": "Provide a general analysis of the video content.",
    "ui_interaction": "Analyze the user interface interactions in the video.",
    "emotion": "Detect and analyze emotions of people in the video.",
    "object_detection": "Identify and describe key objects in the video.",
    "text_recognition": "Recognize and transcribe any text visible in the video.",
}

def get_cache_key(file_content, prompt):
    file_hash = hashlib.md5(file_content).hexdigest()
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    return f"{file_hash}_{prompt_hash}"

def get_cached_result(cache_key):
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        with cache_file.open("r") as f:
            return json.load(f)
    return None

def save_to_cache(cache_key, result):
    cache_file = CACHE_DIR / f"{cache_key}.json"
    with cache_file.open("w") as f:
        json.dump(result, f)

def extract_frames(video_path, output_folder, frame_interval=1):
    video = cv2.VideoCapture(video_path)
    frame_count = 0
    extracted_frames = []

    while True:
        success, frame = video.read()
        if not success:
            break
        
        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_folder, f"frame_{frame_count:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            extracted_frames.append(frame_path)
        
        frame_count += 1

    video.release()
    return extracted_frames

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_frames_with_gpt4(frames, analysis_type, custom_prompt=""):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    system_message = "You are an AI assistant that analyzes video frames and provides insights based on the given prompt."
    
    if analysis_type in ANALYSIS_TYPES:
        prompt = ANALYSIS_TYPES[analysis_type]
    else:
        prompt = custom_prompt if custom_prompt else "Provide a general analysis of the video content."

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": [{"type": "text", "text": f"Analyze the following video frames based on this instruction: {prompt}"}]}
    ]

    for frame in frames[:5]:  # Limit to 5 frames for this example
        base64_image = encode_image(frame)
        messages.append(
            {
                "role": "user",
                "content": [{"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}]
            }
        )

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": messages,
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()

async def process_chunk(chunk: bytes, chunk_number: int, total_chunks: int, analysis_type: str, custom_prompt: str = ""):
    # Process each chunk of the video
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(chunk)
        temp_file_path = temp_file.name

    frames_folder = tempfile.mkdtemp()
    extracted_frames = extract_frames(temp_file_path, frames_folder)
    
    gpt4_analysis = analyze_frames_with_gpt4(extracted_frames, analysis_type, custom_prompt)
    
    result = {
        "chunk_number": chunk_number,
        "total_chunks": total_chunks,
        "frames_extracted": len(extracted_frames),
        "analysis": gpt4_analysis
    }
    
    # Clean up temporary files
    os.unlink(temp_file_path)
    for frame in extracted_frames:
        os.unlink(frame)
    os.rmdir(frames_folder)
    
    return result

def generate_pdf(result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Video Analysis Result", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Filename: {result['filename']}", ln=1)
    pdf.cell(200, 10, txt=f"Analysis Type: {result['analysis_type']}", ln=1)
    
    if 'custom_prompt' in result and result['custom_prompt']:
        pdf.cell(200, 10, txt=f"Custom Prompt: {result['custom_prompt']}", ln=1)
    
    if 'chunks' in result:
        for chunk in result['chunks']:
            pdf.cell(200, 10, txt=f"Chunk {chunk['chunk_number']} of {chunk['total_chunks']}", ln=1)
            pdf.cell(200, 10, txt=f"Frames extracted: {chunk['frames_extracted']}", ln=1)
            pdf.multi_cell(0, 10, txt=f"GPT-4 Analysis:\n{json.dumps(chunk['analysis'], indent=2)}")
    else:
        pdf.cell(200, 10, txt=f"Frames extracted: {result['frames_extracted']}", ln=1)
        pdf.multi_cell(0, 10, txt=f"GPT-4 Analysis:\n{json.dumps(result['analysis'], indent=2)}")
    
    return pdf.output(dest='S').encode('latin-1')

def generate_markdown(result):
    md = f"# Video Analysis Result\n\n"
    md += f"**Filename:** {result['filename']}\n"
    md += f"**Analysis Type:** {result['analysis_type']}\n"
    
    if 'custom_prompt' in result and result['custom_prompt']:
        md += f"**Custom Prompt:** {result['custom_prompt']}\n"
    
    if 'chunks' in result:
        for chunk in result['chunks']:
            md += f"\n## Chunk {chunk['chunk_number']} of {chunk['total_chunks']}\n"
            md += f"**Frames extracted:** {chunk['frames_extracted']}\n"
            md += f"### GPT-4 Analysis:\n```json\n{json.dumps(chunk['analysis'], indent=2)}\n```\n"
    else:
        md += f"\n**Frames extracted:** {result['frames_extracted']}\n"
        md += f"## GPT-4 Analysis:\n```json\n{json.dumps(result['analysis'], indent=2)}\n```\n"
    
    return md

@app.post("/upload_chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    analysis_type: str = Form(...),
    custom_prompt: str = Form("")
):
    chunk_content = await chunk.read()
    result = await process_chunk(chunk_content, chunk_number, total_chunks, analysis_type, custom_prompt)
    return JSONResponse(result)

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    analysis_type: str = Form(...),
    custom_prompt: str = Form("")
):
    file_content = await file.read()
    cache_key = get_cache_key(file_content, f"{analysis_type}_{custom_prompt}")
    
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return JSONResponse(cached_result)

    # Process the entire video if it's small enough
    if len(file_content) < 10 * 1024 * 1024:  # 10 MB threshold
        result = await process_chunk(file_content, 1, 1, analysis_type, custom_prompt)
        save_to_cache(cache_key, result)
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=413, detail="File too large. Please use chunked upload.")

@app.get("/analysis_types")
async def get_analysis_types():
    return JSONResponse(ANALYSIS_TYPES)

@app.get("/download/{format}/{cache_key}")
async def download_result(format: str, cache_key: str):
    result = get_cached_result(cache_key)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if format == "json":
        return JSONResponse(result)
    elif format == "pdf":
        pdf_content = generate_pdf(result)
        return StreamingResponse(iter([pdf_content]), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=analysis_result.pdf"})
    elif format == "markdown":
        md_content = generate_markdown(result)
        return StreamingResponse(iter([md_content.encode()]), media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename=analysis_result.md"})
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
