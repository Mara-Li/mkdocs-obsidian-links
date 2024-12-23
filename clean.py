import shutil
from pathlib import Path


def clean_directories():
    paths_to_clean = ["dist", "*.egg-info", ".pytest_cache"]

    for path in paths_to_clean:
        absolute_path = Path(Path.cwd(), path)
        if Path(absolute_path).is_dir():
            print(f"Removing directory: {absolute_path}")
            shutil.rmtree(absolute_path, ignore_errors=True)
        elif Path(absolute_path).is_file():
            print(f"Removing file: {absolute_path}")
            Path.unlink(absolute_path)
        else:
            print(f"Path does not exist: {absolute_path}")


if __name__ == "__main__":
    clean_directories()
