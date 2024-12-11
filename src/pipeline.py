import argparse
from rich import print
from openai import OpenAI

from prompts import MCQ_EXERCISE_PROMT, MCQ_EXERCISE_CORRECTNESS_PROMPT, TF_EXERCISE_PROMPT, FALLACY_DETECTION_PROMPT, EVALUATION_TEMPLATE
from utils import parse_mcq_exercises, SimilarityFilter, parse_correctness_check, parse_tf_exercise, parse_tf_exercise_answer, parse_mcq_answer, APIkeyDispatcher

from tenacity import retry, stop_after_attempt, wait_random_exponential
import json
import yaml
from tqdm import tqdm
from pathlib import Path
import os
from models import Config, GenConfig
from pydantic import HttpUrl

parser = argparse.ArgumentParser(description='Pipeline configuration')
parser.add_argument('--config_path', type=str, help='Pipeline configuration file', required=True)


@retry(stop=stop_after_attempt(10), wait=wait_random_exponential(multiplier=0.5, max=60))
def generate(base_url: HttpUrl, apy_key: str, model: str, prompt: str, gen_config: GenConfig):
    client = OpenAI(
        api_key=apy_key,
        base_url=str(base_url)
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        **gen_config.model_dump()
    ).choices[0].message.content

    return response.strip() if response else ""


def pipeline(config: Config):
    fpath = Path(
        os.path.join(
            config.output_info.dir,
            f"{config.output_info.fname}-{config.topic}.jsonl"
        )
    )
    fpath.parent.mkdir(parents=True, exist_ok=True)

    similarity_filter = SimilarityFilter(
        config.models.embeddings.model,
        config.models.embeddings.threshold,
        os.path.join(
            config.models.embeddings.faiss_dir,
            f"{config.output_info.fname}-{config.topic}.faiss"
        ),
        config.models.embeddings.save_every
    )

    api_keys_dispatcher = APIkeyDispatcher(
        config.models.generator.api_keys
    )

    exercise_counter = 0
    if fpath.exists():
        with open(fpath, 'r') as fp:
            for line in fp:
                exercise = json.loads(line)
                if exercise['mcq_answer']['failed'] and exercise['difficulty'] == config.difficulty.value:
                    exercise_counter += 1

    with open(fpath, 'a') as fp:
        with tqdm(total=config.max_exercises, initial=exercise_counter) as pbar:
            while exercise_counter < config.max_exercises:
                ## 1. Generate exercises
                exercise_prompt = MCQ_EXERCISE_PROMT.format(
                    topic=config.topic,
                    batch_size=config.batch_size,
                    difficulty=config.difficulty.value
                )

                response = generate(
                    base_url=config.models.generator.base_url,
                    apy_key=api_keys_dispatcher(),
                    model=config.models.generator.model,
                    prompt=exercise_prompt,
                    gen_config=config.models.generator.gen_config
                )

                try:
                    exercises = parse_mcq_exercises(
                        config.topic,
                        config.difficulty.value,
                        config.models.generator.model,
                        response
                    )
                except:
                    print("Failed to parse exercises")
                    continue


                ## 2. Check exercises similarity
                filtered_exercises = similarity_filter.filter(exercises)

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
                        base_url=config.models.generator.base_url,
                        apy_key=api_keys_dispatcher(),
                        model=config.models.generator.model,
                        prompt=correctness_prompt,
                        gen_config=config.models.generator.gen_config
                    )

                    try:
                        correctness = parse_correctness_check(response)
                    except:
                        continue

                    if correctness['correctness']['is_correct']:
                        exercise.update(correctness)
                        correct_exercises.append(exercise)

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
                        base_url=config.models.generator.base_url,
                        apy_key=api_keys_dispatcher(),
                        model=config.models.generator.model,
                        prompt=tf_prompt,
                        gen_config=config.models.generator.gen_config
                    )

                    try:
                        tf_question = parse_tf_exercise(response)
                    except:
                        print("Failed to parse tf question")
                        continue

                    exercise.update(tf_question)
                    exercises_w_tfq.append(exercise)

                ## 5. Check tester model knowledge by true/false excercises
                exercises_w_tfa = []
                for exercise in exercises_w_tfq:
                    fallacy_prompt = FALLACY_DETECTION_PROMPT.format(
                        question=exercise['tf_exercise']['question']
                    )

                    response = generate(
                        base_url=config.models.tester.base_url,
                        apy_key=config.models.tester.api_key,
                        model=config.models.tester.model,
                        prompt=fallacy_prompt,
                        gen_config=config.models.tester.gen_config
                    )

                    try:
                        tester_answer = parse_tf_exercise_answer(config.models.tester.model, response)
                    except:
                        print("Failed to parse tf answer")
                        continue

                    exercise['tf_exercise'].update(tester_answer)
                    if not tester_answer['tester']['answer']:
                        exercises_w_tfa.append(exercise)

                ## 6. MCQ answer by the tester model
                for exercise in exercises_w_tfa:
                    evaluation_prompt = EVALUATION_TEMPLATE.format(
                        question=exercise['question'],
                        A=exercise['options']['A'],
                        B=exercise['options']['B'],
                        C=exercise['options']['C'],
                        D=exercise['options']['D']
                    )

                    response = generate(
                        base_url=config.models.tester.base_url,
                        apy_key=config.models.tester.api_key,
                        model=config.models.tester.model,
                        prompt=evaluation_prompt,
                        gen_config=config.models.tester.gen_config
                    )

                    try:
                        mcq_answer = parse_mcq_answer(config.models.tester.model, response)
                    except:
                        print("Failed to parse mcq answer")
                        continue

                    exercise.update(mcq_answer)
                    fp.write(f"{json.dumps(exercise)}\n")


                    if mcq_answer['mcq_answer']['failed']:
                        similarity_filter.add(exercise)
                        exercise_counter += 1
                        pbar.update(1)

                fp.flush()


if __name__ == '__main__':
    args = parser.parse_args()

    with open(args.config_path) as fp:
        conf = yaml.safe_load(fp)

    config = Config(**conf)

    pipeline(config)
