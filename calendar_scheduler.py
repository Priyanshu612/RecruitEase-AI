# ============================================================
#           WebEarl Technologies — Calendar Scheduler
# ============================================================

import os
from datetime import datetime, timedelta
from config import INTERVIEW_LOCATION
from auth import get_credentials
from config import (
    WORKING_DAYS, DAYS_AFTER_APPLICATION,
    INTERVIEW_SLOTS, INTERVIEW_DURATION_MINUTES,
    LUNCH_BREAK_START, LUNCH_BREAK_END,
    COMPANY_NAME, COMPANY_EMAIL, COMPANY_ADDRESS
)


def get_next_working_day(start_date, days_ahead):
    """
    Calculates next working day skipping weekends.
    """
    current_date = start_date
    working_days_counted = 0

    while working_days_counted < days_ahead:
        current_date += timedelta(days=1)
        if current_date.weekday() in WORKING_DAYS:
            working_days_counted += 1

    return current_date


def get_available_slots(calendar_service, interview_date):
    """
    Checks Google Calendar for already booked slots on interview date.
    Returns list of available time slots.
    """
    try:
        # Get start and end of the interview date
        date_start = datetime.combine(interview_date, datetime.min.time())
        date_end = datetime.combine(interview_date, datetime.max.time())

        # Fetch events from Google Calendar for that day
        events_result = calendar_service.events().list(
            calendarId="primary",
            timeMin=date_start.isoformat() + "Z",
            timeMax=date_end.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        booked_events = events_result.get("items", [])

        # Get booked times
        booked_times = []
        for event in booked_events:
            start = event.get("start", {}).get("dateTime", "")
            if start:
                booked_hour = datetime.fromisoformat(start.replace("Z", "")).strftime("%H:%M")
                booked_times.append(booked_hour)

        # Filter out booked slots and lunch break
        available = []
        for slot in INTERVIEW_SLOTS:
            if slot not in booked_times and slot != LUNCH_BREAK_START:
                available.append(slot)

        return available

    except Exception as e:
        print(f"   ⚠️  Could not check calendar availability: {e}")
        return INTERVIEW_SLOTS


def convert_to_12hr(time_24):
    """
    Converts 24hr time to 12hr format.
    Example: '14:00' → '2:00 PM'
    """
    try:
        dt = datetime.strptime(time_24, "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except:
        return time_24


def ask_user_for_date_confirmation(auto_date, candidate_name, job_role):
    """
    Shows auto-scheduled date and asks user to confirm or pick new date.
    """
    print("\n" + "="*55)
    print(f"  📅 Interview Scheduling — {candidate_name}")
    print("="*55)
    print(f"  Candidate  : {candidate_name}")
    print(f"  Job Role   : {job_role}")
    print(f"\n  Auto-scheduled date: {auto_date.strftime('%A, %d %B %Y')}")
    print("\n  Options:")
    print("  [1] Keep this date (recommended)")
    print("  [2] Pick a different date")
    print("-"*55)

    while True:
        choice = input("  Enter your choice (1 or 2): ").strip()
        if choice == "1":
            return auto_date
        elif choice == "2":
            return ask_user_for_custom_date()
        else:
            print("  ⚠️  Please enter 1 or 2")


def ask_user_for_custom_date():
    """
    Asks user to enter a custom interview date.
    """
    print("\n  Enter custom interview date:")
    print("  Format: DD-MM-YYYY (example: 28-04-2026)")

    while True:
        date_input = input("  Date: ").strip()
        try:
            custom_date = datetime.strptime(date_input, "%d-%m-%Y").date()

            # Check if it's a working day
            if custom_date.weekday() not in WORKING_DAYS:
                print("  ⚠️  That's a weekend! Please pick a working day (Mon-Fri)")
                continue

            # Check if it's in the past
            if custom_date < datetime.today().date():
                print("  ⚠️  That date is in the past! Please pick a future date")
                continue

            print(f"  ✅ Custom date set: {custom_date.strftime('%A, %d %B %Y')}")
            return custom_date

        except ValueError:
            print("  ⚠️  Invalid format! Please use DD-MM-YYYY")


def ask_user_for_time_slot(available_slots, interview_date):
    """
    Shows available time slots and asks user to pick one.
    """
    print(f"\n  Available time slots for {interview_date.strftime('%d %B %Y')}:")
    print("-"*55)

    if not available_slots:
        print("  ⚠️  No slots available on this date!")
        print("  Using default slot: 11:00 AM")
        return "11:00", "11:00 AM"

    for i, slot in enumerate(available_slots, 1):
        print(f"  [{i}] {convert_to_12hr(slot)}")

    print("-"*55)

    while True:
        try:
            choice = int(input(f"  Pick a slot (1-{len(available_slots)}): ").strip())
            if 1 <= choice <= len(available_slots):
                selected_24 = available_slots[choice - 1]
                selected_12 = convert_to_12hr(selected_24)
                print(f"  ✅ Time slot selected: {selected_12}")
                return selected_24, selected_12
            else:
                print(f"  ⚠️  Please enter a number between 1 and {len(available_slots)}")
        except ValueError:
            print("  ⚠️  Please enter a valid number")


def create_calendar_event(calendar_service, candidate_info, interview_date, time_24, time_12):
    """
    Creates interview event in Google Calendar with reminder.
    """
    try:
        # Build event datetime strings
        date_str = interview_date.strftime("%Y-%m-%d")
        hour, minute = map(int, time_24.split(":"))

        start_dt = datetime(
            interview_date.year,
            interview_date.month,
            interview_date.day,
            hour, minute, 0
        )
        end_dt = start_dt + timedelta(minutes=INTERVIEW_DURATION_MINUTES)

        # Format for Google Calendar API (IST = UTC+5:30)
        start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        timezone = "Asia/Kolkata"

        candidate_name = candidate_info.get("name", "Candidate")
        job_role = candidate_info.get("job_role", "Position")
        candidate_email = candidate_info.get("email", "")

        # Event details
        event = {
            "summary": f"Interview — {candidate_name} | {job_role}",
            "location": INTERVIEW_LOCATION,
            "description": (
                f"Interview Details\n"
                f"==================\n"
                f"Candidate  : {candidate_name}\n"
                f"Email      : {candidate_email}\n"
                f"Phone      : {candidate_info.get('phone', 'N/A')}\n"
                f"Job Role   : {job_role}\n"
                f"Type       : {candidate_info.get('application_type', 'N/A')}\n"
                f"Skills     : {candidate_info.get('skills', 'N/A')[:200]}\n\n"
                f"Company    : {COMPANY_NAME}\n"
                f"Scheduled by HR Automation System"
            ),
            "start": {
                "dateTime": start_str,
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_str,
                "timeZone": timezone,
            },
            "attendees": [
                {"email": candidate_email},
                {"email": COMPANY_EMAIL},
            ],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},   # 1 day before
                    {"method": "popup", "minutes": 60},         # 1 hour before
                    {"method": "popup", "minutes": 30},         # 30 mins before
                ],
            },
            "colorId": "2",  # Green color for interview events
        }

        # Create event in Google Calendar
        created_event = calendar_service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all"  # Sends invite email to candidate automatically
        ).execute()

        event_id = created_event.get("id", "")
        event_link = created_event.get("htmlLink", "")

        print(f"\n   ✅ Interview scheduled in Google Calendar!")
        print(f"   📅 Date     : {interview_date.strftime('%A, %d %B %Y')}")
        print(f"   🕐 Time     : {time_12}")
        print(f"   🔗 Event    : {event_link}")

        return {
            "date": interview_date.strftime("%d %b %Y"),
            "time": time_12,
            "time_24": time_24,
            "status": "Scheduled",
            "event_id": event_id,
            "event_link": event_link,
        }

    except Exception as e:
        print(f"   ❌ Could not create calendar event: {e}")
        return None


