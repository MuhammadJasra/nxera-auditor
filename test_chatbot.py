import streamlit as st
from chatbot_widget import render_chatbot_widget, init_chatbot_session

st.set_page_config(page_title="Chatbot Test", page_icon="🧪", layout="centered")

st.title("🧪 Chatbot Widget Test")

st.write("This is a test page to verify the chatbot widget works.")

# Initialize chatbot
init_chatbot_session()

# Render the chatbot widget
render_chatbot_widget()

st.write("You should see a 💬 button in the bottom-right corner. Click it to open the chat!") 