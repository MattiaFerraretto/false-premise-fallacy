import re
from prompts import MCQ_EXERCISE_TEMPLATE

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List

def format_mcq_exercise(excercise: dict):
    return MCQ_EXERCISE_TEMPLATE.format(
        question=excercise['question'],
        A=excercise['options']['A'],
        B=excercise['options']['B'],
        C=excercise['options']['C'],
        D=excercise['options']['D']
    )

class SimilarityFilter:
    def __init__(self, encoder_name: str, similarity_treshold: float=0.7):
        self.encoder_name = encoder_name
        self.similarity_treshold = similarity_treshold
        self.encoder = SentenceTransformer(encoder_name)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)

    
    def filter(self, exercises: List[dict]) -> List[dict]:
        queries = [format_mcq_exercise(exercise) for exercise in exercises]
        embeddings = self.encoder.encode(queries, normalize_embeddings=True)
        embeddings = np.expand_dims(embeddings, axis=0) if embeddings.ndim == 1 else embeddings

        filtered_exercises= []
        for i, embedding in enumerate(embeddings):
            embedding = np.expand_dims(embedding, axis=0)
            distance, _ = self.index.search(embedding, 1)

            if distance[0, 0] < self.similarity_treshold:
                self.index.add(embedding)
                filtered_exercises.append(exercises[i])
        
        return filtered_exercises
        

def parse_mcq_exercises(exercises: str):

    def parse_options(options: str):
        options = re.findall(r"[A-D]\) (.*?)\n", options)
        return {
            "A": options[0].strip(),
            "B": options[1].strip(),
            "C": options[2].strip(),
            "D": options[3].strip(),
        }

    def parse_exercise(exercise: str):
        question = re.search(r"<question>(.*?)</question>", exercise, re.DOTALL).group(1)
        options = re.search(r"<options>(.*?)</options>", exercise, re.DOTALL).group(1)
        false_premise = re.search(r"<false_premise>(.*?)</false_premise>", exercise, re.DOTALL).group(1)
        return {
            "question": question.strip(),
            "options": parse_options(options),
            "false_premise": false_premise.strip(),
        }

    exercises = re.findall(r"<exercise>(.*?)</exercise>", exercises, re.DOTALL)
    return [parse_exercise(exercise) for exercise in exercises]





