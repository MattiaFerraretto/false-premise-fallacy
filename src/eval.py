import argparse
from rich import print
from openai import AsyncOpenAI
from typing import Dict
from tenacity import retry, stop_after_attempt, wait_random_exponential
import json
import yaml
from tqdm import trange
from models import EvalConfig, GenConfig
from pydantic import HttpUrl
from asyncio import run, gather, sleep
from datasets import load_dataset
import re
import hashlib
from pathlib import Path
import os
import tabulate
import numpy as np
from datetime import datetime

from prompts import PREMISE_KNOWHOW_PROMPT_EN, PREMISE_KNOWHOW_PROMPT_IT, EVAL_PROMPT_EN, EVAL_PROMPT_IT

parser = argparse.ArgumentParser(description='Eval configuration')
parser.add_argument('--config_path', type=str, help='Eval configuration file', required=True)

answer_pattern = re.compile(
    #r"\s*\*{0,3}(?:Risposta|Answer):\*{0,3}\s+(A|B|C|D|True|False|Vero|Falso)"
    #r"\s*\*{0,3}(?:Risposta|Answer):\*{0,3}\s+(?:(True|False|Vero|Falso)|\\boxed{(A|B|C|D)})\*{0,3}"
    r"\n*\*{0,3}(?:Risposta|Answer).*:\*{0,3}\s+(A|a|B|b|C|c|D|d|True|true|TRUE|False|false|FALSE|Vero|vero|VERO|Falso|falso|FALSO)\*{0,3}\n*"
)

premise_lang = {
    'en': PREMISE_KNOWHOW_PROMPT_EN,
    'it': PREMISE_KNOWHOW_PROMPT_IT
}

eval_lang = {
    'en': EVAL_PROMPT_EN,
    'it': EVAL_PROMPT_IT
}


@retry(stop=stop_after_attempt(10), wait=wait_random_exponential(multiplier=0.5, max=60))
async def generate(async_client: AsyncOpenAI, model: str, prompt: str, gen_config: GenConfig):

    response = await async_client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        **gen_config.model_dump()
    )

    return response.choices[0].message.content.strip() if response else ""

async def eval_mcq(async_client: AsyncOpenAI, model: str, gen_config: GenConfig, lang: str, mcq_exercise: Dict):

    premise_prompt = premise_lang[lang]
    premise_raw_answer = await generate(
        async_client=async_client,
        model=model,
        prompt=premise_prompt.format(statement=mcq_exercise['statement']),
        gen_config=gen_config
    )

    premise_answer = answer_pattern.search(premise_raw_answer)
    premise_answer = premise_answer.group(1) if premise_answer else ""

    if premise_answer in ['True', 'Vero', '']:
        return {
            'premise_eval': {
                'raw_answer': premise_raw_answer,
                'short_answer': premise_answer,
                'failed': True
            },
            'exercise_eval': None
        }

    eval_prompt = eval_lang[lang]
    exercise_raw_answer = await generate(
        async_client=async_client,
        model=model,
        prompt=eval_prompt.format(
            statement=mcq_exercise['statement'],
            question=mcq_exercise['question'],
            A=mcq_exercise['options']['A'],
            B=mcq_exercise['options']['B'],
            C=mcq_exercise['options']['C'],
            D=mcq_exercise['options']['D'],
        ),
        gen_config=gen_config
    )

    exercise_answer = answer_pattern.search(exercise_raw_answer)
    exercise_answer = exercise_answer.group(1) if exercise_answer else ""
    #exercise_answer = exercise_answer.group(2) if exercise_answer else ""

    return {
        'premise_eval': {
            'raw_answer': premise_raw_answer,
            'short_answer': premise_answer,
            'failed': False
        },
        'exercise_eval': {
            'raw_answer': exercise_raw_answer,
            'short_answer': exercise_answer,
            'failed': exercise_answer != 'D'
        }
    }

async def eval(config: EvalConfig):
    async_client = AsyncOpenAI(
        api_key=config.endpoint.api_key,
        base_url=str(config.endpoint.base_url)
    )

    results = []
    mname = config.endpoint.model.split('/')
    fname = config.output_info.fname.format(
        lang=config.dataset.name,
        model= mname[1] if len(mname) > 1 else mname[0],
        timestamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    )

    for split in config.dataset.splits:
        ds = load_dataset(
            path=config.dataset.path,
            name=config.dataset.name,
            split=split,
            token=config.dataset.token
        )

        #ds = ds.select(list(range(8)))

        fpath = Path(
            os.path.join(
                config.output_info.dir,
                config.output_info.subdir,
                f"{fname}.jsonl"
            )
        )
        fpath.parent.mkdir(parents=True, exist_ok=True)

        premise_failed = []
        exercise_results = []

        with open(fpath, 'a', encoding='utf-8') as fp:
            for i in trange(0, len(ds), config.batch_size, desc=f"Evaluating {split}"):
                batch = ds[i: i + config.batch_size]
                batch = [{key: batch[key][i] for key in batch.keys()}  for i in range(len(batch['statement']))]

                responses = await gather(
                    *[
                        eval_mcq(
                            async_client=async_client,
                            model=config.endpoint.model,
                            gen_config=config.endpoint.gen_config,
                            lang=config.dataset.name,
                            mcq_exercise=exercise
                        ) for exercise in batch]
                )

                for exercise, eval in zip(batch, responses):
                    eval['mcq_id'] = exercise['hash']
                    eval['topic'] = split
                    fp.write(json.dumps(eval) + '\n')

                    if eval['premise_eval']['failed']:
                        premise_failed.append(1)
                        continue

                    exercise_results.append(1 if not eval['exercise_eval']['failed'] else 0)

                fp.flush()

                #await sleep(1)

            accuracy = np.mean(exercise_results)
            std_err = np.std(exercise_results)
            results.append([
                f"{split}_{config.dataset.name}",
                "acc",
                f"{accuracy:.4f}",
                f"{std_err:.4f}",
                f"{len(premise_failed)}",
                f"{len(exercise_results)}",
                f"{len(ds)}"
            ])
            #break

    results_table = tabulate.tabulate(
        results,
        headers=['Tasks', 'Metric', 'Value', 'Stderr', 'Premises failed', 'Answered',  'Total'],
        tablefmt="grid_tables"
    )

    with open(os.path.join(config.output_info.dir, f"{fname}.txt"), 'w', encoding='utf-8') as fp:
        fp.write(results_table)
        fp.flush()

    print(results_table)


if __name__ == '__main__':
    args = parser.parse_args()

    with open(args.config_path) as fp:
        conf = yaml.safe_load(fp)

    config = EvalConfig(**conf)

    run(eval(config))