def schedule_interview(candidate_info):
    """
    Main function — schedules interview for a candidate.
    Handles both auto-scheduling and manual date picking.
    """
    print(f"\n📅 Scheduling interview for: {candidate_info.get('name')}")

    # Get Calendar service
    _, _, calendar_service = get_credentials()

    if not calendar_service:
        print("❌ Could not connect to Google Calendar")
        return None

    candidate_name = candidate_info.get("name", "Candidate")
    job_role = candidate_info.get("job_role", "Position")

    # --- Step 1: Calculate auto date (3 working days from today) ---
    today = datetime.today().date()
    auto_date = get_next_working_day(today, DAYS_AFTER_APPLICATION)

    # --- Step 2: Ask user to confirm or pick different date ---
    interview_date = ask_user_for_date_confirmation(auto_date, candidate_name, job_role)

    # --- Step 3: Check available slots on chosen date ---
    print(f"\n   🔍 Checking available slots on {interview_date.strftime('%d %B %Y')}...")
    available_slots = get_available_slots(calendar_service, interview_date)

    # --- Step 4: Ask user to pick time slot ---
    time_24, time_12 = ask_user_for_time_slot(available_slots, interview_date)

    # --- Step 5: Create event in Google Calendar ---
    print(f"\n   📆 Creating calendar event...")
    interview_info = create_calendar_event(
        calendar_service,
        candidate_info,
        interview_date,
        time_24,
        time_12
    )

    return interview_info


def test_calendar_scheduler():
    """
    Test calendar scheduler with dummy data.
    Run this file directly to test.
    """
    print("\n" + "="*55)
    print("  WebEarl HR — Calendar Scheduler Test")
    print("="*55)

    # Dummy candidate
    test_candidate = {
        "name": "Priyanshu Biswas",
        "email": "p@gmail.com",
        "phone": "+919601599999",
        "address": "Gamdi, Anand, Gujarat",
        "job_role": "AI/ML Developer Intern",
        "application_type": "Internship",
        "skills": "Python, Machine Learning, PyTorch, Flask",
    }

    interview_info = schedule_interview(test_candidate)

    if interview_info:
        print("\n" + "="*55)
        print("  ✅ Interview Scheduled Successfully!")
        print("="*55)
        print(f"  Date     : {interview_info['date']}")
        print(f"  Time     : {interview_info['time']}")
        print(f"  Event ID : {interview_info['event_id']}")
        print(f"  Link     : {interview_info['event_link']}")
    else:
        print("\n❌ Scheduling failed!")


# Run this file directly to test
if __name__ == "__main__":
    test_calendar_scheduler()