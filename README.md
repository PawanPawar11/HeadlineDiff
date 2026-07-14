# HeadlineDiff: Media Bias & Headline Evolution Tracker

HeadlineDiff is a media analysis dashboard that tracks how mainstream news outlets (BBC, CNN, NYTimes, Fox News) alter their headlines and adjust their editorial stance over time. It uses the **Internet Archive Wayback Machine CDX API** for real-time historical data retrieval and the **Google Gemini API** for semantic, bias, and framing analysis.

---

## Features

1. **Stealth Edits Tracker (Mode A):**
   * Paste an article URL from a major news outlet.
   * Fetch all historical snapshot captures recorded by the Wayback Machine.
   * View a chronological timeline showing when updates occurred.
   * Compare edits word-by-word with an in-app visual diff engine (added words highlighted in green, removed words in red).
   * Generates a detailed **AI Narrative Shift Report** mapping framing techniques, bias shifts, and intent.

2. **Narrative Drift Analyzer (Mode B):**
   * Search for a topic (e.g., *inflation*, *vaccines*, *election*) across a timeline (Today, 1 Month Ago, 3 Months Ago, 6 Months Ago, 1 Year Ago).
   * Scrapes matching headlines from the archived front sections of CNN, Fox News, NYTimes, and BBC at those exact points in history.
   * Reviews how the editorial stance and polarization of that topic shifted across the milestones.
   * Generates a **Polarization Index** and buzzword trends timeline.

---

## Technology Stack

* **Backend:** Python 3.10+, FastAPI (high performance API), BeautifulSoup4 & LXML (HTML scrapers), Google Generative AI (Gemini 1.5 Flash).
* **Frontend:** React, Vite, Vanilla CSS (premium dark-mode styling with glassmorphism), Lucide React (vector icon systems).

---

## Setup & Installation

### 1. Prerequisites
Ensure you have **Python 3.10+** and **Node.js** installed.

### 2. Configure Environment Variables
1. Navigate to the `backend/` directory.
2. Open the `.env` file (created automatically from `.env.example`).
3. Add your Gemini API Key (get one free at [Google AI Studio](https://aistudio.google.com/)):
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

---

## Running the Application

### The Easy Way (Windows Double-Click)
Double-click the **`run.bat`** file in the root directory. 
This will automatically launch the FastAPI server in one command prompt and the Vite frontend dev server in another, opening the application ready to go.

*Alternatively, run `run.ps1` from PowerShell.*

### The Manual Way

#### 1. Start the Backend
```bash
cd backend
# Activate the virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API will be available at `http://127.0.0.1:8000`.

#### 2. Start the Frontend
```bash
cd frontend
npm install  # (First time only)
npm run dev
```
Open `http://localhost:5173` in your browser.
