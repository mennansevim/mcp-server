#!/usr/bin/env python3
"""
Local sanity test for AI provider selection and visibility.

Usage (host):
  OPENAI_API_KEY=... python3 scripts/test_ai_provider.py

Usage (docker):
  docker exec -it <container> python scripts/test_ai_provider.py
"""

import asyncio
import sys
from pathlib import Path
import yaml

# Ensure repo root is on sys.path so `import services` works when executed as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.ai_reviewer import AIReviewer


TEST_DIFF = """--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-print('x')
+print('y')
"""


async def main():
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    reviewer = AIReviewer(ai_config=cfg.get("ai", {}))
    result = await reviewer.review(
        diff=TEST_DIFF,
        files_changed=["a.py"],
        focus_areas=["security"],
    )

    print("ai_provider:", reviewer.last_provider_used)
    print("ai_model:", reviewer.last_model_used)
    print("score:", result.score)
    print("summary:", result.summary)


if __name__ == "__main__":
    asyncio.run(main())

