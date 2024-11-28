from rich import print
from openai import OpenAI

from prompts import MCQ_EXERCISE_PROMT, MCQ_EXERCISE_CORRECTNESS_PROMPT, TF_EXERCISE_PROMPT, FALLACY_DETECTION_PROMPT, EVALUATION_TEMPLATE
from utils import parse_mcq_exercises, SimilarityFilter, parse_correctness_check, parse_tf_exercise, parse_tf_exercise_answer, format_mcq_exercise, parse_mcq_answer

from tenacity import retry, stop_after_attempt, wait_random_exponential
from dotenv import load_dotenv
import os
import json

load_dotenv()

GEMINI_APY_KEY = os.environ['GEMINI_APY_KEY']
CEREBRAS_API_KEY = os.environ['CEREBRAS_API_KEY']

GENERATOR="gemini-exp-1121"
#GENERATOR="gemini-1.5-flash"
#GENERATOR="gemini-1.5-pro"
TESTER="llama3.1-70b"

@retry(stop=stop_after_attempt(10), wait=wait_random_exponential(multiplier=0.5, max=60))
def generate(base_url: str, apy_key: str, model: str, prompt: str):
    client = OpenAI(
        api_key=apy_key,
        base_url=base_url
    )

    response = client.chat.completions.create(
        model=model,
        n=1,
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        temperature=1.2,
        top_p= 0.95,
        #top_k=64,
    ).choices[0].message.content

    return response.strip() if response else ""


def main():
    similarity_filter = SimilarityFilter('all-MiniLM-L6-v2')

    with open('exercises.jsonl', 'w') as fp:
        ## 1. Generate exercises
        exercise_prompt = MCQ_EXERCISE_PROMT.format(
            topic="Economics",
            batch_size=5,
            difficulty="Extremely hard, Higly specific"
        )
        response = generate(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            apy_key=GEMINI_APY_KEY,
            model=GENERATOR,
            prompt=exercise_prompt
        )
        exercises = parse_mcq_exercises(GENERATOR, response)

        ## 2. Check exercises similarity
        filtered_exercises = similarity_filter.filter(exercises)
        print(len(filtered_exercises))

        ## 3. Check exercises correctness
        correct_exercises = []
        for exercise in filtered_exercises:
            correctness_prompt = MCQ_EXERCISE_CORRECTNESS_PROMPT.format(
                question=exercise['question'],
                A=exercise['options']['A'],
                B=exercise['options']['B'],
                C=exercise['options']['C'],
                D=exercise['options']['D'],
            )
            response = generate(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                apy_key=GEMINI_APY_KEY,
                model=GENERATOR,
                prompt=correctness_prompt
            )
            correctness = parse_correctness_check(response)
            if correctness['correctness']['is_correct']:
                exercise.update(correctness)
                correct_exercises.append(exercise)

        print(len(correct_exercises))

        ## 4. Transform MCQ exercises into true/false ones
        exercises_w_tfq = []
        for exercise in correct_exercises:
            tf_prompt = TF_EXERCISE_PROMPT.format(
                question=exercise['question'],
                A=exercise['options']['A'],
                B=exercise['options']['B'],
                C=exercise['options']['C'],
                D=exercise['options']['D']
            )
            response = generate(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                apy_key=GEMINI_APY_KEY,
                model=GENERATOR,
                prompt=tf_prompt
            )
            tf_question = parse_tf_exercise(response)
            exercise.update(tf_question)
            exercises_w_tfq.append(exercise)

        print(len(exercises_w_tfq))

        ## 5. Check tester model knowledge by true/false excercises
        exercises_w_tfa = []
        for exercise in exercises_w_tfq:
            fallacy_prompt = FALLACY_DETECTION_PROMPT.format(
                question=exercise['tf_exercise']['question']
            )
            response = generate(
                base_url="https://api.cerebras.ai/v1",
                apy_key=CEREBRAS_API_KEY,
                model=TESTER,
                prompt=fallacy_prompt
            )
            tester_answer = parse_tf_exercise_answer(TESTER, response)
            exercise['tf_exercise'].update(tester_answer)
            if not tester_answer['tester']['answer']:
                exercises_w_tfa.append(exercise)

        ## 6. MCQ answer by the tester model
        mcq_exercises = []
        for exercise in exercises_w_tfa:
            evaluation_prompt = EVALUATION_TEMPLATE.format(
                question=exercise['question'],
                A=exercise['options']['A'],
                B=exercise['options']['B'],
                C=exercise['options']['C'],
                D=exercise['options']['D']
            )
            response = generate(
                base_url="https://api.cerebras.ai/v1",
                apy_key=CEREBRAS_API_KEY,
                model=TESTER,
                prompt=evaluation_prompt
            )
            mcq_answer = parse_mcq_answer(TESTER, response)
            ex = format_mcq_exercise(exercise)
            print(f"{ex}\n\n{response}\n\n")
            exercise.update(mcq_answer)
            mcq_exercises.append(exercise)
            if mcq_answer['mcq_answer']['failed']:
                fp.write(f"{json.dumps(exercise)}\n")



if __name__ == '__main__':
    main()
