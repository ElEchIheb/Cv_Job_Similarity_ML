import traceback
import time
from src.evaluation.evaluator import EvaluationSuite

print('Starting eval...')
start = time.time()
try:
    EvaluationSuite().run_full_evaluation('data/datasets/cv_job_dataset.csv')
    print(f'Success! Finished in {time.time()-start:.2f}s')
except Exception as e:
    traceback.print_exc()
