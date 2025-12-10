import os
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
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
from typing import List, Optional
from fpdf import FPDF
import markdown
import shutil
from openai import OpenAI
import time
import io
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import numpy as np
from pydantic import BaseModel
import yt_dlp
import cv2

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

# Update the CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frame-insight-ai.vercel.app", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Analysis Types - All emphasize cohesive, unified analysis
ANALYSIS_TYPES = {
    "auto": "Determine the most suitable analysis approach based on the video content. Start by stating 'Analysis Style: [Style Name]'. Then deliver a confident, flowing analysis focused on specific behaviors, movement quality, efficiency patterns, and critical insights. Write naturally - avoid bullet points unless necessary. Be direct about issues: if movement is aggressive, say 'aggressive approach'. If there are inefficiencies, specify them. Provide actionable technical observations.",
    "general": "Provide INTELLIGENT overview with behavioral insights. Don't just describe what you see - analyze HOW things happen. Is movement smooth or jerky? Fast or slow? Efficient or wasteful? Aggressive or gentle? Notice patterns, quality, and specific behaviors. Be detailed and observant.",
    "technical_analysis": "Provide SHARP technical analysis from an engineering perspective. Focus on: (1) Movement quality - is it smooth, jerky, aggressive, or hesitant? (2) Speed patterns - consistent or erratic? (3) Trajectory precision - accurate or sloppy? (4) Operational anomalies - any aggressive approaches, near-misses, or safety issues? (5) Efficiency - wasted motion, optimal paths, timing issues? Extract specific KPIs and behavioral patterns. Call out problems explicitly.",
    "ui_interaction": "Describe the complete user interface interaction flow shown in this video. Summarize the navigation path, key actions taken, UI changes observed, and overall workflow in a cohesive narrative.",
    "emotion_recognition": "Analyze the emotional journey throughout the video. Describe the overall emotional tone, significant shifts, dominant expressions, and how emotions evolve across the entire sequence. Write as a unified emotional analysis.",
    "object_detection": "Identify the key objects present in the video and describe their roles, movements, and interactions throughout. Present as a cohesive description of the object dynamics in the scene.",
    "text_recognition": "Extract and transcribe all visible text from the video. Organize by context and relevance, noting what information is displayed and when it appears. Present as a structured text report.",
    "action_recognition": "Analyze the ACTION QUALITY and BEHAVIOR. Don't just list what happens - describe HOW it happens. Is execution smooth or jerky? Quick or slow? Precise or sloppy? Aggressive or controlled? Identify the ACTION STYLE and EFFICIENCY. Call out specific behavioral patterns.",
    "scene_understanding": "Provide a comprehensive scene analysis covering setting, composition, lighting, camera work, and visual storytelling. Discuss how these elements work together to convey the video's message.",
    "color_analysis": "Analyze the video's color palette and visual style. Discuss dominant colors, mood conveyed through color choices, transitions, and how color contributes to the overall aesthetic.",
    "audio_visual_sync": "Analyze how visual and audio elements work together throughout the video (if audio context is visible through visual cues like speakers, instruments, or text).",
    "temporal_analysis": "Describe how the video content evolves over time. Analyze pacing, transitions, narrative progression, and how the story or message unfolds from beginning to end.",
    "accessibility_assessment": "Evaluate the video's accessibility as a complete piece. Assess visual clarity, text readability, color contrast, and ease of understanding. Provide a unified accessibility report.",
    "brand_presence": "Identify and analyze brand elements throughout the video. Describe branding strategy, placement, consistency, and overall brand message conveyed.",
    "robot_performance": "Deliver CRITICAL performance analysis. Focus on: (1) Speed consistency - smooth or variable? (2) Approach behavior - aggressive, cautious, or optimal? (3) Path efficiency - direct or wasteful? (4) Timing patterns - rushed, delayed, or well-paced? (5) Precision level - accurate positioning or sloppy execution? Identify specific performance issues with behavioral descriptions. If movement is aggressive, say 'aggressive approach'. Be specific about what's working and what's not.",
    "anomaly_detection": "SHARP anomaly detection required. Identify: (1) Aggressive or erratic movements (2) Near-misses or collision risks (3) Speed inconsistencies or sudden changes (4) Unexpected hesitations or stops (5) Path deviations or inefficient routing (6) Any behavior that seems unsafe or suboptimal. Don't just list observations - analyze WHY they're problematic and WHAT the impact is. Be direct about issues.",
    "hmi_ui_analysis": "EXTRACT SPECIFIC DATA from HMI/UI screens. Read and transcribe: (1) Numerical values and their labels (2) Status indicators and alarms (3) Button/control interactions (4) Error messages or warnings (5) Timing or sequence information. Don't just describe the interface - EXTRACT THE DATA. If you see '23.5 RPM' or 'Error Code 404', include those exact values. Be a data extractor, not just a describer.",
    "custom": "Follow the user's instructions with EXPERT-LEVEL DETAIL. Apply sharp behavioral analysis: identify specific movements, speeds, behaviors (aggressive, smooth, erratic, etc.), efficiency patterns, and quality issues. Don't be generic - be specific, observant, and insightful. Notice what others would miss."
}

