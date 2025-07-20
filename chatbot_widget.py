import streamlit as st
import streamlit.components.v1 as components
import json
import time
from typing import List, Dict, Optional
import pandas as pd

class ChatBotWidget:
    def __init__(self):
        self.chat_history = []
        self.audit_context = {}
        
    def set_audit_context(self, df: pd.DataFrame, summary: str, compliance: List[Dict], region: str):
        """Set the current audit context for the chatbot"""
        self.audit_context = {
            'data_shape': df.shape if df is not None else None,
            'summary': summary,
            'compliance_count': len(compliance) if compliance else 0,
            'region': region,
            'has_data': df is not None and not df.empty
        }
    
    def get_audit_context_prompt(self) -> str:
        """Generate context-aware prompt for the chatbot"""
        if not self.audit_context.get('has_data'):
            return "I'm here to help with your audit questions. No data has been uploaded yet."
        
        context = f"""
        Current Audit Context:
        - Data: {self.audit_context['data_shape'][0]} transactions, {self.audit_context['data_shape'][1]} columns
        - Summary: {self.audit_context['summary']}
        - Compliance Issues: {self.audit_context['compliance_count']} findings
        - Region: {self.audit_context['region']}
        
        I can help you understand your audit results, explain compliance issues, suggest improvements, and answer questions about financial reporting standards.
        """
        return context
    
    def generate_response(self, user_message: str) -> str:
        """Generate AI response based on user message and audit context"""
        context = self.get_audit_context_prompt()
        
        # Simple response logic - in production, this would connect to your LLM
        if "help" in user_message.lower():
            return f"{context}\n\nI can help you with:\n• Understanding your audit results\n• Explaining compliance findings\n• Financial ratio analysis\n• Fraud risk assessment\n• Best practices for your region\n\nWhat would you like to know?"
        
        elif "compliance" in user_message.lower():
            if self.audit_context.get('compliance_count', 0) > 0:
                return f"You have {self.audit_context['compliance_count']} compliance findings. I can help you understand each one and suggest corrective actions. Would you like me to explain the specific issues?"
            else:
                return "Great news! No compliance issues were detected in your audit. Your financial records appear to meet the standards for your selected region."
        
        elif "fraud" in user_message.lower():
            return "I can help you understand fraud risk indicators in your data. The AI model analyzes transaction patterns, amounts, timing, and descriptions to identify potential fraud. Would you like me to explain the specific risk factors?"
        
        elif "improve" in user_message.lower() or "suggest" in user_message.lower():
            return "Based on your audit results, here are some suggestions:\n• Review transactions with missing descriptions\n• Investigate weekend transactions\n• Consider implementing automated controls\n• Regular reconciliation of accounts\n\nWould you like me to elaborate on any of these?"
        
        elif "ratio" in user_message.lower() or "financial" in user_message.lower():
            return "I can help you understand your financial ratios and what they mean for your business. The key ratios include:\n• Revenue to Expense ratio\n• Cash flow analysis\n• Profitability metrics\n\nWhat specific aspect would you like me to explain?"
        
        else:
            return f"{context}\n\nI understand you're asking about: '{user_message}'. I can help you with audit-related questions, compliance explanations, fraud risk analysis, and financial insights. Could you please be more specific about what you'd like to know?"

