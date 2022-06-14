import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT_PATH, "data")
CASE_BASE_FILE = os.path.join(DATA_PATH, "case_base.xml")
CASE_LIBRARY_FILE = os.path.join(DATA_PATH, "case_library.xml")
USER_THRESHOLD = 0.85
USER_SCORE_THRESHOLD = 0.85
