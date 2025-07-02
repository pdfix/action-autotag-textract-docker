import subprocess
from pathlib import Path

from tests.functional.helpers import compare_pdfs_binary


def test_tag_subcommand(docker_image: str, input_pdf: Path, aws_env: dict, sdk_env: dict, tmp_path: Path) -> None:
    output_file_name: str = "tagged.pdf"
    output_file: Path = tmp_path / output_file_name

    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{input_pdf.parent}:/data/examples",
        "-v",
        f"{tmp_path}:/data/output",
        "-w",
        "/data",
        docker_image,
        "tag",
        "--name",
        sdk_env["NAME"],
        "--key",
        sdk_env["KEY"],
        "--aws_id",
        aws_env["AWS_ACCESS_KEY_ID"],
        "--aws_secret",
        aws_env["AWS_SECRET_ACCESS_KEY"],
        "--aws_region",
        aws_env["AWS_REGION"],
        "-i",
        f"/data/examples/{input_pdf.name}",
        "-o",
        f"/data/output/{output_file_name}",
    ]

    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, check=False, capture_output=True, text=True)

    expected_output_file: Path = Path(__file__).parent / "expected" / "air_quality-tagged.pdf"

    assert result.returncode == 0, f"❌ Process failed: {result.stderr}"
    assert output_file.exists(), "❌ Tagged output PDF not found."
    assert compare_pdfs_binary(output_file, expected_output_file), "❌ PDF was not tagged as expected."


# TODO - add test that compares free SDK version output
