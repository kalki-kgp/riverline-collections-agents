from __future__ import annotations

from app.eval.learning_loop import run_learning_loop
from app.eval.meta_eval import run_meta_evaluation


def main() -> None:
    learning = run_learning_loop()
    meta = run_meta_evaluation()
    print("learning_loop:", learning)
    print("meta_evaluation:", meta)


if __name__ == "__main__":
    main()
