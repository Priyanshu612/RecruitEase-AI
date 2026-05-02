# ============================================================
#           WebEarl Technologies — Main HR Pipeline
# ============================================================

import os
import sys
from datetime import datetime
from email_reader import get_unread_job_emails
from resume_parser import parse_resume
from excel_writer import add_candidate_to_excel, print_all_candidates
from calendar_scheduler import schedule_interview
from email_sender import send_interview_invitation
from config import COMPANY_NAME, OUTPUTS_FOLDER, EXCEL_FILE_NAME


def print_banner():
    """
    Prints welcome banner.
    """
    print("\n" + "="*60)
    print("       WebEarl Technologies — HR Automation System")
    print("="*60)
    print(f"  Company  : {COMPANY_NAME}")
    print(f"  Started  : {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    print("="*60 + "\n")


def print_separator():
    print("\n" + "-"*60 + "\n")


def confirm_action(prompt):
    """
    Asks user for yes/no confirmation.
    """
    while True:
        choice = input(f"\n  {prompt} (y/n): ").strip().lower()
        if choice in ["y", "yes"]:
            return True
        elif choice in ["n", "no"]:
            return False
        else:
            print("  ⚠️  Please enter y or n")


def process_single_candidate(email_data, index, total):
    """
    Processes a single candidate — parse, schedule, save, notify.
    """
    print_separator()
    print(f"  👤 Processing Candidate {index} of {total}")
    print(f"  📧 Email   : {email_data['sender_email']}")
    print(f"  📋 Subject : {email_data['subject']}")
    print_separator()

    results = {
        "email_data": email_data,
        "candidate_info": None,
        "interview_info": None,
        "excel_saved": False,
        "email_sent": False,
    }

    # -------------------------------------------------------
    # STEP 1 — Parse Resume
    # -------------------------------------------------------
    print("  📄 STEP 1: Parsing resume and extracting info...")
    try:
        candidate_info = parse_resume(email_data)
        results["candidate_info"] = candidate_info

        print(f"\n  ✅ Candidate Info Extracted:")
        print(f"     👤 Name    : {candidate_info['name']}")
        print(f"     📧 Email   : {candidate_info['email']}")
        print(f"     📱 Phone   : {candidate_info['phone']}")
        print(f"     📍 Address : {candidate_info['address']}")
        print(f"     💼 Role    : {candidate_info['job_role']}")
        print(f"     📋 Type    : {candidate_info['application_type']}")

    except Exception as e:
        print(f"  ❌ Resume parsing failed: {e}")
        print("  ⏭️  Skipping this candidate")
        return results

    # -------------------------------------------------------
    # STEP 2 — Schedule Interview
    # -------------------------------------------------------
    print_separator()
    print("  📅 STEP 2: Scheduling interview...")

    schedule_now = confirm_action(
        f"Schedule interview for {candidate_info['name']}?"
    )

    if schedule_now:
        try:
            interview_info = schedule_interview(candidate_info)
            results["interview_info"] = interview_info

            if interview_info:
                print(f"\n  ✅ Interview Scheduled:")
                print(f"     📅 Date  : {interview_info['date']}")
                print(f"     🕐 Time  : {interview_info['time']}")
                print(f"     🔗 Link  : {interview_info.get('event_link', 'N/A')}")
            else:
                print("  ⚠️  Interview scheduling failed — continuing without it")

        except Exception as e:
            print(f"  ❌ Scheduling error: {e}")
            print("  ⚠️  Continuing without interview scheduling")
    else:
        print("  ⏭️  Interview scheduling skipped")

    # -------------------------------------------------------
    # STEP 3 — Save to Excel
    # -------------------------------------------------------
    print_separator()
    print("  📊 STEP 3: Saving to Excel sheet...")

    try:
        saved = add_candidate_to_excel(
            candidate_info,
            results["interview_info"]
        )
        results["excel_saved"] = saved

        if saved:
            excel_path = os.path.join(OUTPUTS_FOLDER, EXCEL_FILE_NAME)
            print(f"  ✅ Saved to Excel: {excel_path}")
        else:
            print("  ⚠️  Could not save to Excel")

    except Exception as e:
        print(f"  ❌ Excel save error: {e}")

    # -------------------------------------------------------
    # STEP 4 — Send Interview Invitation Email
    # -------------------------------------------------------
    if results["interview_info"]:
        print_separator()
        print("  📧 STEP 4: Sending interview invitation email...")

        send_now = confirm_action(
            f"Send interview invite to {candidate_info['email']}?"
        )

        if send_now:
            try:
                sent = send_interview_invitation(
                    candidate_info,
                    results["interview_info"]
                )
                results["email_sent"] = sent

                if sent:
                    print(f"  ✅ Invitation sent to {candidate_info['email']}")
                else:
                    print("  ⚠️  Could not send invitation email")

            except Exception as e:
                print(f"  ❌ Email send error: {e}")
        else:
            print("  ⏭️  Email invitation skipped")
    else:
        print_separator()
        print("  📧 STEP 4: Skipped — no interview scheduled yet")

    return results


def print_final_summary(all_results):
    """
    Prints final summary of all processed candidates.
    """
    print("\n" + "="*60)
    print("  📋 Final Processing Summary")
    print("="*60)

    total = len(all_results)
    parsed = sum(1 for r in all_results if r["candidate_info"])
    scheduled = sum(1 for r in all_results if r["interview_info"])
    excel_saved = sum(1 for r in all_results if r["excel_saved"])
    emails_sent = sum(1 for r in all_results if r["email_sent"])

    print(f"\n  Total Applications Found  : {total}")
    print(f"  ✅ Resumes Parsed          : {parsed}")
    print(f"  📅 Interviews Scheduled    : {scheduled}")
    print(f"  📊 Saved to Excel          : {excel_saved}")
    print(f"  📧 Invitations Sent        : {emails_sent}")

    print("\n" + "-"*60)
    print("  Candidate Details:")
    print("-"*60)

    for i, result in enumerate(all_results, 1):
        candidate = result.get("candidate_info")
        interview = result.get("interview_info")

        if candidate:
            print(f"\n  [{i}] {candidate['name']}")
            print(f"      📧 {candidate['email']}")
            print(f"      💼 {candidate['job_role']} ({candidate['application_type']})")

            if interview:
                print(f"      📅 Interview: {interview['date']} at {interview['time']}")
                print(f"      📬 Invite Sent: {'Yes ✅' if result['email_sent'] else 'No ❌'}")
            else:
                print(f"      📅 Interview: Not scheduled")

    print("\n" + "="*60)
    excel_path = os.path.join(OUTPUTS_FOLDER, EXCEL_FILE_NAME)
    print(f"  💾 Excel File: {excel_path}")
    print("="*60 + "\n")


def run_pipeline():
    """
    Main pipeline — runs the complete HR automation workflow.
    """
    print_banner()

    # -------------------------------------------------------
    # PHASE 1 — Fetch Emails
    # -------------------------------------------------------
    print("  📬 PHASE 1: Checking Gmail for new applications...\n")

    try:
        email_list = get_unread_job_emails()
    except Exception as e:
        print(f"  ❌ Could not fetch emails: {e}")
        sys.exit(1)

    if not email_list:
        print("\n  📭 No new job application emails found.")
        print("  💡 Make sure:")
        print("     → Emails are unread")
        print("     → Emails have PDF/DOC resume attached")
        print("     → Subject contains job-related keywords")
        print("\n  ✅ Pipeline finished — nothing to process\n")
        return

    total = len(email_list)
    print(f"\n  ✅ Found {total} new application(s) to process")

    # Ask before processing
    proceed = confirm_action(f"Process all {total} application(s) now?")
    if not proceed:
        print("\n  ⏹️  Pipeline cancelled by user\n")
        return

    # -------------------------------------------------------
    # PHASE 2 — Process Each Candidate
    # -------------------------------------------------------
    print(f"\n  👥 PHASE 2: Processing {total} candidate(s)...\n")

    all_results = []

    for index, email_data in enumerate(email_list, 1):
        try:
            result = process_single_candidate(email_data, index, total)
            all_results.append(result)
        except Exception as e:
            print(f"\n  ❌ Unexpected error for candidate {index}: {e}")
            print("  ⏭️  Moving to next candidate...")
            continue

    # -------------------------------------------------------
    # PHASE 3 — Final Summary
    # -------------------------------------------------------
    print("\n  📊 PHASE 3: Generating summary...\n")
    print_final_summary(all_results)

    # Show all candidates in Excel
    view_all = confirm_action("View all candidates in Excel summary?")
    if view_all:
        print_all_candidates()

    print("\n  🎉 HR Automation Pipeline completed successfully!")
    print(f"  📂 Check your Excel file at: {os.path.join(OUTPUTS_FOLDER, EXCEL_FILE_NAME)}\n")


# -------------------------------------------------------
# Entry Point
# -------------------------------------------------------
if __name__ == "__main__":
    run_pipeline()