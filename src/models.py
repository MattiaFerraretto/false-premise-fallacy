from pydantic import BaseModel, HttpUrl, validator
from typing import List
from enum import Enum

class GenConfig(BaseModel):
    temperature: float
    top_p: float
    frequency_penalty: float = .0
    presence_penalty: float = .0
    max_completion_tokens: int

class EndpointConf(BaseModel):
    base_url: HttpUrl
    api_key: str
    model: str
    gen_config: GenConfig

class EmbeddingsConf(BaseModel):
    model: str
    threshold: float
    batch_size: int

class OuptutInfo(BaseModel):
    dir: str
    subdir: str = ""
    fname: str

class DatasetConf(BaseModel):
    path: str
    name: str
    splits: List[str] = ["math", "law", "economics", "medicice"]
    token: str | None = None


class GenerationExerciseConfig(BaseModel):
    endpoint: EndpointConf
    topic: str
    num_exercises: int
    batch_size: int
    history_size: int
    output_info: OuptutInfo

class DeduplicatinConfig(BaseModel):
    embedder: EmbeddingsConf
    fpath: str
    output_info: OuptutInfo

class TranslatorConfig(BaseModel):
    endpoint: EndpointConf
    dataset: DatasetConf
    batch_size : int
    output_info: OuptutInfo

class EvalConfig(BaseModel):
    endpoint: EndpointConf
    dataset: DatasetConf
    batch_size : int
    output_info: OuptutInfo
