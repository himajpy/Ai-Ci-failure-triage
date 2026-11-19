
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from triage_agent.git_context import get_git_context


# Our known-good baseline
BASE_COMMIT = "4a53a72"

report = get_git_context(BASE_COMMIT)

print(json.dumps(report, indent=4))
