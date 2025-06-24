from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory

from .conversation_memory import ConversationMemory

import os
import uuid
from typing import Optional


llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.5,
    max_tokens=1024
)

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

@CrewBase
class CrewaiConversationalChatbotCrew:
    """CrewaiConversationalChatbot crew with conversation memory"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize the crew with conversation memory"""
        self.conversation_memory = ConversationMemory()
        self.session_id = str(uuid.uuid4())
        self.conversation_id: Optional[int] = None
        self.user_info = {}

    @agent
    def assistant(self) -> Agent:
        return Agent(
            config=self.agents_config["assistant"],
            llm=llm,
            memory=True,
            verbose=False,
        )

    @task
    def assistant_task(self) -> Task:
        return Task(config=self.tasks_config["assistant_task"], agent=self.assistant())

    @crew
    def crew(self) -> Crew:
        """Creates the CrewaiChatbot crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=0,
        )
    
    def start_conversation(self, user_name: Optional[str] = None) -> int:
        """
        Start a new conversation session
        
        Args:
            user_name: Optional user name
            
        Returns:
            Conversation ID
        """
        self.conversation_id = self.conversation_memory.start_conversation(
            self.session_id, user_name
        )
        return self.conversation_id
    
    def add_message(self, role: str, content: str):
        """
        Add a message to the conversation
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        if self.conversation_id is None:
            self.start_conversation()
        
        # Ensure conversation_id is not None before using it
        if self.conversation_id is not None:
            self.conversation_memory.add_message(self.conversation_id, role, content)
    
    def get_conversation_history(self, limit: int = 10) -> list:
        """
        Get conversation history
        
        Args:
            limit: Number of recent messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        if self.conversation_id is None:
            return []
        
        return self.conversation_memory.get_conversation_history(self.conversation_id, limit)
    
    def get_user_info(self) -> dict:
        """
        Get user information for current session
        
        Returns:
            User information dictionary
        """
        return self.conversation_memory.get_user_info(self.session_id) or {}
    
    def update_user_info(self, name: Optional[str] = None, user_type: Optional[str] = None, email: Optional[str] = None):
        """
        Update user information
        
        Args:
            name: User name
            user_type: Type of user (brand, creator, etc.)
            email: User email
        """
        self.conversation_memory.update_user_info(
            self.session_id, name, user_type, email
        )
    
    def get_conversation_context(self) -> str:
        """
        Get conversation context for the assistant
        
        Returns:
            Formatted conversation context
        """
        history = self.get_conversation_history(limit=5)
        user_info = self.get_user_info()
        
        context_parts = []
        
        # Add user information
        if user_info.get('name'):
            context_parts.append(f"User's name: {user_info['name']}")
        if user_info.get('user_type'):
            context_parts.append(f"User type: {user_info['user_type']}")
        
        # Add recent conversation history
        if history:
            context_parts.append("Recent conversation:")
            for msg in history[-3:]:  # Last 3 messages
                role = "User" if msg['role'] == 'user' else "Assistant"
                context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts) if context_parts else "No previous conversation context."
    
    def get_conversation_summary(self) -> dict:
        """
        Get summary of current conversation
        
        Returns:
            Conversation summary dictionary
        """
        if self.conversation_id is None:
            return {}
        
        return self.conversation_memory.get_conversation_summary(self.conversation_id)
