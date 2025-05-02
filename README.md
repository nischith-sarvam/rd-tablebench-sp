# RD Table Bench Invocation + Grading Code

This repo contains the code for invoking each provider and grading the results.

Install poppler

## Quick Start
Download the dependencies and activate the environment
```
poetry install
poetry shell
```

Update input folder in `main.py` based on the provider you want to benchmark. The htmls generated using each provider are available under [data/providers](data/providers/)
```
python rd_tablebench/main.py
```