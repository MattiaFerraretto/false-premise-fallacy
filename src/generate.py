import argparse
from rich import print
from openai import OpenAI
import re
from tenacity import retry, stop_after_attempt, wait_random_exponential
import json
import yaml
from tqdm import tqdm
from pathlib import Path
import os
from models import GenerationExerciseConfig, GenConfig
from pydantic import HttpUrl
from datetime import datetime

from prompts import MCQ_GENERATION_PROMPT, MCQ_EXERCISE_OUTPUT_TEMPLATE


parser = argparse.ArgumentParser(description='Exercise generation configuration')
parser.add_argument('--config_path', type=str, help='Exercise generation configuration file', required=True)

def format_mcq_exercise(exercise: dict):
    return MCQ_EXERCISE_OUTPUT_TEMPLATE.format(
        statement=exercise['statement'],
        question=exercise['question'],
        A=exercise['options']['A'],
        B=exercise['options']['B'],
        C=exercise['options']['C'],
        D=exercise['options']['D']
    )

pattern = re.compile(
    r"Statement:\s*(.*?)\s*"
    r"Question:\s*(.*?)\s*"
    r"Options:\s*((?:[A-D]\) .+?\n?)+)(?:\n---|\Z)",
    re.DOTALL
)

def parse(res):
    matches = pattern.findall(res)

    mcqs = []
    for statement, question, options in matches:
        option_matches = re.findall(r"([A-D])\) (.+)", options)
        if len(option_matches) != 4:
            continue

        mcqs.append({
            "statement": statement.strip(),
            "question": question.strip(),
            "options": {key: value.strip() for key, value in option_matches}
        })

    return mcqs

@retry(stop=stop_after_attempt(10), wait=wait_random_exponential(multiplier=0.5, max=60))
def generate(client: OpenAI, model: str, prompt: str, gen_config: GenConfig):

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


def generate_exercises(config: GenerationExerciseConfig):
    client = OpenAI(
        api_key=config.endpoint.api_key,
        base_url=str(config.endpoint.base_url)
    )

    fpath = Path(
        os.path.join(
            config.output_info.dir,
            config.output_info.fname.format(
                topic=config.topic,
                timestamp=datetime.now().strftime("%Y%m%d-%H%M%S")
            )
        )
    )
    fpath.parent.mkdir(parents=True, exist_ok=True)

    history = []
    exercise_counter = 0
    with open(fpath, 'w') as fp:
        with tqdm(total=config.num_exercises, initial=exercise_counter) as pbar:
            while exercise_counter < config.num_exercises:
                prompt = MCQ_GENERATION_PROMPT.format(
                    topic=config.topic,
                    batch_size=config.batch_size,
                    history = "\n\n---\n\n".join([format_mcq_exercise(exercise) for exercise in history[-config.history_size:]])
                )
                exercises = generate(
                    client=client,
                    model=config.endpoint.model,
                    prompt=prompt,
                    gen_config=config.endpoint.gen_config
                )

                exercises = parse(exercises)

                exercise_counter += len(exercises)
                pbar_updt = len(exercises)
                if len(history) + len(exercises) > config.num_exercises:
                    pbar_updt = config.num_exercises - len(history)

                history.extend(exercises)

                for exercise in exercises:
                    fp.write(f"{json.dumps(exercise)}\n")
                fp.flush()

                pbar.update(pbar_updt)

if __name__ == '__main__':
    args = parser.parse_args()

    with open(args.config_path) as fp:
        conf = yaml.safe_load(fp)

    config = GenerationExerciseConfig(**conf)

    generate_exercises(config)
