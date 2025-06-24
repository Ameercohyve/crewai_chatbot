import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class ConversationMemory:
    """Simple conversation memory using SQLite"""
    
    def __init__(self, db_path: str = "conversation_memory.db"):
        """
        Initialize conversation memory
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        # Create user_info table for storing user details
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                name TEXT,
                user_type TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_conversation(self, session_id: str, user_name: Optional[str] = None) -> int:
        """
        Start a new conversation
        
        Args:
            session_id: Unique session identifier
            user_name: Optional user name
            
        Returns:
            Conversation ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if conversation already exists
        cursor.execute('SELECT id FROM conversations WHERE session_id = ?', (session_id,))
        existing = cursor.fetchone()
        
        if existing:
            conversation_id = existing[0]
        else:
            # Create new conversation
            cursor.execute('''
                INSERT INTO conversations (session_id, user_name)
                VALUES (?, ?)
            ''', (session_id, user_name))
            conversation_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return conversation_id
    
    def add_message(self, conversation_id: int, role: str, content: str):
        """
        Add a message to the conversation
        
        Args:
            conversation_id: ID of the conversation
            role: 'user' or 'assistant'
            content: Message content
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        ''', (conversation_id, role, content))
        
        # Update conversation timestamp
        cursor.execute('''
            UPDATE conversations 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (conversation_id,))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, conversation_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Args:
            conversation_id: ID of the conversation
            limit: Number of recent messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, timestamp
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (conversation_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'role': row[0],
                'content': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return list(reversed(messages))  # Return in chronological order
    
    def get_user_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            User information dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, user_type, email, created_at
            FROM user_info
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'name': row[0],
                'user_type': row[1],
                'email': row[2],
                'created_at': row[3]
            }
        return None
    
    def update_user_info(self, session_id: str, name: Optional[str] = None, user_type: Optional[str] = None, email: Optional[str] = None):
        """
        Update user information
        
        Args:
            session_id: Session identifier
            name: User name
            user_type: Type of user (brand, creator, etc.)
            email: User email
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user info exists
        cursor.execute('SELECT id FROM user_info WHERE session_id = ?', (session_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing user info
            updates = []
            values = []
            if name is not None:
                updates.append('name = ?')
                values.append(name)
            if user_type is not None:
                updates.append('user_type = ?')
                values.append(user_type)
            if email is not None:
                updates.append('email = ?')
                values.append(email)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                values.append(session_id)
                cursor.execute(f'''
                    UPDATE user_info 
                    SET {', '.join(updates)}
                    WHERE session_id = ?
                ''', values)
        else:
            # Create new user info
            cursor.execute('''
                INSERT INTO user_info (session_id, name, user_type, email)
                VALUES (?, ?, ?, ?)
            ''', (session_id, name, user_type, email))
        
        conn.commit()
        conn.close()
    
    def get_conversation_summary(self, conversation_id: int) -> Dict[str, Any]:
        """
        Get a summary of the conversation
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation summary dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get conversation details
        cursor.execute('''
            SELECT session_id, user_name, created_at, updated_at
            FROM conversations
            WHERE id = ?
        ''', (conversation_id,))
        
        conv_row = cursor.fetchone()
        if not conv_row:
            conn.close()
            return {}
        
        # Get message count
        cursor.execute('''
            SELECT COUNT(*) FROM messages WHERE conversation_id = ?
        ''', (conversation_id,))
        
        message_count = cursor.fetchone()[0]
        
        # Get user info
        user_info = self.get_user_info(conv_row[0])
        
        conn.close()
        
        return {
            'conversation_id': conversation_id,
            'session_id': conv_row[0],
            'user_name': conv_row[1],
            'message_count': message_count,
            'created_at': conv_row[2],
            'updated_at': conv_row[3],
            'user_info': user_info
        }
    
    def clear_conversation(self, conversation_id: int):
        """
        Clear all messages from a conversation
        
        Args:
            conversation_id: ID of the conversation
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all conversations (for training/analysis)
        
        Args:
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of conversation summaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_id, user_name, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (limit,))
        
        conversations = []
        for row in cursor.fetchall():
            conv_id = row[0]
            summary = self.get_conversation_summary(conv_id)
            conversations.append(summary)
        
        conn.close()
        return conversations 