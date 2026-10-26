@echo off
set PYTHONPATH=src
python -m coverage run --source=src --branch -m pytest
python -m coverage report -m
