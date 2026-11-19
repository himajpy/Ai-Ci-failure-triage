
import sys
from pathlib import Path
import json

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from triage_agent.log_parser import parse_log


report = parse_log("examples/failure.log")

print(json.dumps(report, indent=4))

