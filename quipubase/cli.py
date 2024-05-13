import os
import subprocess
import sys

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["EMBEDDINGS_URL"] = "https://qembeddings-ih27b7zwaa-tl.a.run.app/embeddings"

PYTHON_EXE = sys.executable
HOST = "0.0.0.0"
PORT = "5454"
ENTRYPOINT = "main:app"


def main():
    """Run the Quipubase server."""
    print("Building Quipubase...")
    subprocess.run([PYTHON_EXE, "setup.py", "build-ext", "--inplace"], check=True)
    print("Quipubase build successful!")
    subprocess.run(
        [PYTHON_EXE, "-m", "uvicorn", ENTRYPOINT, "host", HOST, "port", PORT],
        check=True,
    )
    print(f"Quipubase is running on http://{HOST}:{PORT}/")


if __name__ == "__main__":
    main()
