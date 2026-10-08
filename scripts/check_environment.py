import platform
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    expected_venv = project_root / ".venv"

    print(f"Project root: {project_root}")
    print(f"Python version: {platform.python_version()}")
    print(f"Python executable: {sys.executable}")
    print(f"Operating system: {platform.system()}")

    using_project_venv = (
        Path(sys.prefix).resolve() == expected_venv.resolve()
    )

    if not using_project_venv:
        raise SystemExit(
            "ERROR: Run this script with the project's .venv Python."
        )

    required_dirs = [
        "app",
        "scripts",
        "tests",
        "data/raw",
        "data/processed",
        "evaluation/datasets",
        "evaluation/results",
    ]

    missing_dirs = [
        relative_path
        for relative_path in required_dirs
        if not (project_root / relative_path).is_dir()
    ]

    if missing_dirs:
        raise SystemExit(
            f"ERROR: Missing directories: {', '.join(missing_dirs)}"
        )

    print("OK: Project environment and directories are ready.")


if __name__ == "__main__":
    main()