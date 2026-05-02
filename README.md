# RecruitEase AI
### Intelligent HR Automation System by Priyanshu Biswas

An end-to-end recruitment automation system that reads job application emails, parses resumes using AI, schedules interviews, sends professional email invitations, and manages candidate responses — all powered by free, locally running Hugging Face models with zero subscription cost.

---

## Overview

RecruitEase AI handles the complete recruitment pipeline automatically:

```
Email Arrives  ->  Resume Parsed  ->  Excel Updated  ->  Interview Scheduled  ->  Invite Sent  ->  Responses Handled
```

No paid APIs. No ChatGPT. No subscriptions. Everything runs locally and free forever.

---

## Features

| Feature | Description |
|---|---|
| Gmail Reader | Reads unread job application emails automatically |
| Resume Parser | Extracts name, phone, address and skills from PDF and Word resumes |
| AI Classification | Uses Hugging Face models to detect job roles and candidate response types |
| Excel Writer | Auto fills candidate data into a clean formatted Excel sheet |
| Interview Scheduler | Schedules interviews on Google Calendar with reminders |
| Email Sender | Sends professional HTML interview invitations |
| Response Handler | Detects and handles candidate replies — confirm, reschedule, reject, questions |
| Auto Reminders | Sends reminder emails 2 days and 1 day before interview automatically |

---

## Project Structure

```
RecruitEase-AI/
│
├── config.py                  # Company settings, job roles, email templates
├── auth.py                    # Google OAuth2 authentication
├── email_reader.py            # Gmail reader — fetches job application emails
├── resume_parser.py           # AI powered resume text extraction
├── excel_writer.py            # Auto fills candidates.xlsx
├── calendar_scheduler.py      # Google Calendar interview scheduling
├── email_sender.py            # Sends HTML interview invitation emails
├── response_handler.py        # Handles candidate replies intelligently
├── run_pipeline.py            # Main pipeline — run this to process applications
│
├── requirements.txt           # All Python dependencies
├── README.md                  # This file
├── .gitignore                 # Files excluded from GitHub
│
├── templates/                 # HTML email templates
│   ├── interview_invite.html  # First interview invitation
│   ├── confirmation_ack.html  # When candidate confirms
│   ├── reschedule_invite.html # When interview is rescheduled
│   ├── rejection_ack.html     # When candidate withdraws
│   ├── reminder.html          # 2 days before reminder
│   └── followup.html          # 1 day before final follow up
│
├── resumes/                   # Downloaded resumes — auto created, not on GitHub
├── models/                    # Hugging Face models — download separately
└── outputs/                   # candidates.xlsx saved here — auto created
```

---

## System Requirements

- Python 3.10 or higher
- Windows 10/11 (tested), also works on Mac and Linux
- Stable internet connection for first time model download and Google API
- Google account with Gmail and Google Calendar
- Approximately 3GB free disk space for AI models

---

## Installation

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/RecruitEase-AI.git
cd RecruitEase-AI
```

### Step 2 — Create Required Folders

```bash
mkdir resumes models outputs
```

### Step 3 — Install All Dependencies

```bash
pip install -r requirements.txt
```

This may take 5 to 10 minutes depending on your internet speed. PyTorch alone is around 800MB.

### Step 4 — Download AI Models

See the AI Models section below for direct download links and commands.

### Step 5 — Set Up Google API Credentials

See the Google API Setup section below for step by step instructions.

### Step 6 — Configure Your Settings

Open `config.py` and update your Gmail address:

```python
COMPANY_EMAIL = "your_gmail@gmail.com"
```

### Step 7 — Authenticate with Google

```bash
python auth.py
```

A browser window will open. Log in with your Gmail and click Allow.
A `token.json` file will be created automatically. This only happens once.

### Step 8 — Run the Pipeline

```bash
python run_pipeline.py
```

---

## AI Models — Download Instructions

Models are not included in this repository due to large file size (approximately 2GB total). Run the commands below to download them directly into your models folder.

### Model 1 — BERT NER
Used for extracting candidate name and address from resumes.
Model ID: `dslim/bert-base-NER`
Size: approximately 400MB
Direct link: https://huggingface.co/dslim/bert-base-NER

Download command:
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
AutoTokenizer.from_pretrained("dslim/bert-base-NER", cache_dir="models")
AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER", cache_dir="models")
```

