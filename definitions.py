import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT_PATH, "data")
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

CASE_BASE_FILE = os.path.join(DATA_PATH, "case_base.xml")
CASE_LIBRARY_FILE = os.path.join(DATA_PATH, "case_library.xml")

LOGS_PATH = os.path.join(ROOT_PATH, "logs")
if not os.path.exists(LOGS_PATH):
    os.makedirs(LOGS_PATH)

LOG_FILE = os.path.join(LOGS_PATH, "logfile.log")

USER_MANUAL_FILE = os.path.join(ROOT_PATH, "documentation", "User-Manual.pdf")
