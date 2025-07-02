import json
import shutil
from pathlib import Path


def compare_pdfs_binary(pdf1: Path, pdf2: Path) -> bool:
    output_folder = Path(__file__).parents[2] / "output"
    first_pdf = output_folder / f"compare-{pdf1.name}"
    shutil.copy(pdf1, first_pdf)
    second_pdf = output_folder / f"compare-{pdf2.name}"
    shutil.copy(pdf2, second_pdf)
    return pdf1.read_bytes() == pdf2.read_bytes()


def compare_json_files(file1: Path, file2: Path) -> bool:
    with file1.open() as f1, file2.open() as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
    return data1 == data2
