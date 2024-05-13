import os
import subprocess
import sys

import click

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["EMBEDDINGS_URL"] = "https://qembeddings-ih27b7zwaa-tl.a.run.app/embeddings"

PYTHON_EXE = sys.executable
HOST = "0.0.0.0"
PORT = "5454"
ENTRYPOINT = "main:app"


@click.group()
def main():
    """Quipubase CLI."""
    pass


@main.command()
@click.option("--host", default=HOST, help="The host to run the server on.")
@click.option("--port", default=PORT, help="The port to run the server on.")
def run(host: str, port: str):
    """Run the Quipubase server."""
    print("Building Quipubase...")
    subprocess.run([PYTHON_EXE, "setup.py", "build-ext", "--inplace"], check=True)
    print("Quipubase build successful!")
    subprocess.run(
        [PYTHON_EXE, "-m", "uvicorn", ENTRYPOINT, "host", host, "port", port],
        check=True,
    )
    print(f"Quipubase is running on http://{host}:{port}/")


@main.command()
def test():
    """Run the Quipubase tests."""
    subprocess.run([PYTHON_EXE, "-m", "pytest", "tests"], check=True)
