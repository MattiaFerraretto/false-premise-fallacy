from pydantic import BaseModel, HttpUrl, validator
from typing import List
from enum import Enum


class DifficultyLevel(str, Enum):
    EXTREMELY_EASY = "Extremely easy"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXTREMELY_HARD_HIGHLY_SPECIFIC = "Extremely hard, Highly specific"


DIFFICULTY_MAPPING = {
    0: DifficultyLevel.EXTREMELY_EASY,
    1: DifficultyLevel.EASY,
    2: DifficultyLevel.MEDIUM,
    3: DifficultyLevel.HARD,
    4: DifficultyLevel.EXTREMELY_HARD_HIGHLY_SPECIFIC
}

class Langs(str, Enum):
    EN = 'en'
    IT = 'it'

class GenConfig(BaseModel):
    temperature: float
    top_p: float
    max_completion_tokens: int

class EndpointConf(BaseModel):
    base_url: HttpUrl
    api_key: str
    model: str
    gen_config: GenConfig

class EmbeddingsConf(BaseModel):
    model: str
    threshold: float
    faiss_dir: str
    save_every: int

class OuptutInfo(BaseModel):
    dir: str
    subdir: str = ""
    fname: str

class DatsetConf(BaseModel):
    path: str
    name: str
    splits: List[str] = ["math", "law", "economics", "medicice"]
    token: str | None = None


class TranslatorConfig(BaseModel):
    endpoint: EndpointConf
    dataset: DatsetConf
    batch_size : int
    output_info: OuptutInfo

class EvalConfig(BaseModel):
    endpoint: EndpointConf
    dataset: DatsetConf
    batch_size : int
    output_info: OuptutInfo

'''class Config(BaseModel):
    models: ModelsConf
    batch_size: int
    topic: str
    difficulty: DifficultyLevel
    max_exercises: int
    output_info: OuptutInfo

    @validator("difficulty", pre=True)
    def validate_difficulty(cls, value):
        if  isinstance(value, int):
            try:
                return DIFFICULTY_MAPPING[value]
            except KeyError as e:
                raise ValueError(f"Invalid difficulty integer: {e.args[0]}. Allowed values are {list(DIFFICULTY_MAPPING.keys())}")
        return value'''
