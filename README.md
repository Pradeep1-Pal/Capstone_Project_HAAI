# CV Ranking Dashboard (Capstone_Project_HAAI)

A Streamlit-based intelligent dashboard that scores and ranks CVs against job descriptions using AI models (Gemini and Ollama with LangChain integration).

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Code Structure](#code-structure)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)


## Overview

This project provides an AI-powered solution for automated CV screening and ranking. It compares uploaded resumes against job descriptions and provides intelligent scoring using:

- **Gemini AI** - Google's advanced language model
- **Ollama** - Local model hosting for privacy-focused deployments
- **LangChain** - Framework for building LLM applications

## Prerequisites

Before installation, ensure you have the following:

### Required Software

- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **pip** - Python package manager (included with Python)

### Optional (for local model hosting)

- **Ollama** - Required only if you want to run models locally

#### Installing Ollama

**Windows:**
```powershell
# Download and install from official website
# Visit: https://ollama.com/download/windows
```
or 

```bash
# Using Winget
winget install Ollama.Ollama
```

**macOS:**
```bash
# Using Homebrew
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Managing Ollama Models

After installing Ollama, you can pull and run models:

**Pull a model (download):**
```bash
# Example: Pull Llama 3.1 8B model
ollama pull llama3.1:8b

# Pull other available models
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

**Run a model (start local server):**
```bash
# Example: Run Llama 3.1 8B
ollama run llama3.1:8b

# This starts the model server for inference
# The dashboard will connect to this local endpoint
```

## Installation

### Step 1: Install UV Package Manager

UV is a fast Python package installer and resolver used in this project.

```bash
pip install uv
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/Pradeep1-Pal/Capstone_Project_HAAI.git
cd Capstone_Project_HAAI
```

### Step 3: Sync Dependencies

The repository is already UV-initialized, so you only need to sync:

```bash
uv sync
```

This command will:
- Create a virtual environment (`.venv/`)
- Install all required dependencies
- Lock versions for reproducibility

### Step 4: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### Step 5: Run the Dashboard

```bash
streamlit run ui00Main.py
```

The dashboard will automatically open in your default browser at:
```
http://localhost:8501
```

## Code Structure

```
Capstone_Project_HAAI/
├── cvs/                          # Uploaded resume files (PDFs, DOCs)
│   └── [uploaded CVs]
│
├── jds/                          # Job description files
│   └── [uploaded JDs]
│
├── models/                       # AI model integrations
│   ├── gemini/                   # Google Gemini integration
│   │   ├── avilableModels.py    # List available Gemini models
│   │   ├── creds.py             # Gemini API credentials
│   │   ├── cvProcessingLLM_api.py          # Direct API integration
│   │   └── cvProcessingLLM_api_langchain.py # LangChain integration ⭐
│   │
│   ├── ollama/                   # Ollama local model integration
│   │   ├── avilableModels.py    # List available Ollama models
│   │   ├── cvProcessingLLM.py   # Direct Ollama integration
│   │   ├── cvProcessingLLM_langchain.py    # LangChain integration ⭐
│   │   └── modelDownloader.py   # Helper for model management
│   │
│   └── prompts/                  # Prompt templates
│       └── cvscoringPrompt.py   # CV scoring prompt templates
│
├── pages/                        # Streamlit UI pages
│   ├── ui02Dashboard.py         # Main dashboard view
│   ├── ui03UploadResume.py      # Resume upload interface
│   ├── ui04UploadJD.py          # Job description upload
│   ├── ui05Leaderboard.py       # Ranked results view
│   └── ui06Setting.py           # Application settings
│
├── ui00Main.py                   # Main application entry point ⭐
├── modelconfig.py                # Model configuration and setup ⭐
│
├── pyproject.toml                # Project metadata and dependencies
├── uv.lock                       # Locked dependency versions
├── job_descriptions.csv          # Sample/cached job descriptions
├── resume_database.csv           # Sample/cached resume data
└── README.md                     # This file

⭐ = Key files using LangChain framework
```

### Key Components

#### Models Directory
- **Gemini Integration**: Uses Google's Gemini API for cloud-based inference
  - Files with `langchain` suffix use LangChain framework
  - Provides enterprise-grade AI capabilities
  
- **Ollama Integration**: Local model hosting for privacy and offline use
  - Files with `langchain` suffix use LangChain framework
  - Supports various open-source models (Llama, Mistral, etc.)

- **Prompts**: Centralized prompt engineering templates
  - Ensures consistent CV scoring criteria
  - Easy to modify and version control

#### Pages Directory
Contains modular Streamlit pages for the multi-page application:
- Dashboard: Overview and analytics
- Upload Resume: CV file handling
- Upload JD: Job description management
- Leaderboard: Ranked candidate results
- Settings: Model and configuration management

#### Configuration Files
- `modelconfig.py`: Central configuration for model selection and API keys
- `pyproject.toml`: Python project metadata and dependency declarations
- `uv.lock`: Locked versions ensuring reproducible builds

## Usage

### Basic Workflow

1. **Start the application**
   ```bash
   streamlit run ui00Main.py
   ```

2. **Configure your model** (Settings page)
   - Choose between Gemini or Ollama
   - Select model
   - Set passing Threshold 

3. **Upload job description** (Upload JD page)
   - Paste or upload job description text
   - System will parse key requirements

4. **Upload resumes** (Upload Resume page)
   - Upload PDF or DOC format resumes
   - Bulk upload supported

5. **Dashboard** (Process Resume)
   - Select Job description
   - Select resumes
   - Start Processing.

6. **View rankings** (Leaderboard page)
   - See scored and ranked candidates
   - Export results



## Troubleshooting

### Common Issues

**Issue: "Activate.ps1 cannot be loaded" (Windows)**
```powershell
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Issue: "streamlit: command not found"**
```bash
# Ensure virtual environment is activated
# Then reinstall Streamlit:
pip install streamlit
```

**Issue: "Ollama connection refused"**
```bash
# Ensure Ollama is running:
ollama serve

# Or run a model which auto-starts the server:
ollama run llama3.1:8b
```

**Issue: "Module not found" errors**
```bash
# Resync dependencies:
uv sync

# Or manually install missing package:
pip install <package-name>
```

**Issue: UV sync fails**
```bash
# Clear UV cache and retry:
uv cache clean
uv sync
```

### Getting Help

- Check the [Issues](https://github.com/Pradeep1-Pal/Capstone_Project_HAAI/issues) page
- Review Streamlit logs in the terminal
- Verify all prerequisites are installed
- Ensure Python version is 3.9 or higher

