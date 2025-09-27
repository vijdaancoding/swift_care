import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import google.generativeai as genai

class GlobalHistoryManager:
    """
    Centralized history manager for multi-agent conversations
    """
    
    def __init__(self):
        self.conversation_history = []
        self.agent_transitions = []
        self.current_session_id = None
        self.shared_chat = None  # Single chat instance shared across agents
        
    def start_session(self, session_id: str = None):
        """Start a new conversation session"""
        self.current_session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history = []
        self.agent_transitions = []
        self.shared_chat = None
        print(f"📝 Started new session: {self.current_session_id}")
    
    def add_message(self, role: str, content: str, agent_name: str = None):
        """Add a message to the global history"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,  # 'user' or 'assistant'
            "content": content,
            "agent": agent_name,
            "session_id": self.current_session_id
        }
        self.conversation_history.append(message)
        
        # Print for debugging
        role_label = f"{role.title()}" + (f" ({agent_name})" if agent_name else "")
        print(f"📝 History: {role_label}: {content[:50]}...")
    
    def add_agent_transition(self, from_agent: str, to_agent: str, reason: str = None):
        """Record agent transitions"""
        transition = {
            "timestamp": datetime.now().isoformat(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "reason": reason,
            "session_id": self.current_session_id
        }
        self.agent_transitions.append(transition)
        print(f"🔄 Agent transition: {from_agent} -> {to_agent}")
    
    def get_or_create_shared_chat(self, base_prompt: str, current_agent: str):
        """
        Get the shared chat instance or create it with full context
        """
        if self.shared_chat is None:
            # Create new chat with base prompt
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=base_prompt
            )
            self.shared_chat = model.start_chat()
            self.initial_agent = current_agent
            print(f"🆕 Created shared chat for {current_agent}")
        else:
            # Handle agent transition with proper role switching
            if len(self.agent_transitions) > 0:
                last_transition = self.agent_transitions[-1]
                if last_transition['to_agent'] == current_agent and last_transition['from_agent'] != current_agent:
                    # Send a clear role transition message
                    transition_message = f"""IMPORTANT ROLE CHANGE: 

You are now acting as the {current_agent.upper()} AGENT, not the {last_transition['from_agent']} agent. 

Your new role and instructions:
{base_prompt}

Please acknowledge this role change and continue the conversation as the {current_agent} agent, maintaining the context of our previous discussion but following your new role guidelines."""
                    
                    try:
                        response = self.shared_chat.send_message(transition_message)
                        print(f"🔄 Successfully transitioned to {current_agent} agent")
                        # Log this transition (but don't count it as user/assistant conversation)
                        print(f"🔄 Transition response: {response.text[:100]}...")
                    except Exception as e:
                        print(f"⚠️ Could not send transition message: {e}")
        
        return self.shared_chat
    
    def get_history_summary(self, last_n_messages: int = 10):
        """Get a summary of recent conversation"""
        recent_messages = self.conversation_history[-last_n_messages:] if self.conversation_history else []
        
        if not recent_messages:
            return "No conversation history."
        
        summary_lines = []
        for msg in recent_messages:
            role_label = msg['role'].title()
            if msg.get('agent'):
                role_label += f" ({msg['agent']})"
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            summary_lines.append(f"{role_label}: {content}")
        
        return "\n".join(summary_lines)
    
    def get_stats(self):
        """Get conversation statistics"""
        return {
            "session_id": self.current_session_id,
            "total_messages": len(self.conversation_history),
            "agent_transitions": len(self.agent_transitions),
            "agents_used": list(set(msg.get("agent") for msg in self.conversation_history if msg.get("agent"))),
            "has_shared_chat": self.shared_chat is not None
        }
    
    def print_history_debug(self, last_n: int = 5):
        """Print recent history for debugging"""
        print(f"\n📊 Recent History (last {last_n} messages):")
        print("-" * 50)
        recent = self.conversation_history[-last_n:] if self.conversation_history else []
        
        for i, msg in enumerate(recent, 1):
            role = msg['role'].title()
            agent = f" ({msg.get('agent', 'Unknown')})" if msg.get('agent') else ""
            content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
            print(f"{i}. {role}{agent}: {content}")
        
        if not recent:
            print("No messages yet.")
        print("-" * 50)

# Global instance
history_manager = GlobalHistoryManager()

# Convenience functions for backward compatibility
def add_user(message: str, agent_name: str = None):
    """Add user message to global history"""
    history_manager.add_message("user", message, agent_name)

def add_model(message: str, agent_name: str = None):
    """Add model/assistant message to global history"""
    history_manager.add_message("assistant", message, agent_name)

def get_history():
    """Get conversation history"""
    return history_manager.conversation_history

def print_history():
    """Print conversation history"""
    history_manager.print_history_debug()

def get_shared_chat(base_prompt: str, agent_name: str):
    """Get or create shared chat instance"""
    return history_manager.get_or_create_shared_chat(base_prompt, agent_name)

def start_new_session():
    """Start a new conversation session"""
    history_manager.start_session()

def add_agent_transition(from_agent: str, to_agent: str, reason: str = None):
    """Record agent transition"""
    history_manager.add_agent_transition(from_agent, to_agent, reason)