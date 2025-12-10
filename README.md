# Frame Insight - Video Intelligence, Amplified

A powerful AI-powered video analysis application that extracts KPIs, technical data, sentiment, brand insights, and more from any video. Built with FastAPI, React, and GPT-4o vision capabilities.

## 🌟 Features

### Core Capabilities
- **Smart Frame Extraction**: Intelligent scene change detection + time-based sampling for optimal frame selection
- **AI-Powered Analysis**: GPT-4o vision model for expert-level video understanding
- **Multiple Analysis Types**: 18+ specialized analysis modes including:
  - AUTO (Recommended) - Automatically determines best analysis approach
  - Technical Analysis - For robotics, engineering, and performance data
  - Robot Performance - Cycle times, efficiency, anomaly detection
  - HMI/UI Analysis - Extract data from screens and interfaces
  - Emotion Recognition, Brand Presence, Action Recognition, and more
- **AI Refinement**: Iteratively refine results with additional prompts
- **History Tracking**: Automatically saves all analyses with browser persistence
- **Drag & Drop**: Modern file upload with drag-and-drop support
- **URL Support**: Analyze videos from YouTube, Vimeo, TikTok, and more (via yt-dlp)

### User Experience
- Clean, Apple-inspired UI with glassmorphism effects
- Real-time progress indicators with AI-themed loading messages
- Persistent state across page refreshes
- Responsive design for mobile and desktop
- History panel for accessing past analyses
- Copy and export functionality

## 🏗️ Architecture

```
video-to-prompt/
├── backend/
│   ├── main.py              # FastAPI server with all endpoints
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # OpenAI API key (create this)
│   └── cache/              # Analysis cache (auto-created)
└── frontend/
    ├── src/
    │   ├── App.jsx         # Main React component
    │   ├── App.css         # Styling
    │   └── main.jsx        # React 18 entry point
    ├── public/
    │   └── favicon.svg     # Frame Insight logo
    └── package.json        # Node dependencies
```

## 📋 Prerequisites

- **Python 3.9+** (3.10+ recommended)
- **Node.js 16+** and npm
- **FFmpeg** (for video processing)
- **OpenAI API Key** with GPT-4o access

## 🚀 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd video-to-prompt
```

### 2. Install FFmpeg
**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### 3. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```env
OPENAI_API_KEY=sk-your-key-here
```

### 4. Frontend Setup
```bash
cd frontend
npm install
```

## ▶️ Running the Application

### Start Backend (Terminal 1)
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Backend runs at: `http://127.0.0.1:8000`

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

Frontend runs at: `http://localhost:3000`

## 📖 Usage Guide

### Basic Analysis
1. **Upload Video**: Drag & drop or click to browse (supports MP4, MOV, AVI, WebM)
2. **Select Analysis Type**: Choose from dropdown or use AUTO for intelligent selection
3. **Analyze**: Click "Analyze Video" and wait for AI processing
4. **View Results**: See comprehensive analysis with frame count and insights

### URL Analysis
1. Switch to "Video URL" tab
2. Paste YouTube/Vimeo/TikTok link
3. Analyze (note: some platforms may block downloads - use file upload as fallback)

### AI Refinement
1. After getting results, use the "AI Refinement" text box
2. Ask AI to format, summarize, or extract specific details
3. New refined results appear below original analysis
4. Chain multiple refinements for iterative improvement

### History
1. Click "History" button in navbar
2. View all past analyses with timestamps
3. Click "View" to restore any previous analysis
4. Delete individual items or clear all history

## 🎯 Analysis Types

### Technical & Robotics
- **Technical Analysis**: Engineering data extraction, KPIs, performance metrics
- **Robot Performance**: Speed, accuracy, efficiency, bottleneck identification
- **Anomaly Detection**: Irregular movements, safety issues, deviations
- **HMI/UI Analysis**: Extract data from screens, alarms, status indicators

### General Purpose
- **AUTO**: Intelligently selects best analysis approach
- **General**: Comprehensive overview with behavioral insights
- **Action Recognition**: Movement quality and behavior patterns
- **Scene Understanding**: Composition, lighting, camera work analysis

### Specialized
- **Emotion Recognition**: Facial expressions, body language, emotional journey
- **Brand Presence**: Logo detection, product placement, brand strategy
- **Object Detection**: Key objects, positions, movements, interactions
- **Text Recognition**: OCR for on-screen text and displays
- **Color Analysis**: Palette analysis and mood assessment
- **Temporal Analysis**: How content evolves over time

