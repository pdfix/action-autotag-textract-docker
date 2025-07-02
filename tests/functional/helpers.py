import json
import tempfile
from pathlib import Path

from pdfixsdk import GetPdfix, PdfDoc, Pdfix, PdfJsonConversion, PdfJsonParams, kJsonExportStructTree


def compare_json_files(file1: Path, file2: Path) -> bool:
    with file1.open() as f1, file2.open() as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
    return data1 == data2


def compare_tagged_pdfs(pdf1: Path, pdf2: Path) -> bool:
    pdfix: Pdfix = GetPdfix()
    try:
        with (
            tempfile.NamedTemporaryFile(suffix=".json") as temp_file_1,
            tempfile.NamedTemporaryFile(suffix=".json") as temp_file_2,
        ):
            if not convert_pdf_to_json(pdfix, pdf1, temp_file_1.name):
                return False
            if not convert_pdf_to_json(pdfix, pdf2, temp_file_2.name):
                return False
            return compare_json_files(Path(temp_file_1.name), Path(temp_file_2.name))
    finally:
        pdfix.Destroy()


def convert_pdf_to_json(pdfix: Pdfix, pdf_path: Path, temp_file_path: str) -> bool:
    doc: PdfDoc = pdfix.OpenDoc(str(pdf_path), "")
    if doc is None:
        return False
    try:
        conv: PdfJsonConversion = doc.CreateJsonConversion()
        if conv is None:
            return False
        try:
            conv_params: PdfJsonParams = PdfJsonParams()
            conv_params.flags = kJsonExportStructTree
            if not conv.SetParams(conv_params):
                return False
            if not conv.Save(temp_file_path):
                return False
        finally:
            conv.Destroy()
    finally:
        doc.Close()

    return True
