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


def combine_language_datasets(output_dir: Path, languages: list[str]) -> Path:
    """
    Combine multiple language datasets into a single JSONL file.

    Args:
        output_dir: Directory containing individual language JSONL files
        languages: List of language codes to combine (e.g., ['c', 'py', 'go'])

    Returns:
        Path to the combined JSONL file
    """
    combined_file = output_dir / "tasks_combined.jsonl"

    # Remove existing combined file
    if combined_file.exists():
        combined_file.unlink()

    total_tasks = 0
    with open(combined_file, 'w') as outfile:
        for lang in languages:
            lang_file = output_dir / f"tasks_{lang}.jsonl"

            if not lang_file.exists():
                print(f"Warning: {lang_file} does not exist, skipping language '{lang}'")
                continue

            lang_task_count = 0
            with open(lang_file, 'r') as infile:
                for line in infile:
                    outfile.write(line)
                    lang_task_count += 1

            print(f"Added {lang_task_count} tasks for language: {lang}")
            total_tasks += lang_task_count

    print(f"Combined {total_tasks} total tasks from {len(languages)} language(s) into {combined_file}")
    return combined_file


def main(output_dir: str, languages: str = None):
    """
    Prepare CWEval datasets.

    Args:
        output_dir: Directory to write output files
        languages: Comma-separated list of languages (e.g., "c,py,go") or None for all
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Prepare individual language datasets for all languages
    for lang in LANGS:
        prepare_language_dataset(lang, output_path)

    # If specific languages requested, combine them
    if languages:
        lang_list = [lang.strip() for lang in languages.split(',')]
        combined_file = combine_language_datasets(output_path, lang_list)
        print(f"Dataset preparation complete: {output_dir}")
        print(f"Combined dataset: {combined_file}")
    else:
        print(f"Dataset preparation complete: {output_dir}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prepare_dataset.py <output_dir> [languages]")
        print("  output_dir: Directory to write output files")
        print("  languages: Optional comma-separated list (e.g., 'c,py,go'). If not provided, prepares all languages without combining.")
        sys.exit(1)

    output_dir = sys.argv[1]
    languages = sys.argv[2] if len(sys.argv) > 2 else None

    main(output_dir, languages)
