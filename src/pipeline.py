from rich import print
from openai import OpenAI

from prompts import MCQ_EXERCISE_PROMT
from utils import parse_mcq_exercises, SimilarityFilter, format_mcq_exercise



def generate(messages):
    client = OpenAI(
        api_key='',
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    response = client.chat.completions.create(
        model="gemini-exp-1121", n=1, messages=messages,
        temperature=1,
        top_p= 0.95,
        top_k=64,
    )

    return response.choices[0].message.content.strip()


def main():
    similarity_filter = SimilarityFilter('all-MiniLM-L6-v2')

    ## 1. Generate exercises
    messages = [
        {
            'role': 'user',
            'content': MCQ_EXERCISE_PROMT.format(
                topic="Economics",
                batch_size=5,
                difficulty="Medium"
            )
        }
    ]

    res = generate(messages=messages)
    exercises = parse_mcq_exercises(res)

    ## 2. Check exercises similarity
    filtered_exercises = similarity_filter.filter(exercises)
    print(filtered_exercises)

    ## 3. Check exercises correctness

    ## 4. Transform MCQ exercises into true/false ones

    ## 5. Ceck tester model knowledge by true/false excercises

    ## 6. MCQ answer by the tester model



if __name__ == '__main__':
    main()