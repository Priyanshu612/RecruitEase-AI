# ============================================================
#           WebEarl Technologies — Resume Parser
# ============================================================

import os
import re
import pdfplumber
from docx import Document
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from config import MODELS_FOLDER, JOB_ROLES, RESUMES_FOLDER
# --- Model Names ---
NER_MODEL_NAME = "dslim/bert-base-NER"
CLASSIFIER_MODEL_NAME = "facebook/bart-large-mnli"

# --- Global model variables (loaded once, reused) ---
ner_pipeline = None
classifier_pipeline = None


def load_models():
    """
    Loads Hugging Face models.
    Downloads on first run, uses cached version after that.
    """
    global ner_pipeline, classifier_pipeline

    os.makedirs(MODELS_FOLDER, exist_ok=True)
    cache_dir = os.path.abspath(MODELS_FOLDER)

    # --- Load NER Model ---
    if ner_pipeline is None:
        print("\n🤖 Loading NER model (for name/email/phone extraction)...")
        print("   (First time: downloading ~400MB — please wait...)")
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                NER_MODEL_NAME,
                cache_dir=cache_dir
            )
            model = AutoModelForTokenClassification.from_pretrained(
                NER_MODEL_NAME,
                cache_dir=cache_dir
            )
            ner_pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple"
            )
            print("✅ NER model loaded successfully!")
        except Exception as e:
            print(f"❌ Could not load NER model: {e}")
            ner_pipeline = None

    # --- Load Classifier Model ---
    if classifier_pipeline is None:
        print("\n🤖 Loading classifier model (for job role detection)...")
        print("   (First time: downloading ~1.6GB — please wait...)")
        try:
            classifier_pipeline = pipeline(
                "zero-shot-classification",
                model=CLASSIFIER_MODEL_NAME,
                cache_dir=cache_dir
            )
            print("✅ Classifier model loaded successfully!")
        except Exception as e:
            print(f"❌ Could not load classifier model: {e}")
            classifier_pipeline = None