### Advanced
- **Custom**: Enter your own analysis prompt for specific needs

## 🔧 Configuration

### Frame Extraction
Smart extraction with multiple strategies:
- **Short videos (<20s)**: 1 frame/second
- **Medium videos (20-90s)**: Dynamic interval (~25-30 frames)
- **Long videos (>90s)**: Scene change detection + time-based fallback

Maximum frames: 30 per video (configurable in `main.py`)

### Model Settings
- **Model**: gpt-4o (best vision performance)
- **Max Tokens**: 4000 (detailed analysis)
- **Temperature**: 0.7 (balanced creativity/accuracy)
- **Image Detail**: high (768px max dimension)

### Storage
- **Analysis Cache**: Backend `/cache` directory (temporary)
- **History**: Browser localStorage (persistent)
- **Videos**: System temp folder (auto-deleted after analysis)
- **History Limit**: Last 50 analyses

## 🛠️ Technical Details

### Backend (FastAPI)
- `/upload` - Main analysis endpoint (file or URL)
- `/refine` - AI refinement endpoint
- `/analysis_types` - Get available analysis modes
- `/clear_cache` - Clear analysis cache
- CORS enabled for localhost:3000
- Rate limiting: 30 requests/minute

### Frontend (React 18)
- Modern createRoot API
- FontAwesome icons
- Axios for API calls
- localStorage for persistence
- Responsive CSS with CSS variables

### AI Prompting
- Expert-level system prompts for sharp analysis
- Behavioral focus (aggressive, smooth, efficient, etc.)
- Anti-generic instructions
- Context-aware refinement prompts
- Examples of good vs bad analysis

### Video Processing
- yt-dlp with iOS/Android/Web client fallbacks
- FFmpeg transcoding for compatibility
- OpenCV scene change detection
- Pillow image optimization
- Automatic cleanup of temp files

## 📊 Performance & Costs

### Frame Processing
- **Analysis Time**: 15-45 seconds (depending on frames)
- **Frames Extracted**: 15-30 intelligently selected frames
- **Frame Quality**: 768px max dimension, 90% JPEG quality

### OpenAI Costs
- **Average Cost**: $0.02-0.04 per video
- **Token Usage**: ~8,000-15,000 tokens per analysis
- **Model**: gpt-4o ($2.50/1M input tokens)

## 🔒 Security & Privacy

- Videos stored temporarily (~10-30 seconds) in system temp folder
- Automatic deletion after analysis
- No permanent video storage
- Analysis results stored locally in browser
- API key secured via environment variable
- CORS restricted to localhost

## 🐛 Troubleshooting

### YouTube 403 Errors
- App uses 4-tier fallback (iOS/Android/Web clients)
- If URL fails, download video manually and use file upload
- Success rate: ~70-80% for public videos

### "Blank Page" After Analysis
- Clear browser cache
- Click "Reset" button
- Check browser console for errors

### FFmpeg Not Found
```bash
# Verify FFmpeg installation
ffmpeg -version

# If not found, reinstall and add to PATH
```

### Out of Memory
- Reduce max_frames in `main.py` (line 178)
- Close other applications
- Use shorter videos or lower resolution

### OpenAI Rate Limits
- Check your OpenAI account tier
- Wait a few minutes between requests
- Upgrade to higher tier if needed

## 📝 Development

### Code Style
- Senior Staff Engineer approach
- Minimal documentation (self-documenting code)
- No unnecessary refactoring
- Production-ready code only

### Key Files
- `backend/main.py`: All backend logic, prompts, and endpoints
- `frontend/src/App.jsx`: Main React component with all UI logic
- `frontend/src/App.css`: Complete styling with CSS variables

## 🤝 Contributing

Contributions welcome! Please:
1. Follow existing code style
2. Test thoroughly before PR
3. Update README if adding features
4. No breaking changes without discussion

## 📄 License

MIT License - Use freely for personal or commercial projects

## 🙏 Acknowledgments

- OpenAI GPT-4o for vision capabilities
- FastAPI for robust backend framework
- React team for excellent frontend library
- yt-dlp community for video download support
- FFmpeg for video processing capabilities

---

**Frame Insight** - Engineered for precision.

For issues or questions, open a GitHub issue or contact the development team.
