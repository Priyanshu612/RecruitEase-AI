# ============================================================
#           WebEarl Technologies — HR Automation Config
# ============================================================

# --- Company Info ---
COMPANY_NAME = "WebEarl Technologies Pvt Ltd."
COMPANY_WEBSITE = "https://webearl.com"
COMPANY_ADDRESS = "11 Cradle, EDII, Gandhinagar-Ahmedabad Rd, Bhat, Ahmedabad, Gujarat 382428"
INTERVIEW_MODE = "Offline (In-Person)"
INTERVIEW_LOCATION = "11 Cradle, EDII, Gandhinagar-Ahmedabad Rd, Next to Apollo Hospital, Bhat, Ahmedabad, Gujarat 382428"

# --- Your Gmail (the one connected to Google Cloud) ---
COMPANY_EMAIL = "priyanshu.webearltechnologies@gmail.com"  # Replace with your actual Gmail

# --- Job Roles WebEarl Offers ---
JOB_ROLES = [
    "Web Developer",
    "Frontend Developer",
    "Backend Developer",
    "Fullstack Developer",
    "Mobile App Developer",
    "Android Developer",
    "iOS Developer",
    "Flutter Developer",
    "Game Developer",
    "Digital Marketing Executive",
    "E-Commerce Developer",
    "CRM Developer",
    "ERP Developer",
    "API Developer",
    "UI/UX Designer",
    "AI/ML Developer Intern",
    "Social Media Creator Intern",
    "Software Developer Intern",
    "Web Developer Intern",
]

# --- Interview Schedule Settings ---
WORKING_DAYS = [0, 1, 2, 3, 4]        # 0=Monday, 4=Friday (Sat & Sun off)
DAYS_AFTER_APPLICATION = 3             # Auto schedule 3 working days later

# --- Available Interview Time Slots (24hr format) ---
INTERVIEW_SLOTS = [
    "11:00",
    "12:00",
    "14:00",   # 2:00 PM
    "15:00",   # 3:00 PM
    "16:00",   # 4:00 PM
]

INTERVIEW_DURATION_MINUTES = 30        # Each interview = 30 minutes
LUNCH_BREAK_START = "13:00"            # 1:00 PM
LUNCH_BREAK_END = "14:00"              # 2:00 PM

# --- Folder Paths ---
RESUMES_FOLDER = "resumes"             # Downloaded resumes saved here
MODELS_FOLDER = "models"               # Hugging Face models saved here
OUTPUTS_FOLDER = "outputs"             # Excel sheet saved here

# --- Excel Sheet Settings ---
EXCEL_FILE_NAME = "candidates.xlsx"
EXCEL_COLUMNS = [
    "Date Received",
    "Candidate Name",
    "Email",
    "Phone",
    "Address",
    "Job Role Applied",
    "Application Type",    # Internship or Full-Time
    "Skills",
    "Resume File",
    "Interview Date",
    "Interview Time",
    "Interview Status",    # Scheduled / Rescheduled / Done
    "Calendar Event ID",   # Saved for rescheduling later
]

# --- Email Templates ---
INTERVIEW_EMAIL_SUBJECT = "Interview Invitation — {role} | WebEarl Technologies"

INTERVIEW_EMAIL_BODY = """
Dear {candidate_name},

Thank you for applying for the {role} position at WebEarl Technologies Pvt Ltd.

We are pleased to inform you that we have reviewed your application and would like to invite you for an interview.

Interview Details:
------------------
Date       : {interview_date}
Time       : {interview_time}
Mode       : Online (Google Meet / Zoom link will be shared shortly)
Company    : WebEarl Technologies Pvt Ltd.
Website    : https://webearl.com

Please confirm your availability by replying to this email.

If you need to reschedule, feel free to reach out to us at {company_email}

We look forward to speaking with you!

Best Regards,
HR Team
WebEarl Technologies Pvt Ltd.
{company_address}
{company_website}
"""

# --- Google API Scopes (do not change) ---
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]

ALL_SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES

# --- Hugging Face Model Names (downloaded once, run locally) ---
NER_MODEL = "dslim/bert-base-NER"                    # Name, address extraction
JOB_MODEL = "jjzha/jobbert-base-cased"               # Job role & skills extraction
CLASSIFIER_MODEL = "facebook/bart-large-mnli"        # Internship vs Full-time