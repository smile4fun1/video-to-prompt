# Video Analysis App

This project consists of a FastAPI backend and a React + Vite frontend for analyzing videos using OpenCV and GPT-4.

## Project Structure

```
video-analysis-app/
├── backend/
│   ├── venv/
│   ├── main.py
│   ├── requirements.txt
│   ├── setup.py
│   └── cache/
└── frontend/
    ├── public/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

## Prerequisites

- Python 3.7+
- Node.js 14+
- npm 6+
- OpenAI API key

## Installation and Setup

### Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the backend package:
   ```
   pip install -e .
   ```

4. Create a `.env` file in the backend directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Create a `cache` directory in the backend folder:
   ```
   mkdir cache
   ```

### Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install the required packages:
   ```
   npm install
   ```

## Running the Application

### Backend

1. From the backend directory, activate the virtual environment if not already activated:
   ```
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Run the FastAPI server:
   ```
   video-analysis-app-backend
   ```

The backend will be available at `http://localhost:8000`.

### Frontend

1. From the frontend directory, run the development server:
   ```
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`.

## Usage

1. Open your web browser and go to `http://localhost:5173`.
2. Select a video file using the file input.
3. Choose an analysis type from the dropdown menu:
   - General Analysis
   - UI Interaction Analysis
   - Emotion Detection
   - Object Detection
   - Text Recognition
   - Custom (allows you to enter a custom prompt)
4. If you selected "Custom", enter your custom analysis prompt.
5. Click "Upload and Analyze" to process the video.
6. For large videos, you'll see a progress bar indicating the upload and processing progress.
7. Once complete, the app will display:
   - The filename of the uploaded video
   - The selected analysis type (and custom prompt if applicable)
   - For each chunk (if applicable):
     - The number of frames extracted
     - The GPT-4 analysis of the video content based on the selected analysis type
8. You can download the analysis results in JSON, PDF, or Markdown format using the provided download buttons.

## Features

- Video upload and frame extraction using OpenCV
- GPT-4 integration for video content analysis
- User-friendly interface with error handling and loading states
- Responsive design for various screen sizes
- Caching mechanism for processed videos to improve performance
- Support for large video files through chunked uploads and progressive analysis
- Multiple predefined analysis types and custom prompt option
- Download analysis results in JSON, PDF, or Markdown format

## Development

To set up the project for development:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/video-analysis-app.git
   cd video-analysis-app
   ```

2. Follow the installation steps for both backend and frontend.

3. Make your changes and test them using the development servers.

4. To build the frontend for production:
   ```
   cd frontend
   npm run build
   ```

## Troubleshooting

If you encounter issues with the OpenAI API, ensure that:
1. Your API key is correctly set in the `.env` file
2. You have sufficient credits in your OpenAI account
3. You have access to the GPT-4 API (as it may be in limited beta)

For other issues, check the console logs in both the frontend and backend for error messages.

## Contributing

Contributions to improve the app are welcome. Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.
