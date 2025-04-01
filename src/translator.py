import argparse
from rich import print
from openai import AsyncOpenAI

from tenacity import retry, stop_after_attempt, wait_random_exponential
import json
import yaml
from tqdm import trange
from models import TranslatorConfig, GenConfig
from pydantic import HttpUrl
from asyncio import run, gather, sleep
from datasets import load_dataset
import re
import hashlib
from pathlib import Path
import os
from prompts import TRANSLATION_PROMPT

parser = argparse.ArgumentParser(description='Translator configuration')
parser.add_argument('--config_path', type=str, help='Transaltor configuration file', required=True)


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
      mcqs.append({
          "statement": statement.strip(),
          "question": question.strip(),
          "options": {key: value.strip() for key, value in option_matches}
      })

  return mcqs

def generate_hash(exercise):
        exercise_str = json.dumps(exercise, sort_keys=True)
        return hashlib.md5(exercise_str.encode()).hexdigest()

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


async def translate(config: TranslatorConfig):
    async_client = AsyncOpenAI(
        api_key=config.endpoint.api_key,
        base_url=str(config.endpoint.base_url)
    )

    for split in config.dataset.splits:
        ds = load_dataset(
            path=config.dataset.path,
            name=config.dataset.name,
            split=split,
            token=config.dataset.token
        )

        fpath = Path(
            os.path.join(
                config.output_info.dir,
                config.output_info.fname.format(topic=split)
            )
        )
        fpath.parent.mkdir(parents=True, exist_ok=True)

        with open(fpath, 'w', encoding='utf-8') as fp:
            for i in trange(0, len(ds), config.batch_size, desc=f"Translating {split}"):
                batch = ds[i: i + config.batch_size]
                batch = [{key: batch[key][i] for key in batch.keys()}  for i in range(len(batch['statement']))]

                responses = await gather(
                    *[
                        generate(
                            async_client=async_client,
                            model=config.endpoint.model,
                            prompt=TRANSLATION_PROMPT.format(
                                statement=exercise['statement'],
                                question=exercise['question'],
                                A=exercise['options']['A'],
                                B=exercise['options']['B'],
                                C=exercise['options']['C'],
                                D=exercise['options']['D']
                            ),
                            gen_config=config.endpoint.gen_config
                        ) for exercise in batch]
                )

                for exercise in responses:
                    exercise = parse(exercise)[0]
                    exercise['hash'] = generate_hash(exercise)
                    fp.write(json.dumps(exercise) + '\n')

                fp.flush()

                await sleep(1)


if __name__ == '__main__':
    args = parser.parse_args()

    with open(args.config_path) as fp:
        conf = yaml.safe_load(fp)

    config = TranslatorConfig(**conf)

    run(translate(config))
