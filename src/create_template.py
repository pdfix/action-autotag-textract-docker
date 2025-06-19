import json
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, cast

from pdfixsdk import (
    GetPdfix,
    Pdfix,
    PdfPage,
    PdfPageView,
    kRotate0,
)
from tqdm import tqdm

from ai import process_image
from convertor import ConvertDocumentToDictionary
from exceptions import PdfixException
from page_renderer import render_page
from template_json import TemplateJsonCreator
from utils_sdk import authorize_sdk


class CreateTemplateJsonUsingAmazonTextract:
    def __init__(
        self,
        license_name: Optional[str],
        license_key: Optional[str],
        input_path: str,
        output_path: str,
        zoom: float,
    ) -> None:
        """
        Initialize class for tagging pdf(s).

        Args:
            license_name (Optional[str]): Pdfix sdk license name (e-mail).
            license_key (Optional[str]): Pdfix sdk license key.
            input_path (str): Path to PDF document.
            output_path (str): Path where template JSON should be saved.
            zoom (float): Zoom level for rendering the page.
        """
        self.license_name = license_name
        self.license_key = license_key
        self.input_path_str = input_path
        self.output_path_str = output_path
        self.zoom = zoom

    def process_file(self) -> None:
        """
        Automatically creates template json.
        """
        id: str = Path(self.input_path_str).stem

        pdfix = GetPdfix()
        if pdfix is None:
            raise Exception("Pdfix Initialization failed")

        # Try to authorize PDFix SDK
        authorize_sdk(pdfix, self.license_name, self.license_key)

        # Open the document
        doc = pdfix.OpenDoc(self.input_path_str, "")
        if doc is None:
            raise PdfixException(pdfix, "Unable to open PDF")

        # Process images of each page
        num_pages = doc.GetNumPages()
        template_json_creator = TemplateJsonCreator()

        for page_index in tqdm(range(0, num_pages), desc="Processing pages"):
            # Acquire the page
            page: PdfPage = doc.AcquirePage(page_index)
            if page is None:
                raise PdfixException(pdfix, "Unable to acquire the page")

            try:
                self._process_pdf_file_page(pdfix, id, page, page_index, template_json_creator)
            except Exception:
                raise
            finally:
                page.Release()

        # Create template for whole document
        template_json_dict: dict = template_json_creator.create_json_dict_for_document(self.zoom)
        output_data: dict = template_json_dict

        # Save template json
        with open(self.output_path_str, "w") as file:
            file.write(json.dumps(output_data, indent=2))

    def _process_pdf_file_page(
        self,
        pdfix: Pdfix,
        id: str,
        page: PdfPage,
        page_index: int,
        templateJsonCreator: TemplateJsonCreator,
    ) -> None:
        """
        Create template json for current PDF document page.

        Args:
            pdfix (Pdfix): Pdfix SDK.
            id (string): PDF document name.
            page (PdfPage): The PDF document page to process.
            page_index (int): PDF file page index.
            templateJsonCreator (TemplateJsonCreator): Template JSON creator.
        """
        page_number = page_index + 1

        # Define rotation for rendering the page
        page_view: PdfPageView = page.AcquirePageView(self.zoom, kRotate0)
        if page_view is None:
            raise PdfixException(pdfix, "Unable to acquire page view")

        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
                # Render the page as an image
                render_page(pdfix, page, page_view, cast(BinaryIO, temp_file))
                temp_image_path = temp_file.name

                # Run layout analysis
                result = process_image(temp_image_path)

                # Custom conversion to dict and saving to json file
                convertor = ConvertDocumentToDictionary(result, id, page_number)
                convertor.save_as_json()

                # Process the results
                templateJsonCreator.process_page(result, page_number, page_view)
        except Exception:
            raise
        finally:
            # Release resources
            page_view.Release()
