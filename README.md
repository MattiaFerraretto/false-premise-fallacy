# FPFEval

This repository contains all the necessary scripts for generating False Premise Fallacy (FPF) exercises and evaluating Large Language Models (LLMs) against the False Premise Fallacy as detailed in the technical report located in the `_report` folder of this repository.

## Getting Started

To start generating exercises or run the benchmark, copy and paste these commands in your terminal:

```
git clone https://github.com/MattiaFerraretto/false-premise-fallacy.git
cd false-premise-fallacy
```

Then create a Python virtual environment and install all the necessary dependencies using the conda command:

```
conda create --name <env> --file requirements.txt
```

## Usage

To generate FPF exercises, run the command:

```
python src/generate.py --config_path ./conf-examples/exercise-gen-conf-example.yaml
```

To deduplicate exercises, run the command:

```
python src/deduplicate.py --config_path ./conf-examples/dedup-conf-example.yaml
```

To run the MCQ analyzer:

```
streamlit run src/mcq_analyzer/home.py
```

To run the benchmark, use the following command:

```
python src/evaluate.py --config_path ./conf-examples/eval-conf-example.yaml
```

## Maestrale

Our model Maestrale can be found [here](https://huggingface.co/mii-llm/maestrale-chat-v0.4-beta).

## Benchmark Dataset

The dataset used for reporting results in the technical report can be found [here](https://huggingface.co/datasets/mferraretto/fpfeval).

## Authors

[Mattia Ferraretto](https://github.com/MattiaFerraretto) and [Edoardo Federici](https://github.com/banda-larga)
