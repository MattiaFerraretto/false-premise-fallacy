import argparse
from rich import print
import json
import yaml
from tqdm import trange
from typing import List, Dict
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import os
import re

from models import DeduplicatinConfig
from prompts import MCQ_EXERCISE_DEDUP_TEMPLATE

parser = argparse.ArgumentParser(description='Deduplication configuration')
parser.add_argument('--config_path', type=str, help='Deduplication configuration file', required=True)

class SemanticDeduplicator:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.embedder = SentenceTransformer(model_name)
        self.embedding_dimension = self.embedder.get_sentence_embedding_dimension()
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dimension)


    def _format(self, exercise: Dict) -> str:
        return MCQ_EXERCISE_DEDUP_TEMPLATE.format(
            statement=exercise['statement'],
            question=exercise['question'],
            A=exercise['options']['A'],
            B=exercise['options']['B'],
            C=exercise['options']['C'],
            D=exercise['options']['D']
        )

    def deduplicate(
        self,
        exercises: List[Dict],
        batch_size: int,
        threshold: float
    ) -> List[Dict]:
        dedup_exercises = []

        for i in trange(0, len(exercises), batch_size):
            batch = exercises[i : i + batch_size]

            embeddings = self.embedder.encode(
                [self._format(exercise) for exercise in batch],
                normalize_embeddings=True
            )
            if embeddings.ndim == 1:
                embeddings = np.expand_dims(embeddings, axis=0)

            for j, embedding in enumerate(embeddings):
                embedding = np.expand_dims(embedding, axis=0)
                distance, _ = self.faiss_index.search(embedding, 1)

                if distance[0, 0] < threshold:
                    self.faiss_index.add(x=embedding)
                    dedup_exercises.append(batch[j])

        return dedup_exercises


def deduplicate(config: DeduplicatinConfig):
    sem_deduplicator = SemanticDeduplicator(
        model_name=config.embedder.model
    )

    with open(config.fpath, 'r') as fp:
        exercises = [json.loads(line.strip()) for line in fp]

    dedup_exercies = sem_deduplicator.deduplicate(
        exercises=exercises,
        batch_size=config.embedder.batch_size,
        threshold=config.embedder.threshold
    )

    match = re.search(r"([a-z]+)-raw-(\d{8}-\d{6})\.jsonl", config.fpath)
    topic = match.group(1) if match else ""
    timestamp = match.group(2) if match else ""

    fpath = Path(
        os.path.join(
            config.output_info.dir,
            config.output_info.fname.format(
                topic=topic,
                timestamp=timestamp
            )
        )
    )
    fpath.parent.mkdir(parents=True, exist_ok=True)

    with open(fpath, 'w') as fp:
        for exercise in dedup_exercies:
            fp.write(f"{json.dumps(exercise)}\n")

        fp.flush()


if __name__ == '__main__':
    args = parser.parse_args()

    with open(args.config_path) as fp:
        conf = yaml.safe_load(fp)

    config = DeduplicatinConfig(**conf)

    deduplicate(config)
