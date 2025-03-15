import re
import json
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import OpenAI
from tqdm import trange
from tqdm import tqdm

CORECTNESS_PROMPT="""Evaluate the provided false premise multiple choice exercise using these criteria:

## 1. Statement Analysis
- ✓ Is the statement (2-3 sentences) about {topic} clearly identifiable? [YES/NO]
- ✓ Does the statement contain a false premise or error? [YES/NO]
- ✓ Is the false premise subtle and plausible rather than obviously incorrect? [YES/NO]
- **Justification:** [Identify the false premise/error and explain why it's subtle yet incorrect]

## 2. Error Impact Assessment
- ✓ Does the error in the statement directly impact question and options? [YES/NO]
- ✓ Does answering the question require recognizing the error? [YES/NO]
- **Justification:** [Explain how the error relates to answering the question]

## 3. Question Assessment
- ✓ Does the question naturally follow from the statement? [YES/NO]
- ✓ Does the question avoid explicitly referencing the statement? (such as: according to this.., based on this.., ecc.) [YES/NO]
- ✓ Is the question answerable in a wrong way only by accepting the flawed premise? [YES/NO]
- **Justification:** [Explain how the question builds upon the false premise]

## 4. Answer Choice Evaluation
- ✓ Do options A, B, and C logically follow from the false premise? [YES/NO]
- ✓ Is option D precisely "None of the above"? [YES/NO]
- ✓ Are all options written in clear, conversational language? [YES/NO]
- **Justification:** [Explain how options A-C require accepting the false premise]

## 5. Critical Thinking Assessment
- ✓ Does the exercise effectively test critical thinking skills? [YES/NO]
- ✓ Would a student need to verify information rather than simply accepting it? [YES/NO]
- ✓ Is there a clear correct answer for someone who applies proper critical thinking? [YES/NO]
- **Justification:** [Explain how the exercise tests critical thinking and what the correct approach would be]

Check systematically each criteria by answering YES when it is met, otherwise NO.

**Important:**
 - Do not introduction or comments.
 - Strictly adhere to the output format.

---

Statement: {statement}

Question: {question}

Options:
A) {A}
B) {B}
C) {C}
D) {D}"""

class GetNextKey:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def __call__(self):
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

pattern = re.compile(
    r"Statement:\s*(.*?)\s*"
    r"Question:\s*(.*?)\s*"
    r"Options:\s*((?:[A-D]\) .+?\n?)+)(?:\n--|\Z)",
    re.DOTALL
)

def parse(res):
    matches = pattern.findall(res)

    mcqs = []
    for statement, question, options in matches:
        option_matches = re.findall(r"([A-D])\) (.+)", options)
        mcqs.append({
            "statement": statement.strip(),
            "question": question.strip(),
            "options": {key: value.strip() for key, value in option_matches}
        })

    return mcqs

@retry(stop=stop_after_attempt(10), wait=wait_random_exponential(multiplier=0.5, max=60))
def generate(client: OpenAI, model: str, prompt: str):

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        temperature=1,
        top_p=0.95,
        max_completion_tokens= 8192
    ).choices[0].message.content


    if not response:
        return {
            'eval': {
                'correctness': "",
                'score': 0,
                'failed': True
            }
        }

    count = sum(1 for _ in re.finditer(r"\[NO\]", response, re.MULTILINE))

    return {
        'eval': {
            'correctness': response.strip(),
            'score': round(count/14, 4),
            'failed': True if count > 0 else False
       }
    }


def main():
    next_key = GetNextKey([
        "AIzaSyDWaK6kh7IrtPLbR6HesCzg-Lh7fHmrkSk",
        "AIzaSyAtxSwzt_BrGFhzkaS8dMmdcoNnStdLbzY",
        "AIzaSyB0vEa6wcLxLBHnu7109DYDjuNtrhk829A",
        "AIzaSyBrm8g8sBhFcG7y6Le2MsSNv15wdUiNxas",
        "AIzaSyAabmbGLnf9UmE6SThH6Fko6THTBzJHsyg"]
    )

    with open('./output/law-raw.txt', 'r') as fp:
        exercises = fp.read()

    exercises = parse(exercises)

    with open("./output/law-raw-eval.jsonl", "a") as fp:
        for exercise in tqdm(exercises):
            res = generate(
                client=OpenAI(
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=next_key()
                ),
                model="gemini-2.0-pro-exp-02-05",
                prompt=CORECTNESS_PROMPT.format(
                    topic="law",
                    statement=exercise['statement'],
                    question=exercise['question'],
                    A=exercise['options']['A'],
                    B=exercise['options']['B'],
                    C=exercise['options']['C'],
                    D=exercise['options']['D']
                )
            )

            exercise.update(res)
            fp.write(f"{json.dumps(exercise)}\n")
            fp.flush()


if __name__ == '__main__':
    main()
