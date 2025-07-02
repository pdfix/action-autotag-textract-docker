import os
import subprocess
from pathlib import Path
from typing import Iterator

import pytest

IMAGE: str = "pdfix/autotag-textract:test"
EXAMPLES_DIR: Path = Path(__file__).parents[2] / "examples"


@pytest.fixture(scope="session")
def docker_image() -> Iterator[str]:
    print(f"\n🔧 Building Docker image {IMAGE} (this may take a moment)...")
    subprocess.run(
        ["docker", "build", "-t", IMAGE, "."], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True
    )

    yield IMAGE

    print(f"\n🧹 Removing Docker image {IMAGE}...")
    subprocess.run(["docker", "rmi", IMAGE], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False)


@pytest.fixture(scope="session")
def input_pdf() -> Path:
    return (EXAMPLES_DIR / "air_quality.pdf").resolve()


@pytest.fixture(scope="session")
def aws_env() -> dict:
    return {
        "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
    }


@pytest.fixture(scope="session")
def sdk_env() -> dict:
    return {
        "NAME": os.environ.get("PDFIX_SDK_NAME", ""),
        "KEY": os.environ.get("PDFIX_SDK_KEY", ""),
    }
