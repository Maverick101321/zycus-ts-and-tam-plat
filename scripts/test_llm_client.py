"""Manual test script for LLM client integration."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.llm_client import get_llm_client


def main():
    print("Initializing LLM client...")
    client = get_llm_client()
    print(f"Client type: {type(client).__name__}")
    print("Sending test generation request: 'Say OK if you can read this.'")
    try:
        response = client.generate("Say OK if you can read this.")
        print("\n--- LLM Response ---")
        print(response)
        print("--------------------")
    except Exception as e:
        print(f"\nError occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
