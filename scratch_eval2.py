import traceback
import time
from src.evaluation.evaluator import EvaluationSuite
import pandas as pd
from src.models.tfidf_model import TFIDFMatcher
from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.fusion.hybrid_scorer import HybridMatcher

print('Starting debug eval...')

df = pd.read_csv('data/datasets/cv_job_dataset.csv')
print("Dataset loaded")
eval_suite = EvaluationSuite()
split = eval_suite.stratified_split(df)
print("Data split complete")

print("Fitting TFIDF...")
tfidf = TFIDFMatcher().fit_pairs(split.train["cv_text"].tolist(), split.train["job_text"].tolist())
print("TFIDF done")

print("Init Embedding...")
embedding = EmbeddingMatcher()
print("Init Skill...")
skill = SkillMatcher()
print("Init Hybrid...")
hybrid = HybridMatcher()

print("Optimizing hybrid weights...")
try:
    hybrid.optimize_weights(split.train, split.validation)
    print("Optimization done")
except Exception as e:
    print("Error in optimize_weights")
    traceback.print_exc()

print("Evaluating...")
try:
    eval_suite.run_full_evaluation('data/datasets/cv_job_dataset.csv')
    print("Done")
except Exception as e:
    print("Error in run_full_evaluation")
    traceback.print_exc()