def render_chatbot_widget():
    """Render the popup chatbot widget"""
    
    # Initialize session state for chat
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ChatBotWidget()
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False
    
    # Custom CSS for the chatbot widget
    chatbot_css = """
    <style>
    .chatbot-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .chatbot-button {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #007acc, #005a9e);
        border: none;
        color: white;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0, 122, 204, 0.3);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .chatbot-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0, 122, 204, 0.4);
    }
    
    .chatbot-window {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 350px;
        height: 500px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border: 1px solid #e0e0e0;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        z-index: 10000;
    }
    
    .chatbot-header {
        background: linear-gradient(135deg, #007acc, #005a9e);
        color: white;
        padding: 15px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .chatbot-header button {
        background: none;
        border: none;
        color: white;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
    }
    
    .chatbot-messages {
        flex: 1;
        padding: 15px;
        overflow-y: auto;
        background: #f8f9fa;
    }
    
    .message {
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
    }
    
    .message.user {
        align-items: flex-end;
    }
    
    .message.bot {
        align-items: flex-start;
    }
    
    .message-content {
        max-width: 80%;
        padding: 10px 12px;
        border-radius: 18px;
        font-size: 14px;
        line-height: 1.4;
        word-wrap: break-word;
    }
    
    .message.user .message-content {
        background: #007acc;
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .message.bot .message-content {
        background: white;
        color: #333;
        border: 1px solid #e0e0e0;
        border-bottom-left-radius: 4px;
    }
    
    .message-time {
        font-size: 11px;
        color: #999;
        margin-top: 4px;
    }
    
    .chatbot-input {
        padding: 15px;
        border-top: 1px solid #e0e0e0;
        background: white;
        display: flex;
        gap: 8px;
    }
    
    .chatbot-input input {
        flex: 1;
        padding: 10px 12px;
        border: 1px solid #ddd;
        border-radius: 20px;
        font-size: 14px;
        outline: none;
    }
    
    .chatbot-input input:focus {
        border-color: #007acc;
    }
    
    .chatbot-input button {
        background: #007acc;
        color: white;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    
    .chatbot-input button:hover {
        background: #005a9e;
    }
    
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 10px 12px;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 18px;
        border-bottom-left-radius: 4px;
        max-width: 80%;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #999;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    </style>
    """
    
    # JavaScript for the chatbot functionality
    chatbot_js = """
    <script>
    function toggleChat() {
        const chatWindow = document.getElementById('chatbot-window');
        if (chatWindow.style.display === 'none' || chatWindow.style.display === '') {
            chatWindow.style.display = 'flex';
        } else {
            chatWindow.style.display = 'none';
        }
    }
    
    function sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (message) {
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Simulate bot response (in production, this would be an API call)
            setTimeout(() => {
                hideTypingIndicator();
                const botResponse = generateBotResponse(message);
                addMessage(botResponse, 'bot');
            }, 1000 + Math.random() * 2000);
        }
    }
    
    function addMessage(text, sender) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-time">${time}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function generateBotResponse(userMessage) {
        // Simple response logic - in production, this would be replaced with actual AI
        const responses = [
            "I can help you understand your audit results and compliance findings. What specific aspect would you like me to explain?",
            "Based on your audit data, I can provide insights on fraud risk, financial ratios, and compliance issues. What would you like to know?",
            "I'm here to help with your audit questions. I can explain any findings, suggest improvements, or answer questions about financial standards.",
            "Your audit shows some interesting patterns. Would you like me to explain the compliance findings or help you understand the financial ratios?"
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    // Handle Enter key in input
    document.addEventListener('DOMContentLoaded', function() {
        const input = document.getElementById('chat-input');
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        }
    });
    </script>
    """
    
    # HTML for the chatbot widget
    chatbot_html = f"""
    {chatbot_css}
    
    <div class="chatbot-container">
        <button class="chatbot-button" onclick="toggleChat()" title="Chat with AI Auditor">
            💬
        </button>
        
        <div class="chatbot-window" id="chatbot-window" style="display: none;">
            <div class="chatbot-header">
                <span>🤖 AI Auditor Assistant</span>
                <button onclick="toggleChat()">×</button>
            </div>
            
            <div class="chatbot-messages" id="chat-messages">
                <div class="message bot">
                    <div class="message-content">
                        Hello! I'm your AI Auditor assistant. I can help you understand your audit results, explain compliance findings, and answer questions about financial reporting. How can I help you today?
                    </div>
                    <div class="message-time">{time.strftime('%H:%M')}</div>
                </div>
            </div>
            
            <div class="chatbot-input">
                <input type="text" id="chat-input" placeholder="Ask me about your audit..." />
                <button onclick="sendMessage()">➤</button>
            </div>
        </div>
    </div>
    
    {chatbot_js}
    """
    
    # Render the chatbot widget
    components.html(chatbot_html, height=0)
    
    # Add a small debug indicator (you can remove this later)
    st.markdown("<!-- Chatbot widget rendered -->", unsafe_allow_html=True)

def init_chatbot_session():
    """Initialize chatbot session state"""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ChatBotWidget()
    
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False

def update_chatbot_context(df: pd.DataFrame, summary: str, compliance: List[Dict], region: str):
    """Update the chatbot with current audit context"""
    if 'chatbot' in st.session_state:
        st.session_state.chatbot.set_audit_context(df, summary, compliance, region) 