import streamlit as st
import json

st.set_page_config(page_title="MCQ Review - Settings", layout="centered")

st.title("⚙️ MCQ Review Settings")

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = {
        'input_file': None,
        'output_file': None,
        'setup_complete': False
    }

with st.form("settings_form"):
    input_file = st.file_uploader("Upload JSONL file", type=['jsonl'])
    output_file = st.text_input("Output file path", "reviewed_exercises.jsonl")

    submitted = st.form_submit_button("Save Settings")

    if submitted and input_file and output_file:
        # Save the content to a temporary file
        content = input_file.getvalue().decode('utf-8')
        exercises = [json.loads(line) for line in content.split('\n') if line.strip()]

        # Store settings in session state
        st.session_state.config['input_file'] = exercises
        st.session_state.config['output_file'] = output_file
        st.session_state.config['setup_complete'] = True

        st.success("Settings saved! Please go to the Review page to start reviewing exercises.")
    elif submitted:
        st.error("Please provide both input and output files.")
