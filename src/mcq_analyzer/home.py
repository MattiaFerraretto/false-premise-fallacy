import streamlit as st

st.set_page_config(page_title="MCQ Review - Home", layout="centered")

st.title("🏠 MCQ Review App")

st.markdown("""
Welcome to the MCQ Review App! This application helps you review multiple choice questions efficiently.

### How to use:
1. Go to the ⚙️ Settings page to:
   - Upload your JSONL file containing the exercises
   - Set the output file path for reviewed exercises

2. Then proceed to the 📝 Review page to:
   - Review exercises one by one
   - Mark them as correct or wrong
   - Navigate through the questions
   - Copy questions to clipboard when needed

### File Format
Your input file should be a JSONL file with the following structure:
```json
{
    "statement": "Your statement here",
    "question": "Your question here",
    "options": {
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
    }
}
```
""")
