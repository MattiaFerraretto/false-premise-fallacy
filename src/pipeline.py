from rich import print
from openai import OpenAI

from prompts import MCQ_EXERCISE_PROMT, MCQ_EXERCISE_CORRECTNESS_PROMPT
from utils import parse_mcq_exercises, SimilarityFilter, parse_correctness_check



def generate(prompt):
    client = OpenAI(
        api_key='',
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    response = client.chat.completions.create(
        model="gemini-exp-1121",
        n=1, 
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        temperature=1,
        top_p= 0.95,
        #top_k=64,
    )

    return response.choices[0].message.content.strip()


def main():
    similarity_filter = SimilarityFilter('all-MiniLM-L6-v2')

    ## 1. Generate exercises
    exercise_prompt = MCQ_EXERCISE_PROMT.format(
        topic="Economics",
        batch_size=5,
        difficulty="Medium"
    )
    response = generate(prompt=exercise_prompt)
    exercises = parse_mcq_exercises(response)

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
        response = generate(prompt=correctness_prompt)
        correctness = parse_correctness_check(response)
        if correctness['correctness']['is_correct']:
            exercise.update(correctness)
            correct_exercises.append(exercise)

    print(correct_exercises)


    ## 4. Transform MCQ exercises into true/false ones

    ## 5. Check tester model knowledge by true/false excercises

    ## 6. MCQ answer by the tester model



if __name__ == '__main__':
    main()