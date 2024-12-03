import re
from prompts import MCQ_EXERCISE_TEMPLATE

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List
from hashlib import md5
from datetime import datetime

class APIkeyDispatcher:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def __call__(self):
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

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
                self.index.add(x=embedding)
                filtered_exercises.append(exercises[i])

        return filtered_exercises


def parse_mcq_exercises(generator: str, exercises: str):
    def parse_options(options: str):
        options_list = re.findall(r"[A-D]\) (.*?)\n", options)
        return {
            "A": options_list[0].strip(),
            "B": options_list[1].strip(),
            "C": options_list[2].strip(),
            "D": options_list[3].strip(),
        }

    def parse_exercise(generator: str, exercise: str):
        question = re.search(r"<question>(.*?)</question>", exercise, re.DOTALL)
        question = question.group(1) if question else ""

        options = re.search(r"<options>(.*?)</options>", exercise, re.DOTALL)
        options = options.group(1) if options else ""

        false_premise = re.search(r"<false_premise>(.*?)</false_premise>", exercise, re.DOTALL)
        false_premise = false_premise.group(1) if false_premise else ""

        return {
            'mcq_id': md5(f"{question.strip()}\n\n{options.strip()}".encode()).hexdigest(),
            'generator': generator,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question.strip(),
            "options": parse_options(options),
            "false_premise": false_premise.strip()
        }

    exercises_list = re.findall(r"<exercise>(.*?)</exercise>", exercises, re.DOTALL)
    return [parse_exercise(generator, exercise) for exercise in exercises_list]

def parse_correctness_check(correctness_response: str):
    reasoning = re.search(r"<classification_reasoning>\s*(.*?)\s*</classification_reasoning>", correctness_response, re.DOTALL)
    reasoning = reasoning.group(1) if reasoning else ""

    result = re.search(r"<classification>\s*(.*?)\s*</classification>", correctness_response, re.DOTALL)
    result = result.group(1) if result else ""

    return {
        'correctness':{
            'reasoning': reasoning,
            'is_correct': True if result == 'correct' else False
        }
    }

def parse_tf_exercise(tf_exercise: str):
    def parse_options(options: str):
        options_list = re.findall(r"[A-B]\) (.*?)\n", options)
        return {
            "A": options_list[0].strip(),
            "B": options_list[1].strip()
        }

    question = re.search(r"<question>(.*?)</question>", tf_exercise, re.DOTALL)
    question = question.group(1) if question else ""

    options = re.search(r"<options>(.*?)</options>", tf_exercise, re.DOTALL)
    options = options.group(1) if options else ""

    return {
        "tf_exercise":{
            "question": question.strip(),
            "options": parse_options(options)
        }
    }

def parse_tf_exercise_answer(tester: str, tf_answer: str):
    return {
        'tester': {
            'name': tester,
            'answer': True if tf_answer == 'True' else False
        }
    }

def parse_mcq_answer(tester: str, mcq_answer: str):
    answer = re.search(r"Answer: ([A-D])", mcq_answer)
    answer = answer.group(1) if answer else ""

    return {
        'mcq_answer': {
            'tester': tester,
            'answer': answer,
            'failed': True if answer != 'D' else False
        }
    }
