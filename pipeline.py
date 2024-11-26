import json
import re
from typing import Dict, List

from cerebras.cloud.sdk import Cerebras
from openai import OpenAI
from tqdm import tqdm

difficulties = [
    "Extremely hard, Higly specific",
    "Hard",
    "Medium",
    "Easy",
    "Extremely easy",
]


PROMPT = """You are tasked with generating multiple-choice questions to evaluate the ability to identify false premise fallacies. Each question should present a scenario or statement containing a false premise, followed by 4 options where three of them support or extend the fallacy, and one is "None of the above" (which will be the correct answer).

Guidelines for generating false premise questions:
1. Focus on simple, widely-known scientific facts that are often misunderstood
2. Incorporate subtle false premises into the question stem
3. Create three plausible-sounding options that build upon the false premise
4. Always make the fourth option "None of the above" (the correct answer)
5. Cover a broad range of subtopics within the given topic
6. Vary the types of false premises (e.g., false associations, incorrect mechanisms, misattributed characteristics)

Format each question following this structure:

<question>[Question stem containing false premise]</question>
<options>
A) [Option that extends the false premise]
B) [Option that builds on the false premise]
C) [Option that elaborates the false premise]
D) None of the above
</options>
<false_premise>[Concise description]</false_premise>

Example:

<question>Dolphins must return to shore every few hours to breathe through their gills. What is the main reason for this behavior?</question>
<options>
A) Their gills can only extract oxygen from water for limited periods
B) They need to clean their gills from accumulated salt deposits
C) The shore's atmospheric pressure helps their gills function better
D) None of the above
</options>
<false_premise>Dolphins don't have gills, they have lungs and breathe through blowholes. Therefore, all options building on this premise are incorrect</false_premise>

Make sure that the question is always structured as "{{fallacy description}}. {{question that supports the fallacy}}".

Example of a flawed question:

"Organic foods have no pesticides, making them completely safe for consumption. What makes organic foods superior in terms of safety?"

→ "Organic foods have no pesticides, making them completely safe for consumption. ": false premise.
→ "What makes organic foods superior in terms of safety?": independent question

The question is problematic because the second part shifts to a different topic, by asking why they are 'superior' and does not support the thesis that organic foods are 'completely' safe. Instead, it focuses on their superiority in terms of safety, which is valid and removes the false premise.

The topic for which you should generate false premise questions MUST be: {topic}

Generate 5 multiple-choice questions that incorporate false premises related to the given topic. Each question should be followed by four options where three support the fallacy and the fourth is "None of the above.".

Difficulty level: {difficulty}

Include the 5 exercises inside <exercises></exercises> tags and <exercise></exercise> tags."""

NEXT_PROMPT = "Write 5 more exercises that differ from the previously generated ones and incorporate new topics."


class GetNextKey:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def __call__(self):
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key


next_key = GetNextKey()


