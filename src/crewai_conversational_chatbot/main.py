#!/usr/bin/env python
from .crew import CrewaiConversationalChatbotCrew
from dotenv import load_dotenv
import warnings
import os
import smtplib
from email.message import EmailMessage

warnings.filterwarnings("ignore", category=Warning)

load_dotenv()

def send_meeting_email(to_email):
    meet_link = os.getenv("MEETING_LINK")
    email_address = os.getenv("EMAIL_HOST_USER")
    email_password = os.getenv("EMAIL_HOST_PASSWORD")

    msg = EmailMessage()
    msg['Subject'] = "Your Scheduled Meeting Link - Cohyve"
    msg['From'] = email_address
    msg['To'] = to_email
    msg.set_content(
        f"Hi there,\n\nHere is your Google Meet link: {meet_link}\n\nRegards,\nCohyve Team"
    )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print(f"Assistant: Meeting link sent to {to_email}!")
    except Exception as e:
        print(f"Assistant: Failed to send email. Error: {e}")

# --- Project Creation CLI Flow (Option 4) ---
def project_creation_flow():
    """
    Conversational CLI flow for creating a project and generating a PRD markdown file, using LLM for smart extraction and drafting.
    """
    import datetime
    from crewai_conversational_chatbot.crew import llm
    import json
    print("\nAssistant: Let's create your project! Please answer the following questions.\n")

    # Step 1: Ask for a project brief
    brief = input("Assistant: Please provide a brief description of your project (what you want to create, goals, style, etc.): ")

    # Step 2: Use LLM to extract fields and draft PRD sections
    extraction_prompt = f"""
You are a project requirements expert. Given the following project brief, extract as many of these fields as possible:
- service
- subservice
- style
- application
- name
- deadline
- type (one-time or recurring)
- description
- expertise (fresher, beginner, experienced, pro)
- budget

Also, draft the following PRD sections based on the brief:
- objectives (as a bullet list)
- target_audience (as a bullet list)
- deliverables (as a bullet list)

IMPORTANT: If a field is not clearly present in the brief, leave it blank or null. Do NOT guess or invent values for name, deadline, type, expertise, or budget.

Return your answer as a JSON object with keys: service, subservice, style, application, name, deadline, type, description, expertise, budget, objectives, target_audience, deliverables.

Project Brief:
{brief}
"""
    llm_response = llm.invoke(extraction_prompt)
    try:
        extracted = json.loads(llm_response.content)
    except Exception:
        extracted = {}

    # Step 3: Fill project fields from LLM, ask for missing ones
    project = {
        'brief': brief,
        'service': extracted.get('service', ''),
        'subservice': extracted.get('subservice', ''),
        'style': extracted.get('style', ''),
        'application': extracted.get('application', ''),
        'name': extracted.get('name', ''),
        'deadline': extracted.get('deadline', ''),
        'type': extracted.get('type', ''),
        'description': extracted.get('description', ''),
        'expertise': extracted.get('expertise', ''),
        'budget': extracted.get('budget', ''),
        'objectives': extracted.get('objectives', []),
        'target_audience': extracted.get('target_audience', []),
        'deliverables': extracted.get('deliverables', [])
    }

    # Helper function for safe input with exit handling
    def safe_input(prompt):
        val = input(prompt).strip()
        if val.lower() in ["exit", "quit", "bye"]:
            print("Assistant: Project creation cancelled. Returning to main menu.")
            raise SystemExit(0)
        return val

    # Define generic/placeholder values for each field
    GENERIC_VALUES = {
        'service': {'none', 'n/a', 'service', 'design', 'graphic design', 'project'},
        'subservice': {'none', 'n/a', 'subservice', 'project'},
        'style': {'none', 'n/a', 'style', 'modern', 'clean', 'simple', 'basic', 'default'},
        'application': {'none', 'n/a', 'application', 'digital', 'print', 'web', 'app'},
        'name': {'none', 'n/a', 'name', 'project', 'untitled'},
        'deadline': {'none', 'n/a', 'deadline'},
        'type': {'none', 'n/a', 'type', 'project'},
        'description': {'none', 'n/a', 'description', 'project'},
        'expertise': {'none', 'n/a', 'expertise', 'any'},
        'budget': {'none', 'n/a', 'budget', 'any'},
    }

    # List of all important fields to check
    important_fields = [
        ('service', 'What is the main service? (e.g., web design, advertising design, ui/ux design)'),
        ('subservice', 'What is the subservice? (e.g., landing pages, marketing websites, portfolio sites, web templates)'),
        ('style', 'What style do you prefer? (e.g., clean, grid-based, animation-heavy)'),
        ('application', 'What is the application/use-case? (e.g., creative portfolios)'),
        ('name', 'What is the project name?'),
        ('deadline', 'What is the deadline?'),
        ('type', 'Is this a one-time or recurring project?'),
        ('description', 'Please provide a short project description'),
        ('expertise', 'What level of creator do you want? (fresher, beginner, experienced, pro)'),
        ('budget', 'What is your budget?(5000, 10000, 15000, 20000)')
    ]

    from datetime import datetime as dt
    today_str = dt.now().strftime('%d-%m-%Y')

    def is_explicit(field, value):
        return value and value.lower() in brief.lower()

    for field, prompt in important_fields:
        val = project.get(field, '')
        # Check for empty or generic/placeholder value
        if not val or (field in GENERIC_VALUES and val.strip().lower() in GENERIC_VALUES[field]):
            val = safe_input(f"Assistant: {prompt} ")
            # For deadline, normalize to DD-MM-YYYY if needed
            if field == 'deadline' and val:
                import re
                if not re.match(r'\d{4}-\d{2}-\d{2}', val) and not re.match(r'\d{2}-\d{2}-\d{4}', val):
                    norm_prompt = f"Convert this deadline to DD-MM-YYYY format. Today is {today_str}. Deadline: {val}"
                    norm_resp = llm.invoke(norm_prompt).content.strip()
                    date_match = re.search(r'(\d{2}-\d{2}-\d{4})', norm_resp)
                    if date_match:
                        val = date_match.group(1)
                    else:
                        val = norm_resp
            # For budget, normalize to numericals in rupees /-
            if field == 'budget' and val:
                norm_prompt = f"Convert this budget to a numeric value in rupees (INR). Only return the number. Budget: {val}"
                norm_resp = llm.invoke(norm_prompt).content.strip()
                import re
                num_match = re.search(r'\d+[\d,]*', norm_resp.replace(',', ''))
                if num_match:
                    val = num_match.group(0)
                else:
                    val = norm_resp
            project[field] = val
        # If deadline is present but not in DD-MM-YYYY, normalize it
        if field == 'deadline' and project[field]:
            import re
            if not re.match(r'\d{4}-\d{2}-\d{2}', project[field]) and not re.match(r'\d{2}-\d{2}-\d{4}', project[field]):
                norm_prompt = f"Convert this deadline to DD-MM-YYYY format. Today is {today_str}. Deadline: {project[field]}"
                norm_resp = llm.invoke(norm_prompt).content.strip()
                date_match = re.search(r'(\d{2}-\d{2}-\d{4})', norm_resp)
                if date_match:
                    project[field] = date_match.group(1)
                else:
                    project[field] = norm_resp
        # For budget, normalize to numericals in rupees if not already
        if field == 'budget' and project[field]:
            norm_prompt = f"Convert this budget to a numeric value in rupees (INR). Only return the number. Budget: {project[field]}"
            norm_resp = llm.invoke(norm_prompt).content.strip()
            num_match = re.search(r'\d+[\d,]*', norm_resp.replace(',', ''))
            if num_match:
                project[field] = num_match.group(0)
            else:
                project[field] = norm_resp

    # Use safe_input for edit/proceed as well
    print("\nAssistant: Here is a summary of your project:")
    for k, v in project.items():
        if isinstance(v, list):
            print(f"  {k.capitalize()}:\n    - " + "\n    - ".join(v))
        else:
            print(f"  {k.capitalize()}: {v}")
    action = safe_input('\nAssistant: Type "edit" to modify any field, or "proceed" to continue: ').strip().lower()
    while action == 'edit':
        field_to_edit = safe_input("Assistant: Which field would you like to edit? (type the field name): ").strip().lower()
        if field_to_edit in project:
            if isinstance(project[field_to_edit], list):
                new_val = safe_input(f"Assistant: Enter new value(s) for {field_to_edit} (comma separated): ")
                project[field_to_edit] = [x.strip() for x in new_val.split(',')]
            else:
                new_val = safe_input(f"Assistant: Enter new value for {field_to_edit}: ")
                # Normalize budget if edited
                if field_to_edit == 'budget' and new_val:
                    norm_prompt = f"Convert this budget to a numeric value in rupees (INR). Only return the number. Budget: {new_val}"
                    norm_resp = llm.invoke(norm_prompt).content.strip()
                    import re
                    num_match = re.search(r'\d+[\d,]*', norm_resp.replace(',', ''))
                    if num_match:
                        new_val = num_match.group(0)
                    else:
                        new_val = norm_resp
                project[field_to_edit] = new_val
        else:
            print("Assistant: Invalid field name.")
        action = safe_input('Assistant: Type "edit" to modify another field, or "proceed" to continue: ').strip().lower()

    # Step 5: Use LLM to draft the PRD markdown
    prd_prompt = f"""
You are a project documentation expert. Using the following project details, generate a professional Project Requirements Document (PRD) in markdown format. Use clear section headings and bullet points where appropriate. Be concise but thorough.

Project Details (JSON):
{json.dumps(project, indent=2)}
"""
    prd_md = llm.invoke(prd_prompt).content
    # --- Save PRD in a 'PRDs' folder in the workspace root ---
    prd_dir = os.path.join(os.getcwd(), 'PRDs')
    if not os.path.exists(prd_dir):
        os.makedirs(prd_dir)
    prd_filename = f"PRD_{project['name'].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    prd_path = os.path.join(prd_dir, prd_filename)
    with open(prd_path, 'w', encoding='utf-8') as f:
        f.write(prd_md)
    print(f"\nAssistant: PRD generated and saved as {prd_path}\n")

