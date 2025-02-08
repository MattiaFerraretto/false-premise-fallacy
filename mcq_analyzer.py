import streamlit as st
import json
from pathlib import Path
import pyperclip
from datetime import datetime
import pandas as pd

# Set page config for a cleaner look
st.set_page_config(
    page_title="MCQ Analyzer",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="📚"
)

# Enhanced custom CSS for a more polished look
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Card-like container for questions */
    .question-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }

    /* Options styling */
    .options-list {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .option-item {
        padding: 0.5rem 0;
        margin-left: 2rem;
    }

    /* Button styling */
    .stButton>button {
        background-color: #4F8BF9;
        color: white;
        border-radius: 50px;
        padding: 0.5rem 1rem;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #3670d6;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #4F8BF9;
    }

    /* Success message styling */
    .success-message {
        color: #28a745;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 1rem 0;
    }

    /* Metrics styling */
    .metrics-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'correct_count' not in st.session_state:
    st.session_state.correct_count = 0
if 'history' not in st.session_state:
    st.session_state.history = []

def load_exercises():
    """Load and validate exercises from JSONL file"""
    exercises = []
    try:
        with open('./output/mcq_math-gtp4o.jsonl', 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    exercise = json.loads(line.strip())
                    required_fields = ['statement', 'question', 'options']
                    if all(field in exercise for field in required_fields):
                        exercises.append(exercise)
                    else:
                        st.warning(f"Invalid exercise format at line {line_num}")
                except json.JSONDecodeError:
                    st.warning(f"Invalid JSON at line {line_num}")
    except FileNotFoundError:
        st.error("📁 No exercises file found. Please create 'exercises.jsonl'")
        return []
    return exercises

def save_correct_exercise(exercise):
    """Save correct exercise with metadata"""
    correct_file = Path('correct_exercises.jsonl')
    exercise_with_metadata = {
        **exercise,
        'marked_date': datetime.now().isoformat(),
        'session_id': st.session_state.get('session_id', 'default')
    }
    mode = 'a' if correct_file.exists() else 'w'
    with open(correct_file, mode, encoding='utf-8') as f:
        f.write(json.dumps(exercise_with_metadata) + '\n')
    st.session_state.correct_count += 1
    st.session_state.history.append({
        'index': st.session_state.current_index,
        'action': 'marked_correct',
        'timestamp': datetime.now().isoformat()
    })

def format_question_text(exercise):
    """Format the question text with proper spacing and formatting"""
    return f"""Answer the following multiple choice question. You MUST answer by using the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Before answer reason briefly.

{exercise['statement']} {exercise['question']}

A) {exercise['options']['A']}\n
B) {exercise['options']['B']}\n
C) {exercise['options']['C']}\n
D) {exercise['options']['D']}\n"""

def get_progress_stats():
    """Calculate and return progress statistics"""
    total = len(exercises)
    correct = st.session_state.correct_count
    remaining = total - correct
    return {
        'total': total,
        'correct': correct,
        'remaining': remaining,
        'progress': (correct / total * 100) if total > 0 else 0
    }

# Load exercises
exercises = load_exercises()

if exercises:
    # Display header with progress
    st.title("📚 MCQ Analyzer")
    stats = get_progress_stats()

    # Progress metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Exercises", stats['total'])
    with col2:
        st.metric("Completed", stats['correct'])
    with col3:
        st.metric("Remaining", stats['remaining'])

    # Progress bar
    st.progress(stats['progress'] / 100)

    # Current exercise
    current_exercise = exercises[st.session_state.current_index]

    # Format and display question in styled container
    with st.container():
        st.markdown('<div class="question-container">', unsafe_allow_html=True)
        st.markdown(format_question_text(current_exercise))
        st.markdown('</div>', unsafe_allow_html=True)

    # Navigation and action buttons with improved layout
    col1, col2, col3, col4 = st.columns([1,1,1,2])

    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.current_index == 0):
            st.session_state.current_index -= 1
            st.rerun()

    with col2:
        if st.button("✅ Correct"):
            save_correct_exercise(current_exercise)
            st.success("Exercise saved successfully!")

    with col3:
        if st.button("➡️ Next", disabled=st.session_state.current_index == len(exercises) - 1):
            st.session_state.current_index += 1
            st.rerun()

    with col4:
        if st.button("📋 Copy to Clipboard"):
            pyperclip.copy(format_question_text(current_exercise))
            st.success("Copied to clipboard!")

    # Exercise counter with improved styling
    st.markdown(f"<div style='text-align: center; color: #666;'>Exercise {st.session_state.current_index + 1} of {len(exercises)}</div>", unsafe_allow_html=True)

    # Session statistics in expandable section
    with st.expander("📊 Session Statistics"):
        st.markdown("### Current Session Overview")
        df = pd.DataFrame(st.session_state.history)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No actions recorded in this session yet.")

else:
    st.error("No exercises found. Please add exercises to 'exercises.jsonl'")
    st.markdown("""
    ### Expected Format:
    ```json
    {"statement": "...", "question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}}
    ```
    """)