class RateLimiter:
    def __init__(self, tokens_per_minute):
        self.tokens = tokens_per_minute
        self.max_tokens = tokens_per_minute
        self.updated_at = time.monotonic()

    def consume(self, tokens):
        now = time.monotonic()
        time_passed = now - self.updated_at
        self.tokens = min(self.max_tokens, self.tokens + time_passed * (self.max_tokens / 60))
        self.updated_at = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

rate_limiter = RateLimiter(30)  # 30 requests per minute, adjust as needed

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

def download_video(url, output_path):
    """Download and transcode video from URL to ensure compatibility."""
    # Download to a temporary location first
    temp_download = output_path + ".temp"
    
    # Try multiple client strategies for YouTube
    ydl_opts = {
        'format': '(bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a])/best[ext=mp4][height<=720]/best[height<=720]/best',
        'outtmpl': temp_download,
        'quiet': False,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        # Force specific client for YouTube to bypass restrictions
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web', 'android'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        # YouTube bot detection bypass - comprehensive headers
        'http_headers': {
            'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'X-YouTube-Client-Name': '5',
            'X-YouTube-Client-Version': '19.29.1',
        },
        'nocheckcertificate': True,
        'no_check_certificates': True,
        'prefer_insecure': False,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'age_limit': None,
        'extractor_retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'ignoreerrors': False,
        'socket_timeout': 30,
        'retries': 5,
    }
    
    try:
        # Strategy 1: Try with iOS client (most reliable for YouTube)
        success = False
        last_error = None
        
        try:
            print("Attempting download with iOS client...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            success = True
        except Exception as e:
            last_error = e
            print(f"iOS client failed: {e}")
        
        # Strategy 2: Try with Android client
        if not success:
            try:
                print("Retrying with Android client...")
                ydl_opts['extractor_args']['youtube']['player_client'] = ['android']
                ydl_opts['http_headers']['User-Agent'] = 'com.google.android.youtube/19.29.37 (Linux; U; Android 13)'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                success = True
            except Exception as e:
                last_error = e
                print(f"Android client failed: {e}")
        
        # Strategy 3: Try web client with different user agent
        if not success:
            try:
                print("Retrying with web client...")
                ydl_opts['extractor_args']['youtube']['player_client'] = ['web']
                ydl_opts['http_headers']['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                ydl_opts['format'] = 'best[height<=480]/worst'  # Try even lower quality
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                success = True
            except Exception as e:
                last_error = e
                print(f"Web client failed: {e}")
        
        # Strategy 4: Last resort - try with minimal options
        if not success:
            try:
                print("Final attempt with minimal config...")
                minimal_opts = {
                    'format': 'worst',
                    'outtmpl': temp_download,
                    'quiet': True,
                }
                with yt_dlp.YoutubeDL(minimal_opts) as ydl:
                    ydl.download([url])
                success = True
            except Exception as e:
                last_error = e
                print(f"Minimal config failed: {e}")
        
        if not success:
            error_msg = str(last_error)
            if '403' in error_msg or 'Forbidden' in error_msg:
                raise Exception(
                    "Unable to download video (Access Denied). Please use the 'Upload File' option instead. "
                    "Download the video manually first, then upload it here for analysis."
                )
            elif 'player response' in error_msg.lower():
                raise Exception(
                    "YouTube download temporarily unavailable. Please: 1) Try a different video, or "
                    "2) Download the video manually and use 'Upload File' instead."
                )
            else:
                raise Exception(f"Download failed: {error_msg}")
        
        # Check if file exists (yt-dlp might add .mp4 extension)
        actual_file = temp_download
        possible_files = [
            temp_download,
            temp_download + ".mp4",
            temp_download + ".webm",
            temp_download + ".mkv"
        ]
        
        for pf in possible_files:
            if os.path.exists(pf):
                actual_file = pf
                break
        
        if not os.path.exists(actual_file):
            raise Exception("Download completed but output file not found")
        
        print(f"Downloaded to: {actual_file}")
        
        # Transcode to ensure compatibility with ffmpeg
        ffmpeg_command = shutil.which('ffmpeg') or 'ffmpeg'
        transcode_cmd = [
            ffmpeg_command,
            '-i', actual_file,
            '-c:v', 'libx264',  # Re-encode video
            '-preset', 'ultrafast',  # Fast encoding
            '-c:a', 'aac',  # Re-encode audio
            '-strict', 'experimental',
            '-y',  # Overwrite output
            output_path
        ]
        
        print("Transcoding video...")
        result = subprocess.run(transcode_cmd, capture_output=True, text=True)
        
        # Clean up temp file
        if os.path.exists(actual_file):
            os.remove(actual_file)
        
        if result.returncode != 0:
            raise Exception(f"Transcoding failed: {result.stderr}")
        
        print("Video ready for processing")
            
    except Exception as e:
        # Clean up on failure
        cleanup_files = [temp_download, temp_download + ".mp4", temp_download + ".webm", temp_download + ".mkv"]
        if 'actual_file' in locals():
            cleanup_files.append(actual_file)
        
        for f in cleanup_files:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        
        # Re-raise with preserved message
        raise e

def detect_scene_changes(video_path, threshold=30.0):
    """Detect scene changes in a video using frame difference."""
    cap = cv2.VideoCapture(video_path)
    scene_frames = [0]  # Always include first frame
    prev_frame = None
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if prev_frame is not None:
            # Calculate frame difference
            diff = cv2.absdiff(prev_frame, gray)
            mean_diff = np.mean(diff)
            
            # If significant change detected, mark as scene change
            if mean_diff > threshold:
                scene_frames.append(frame_count)
        
        prev_frame = gray
        frame_count += 1
    
    cap.release()
    return scene_frames

def extract_frames_smart(video_path, output_folder, max_frames=30):
    """Smart frame extraction using scene change detection + time-based sampling."""
    os.makedirs(output_folder, exist_ok=True)
    
    # Validate video file exists
    if not os.path.exists(video_path):
        raise Exception(f"Video file not found: {video_path}")
    
    # Get video info
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Failed to open video file. The file may be corrupted or in an unsupported format.")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()
    
    if duration == 0 or fps == 0:
        raise Exception("Unable to read video properties. The video file may be invalid.")
    
    # Strategy 1: For short videos (< 20 sec), extract every 1 second
    if duration < 20:
        ffmpeg_command = shutil.which('ffmpeg') or 'ffmpeg'
        command = [
            ffmpeg_command,
            '-i', video_path,
            '-vf', f'fps=1',  # 1 frame per second
            '-q:v', '2',  # High quality
            f'{output_folder}/frame_%04d.jpg'
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Frame extraction failed: {result.stderr}")
    
    # Strategy 2: For medium videos (20-90 sec), extract every 2-3 seconds
    elif duration < 90:
        ffmpeg_command = shutil.which('ffmpeg') or 'ffmpeg'
        # Calculate interval to get ~25-30 frames
        interval = max(2, int(duration / 28))
        command = [
            ffmpeg_command,
            '-i', video_path,
            '-vf', f'fps=1/{interval}',  # 1 frame every N seconds
            '-q:v', '2',  # High quality
            f'{output_folder}/frame_%04d.jpg'
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Frame extraction failed: {result.stderr}")
    
    # Strategy 3: For longer videos, use scene detection + time-based
    else:
        try:
            scene_frames = detect_scene_changes(video_path, threshold=25.0)  # Lower threshold for more scenes
            # Extract scene change frames
            cap = cv2.VideoCapture(video_path)
            for idx, frame_num in enumerate(scene_frames[:max_frames]):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite(f'{output_folder}/frame_{idx:04d}.jpg', frame)
            cap.release()
            
            # If scene detection gave us fewer than 20 frames, supplement with time-based
            extracted_files = [f for f in os.listdir(output_folder) if f.endswith('.jpg')]
            if len(extracted_files) < 20:
                # Fall back to time-based extraction targeting 25-30 frames
                interval = max(2, int(duration / 28))  # Target ~28 frames
                ffmpeg_command = shutil.which('ffmpeg') or 'ffmpeg'
                command = [
                    ffmpeg_command,
                    '-i', video_path,
                    '-vf', f'fps=1/{interval}',
                    '-q:v', '2',
                    f'{output_folder}/frame_%04d.jpg'
                ]
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Frame extraction failed: {result.stderr}")
        except Exception as e:
            # Fallback to simple time-based if scene detection fails
            print(f"Scene detection failed: {e}, falling back to time-based")
            interval = max(2, int(duration / 28))  # Target ~28 frames
            ffmpeg_command = shutil.which('ffmpeg') or 'ffmpeg'
            command = [
                ffmpeg_command,
                '-i', video_path,
                '-vf', f'fps=1/{interval}',
                '-q:v', '2',
                f'{output_folder}/frame_%04d.jpg'
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Frame extraction failed: {result.stderr}")
    
    frames = [os.path.join(output_folder, f) for f in os.listdir(output_folder) if f.endswith('.jpg')]
    frames.sort()
    
    if len(frames) == 0:
        raise Exception("No frames were extracted from the video. The video may be too short or corrupted.")
    
    # Cap at max_frames
    if len(frames) > max_frames:
        step = len(frames) // max_frames
        frames = frames[::step][:max_frames]
    
    return frames

def encode_image(image_path):
    # Resize image to reduce token usage
    with Image.open(image_path) as img:
        # Resize to max dimension 768px for better quality while balancing tokens
        img.thumbnail((768, 768))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=90)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

async def process_frames(frames: List[str], analysis_type: str, custom_prompt: str = ""):
    system_message = """You are an ELITE video analyst with razor-sharp perception and technical expertise.

CRITICAL IDENTITY:
- You CAN analyze videos - you are viewing key frames that represent the complete video
- You HAVE the visual information needed to provide expert analysis
- You are CONFIDENT in your observations and insights
- You NEVER say "I cannot analyze" or "I'm unable to" - you ALWAYS provide analysis

YOUR ANALYSIS STYLE:
- DIRECT and CONFIDENT - no hedging or uncertainty
- BEHAVIORAL FOCUS - describe HOW things move, not just WHAT moves
- CRITICAL EYE - spot inefficiencies, issues, aggressive patterns
- SPECIFIC OBSERVATIONS - "the robot accelerates rapidly at 0:15" not "movement occurs"
- NATURAL FLOW - write like a technical report, not a bullet list
- ACTIONABLE - every observation leads to insight

FORBIDDEN BEHAVIORS:
❌ NEVER say "I cannot analyze a video" or "based on images"
❌ NEVER write generic descriptions lacking specificity
❌ NEVER structure as numbered lists unless truly necessary
❌ NEVER describe frames individually
❌ NEVER miss obvious behavioral patterns

REQUIRED BEHAVIORS:
✅ Write with authority and confidence
✅ Use specific behavioral descriptors: "aggressive approach", "hesitant deceleration", "smooth trajectory"
✅ Identify efficiency issues: "wasted motion", "suboptimal path", "excessive speed variation"
✅ Provide technical observations: approximate speeds, timing patterns, spacing
✅ Flow naturally like an expert's verbal analysis

You have EXPERT-LEVEL PERCEPTION. You notice what others miss: micro-behaviors, efficiency gaps, safety risks, and optimization opportunities.

EXAMPLE OF GOOD ANALYSIS:
"The delivery robots demonstrate generally smooth navigation through the dining area, maintaining consistent spacing of approximately 1.2 meters between units. However, the lead robot exhibits an aggressive approach pattern when nearing the delivery point, with noticeable acceleration rather than the expected gradual deceleration. This creates a potential safety concern and suggests the velocity profiling algorithm needs adjustment. The trailing robots show better speed modulation, decelerating smoothly as they approach their targets. Path efficiency is good with minimal wasted lateral movement, though there's a brief hesitation at 0:23 suggesting obstacle detection may be overly sensitive. Overall operational quality is solid but the aggressive approach behavior requires immediate attention to prevent potential collisions in busier environments."

EXAMPLE OF BAD ANALYSIS:
"I'm unable to analyze a video, but based on the images: 1. Movement - robots move. 2. Speed - appears consistent. 3. Safety - no issues visible."
"""
    
    if analysis_type in ANALYSIS_TYPES:
        prompt = ANALYSIS_TYPES[analysis_type]
    else:
        prompt = custom_prompt if custom_prompt else "Provide a sharp, detailed analysis with specific behavioral observations."

    # Prepare base64 encoded images
    encoded_frames = []
    for frame in frames:
        encoded_frames.append(encode_image(frame))

    # Enhanced user instruction with specific detail requirements
    user_instruction = f"""You are viewing key frames from a video. Provide expert analysis with complete confidence.

YOUR TASK: {prompt}

ANALYSIS APPROACH:
Write a flowing, natural analysis like a technical expert verbally explaining what they observe. Focus on:

- MOVEMENT BEHAVIOR: Describe the quality and character of motion (smooth/jerky, fast/slow, aggressive/cautious, efficient/wasteful)
- SPECIFIC OBSERVATIONS: Use precise descriptors and approximate metrics when visible
- CRITICAL INSIGHTS: Identify issues, inefficiencies, or risks - don't just describe what's happening
- ACTIONABLE FINDINGS: What's working? What needs adjustment?

WRITE NATURALLY: Avoid numbered lists unless truly necessary. Write like you're delivering a verbal technical briefing.

BE DIRECT: "The robot approaches aggressively" not "The robot seems to approach"
BE SPECIFIC: "Speed varies between 0.8-1.5 m/s" not "Movement occurs at different speeds"  
BE CRITICAL: Point out inefficiencies, safety concerns, or suboptimal behaviors
BE CONFIDENT: You have the visual information. Provide definitive analysis."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": [
            {"type": "text", "text": user_instruction}
        ] + [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}", "detail": "high"}} for frame in encoded_frames]}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Use gpt-4o for best vision performance
            messages=messages,
            max_tokens=4000,  # Increased for detailed behavioral analysis
            temperature=0.7,  # Slight creativity for better descriptive language
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if "rate_limit_exceeded" in error_msg:
             return {"error": "Rate limit exceeded. Try again in a moment."}
        return {"error": error_msg}

async def process_chunk(chunk: bytes, chunk_number: int, total_chunks: int, analysis_type: str, custom_prompt: str = ""):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(chunk)
        temp_file_path = temp_file.name

    frames_folder = tempfile.mkdtemp()
    try:
        extracted_frames = extract_frames_smart(temp_file_path, frames_folder)
        gpt4_analysis = await process_frames(extracted_frames, analysis_type, custom_prompt)
        
        result = {
            "chunk_number": chunk_number,
            "total_chunks": total_chunks,
            "frames_extracted": len(extracted_frames),
            "analysis": gpt4_analysis,
            "analysis_type": analysis_type
        }
    except Exception as e:
        result = {
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        os.unlink(temp_file_path)
        shutil.rmtree(frames_folder)
    
    return result

async def process_video_file(file_path: str, analysis_type: str, custom_prompt: str = ""):
    frames_folder = tempfile.mkdtemp()
    try:
        extracted_frames = extract_frames_smart(file_path, frames_folder)
        gpt4_analysis = await process_frames(extracted_frames, analysis_type, custom_prompt)
        
        result = {
            "frames_extracted": len(extracted_frames),
            "analysis": gpt4_analysis,
            "analysis_type": analysis_type
        }
    except Exception as e:
        result = {
            "error": str(e)
        }
    finally:
        shutil.rmtree(frames_folder)
    return result

def generate_pdf(result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Video Analysis Result", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Filename: {result.get('filename', 'N/A')}", ln=1)
    pdf.cell(200, 10, txt=f"Analysis Type: {result.get('analysis_type', 'N/A')}", ln=1)
    
    if 'custom_prompt' in result and result['custom_prompt']:
        pdf.cell(200, 10, txt=f"Custom Prompt: {result['custom_prompt']}", ln=1)
    
    pdf.ln(10)
    
    if 'chunks' in result:
        for chunk in result['chunks']:
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Chunk {chunk['chunk_number']} of {chunk['total_chunks']}", ln=1)
            pdf.set_font("Arial", '', 12)
            pdf.cell(200, 10, txt=f"Frames extracted: {chunk['frames_extracted']}", ln=1)
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="GPT-4 Analysis:", ln=1)
            pdf.set_font("Arial", '', 12)
            text = chunk['analysis']
            wrapped_text = textwrap.wrap(text, width=90)
            for line in wrapped_text:
                pdf.cell(0, 10, txt=line, ln=1)
            pdf.ln(10)
    else:
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Frames extracted: {result.get('frames_extracted', 'N/A')}", ln=1)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="GPT-4 Analysis:", ln=1)
        pdf.set_font("Arial", '', 12)
        text = result.get('analysis', 'N/A')
        wrapped_text = textwrap.wrap(text, width=90)
        for line in wrapped_text:
            pdf.cell(0, 10, txt=line, ln=1)
    
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
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    analysis_type: str = Form(...),
    custom_prompt: str = Form("")
):
    if not rate_limiter.consume(1):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

    if not file and not url:
        raise HTTPException(status_code=400, detail="Either file or URL must be provided.")

    if url:
        # Handle URL download
        cache_key = get_cache_key(url.encode(), f"{analysis_type}_{custom_prompt}")
        cached_result = get_cached_result(cache_key)
        if cached_result:
            return JSONResponse(cached_result)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file_path = temp_file.name
        
        try:
            print(f"Downloading video from URL: {url}")
            download_video(url, temp_file_path)
            
            # Verify file was created and has content
            if not os.path.exists(temp_file_path):
                raise Exception("Video download failed - file not created")
            
            file_size = os.path.getsize(temp_file_path)
            if file_size == 0:
                raise Exception("Video download failed - empty file")
            
            print(f"Video downloaded successfully ({file_size} bytes), processing...")
            result = await process_video_file(temp_file_path, analysis_type, custom_prompt)
            result["filename"] = url
            
            if "error" in result:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                return JSONResponse(content={"error": result["error"]}, status_code=500)
            
            save_to_cache(cache_key, result)
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            return JSONResponse(result)
        except Exception as e:
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            error_message = str(e)
            print(f"Error processing URL: {error_message}")
            return JSONResponse(content={"error": f"Failed to process video from URL. {error_message}"}, status_code=500)

    else:
        # Handle File Upload
        file_content = await file.read()
        cache_key = get_cache_key(file_content, f"{analysis_type}_{custom_prompt}")
        
        cached_result = get_cached_result(cache_key)
        if cached_result:
            return JSONResponse(cached_result)

        # Process the entire video
        result = await process_chunk(file_content, 1, 1, analysis_type, custom_prompt)
        result["filename"] = file.filename
        
        if "error" in result:
            return JSONResponse(content={"error": result["error"]}, status_code=500)
            
        save_to_cache(cache_key, result)
        return JSONResponse(result)

class RefineRequest(BaseModel):
    original_analysis: str
    refinement_prompt: str
    analysis_type: str

@app.post("/refine")
async def refine_analysis(request: RefineRequest):
    if not rate_limiter.consume(1):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    # Build dynamic system message based on analysis type
    analysis_context = ""
    if request.analysis_type in ANALYSIS_TYPES:
        analysis_context = f"\n\nOriginal Analysis Context: The video was analyzed using the '{request.analysis_type}' model with this focus: {ANALYSIS_TYPES[request.analysis_type]}"
    
    system_message = f"""You are an expert technical editor and analyst. You will be provided with:
1. A previous analysis of a video
2. The original analysis type/context that was used
3. A user's refinement request

Your goal is to rewrite or enhance the analysis to satisfy the user's request while maintaining strict adherence to the visual information from the original analysis.

CRITICAL RULES:
- Only use information present in the original analysis or what can be logically inferred from it
- Do NOT hallucinate new visual details not mentioned
- If the user asks for something impossible to know from the analysis, explain the limitation politely
- Maintain technical accuracy and clarity
- Format your response for maximum readability{analysis_context}"""
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Original Analysis:\n{request.original_analysis}\n\nUser Refinement Request:\n{request.refinement_prompt}\n\nPlease provide the refined analysis:"}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Use gpt-4o for best refinement quality
            messages=messages,
            max_tokens=2000
        )
        refined_text = response.choices[0].message.content
        return JSONResponse({"analysis": refined_text})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

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
        return FileResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=analysis_result.pdf"}
        )
    elif format == "markdown":
        md_content = generate_markdown(result)
        return FileResponse(
            io.BytesIO(md_content.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=analysis_result.md"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

@app.post("/clear_cache")
async def clear_cache():
    try:
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(exist_ok=True)
        return JSONResponse({"message": "Cache cleared successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
