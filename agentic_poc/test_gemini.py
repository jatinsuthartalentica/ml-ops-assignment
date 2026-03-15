import os
import google.generativeai as genai

genai.configure(api_key="AIzaSyCi_xQnnCVyfdoATWvL_8Np2G9w7M5AjiY")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
