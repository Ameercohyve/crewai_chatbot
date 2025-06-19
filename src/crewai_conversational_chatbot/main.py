#!/usr/bin/env python
from crewai_conversational_chatbot.crew import CrewaiConversationalChatbotCrew
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

def run():
    crew = CrewaiConversationalChatbotCrew().crew()

    print("Hey there! Welcome to Cohyve!!")
    print("I’m here to answer your questions. But first tell me a bit about yourself.")
    print("1. I'm a Brand")
    print("2. I'm a Creator")
    print("3. Book a demo for me")
    print("4. Schedule a meeting for me")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Assistant: Goodbye! It was nice talking to you.")
            break

        if user_input.strip() == "4" or "schedule a meeting" in user_input.lower():
            email = input("Assistant: Sure! Please enter your email address: ")
            send_meeting_email(email)
            continue

        inputs = {
            "user_message": user_input,
            "context": ""
        }

        response = crew.kickoff(inputs=inputs)
        print(f"Assistant: {response}")

if __name__ == "__main__":
    run()
