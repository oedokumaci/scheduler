import pandas as pd

from scheduler.config import YAML_CONFIG
from scheduler.path import INPUTS_DIR

df_exams = pd.read_excel(INPUTS_DIR / YAML_CONFIG.exams_file)
