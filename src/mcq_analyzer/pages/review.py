import streamlit as st
import json
import hashlib
from datetime import datetime
import pyperclip
from pathlib import Path

def generate_hash(exercise):
    """Generate a unique hash for an exercise"""
    exercise_str = json.dumps(exercise, sort_keys=True)
    return hashlib.md5(exercise_str.encode()).hexdigest()

def copy_to_clipboard(exercise):
    """Format and copy exercise to clipboard"""
    eval_template = f"""Answer the following multiple choice question. You MUST answer by using the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Before answer reason briefly.

{exercise['statement']} {exercise['question']}

A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}"""

    eval_template1 = f"""Statement: {exercise['statement']}

Question: {exercise['question']}

Options:
A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}"""

    eval_template2 = f"""Answer the following multiple-choice question. Reason briefly before concluding your answer using the format: 'Answer: $LETTER' (without quotes) where LETTER is one option among A, B, C, D.

{exercise['statement']} {exercise['question']}

Options:
A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}"""

    pyperclip.copy(eval_template1)

st.set_page_config(page_title="MCQ Review - Review", layout="centered")

# Apply custom CSS
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 4px;
        margin: 2px;
    }
    .main {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Check if setup is complete
if 'config' not in st.session_state or not st.session_state.config.get('setup_complete'):
    st.error("⚠️ Please configure the input and output files in the Settings page first.")
    st.stop()

# Initialize review session state
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'exercises' not in st.session_state:
    exercises = st.session_state.config['input_file']

    # If output file exists, load reviewed exercises and filter them out
    output_file = st.session_state.config['output_file']
    if Path(output_file).exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            reviewed_exercises = [json.loads(line) for line in f if line.strip()]
            reviewed_hashes = {exercise.get('hash') for exercise in reviewed_exercises}
            exercises = [ex for ex in exercises
                        if generate_hash(ex) not in reviewed_hashes]

    st.session_state.exercises = exercises
if 'reviewed_count' not in st.session_state:
    st.session_state.reviewed_count = 0
if 'total_count' not in st.session_state:
    st.session_state.total_count = len(st.session_state.exercises)

st.title("📝 MCQ Review")

# Display exercise if available
if st.session_state.exercises and st.session_state.current_index < len(st.session_state.exercises):
    exercise = st.session_state.exercises[st.session_state.current_index]

    # Progress bar
    progress = (st.session_state.reviewed_count / st.session_state.total_count
               if st.session_state.total_count > 0 else 0)
    st.progress(progress)
    st.write(f"Reviewed: {st.session_state.reviewed_count}/{st.session_state.total_count}")

    # Display exercise
    st.markdown("### Statement")
    st.write(exercise['statement'])

    st.markdown("### Question")
    st.write(exercise['question'])

    st.markdown("### Options")
    for key, value in exercise['options'].items():
        st.write(f"{key}) {value}")

    # Buttons
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("⬅️ Previous"):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
            st.rerun()

    with col2:
        if st.button("❌ Wrong"):
            st.session_state.reviewed_count += 1
            st.session_state.exercises.pop(st.session_state.current_index)
            if st.session_state.current_index >= len(st.session_state.exercises):
                st.session_state.current_index = max(0, len(st.session_state.exercises) - 1)
            st.rerun()

    with col3:
        if st.button("✅ Correct"):
            # Add metadata and save
            exercise['hash'] = generate_hash(exercise)
            exercise['review_date'] = datetime.now().isoformat()

            # Append to output file
            output_file = st.session_state.config['output_file']
            with open(output_file, 'a', encoding='utf-8') as f:
                json.dump(exercise, f, ensure_ascii=False)
                f.write('\n')

            st.session_state.reviewed_count += 1
            st.session_state.exercises.pop(st.session_state.current_index)
            if st.session_state.current_index >= len(st.session_state.exercises):
                st.session_state.current_index = max(0, len(st.session_state.exercises) - 1)
            st.rerun()

    with col4:
        if st.button("➡️ Next"):
            if st.session_state.current_index < len(st.session_state.exercises) - 1:
                st.session_state.current_index += 1
            st.rerun()

    with col5:
        if st.button("📋 Copy"):
            copy_to_clipboard(exercise)
            st.toast("Copied to clipboard!")

elif st.session_state.total_count > 0:
    st.success("🎉 All exercises have been reviewed!")
    if st.button("Start Over"):
        # Clear session state
        for key in list(st.session_state.keys()):
            if key != 'config':
                del st.session_state[key]
        st.rerun()
