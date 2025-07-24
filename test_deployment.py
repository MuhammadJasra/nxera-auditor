# test_deployment.py - Test all imports for deployment
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import shap
import reportlab
import arabic_reshaper
import python_bidi
import pyhanko
import cryptography
import asn1crypto
import oscrypto
import cffi
import pycparser
import tqdm
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from xhtml2pdf import pisa

st.set_page_config(page_title="Deployment Test", page_icon="✅")

st.title("✅ Deployment Test")
st.write("All imports successful!")

# Test basic functionality
df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-02'],
    'description': ['Test 1', 'Test 2'],
    'amount': [100, -50]
})

st.write("Sample DataFrame:")
st.dataframe(df)

st.success("🎉 All dependencies are working correctly!")
st.info("Your AI Auditor should deploy successfully on Streamlit Cloud.") 