"""CLI entry point: python -m backbone_agent "<task>" """

import sys

from .loop import run_agent


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python -m backbone_agent "<task>"', file=sys.stderr)
        sys.exit(1)

    task = sys.argv[1]
    answer = run_agent(task)
    print("\n=== FINAL ANSWER ===")
    print(answer)


if __name__ == "__main__":
    main()
