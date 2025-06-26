#!/usr/bin/env python
"""
Launcher script to run the CrewAI Conversational Chatbot with suppressed warnings
"""
import os
import warnings
import sys

# Set environment variables to suppress warnings
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning,ignore::FutureWarning'

# Suppress all warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Add src to path and run the main application
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crewai_conversational_chatbot.main import run

if __name__ == "__main__":
    run() 