def read_resume_text(resume_path):
    """
    Reads text from PDF or Word resume file.
    """
    text = ""
    ext = os.path.splitext(resume_path.lower())[1]

    try:
        if ext == ".pdf":
            with pdfplumber.open(resume_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        elif ext in [".doc", ".docx"]:
            doc = Document(resume_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"

        else:
            print(f"⚠️  Unsupported file format: {ext}")
            return ""

    except Exception as e:
        print(f"❌ Error reading resume file: {e}")
        return ""

    return text.strip()


def extract_email_from_text(text):
    """
    Extracts email address using regex.
    """
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    matches = re.findall(pattern, text)
    return matches[0] if matches else ""


def extract_phone_from_text(text):
    """
    Extracts phone number using regex.
    Handles Indian and international formats.
    """
    patterns = [
        r"(\+91[\s\-]?)?[6-9]\d{9}",           # Indian mobile
        r"\+?[\d\s\-\(\)]{10,15}",              # General international
        r"\b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b",    # US format
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            phone = re.sub(r"[^\d+]", "", matches[0])
            if len(phone) >= 10:
                return phone
    return ""


def extract_name_from_ner(text):
    """
    Extracts candidate name using BERT NER model.
    Falls back to first line of resume if NER fails.
    """
    if ner_pipeline is None:
        return extract_name_fallback(text)

    try:
        # Use first 512 characters for name extraction
        short_text = text[:512]
        entities = ner_pipeline(short_text)

        # Find PERSON entities
        person_names = []
        for entity in entities:
            if entity["entity_group"] == "PER" and entity["score"] > 0.85:
                name = entity["word"].strip()
                if len(name) > 2:
                    person_names.append(name)

        if person_names:
            # Return the longest person name found (most likely full name)
            return max(person_names, key=len)

    except Exception as e:
        print(f"⚠️  NER name extraction failed: {e}")

    return extract_name_fallback(text)


def extract_name_fallback(text):
    """
    Fallback: tries to get name from first non-empty line of resume.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:
        # Name lines are usually short (2-5 words) and no special characters
        words = line.split()
        if 2 <= len(words) <= 5 and all(w.replace("-", "").isalpha() for w in words):
            return line
    return ""


def extract_address_from_text(text):
    """
    Extracts address using NER and keyword patterns.
    """
    if ner_pipeline is None:
        return extract_address_fallback(text)

    try:
        # Process in chunks of 512 chars
        chunks = [text[i:i+512] for i in range(0, min(len(text), 2048), 512)]
        locations = []

        for chunk in chunks:
            entities = ner_pipeline(chunk)
            for entity in entities:
                if entity["entity_group"] == "LOC" and entity["score"] > 0.80:
                    loc = entity["word"].strip()
                    if len(loc) > 2:
                        locations.append(loc)

        if locations:
            return ", ".join(list(dict.fromkeys(locations)))  # Remove duplicates

    except Exception as e:
        print(f"⚠️  NER address extraction failed: {e}")

    return extract_address_fallback(text)


def extract_address_fallback(text):
    """
    Fallback: looks for address keywords in text.
    """
    address_keywords = [
        "address", "location", "city", "state", "pin", "pincode",
        "street", "road", "nagar", "colony", "gujarat", "ahmedabad",
        "mumbai", "delhi", "bangalore", "pune", "hyderabad"
    ]
    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in address_keywords):
            clean = line.replace("Address:", "").replace("Location:", "").strip()
            if clean:
                return clean
    return ""


def extract_skills_from_text(text):
    """
    Extracts skills and technologies from resume text.
    Uses keyword matching against common tech skills.
    """
    common_skills = [
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "php",
        "swift", "kotlin", "dart", "go", "rust", "r", "scala",

        # Web Development
        "html", "css", "react", "angular", "vue", "nodejs", "express",
        "django", "flask", "laravel", "bootstrap", "jquery", "nextjs",

        # Mobile
        "flutter", "android", "ios", "react native", "xamarin",

        # AI/ML
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
        "numpy", "opencv", "hugging face", "bert", "gpt",

        # Database
        "mysql", "postgresql", "mongodb", "sqlite", "firebase",
        "redis", "oracle", "sql",

        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "git",
        "github", "linux", "jenkins", "ci/cd",

        # Design
        "figma", "adobe xd", "photoshop", "illustrator", "canva",
        "ui/ux", "wireframing", "prototyping",

        # Digital Marketing
        "seo", "sem", "google ads", "facebook ads", "instagram",
        "content creation", "social media", "email marketing",
        "google analytics", "wordpress",

        # Game Development
        "unity", "unreal engine", "blender", "c#", "game design",

        # General
        "excel", "powerpoint", "communication", "leadership",
        "problem solving", "teamwork", "agile", "scrum",
    ]

    text_lower = text.lower()
    found_skills = []

    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())

    return ", ".join(found_skills) if found_skills else "Not specified"


def detect_job_role(subject, body, resume_text):
    """
    Detects the job role being applied for.
    First checks email subject, then uses AI classifier.
    """
    combined_text = f"{subject} {body} {resume_text[:500]}"
    combined_lower = combined_text.lower()

    # First try direct keyword matching from subject/body
    for role in JOB_ROLES:
        if role.lower() in combined_lower:
            return role

    # Use AI zero-shot classifier as fallback
    if classifier_pipeline is not None:
        try:
            result = classifier_pipeline(
                combined_text[:1000],
                candidate_labels=JOB_ROLES,
                multi_label=False
            )
            top_role = result["labels"][0]
            top_score = result["scores"][0]

            if top_score > 0.30:
                return top_role
        except Exception as e:
            print(f"⚠️  Job role classification failed: {e}")

    return "Not specified"


def detect_application_type(subject, body):
    """
    Detects if application is for Internship or Full-Time job.
    """
    text = (subject + " " + body).lower()

    internship_keywords = ["intern", "internship", "training", "fresher", "student"]
    fulltime_keywords = ["full time", "full-time", "permanent", "experienced", "job opening"]

    intern_score = sum(1 for kw in internship_keywords if kw in text)
    fulltime_score = sum(1 for kw in fulltime_keywords if kw in text)

    if intern_score > fulltime_score:
        return "Internship"
    elif fulltime_score > intern_score:
        return "Full-Time"
    else:
        return "Not specified"


def parse_resume(email_data):
    """
    Main function — parses resume and extracts all candidate info.
    Takes email_data from email_reader.py and returns candidate info dict.
    """
    print(f"\n📄 Parsing resume for: {email_data['sender_email']}")

    resume_path = email_data.get("resume_path", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")
    sender_name = email_data.get("sender_name", "")
    sender_email = email_data.get("sender_email", "")

    # Read resume text
    resume_text = ""
    if resume_path and resume_path != "No attachment" and os.path.exists(resume_path):
        print(f"   📖 Reading resume file...")
        resume_text = read_resume_text(resume_path)
        if resume_text:
            print(f"   ✅ Resume text extracted ({len(resume_text)} characters)")
        else:
            print(f"   ⚠️  Could not extract text from resume")
    else:
        print(f"   ⚠️  No resume file found, using email body only")

    # Combine all available text
    all_text = f"{body}\n{resume_text}"

    # Load AI models
    load_models()

    # --- Extract all info ---
    print(f"   🔍 Extracting candidate information...")

    # Name — use sender name from email if available, else extract from resume
    name = sender_name if sender_name else extract_name_from_ner(resume_text if resume_text else body)

    # Email — use sender email from Gmail (most reliable)
    email = sender_email if sender_email else extract_email_from_text(all_text)

    # Phone
    phone = extract_phone_from_text(all_text)

    # Address
    address = extract_address_from_text(resume_text if resume_text else body)

    # Skills
    skills = extract_skills_from_text(all_text)

    # Job Role
    job_role = detect_job_role(subject, body, resume_text)

    # Application Type
    app_type = detect_application_type(subject, body)

    candidate_info = {
        "name": name if name else "Unknown",
        "email": email if email else sender_email,
        "phone": phone if phone else "Not found",
        "address": address if address else "Not found",
        "skills": skills,
        "job_role": job_role,
        "application_type": app_type,
        "resume_path": resume_path,
        "date_received": email_data.get("date_received", ""),
        "subject": subject,
    }

    print(f"\n   ✅ Extraction complete!")
    print(f"   👤 Name          : {candidate_info['name']}")
    print(f"   📧 Email         : {candidate_info['email']}")
    print(f"   📱 Phone         : {candidate_info['phone']}")
    print(f"   📍 Address       : {candidate_info['address']}")
    print(f"   💼 Job Role      : {candidate_info['job_role']}")
    print(f"   📋 Type          : {candidate_info['application_type']}")
    print(f"   🛠️  Skills        : {candidate_info['skills'][:80]}...")

    return candidate_info


def test_resume_parser():
    """
    Test resume parser — run this file directly to test.
    """
    print("\n" + "="*50)
    print("  WebEarl HR — Resume Parser Test")
    print("="*50)

    # Check if any resumes exist in resumes folder
    if not os.path.exists(RESUMES_FOLDER) or not os.listdir(RESUMES_FOLDER):
        print("\n⚠️  No resumes found in resumes/ folder")
        print("   Please run email_reader.py first to download resumes")
        return

    # Get first resume for testing
    resume_files = [f for f in os.listdir(RESUMES_FOLDER)
                   if f.endswith((".pdf", ".doc", ".docx"))]

    if not resume_files:
        print("\n⚠️  No PDF or Word files found in resumes/ folder")
        return

    # Create a dummy email_data for testing
    test_email_data = {
        "sender_name": "Test Candidate",
        "sender_email": "test@example.com",
        "subject": "Job Application — AI/ML Developer Intern",
        "body": "Hi, I am applying for the AI/ML Developer Intern position. Please find my resume attached.",
        "resume_path": os.path.join(RESUMES_FOLDER, resume_files[0]),
        "date_received": "2026-04-22",
    }

    print(f"\n📄 Testing with resume: {resume_files[0]}")
    candidate = parse_resume(test_email_data)

    print("\n" + "="*50)
    print("  Final Extracted Data:")
    print("="*50)
    for key, value in candidate.items():
        if key != "resume_path":
            print(f"  {key:20} : {value}")


# Run this file directly to test
if __name__ == "__main__":
    test_resume_parser()