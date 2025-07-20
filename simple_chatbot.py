import streamlit as st
import time

def init_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def render_simple_chatbot():
    """Render a simple chatbot using Streamlit native components"""
    
    # Initialize chat
    init_chat()
    
    # Chatbot button in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 AI Auditor Chat")
        
        # Show chat history
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**AI:** {message['content']}")
        
        # Chat input
        user_input = st.text_input("Ask me about your audit:", key="chat_input")
        
        if st.button("Send", key="send_button") and user_input:
            # Add user message
            add_message("user", user_input)
            
            # Generate AI response
            ai_response = generate_ai_response(user_input)
            add_message("assistant", ai_response)
            
            # Rerun to show new messages
            st.rerun()

def generate_ai_response(user_message):
    """Generate a simple AI response"""
    user_message = user_message.lower()
    
    if "help" in user_message:
        return "I can help you with:\n• Understanding audit results\n• Explaining compliance findings\n• Financial ratio analysis\n• Fraud risk assessment\n\nWhat would you like to know?"
    
    elif "compliance" in user_message:
        return "I can explain compliance findings and help you understand what they mean for your business. What specific compliance issue would you like me to explain?"
    
    elif "fraud" in user_message:
        return "I can help you understand fraud risk indicators in your data. The AI model analyzes transaction patterns, amounts, timing, and descriptions to identify potential fraud."
    
    elif "ratio" in user_message or "financial" in user_message:
        return "I can help you understand your financial ratios and what they mean for your business. Key ratios include revenue to expense ratio, cash flow analysis, and profitability metrics."
    
    else:
        return "I'm here to help with your audit questions! I can explain findings, suggest improvements, and answer questions about financial reporting standards. What would you like to know?"

# Main app
st.set_page_config(page_title="Simple Chatbot Test", page_icon="💬", layout="wide")

st.title("💬 Simple Chatbot Test")
st.write("This is a simple chatbot using only Streamlit native components.")

# Render the chatbot
render_simple_chatbot()

st.write("The chatbot should appear in the sidebar. Try asking it questions!") 