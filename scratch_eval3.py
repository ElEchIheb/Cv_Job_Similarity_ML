import os
os.environ["EMBEDDING_MODEL_ML"] = "all-MiniLM-L6-v2"
os.environ["EMBEDDING_MODEL_EN"] = "all-MiniLM-L6-v2"

import traceback
import time
from src.evaluation.evaluator import EvaluationSuite

print('Starting eval...')
try:
    EvaluationSuite().run_full_evaluation('data/datasets/cv_job_dataset.csv')
    print('Success!')
except Exception as e:
    print('Failed!')
    traceback.print_exc()
