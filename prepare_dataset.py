import os
import json
from pathlib import Path

BENCHMARK_DIR = Path("benchmark")
LANGS = ["c", "cpp", "go", "js", "py"]

BEGIN_PROMPT_ANCHOR = "BEGIN PROMPT"
BEGIN_SOLUTION_ANCHOR = "BEGIN SOLUTION"


def extract_prompt(task_file_path: str) -> str:
    """
    Extract code prompt from task file.

    CWEval has two formats:
    1. With BEGIN PROMPT (C/C++/Go, some Python):
       // BEGIN PROMPT
       // Function description
       // BEGIN SOLUTION

    2. Without BEGIN PROMPT (some Python):
       def function():
           '''Docstring'''
           # BEGIN SOLUTION

    - If BEGIN PROMPT exists: extract text between BEGIN PROMPT and BEGIN SOLUTION
    - If BEGIN PROMPT missing: extract text from start to BEGIN SOLUTION
    """
    with open(task_file_path, 'r') as f:
        content = f.read()

    for line in content.splitlines():
        if BEGIN_SOLUTION_ANCHOR in line:
            begin_solution_line = line
            break
    else:
        raise ValueError(f"No {BEGIN_SOLUTION_ANCHOR} found in {task_file_path}")

    prompt = (
        content.split(BEGIN_PROMPT_ANCHOR)[-1]
        .split(begin_solution_line)[0]
        .strip()
    )

    return prompt


def prepare_language_dataset(lang: str, output_dir: Path):
    """Prepare dataset for a single language."""
    tasks = []
    lang_dir = BENCHMARK_DIR / "core" / lang

    if not lang_dir.exists():
        print(f"Warning: {lang_dir} does not exist, skipping")
        return

    for task_file in sorted(lang_dir.glob(f"*_task.{lang}")):
        task_id = task_file.stem.replace("_task", "")
        prompt = extract_prompt(str(task_file))

        tasks.append({
            "task_id": task_id,
            "prompt": prompt,
            "language": lang,
            "task_file": str(task_file.relative_to(BENCHMARK_DIR)),
        })

    output_file = output_dir / f"tasks_{lang}.jsonl"
    with open(output_file, 'w') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')

    print(f"Created {output_file} with {len(tasks)} tasks")


def main(output_dir: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for lang in LANGS:
        prepare_language_dataset(lang, output_path)

    print(f"Dataset preparation complete: {output_dir}")


if __name__ == "__main__":
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "data/prepared"
    main(output_dir)
