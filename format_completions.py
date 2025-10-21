import json
import sys
from pathlib import Path


def format_completions_for_cweval(
    inference_file: str,
    output_base: str,
    n: int
):
    """
    Format eval-cli completions into CWEval's expected directory structure.

    inference-file format (JSONL):
    {
        "task_id": "cwe_022_0_c",
        "prompt": "...",
        "completion": ["code1", "code2", ...] or "code",
        "language": "c",
        "task_file": "core/c/cwe_022_0_c_task.c"
    }

    CWEval expected format (directory structure):
    generated_0/core/c/cwe_022_0_c_raw.c
    generated_1/core/c/cwe_022_0_c_raw.c
    ...
    generated_{n-1}/core/c/cwe_022_0_c_raw.c
    """
    tasks = {}
    with open(inference_file, 'r') as f:
        for line in f:
            result = json.loads(line)
            task_id = result['task_id']

            completion_data = result['completion']
            if isinstance(completion_data, str):
                completions_list = [completion_data]
            else:
                completions_list = completion_data

            if task_id not in tasks:
                tasks[task_id] = {
                    'completions': completions_list,
                    'task_file': result['task_file']
                }

    for idx in range(n):
        gen_dir = Path(output_base) / f"generated_{idx}"

        for task_id, task_data in tasks.items():
            completions_list = task_data['completions']

            if idx >= len(completions_list):
                code = completions_list[-1]
            else:
                code = completions_list[idx]

            task_file = task_data['task_file']
            raw_file = task_file.replace("_task.", "_raw.")

            output_file = gen_dir / raw_file
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w') as f:
                f.write(code)

    print(f"Formatted {len(tasks)} tasks x {n} samples to {output_base}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python format_completions.py <inference_file> <output_base> <n>")
        print()
        print("Arguments:")
        print("  inference_file: Path to eval-cli output JSONL file")
        print("  output_base: Base directory to create generated_X folders in")
        print("  n: Number of samples per task")
        sys.exit(1)

    inference_file = sys.argv[1]
    output_base = sys.argv[2]
    n = int(sys.argv[3])

    format_completions_for_cweval(inference_file, output_base, n)


if __name__ == "__main__":
    main()