### Model 2 — BART Large MNLI
Used for classifying job roles and detecting candidate response types (confirm, reschedule, reject, question).
Model ID: `facebook/bart-large-mnli`
Size: approximately 1.6GB
Direct link: https://huggingface.co/facebook/bart-large-mnli

Download command:
```python
from transformers import pipeline
pipeline("zero-shot-classification", model="facebook/bart-large-mnli", cache_dir="models")
```

Easiest method: Simply run `python resume_parser.py` once after installation. It will automatically download both models to your models folder. After that, everything runs fully offline with no internet required.

---

## Google API Setup

### Step 1 — Create Google Cloud Project
1. Go to console.cloud.google.com
2. Sign in with the Gmail that receives job applications
3. Click the project dropdown at the top and select New Project
4. Name it RecruitEase and click Create

### Step 2 — Enable APIs
1. Go to APIs and Services then Library
2. Search for Gmail API and click Enable
3. Go back to Library
4. Search for Google Calendar API and click Enable

### Step 3 — OAuth Consent Screen
1. Go to APIs and Services then OAuth consent screen
2. Select External and click Create
3. Fill in App name and your Gmail address
4. Add your Gmail as a Test User
5. Click Save and Continue through all steps

### Step 4 — Create Credentials
1. Go to APIs and Services then Credentials
2. Click Create Credentials and select OAuth Client ID
3. Select Desktop app as application type
4. Click Create and download the JSON file
5. Rename the downloaded file to exactly `credentials.json`
6. Place it inside the RecruitEase-AI folder

### Step 5 — First Run
```bash
python auth.py
```
Browser opens, you log in, click Allow, done. Never needs login again after this.

---

## Configuration

Open `config.py` and update the following:

```python
# Company details
COMPANY_NAME    = "Your Company Name"
COMPANY_EMAIL   = "your_gmail@gmail.com"
COMPANY_WEBSITE = "https://yourwebsite.com"
COMPANY_ADDRESS = "Your Full Office Address"

# Interview settings
INTERVIEW_MODE     = "Offline (In-Person)"
INTERVIEW_LOCATION = "Your Full Office Address"

# Schedule settings
WORKING_DAYS           = [0, 1, 2, 3, 4]    # 0 is Monday, 4 is Friday
DAYS_AFTER_APPLICATION = 3                   # Auto schedule 3 working days later
INTERVIEW_SLOTS        = ["11:00", "12:00", "14:00", "15:00", "16:00"]

# Job roles your company offers
JOB_ROLES = [
    "Web Developer",
    "AI/ML Developer",
    "Data Science",
    "Mobile App Developer",
    # Add more roles here
]
```

---

## How to Run

### Process New Job Applications
```bash
python run_pipeline.py
```
Scans Gmail, downloads resumes, parses candidate info, schedules interview, sends invite, saves to Excel.

### Handle Candidate Replies
```bash
python response_handler.py
```
Scans Gmail for replies, AI detects intent, handles confirm, reschedule, reject and question automatically.

### Test Individual Modules
```bash
python auth.py                  # Test Google connection
python email_reader.py          # Test Gmail reading
python resume_parser.py         # Test resume parsing
python excel_writer.py          # Test Excel writing
python email_sender.py          # Test email sending
python calendar_scheduler.py    # Test interview scheduling
```

---

## Tech Stack

| Technology | Purpose | Cost |
|---|---|---|
| Python 3.13 | Core language | Free |
| Gmail API | Read and send emails | Free |
| Google Calendar API | Schedule interviews | Free |
| dslim/bert-base-NER | Extract names and addresses from resumes | Free |
| facebook/bart-large-mnli | Classify job roles and candidate responses | Free |
| pdfplumber | Read PDF resumes | Free |
| python-docx | Read Word resumes | Free |
| openpyxl | Write and format Excel sheets | Free |
| transformers + PyTorch | Run AI models locally offline | Free |

---

## Privacy and Security

The following files are excluded from this repository:

| File | Reason |
|---|---|
| credentials.json | Google OAuth client secret — never share this |
| token.json | Your personal Google access token |
| models/ | Too large at approximately 2GB — download separately |
| resumes/ | Contains candidate personal data |
| outputs/ | Contains candidate Excel database |
| .env | Environment variables — removed for privacy |

Never commit credentials.json or token.json to any public or private repository.

---

## About

Built by Priyanshu Biswas
Built with purpose — 100% Free, Open Source, Zero Paid APIs
