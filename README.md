# Sermon Ingestion Engine & ProPresenter Compiler

A high-fidelity web application and python compilation engine designed to parse sermon notes (PDF/DOCX), fetch scriptures via Bolls Bible API, auto-split slides using grammatical scoring, format themes dynamically (Midtown Landscape vs. Downtown Vertical), and compile a downloadable ProPresenter `.pro` presentation file.

---

## 🚀 Quick Start with Docker (Recommended)

To run the application in a fully self-contained environment without manual python/node package setups:

1. **Ensure Docker is installed** and running on your system.
2. **Open a terminal** in the `sermon_ingest` directory.
3. **(Optional)** Inject your Gemini API Key directly into the container by setting it in your shell environment:
   - **Windows PowerShell**:
     ```powershell
     $env:GEMINI_API_KEY="your-api-key-here"
     ```
   - **Linux / macOS**:
     ```bash
     export GEMINI_API_KEY="your-api-key-here"
     ```
     _(Note: You can also enter your API Key directly on the dashboard page at runtime)_
4. **Launch the container**:
   ```bash
   docker compose up --build
   ```
5. **Open your web browser** and navigate to:
   ```
   http://localhost:3000
   ```

---

## 💻 Native Local Execution (Development)

If you prefer to run the application natively on your local machine:

### Prerequisites

- **Python 3.10+** (tested on 3.11)
- **Node.js 18+** (tested on 20 & 24)

### 1. Python Backend Installation

Install python libraries required for PDF reading and Word Document parsing:

```bash
pip install -r requirements.txt
```

### 2. Next.js Frontend Installation

Navigate to the `web_app` directory and install NPM packages:

```bash
cd web_app
npm install
```

### 3. Start Development Server

Run the dev command from inside `web_app`:

```bash
npm run dev
```

Open **`http://localhost:3000`** in your browser.

---

## 📂 Project Structure

- `main.py`: Main python entrypoint orchestrating parsing, scripture fetches, and compiler builders.
- `ProCore/`: Self-contained folder containing ProPresenter 7 Protobuf structures and compiled pb2 classes.
- `web_app/`: Next.js App Router project folder.
  - `src/app/page.js`: Premium glassmorphic React dashboard with slide previews.
  - `src/app/globals.css`: Vanilla CSS design system (neon overlays, tab grids, responsive layout proportions).
  - `src/app/api/ingest/route.js`: Serverless-style API endpoint invoking Python compilers as child processes.
  - `src/app/api/download/route.js`: File streaming endpoint that serves compiled `.pro` binary packages.
- `cache/`: Local cache directory preserving scriptures and AI JSON extractions (optimizes rate quotas).
- `requirements.txt`: Python package configurations (`pymupdf`, `python-docx`, `pillow`).

---

## ⚙️ Configuration Options

- **Location / Screen Theme**:
  - **Midtown**: Generates `1920x1080` landscape slides using bold headers and a standard body text box.
  - **Downtown**: Generates `840x1080` vertical slides using regular font-weights matching the `HenusRegular` format. Fits fewer characters per slide, automatically distributing verses across more pages.
- **Bible Translation**: Choose NASB, ESV, KJV, WEB, BSB, or use defaults mentioned in sermon notes.
- **AI Ingestion Agent**:
  - **Enabled**: Employs Gemini agentic models to split scripture clauses and parse point headers.
  - **Disabled (Default)**: Falls back to a manual heuristic parser and grammatical dynamic programming splitter. Runs 100% locally and is immune to internet failures or rate-limiting quotas.
