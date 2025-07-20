import streamlit as st
import time

def init_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

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

def render_floating_chatbot():
    """Render a floating chatbot using Streamlit native components"""
    
    # Initialize chat
    init_chat()
    
    # Create columns for floating button
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col5:
        if st.button("💬", help="Chat with AI Auditor", key="chat_button"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()
    
    # Chat window (appears below when open)
    if st.session_state.chat_open:
        st.markdown("---")
        st.markdown("### 🤖 AI Auditor Chat")
        
        # Chat container with border
        chat_container = st.container()
        with chat_container:
            st.markdown("""
            <style>
            .chat-container {
                border: 2px solid #007acc;
                border-radius: 10px;
                padding: 20px;
                background-color: #f8f9fa;
                margin: 10px 0;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Show chat history
            if st.session_state.messages:
                for message in st.session_state.messages:
                    if message["role"] == "user":
                        st.markdown(f"**You:** {message['content']}")
                    else:
                        st.markdown(f"**AI:** {message['content']}")
            else:
                st.info("Hello! I'm your AI Auditor assistant. Ask me anything about your audit, compliance, or financial data!")
            
            # Chat input
            col1, col2 = st.columns([4, 1])
            with col1:
                user_input = st.text_input("Ask me about your audit:", key="chat_input", placeholder="Type your question here...")
            with col2:
                if st.button("Send", key="send_button") and user_input:
                    # Add user message
                    add_message("user", user_input)
                    
                    # Generate AI response
                    ai_response = generate_ai_response(user_input)
                    add_message("assistant", ai_response)
                    
                    # Rerun to show new messages
                    st.rerun()

# Main app
st.set_page_config(page_title="Floating Chatbot Test", page_icon="💬", layout="wide")

st.title("💬 Floating Chatbot Test")
st.write("This is a floating chatbot using Streamlit native components.")

# Render the floating chatbot
render_floating_chatbot()

st.write("Click the 💬 button in the top-right to open the chat!") 