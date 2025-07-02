import subprocess
from pathlib import Path

from tests.functional.helpers import compare_json_files


def test_template_subcommand(docker_image: str, input_pdf: Path, aws_env: dict, tmp_path: Path) -> None:
    output_file_name: str = "template.json"
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
        "template",
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

    expected_output_file: Path = Path(__file__).parent / "expected" / "air_quality-template.json"

    assert result.returncode == 0, f"❌ Process failed: {result.stderr}"
    assert output_file.exists(), "❌ Layout template not found."
    assert compare_json_files(output_file, expected_output_file), "❌ Layout template was not created as expected."