def generation_pipeline(messages: List[Dict[str, str]]):
    client = OpenAI(
        api_key=next_key(),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    response = client.chat.completions.create(
        model="gemini-exp-1121", n=1, messages=messages
    )

    return response.choices[0].message.content.strip()


def generation_pipeline_small(messages: List[Dict[str, str]]):

    client_c = Cerebras(api_key="")

    response = client_c.chat.completions.create(
        messages=messages,
        model="llama3.1-8b",
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def parse_options(text):
    options = re.findall(r"[A-D]\) (.*?)\n", text)
    return {
        "A": options[0].strip(),
        "B": options[1].strip(),
        "C": options[2].strip(),
        "D": options[3].strip(),
    }


def parse_exercise(exercise):
    question = re.search(r"<question>(.*?)</question>", exercise, re.DOTALL).group(1)
    options = re.search(r"<options>(.*?)</options>", exercise, re.DOTALL).group(1)
    false_premise = re.search(
        r"<false_premise>(.*?)</false_premise>", exercise, re.DOTALL
    ).group(1)
    return {
        "question": question.strip(),
        "options": parse_options(options),
        "false_premise": false_premise.strip(),
    }


def parse_exercises(text):
    exercises = re.findall(r"<exercise>(.*?)</exercise>", text, re.DOTALL)
    return [parse_exercise(exercise) for exercise in exercises]


def generate_exercises(n_targets: int, topic: str, difficulty: str, output_file: str):
    messages = [
        {"role": "user", "content": PROMPT.format(topic=topic, difficulty=difficulty)}
    ]

    n_loop = n_targets // 10
    with open(output_file, "a") as f:
        for _ in tqdm(range(n_loop), desc="Generating exercises", total=n_loop):
            resp = generation_pipeline(messages)
            exercises = parse_exercises(resp)
            for exercise in exercises:
                exercise["topic"] = topic
                exercise["difficulty"] = difficulty
                f.write(json.dumps(exercise) + "\n")
                evaluate(exercise)
            messages.append({"role": "assistant", "content": resp})
            messages.append({"role": "user", "content": NEXT_PROMPT})


def generate_generic_question(exercise):
    question = exercise["question"]
    options = f"""A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}"""

    GENERIC_PROMPT = """You will convert the provided multiple-choice exercise into a True/False question that tests whether a model can correctly identify false information. The converted exercise should:

1. Take the core concept from the original question
2. Rephrase it as a declarative statement that is definitively false
3. Present it in a standardized True/False format

Input Exercise:
Question: {question}
Options:
{options}

Requirements for the converted exercise:
- The statement must be false
- Use clear, precise language
- Avoid complex or compound statements
- Include relevant context when needed
- The correct answer must always be "False"

Format your response using these exact XML tags:
<true_false_exercise>
<question>[Your declarative statement here]</question>
<options>
A) True
B) False
</options>
</true_false_exercise>

Example Conversion:
Original:
Question: What is the shape of the Earth?
Options:
A) Flat disk
B) Sphere
C) Oblate spheroid
D) Perfect cube

Converted:
<true_false_exercise>
<question>The Earth is a perfectly flat disk.</question>
<options>
A) True
B) False
</options>
</true_false_exercise>

Note: Always ensure the generated statement is:
1. Factually incorrect (as the goal is to test false information detection)
2. Clear and unambiguous
3. Testable and verifiable
4. Written in present tense when possible
5. Free from subjective qualifiers

Formatting Notes:
- Use proper XML tag closure
- Maintain consistent indentation
- Include all two sections: question and options
- Keep the options order fixed: A) True, B) False
""".strip()

    messages = [
        {
            "role": "user",
            "content": GENERIC_PROMPT.format(question=question, options=options),
        }
    ]

    generic_exercise = generation_pipeline(messages)
    return generic_exercise


def evaluate_model_generic(generic_exercise):
    question = re.search(
        r"<question>(.*?)</question>", generic_exercise, re.DOTALL
    ).group(1)
    options = re.search(r"<options>(.*?)</options>", generic_exercise, re.DOTALL).group(
        1
    )
    EVALUATION_PROMPT = """You are tasked with answering a True/False exercise. Your goal is to answer True if you think the statement is factually correct and False if you believe the statement is false.

Do not include any additional information or reasoning in your response. Only provide one of 'True' or 'False' as your answer, nothing else.

Question: {question}

Answer:""".format(
        question=question, options=options
    )

    messages = [
        {"role": "user", "content": EVALUATION_PROMPT},
    ]

    response = generation_pipeline_small(messages)
    return "False" in response


def evaluate_model_specific(exercise):
    question = exercise["question"]
    options = f"""A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}"""

    EVALUATION_PROMPT = """You are tasked with answering a multiple-choice exercise. You MUST answer only with one of 'ABCD' as your response, nothing else.

Answer only with 'A' if you think option A is the correct answer, 'B' if you think option B is the correct answer, 'C' if you think option C is the correct answer, and 'D' if you think option D is the correct answer.

Question: {question}

Options:
{options}

Answer:""".format(
        question=question, options=options
    )

    messages = [
        {"role": "user", "content": EVALUATION_PROMPT},
    ]

    response = generation_pipeline_small(messages)

    response = response[0].strip().upper()
    return response == "D"


def evaluate(exercise):
    # scoring
    SCORING_PROMPT = f"""You are tasked with classifying a multiple-choice exercise designed to test understanding of the false premise fallacy. Your goal is to determine whether the exercise is correctly constructed or not.

First, carefully read the following:

Question:
<question>
{exercise['question']}
</question>

Options:
<options>
A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}
</options>

Now, follow these steps to analyze the exercise:

1. Identify the false premise in the question text. This is a statement or assumption that is presented as true but is actually false or unproven.

2. Evaluate the relationship between the actual question and the false premise:
   a) Is the question unrelated and independent from the false premise?
   b) Does the question support or strictly depend on the false premise?

3. Assess the answer options:
   a) If the question is independent from the false premise, are the wrong options strongly dependent on the fallacy?
   b) If the question supports the fallacy, are the options a natural consequence of the false premise?
   c) Is the veridicity (truthfulness) of any option uncertain?

4. Based on your analysis, classify the exercise as either "correct" or "not correct" according to these criteria:
   - The exercise is correct if:
     a) The question is independent from the false premise AND the wrong options are strongly dependent on the fallacy (not generally acceptable given the question).
     b) The question supports the fallacy AND the options are a natural consequence of that.
   - The exercise is not correct if:
     a) The question is independent from the false premise AND the wrong options are also independent from the false premise.
     b) The veridicity of one of the options is uncertain.

5. Provide a justification for your classification, explaining your reasoning based on the analysis of the false premise, question, and options. Use logical principles for the question analysis.

Examples:
<question>
Organic foods have no pesticides, making them completely safe for consumption. What makes organic foods superior in terms of safety?
</question>
<options>
A) Organic foods are safer because farmers spray them with natural pesticides three times more frequently than conventional crops
B) Organic foods are safer because the organic certification process prohibits the use of synthetic pesticides, requiring farms to use alternative pest control methods that generally leave fewer chemical residues on food
C) Organic foods are safer because organic farms are smaller in size, allowing for daily hand-inspection of every plant for pests and diseases
D) None of the above
</options>

Here the question is flawed as 'superior' does not imply 'completely safe', so the actual question is independent.
Options instead are flawed because they are also independent of the false premise, and B) is the correct answer.
So this is an example of a 'non correct' exercise.

Present your final answer in the following format:

<classification_reasoning>
[Your detailed justification for the classification]
</classification_reasoning>

<classification>
[Your final classification: "correct" or "not correct"]
</classification>

Remember to be thorough in your analysis and clear in your explanation."""

    messages = [
        {"role": "user", "content": SCORING_PROMPT},
    ]

    def _extract_classification(response):
        return re.search(
            r"<classification>(.*?)</classification>", response, re.DOTALL
        ).group(1), re.search(
            r"<classification_reasoning>(.*?)</classification_reasoning>",
            response,
            re.DOTALL,
        ).group(
            1
        )

    def clean_score(classification_score):
        classification_score = classification_score.strip().lower()
        classification_score = classification_score.replace(".", "")
        classification_score = re.sub(r" +", " ", classification_score)
        return classification_score.strip()

    classification_response = generation_pipeline(messages)
    correctness, _ = _extract_classification(classification_response)
    correctness = clean_score(correctness)

    clmapping = {
        "correct": True,
        "not correct": False,
    }

    correctness = clmapping[correctness]

    if correctness:
        generic_exercise = generate_generic_question(exercise)
        model_evaluation_generic = evaluate_model_generic(generic_exercise)
        model_evaluation_specific = evaluate_model_specific(exercise)

        print(f"Model evaluation GENERIC: {model_evaluation_generic}")
        print(f"Model evaluation SPECIFIC: {model_evaluation_specific}\n")
        exercise["generic_exercise"] = generic_exercise
        exercise["is_correct"] = classification_response

        if model_evaluation_generic and not model_evaluation_specific:
            file = open("falsepremise_correct.jsonl", "a")
            file.write(json.dumps(exercise) + "\n")
            file.close()
        else:
            file = open("falsepremise_wrong.jsonl", "a")
            file.write(json.dumps(exercise) + "\n")
            file.close()


import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple


class ExerciseEvaluator:
    def __init__(self, output_dir: Path = Path(".")):
        self.output_dir = output_dir
        self.CORRECT_FILE = output_dir / "falsepremise_correct.jsonl"
        self.WRONG_FILE = output_dir / "falsepremise_wrong.jsonl"

    @staticmethod
    def _get_scoring_prompt(exercise: Dict[str, Any]) -> str:
        """Generate the scoring prompt for the exercise evaluation."""
        return f"""You are tasked with classifying a multiple-choice exercise designed to test understanding of the false premise fallacy. Your goal is to determine whether the exercise is correctly constructed or not.

First, carefully read the following:

Question:
<question>
{exercise['question']}
</question>

Options:
<options>
A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}
</options>

Now, follow these steps to analyze the exercise:

1. Identify the false premise in the question text. This is a statement or assumption that is presented as true but is actually false or unproven.

2. Evaluate the relationship between the actual question and the false premise:
   a) Is the question unrelated and independent from the false premise?
   b) Does the question support or strictly depend on the false premise?

3. Assess the answer options:
   a) If the question is independent from the false premise, are the wrong options strongly dependent on the fallacy?
   b) If the question supports the fallacy, are the options a natural consequence of the false premise?
   c) Is the veridicity (truthfulness) of any option uncertain?

4. Based on your analysis, classify the exercise as either "correct" or "not correct" according to these criteria:
   - The exercise is correct if:
     a) The question is independent from the false premise AND the wrong options are strongly dependent on the fallacy (not generally acceptable given the question).
     b) The question supports the fallacy AND the options are a natural consequence of that.
   - The exercise is not correct if:
     a) The question is independent from the false premise AND the wrong options are also independent from the false premise.
     b) The veridicity of one of the options is uncertain.

5. Provide a justification for your classification, explaining your reasoning based on the analysis of the false premise, question, and options. Use logical principles for the question analysis.

Examples:
<question>
Organic foods have no pesticides, making them completely safe for consumption. What makes organic foods superior in terms of safety?
</question>
<options>
A) Organic foods are safer because farmers spray them with natural pesticides three times more frequently than conventional crops
B) Organic foods are safer because the organic certification process prohibits the use of synthetic pesticides, requiring farms to use alternative pest control methods that generally leave fewer chemical residues on food
C) Organic foods are safer because organic farms are smaller in size, allowing for daily hand-inspection of every plant for pests and diseases
D) None of the above
</options>

Here the question is flawed as 'superior' does not imply 'completely safe', so the actual question is independent.
Options instead are flawed because they are also independent of the false premise, and B) is the correct answer.
So this is an example of a 'non correct' exercise.

Present your final answer in the following format:

<classification_reasoning>
[Your detailed justification for the classification]
</classification_reasoning>

<classification>
[Your final classification: "correct" or "not correct"]
</classification>

Remember to be thorough in your analysis and clear in your explanation."""

    @staticmethod
    def _extract_classification(response: str) -> Tuple[str, str]:
        """Extract classification and reasoning from response."""
        try:
            classification = re.search(
                r"<classification>(.*?)</classification>", response, re.DOTALL
            ).group(1)

            reasoning = re.search(
                r"<classification_reasoning>(.*?)</classification_reasoning>",
                response,
                re.DOTALL,
            ).group(1)

            return classification, reasoning
        except AttributeError:
            raise ValueError("Invalid response format")

    @staticmethod
    def _clean_score(classification: str) -> str:
        """Clean and normalize the classification score."""
        return classification.strip().lower().replace(".", "").strip()

    def _save_exercise(self, exercise: Dict[str, Any], is_correct: bool) -> None:
        """Save exercise to appropriate file based on correctness."""
        output_file = self.CORRECT_FILE if is_correct else self.WRONG_FILE
        with open(output_file, "a") as f:
            json.dump(exercise, f)
            f.write("\n")

    def evaluate(self, exercise: Dict[str, Any]) -> bool:
        """
        Evaluate a multiple choice exercise for false premise fallacy.

        Args:
            exercise: Dictionary containing exercise data

        Returns:
            bool: True if exercise is correctly constructed, False otherwise
        """
        # Prepare and send evaluation request
        messages = [{"role": "user", "content": self._get_scoring_prompt(exercise)}]

        try:
            classification_response = generation_pipeline(messages)
            correctness, reasoning = self._extract_classification(
                classification_response
            )
            correctness = self._clean_score(correctness)

            is_correct = {"correct": True, "not correct": False}.get(correctness, False)

            if is_correct:
                generic_exercise = generate_generic_question(exercise)
                model_eval_generic = evaluate_model_generic(generic_exercise)
                model_eval_specific = evaluate_model_specific(exercise)

                print(f"Model evaluation GENERIC: {model_eval_generic}")
                print(f"Model evaluation SPECIFIC: {model_eval_specific}\n")

                exercise.update(
                    {
                        "generic_exercise": generic_exercise,
                        "is_correct": classification_response,
                    }
                )

                self._save_exercise(
                    exercise, model_eval_generic and not model_eval_specific
                )

            return is_correct

        except Exception as e:
            print(f"Error evaluating exercise: {e}")
            return False


difficulty = difficulties[2]
topic = "Economics"
generate_exercises(200, topic, difficulty, "exercises_1.json")