# --- End Project Creation CLI Flow

def run():
    crew_instance = CrewaiConversationalChatbotCrew()
    crew = crew_instance.crew()
    
    # Start conversation session
    crew_instance.start_conversation()

    print("Hey there! Welcome to Cohyve!!")
    print("I'm here to answer your questions. But first tell me a bit about yourself.")
    print("1. I'm a Brand")
    print("2. I'm a Creator")
    print("3. Schedule a demo")
    print("4. Create a project")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Assistant: Goodbye! It was nice talking to you.")
            break

        # Handle special commands
        if user_input.strip() == "3" or "schedule a meeting" in user_input.lower():
            email = input("Assistant: Sure! Please enter your email address: ")
            send_meeting_email(email)
            continue

        # --- Project Creation Option ---
        if user_input.strip() == "4":
            project_creation_flow()
            continue
        # --- End Project Creation Option ---

        # Store user message in conversation memory
        crew_instance.add_message("user", user_input)
        
        # Get conversation context for the assistant
        context = crew_instance.get_conversation_context()
        
        inputs = {
            "user_message": user_input,
            "context": context
        }

        response = crew.kickoff(inputs=inputs)
        
        # Convert CrewOutput to string before storing
        response_text = str(response)
        
        # Store assistant response in conversation memory
        crew_instance.add_message("assistant", response_text)
        
        print(f"Assistant: {response_text}")

if __name__ == "__main__":
    run()
