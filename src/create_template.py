import json
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, cast

from pdfixsdk import (
    GetPdfix,
    PdfDoc,
    Pdfix,
    PdfPage,
    PdfPageView,
    kRotate0,
)
from textractor.entities.document import Document
from tqdm import tqdm

from ai import process_image
from constants import (
    PERCENT_AI,
    PERCENT_RENDER,
    PERCENT_TEMPLATE,
    PROGRESS_FIRST_STEP,
    PROGRESS_FOURTH_STEP,
    PROGRESS_SECOND_STEP,
    PROGRESS_THIRD_STEP,
)
from convertor import ConvertDocumentToDictionary
from exceptions import PdfixFailedToCreateTemplateException, PdfixFailedToOpenException, PdfixInitializeException
from page_renderer import render_page
from template_json import TemplateJsonCreator
from utils_sdk import authorize_sdk


class CreateTemplateJsonUsingAmazonTextract:
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        license_name: Optional[str],
        license_key: Optional[str],
        input_path: str,
        output_path: str,
        zoom: float,
    ) -> None:
        """
        Initialize class for tagging pdf(s).

        Args:
            aws_access_key_id (str): AWS Access Key ID.
            aws_secret_access_key (str): AWS Secret Access Key.
            aws_region (str): AWS Region.
            license_name (Optional[str]): Pdfix sdk license name (e-mail).
            license_key (Optional[str]): Pdfix sdk license key.
            input_path (str): Path to PDF document.
            output_path (str): Path where template JSON should be saved.
            zoom (float): Zoom level for rendering the page.
        """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.license_name = license_name
        self.license_key = license_key
        self.input_path_str = input_path
        self.output_path_str = output_path
        self.zoom = zoom

    def process_file(self) -> None:
        """
        Automatically creates template json.
        """
        total_progress_count: int = (
            PROGRESS_FIRST_STEP + PROGRESS_SECOND_STEP + PROGRESS_THIRD_STEP + PROGRESS_FOURTH_STEP
        )
        with tqdm(total=total_progress_count) as progress_bar:
            progress_bar.set_description("Initializing")

            id: str = Path(self.input_path_str).stem

            pdfix: Optional[Pdfix] = GetPdfix()
            if pdfix is None:
                raise PdfixInitializeException()

            # Try to authorize PDFix SDK
            authorize_sdk(pdfix, self.license_name, self.license_key)

            # Open the document
            doc: Optional[PdfDoc] = pdfix.OpenDoc(self.input_path_str, "")
            if doc is None:
                raise PdfixFailedToOpenException(pdfix, self.input_path_str)

            # Process images of each page
            number_of_pages: int = doc.GetNumPages()
            template_json_creator: TemplateJsonCreator = TemplateJsonCreator()

            progress_bar.update(PROGRESS_FIRST_STEP)
            progress_bar.set_description("Processing pages")
            step_count: float = float(PROGRESS_SECOND_STEP) / number_of_pages

            for page_index in range(number_of_pages):
                # Acquire the page
                page: Optional[PdfPage] = doc.AcquirePage(page_index)
                if page is None:
                    raise PdfixFailedToCreateTemplateException(pdfix, "Unable to acquire the page")

                try:
                    self._process_pdf_file_page(
                        pdfix, id, page, page_index, template_json_creator, progress_bar, step_count
                    )
                except Exception:
                    raise
                finally:
                    page.Release()

            progress_bar.n = PROGRESS_FIRST_STEP + PROGRESS_SECOND_STEP
            progress_bar.set_description("Saving template")
            progress_bar.refresh()

            # Create template for whole document
            template_json_dict: dict = template_json_creator.create_json_dict_for_document(self.zoom)
            output_data: dict = template_json_dict

            # Save template json
            with open(self.output_path_str, "w") as file:
                file.write(json.dumps(output_data, indent=2))

            progress_bar.n = total_progress_count
            progress_bar.set_description("Done")
            progress_bar.refresh()

    def _process_pdf_file_page(
        self,
        pdfix: Pdfix,
        id: str,
        page: PdfPage,
        page_index: int,
        templateJsonCreator: TemplateJsonCreator,
        progress_bar: tqdm,
        total_units_for_page_processing: float,
    ) -> None:
        """
        Create template json for current PDF document page.

        Args:
            pdfix (Pdfix): Pdfix SDK.
            id (string): PDF document name.
            page (PdfPage): The PDF document page to process.
            page_index (int): PDF file page index.
            templateJsonCreator (TemplateJsonCreator): Template JSON creator.
            progress_bar (tqdm): Progress bar.
            total_units_for_page_processing (float): How many units progress bar needs to update.
        """
        page_number: int = page_index + 1

        render_step_units: float = total_units_for_page_processing * PERCENT_RENDER
        ai_step_units: float = total_units_for_page_processing * PERCENT_AI
        template_step_units: float = total_units_for_page_processing * PERCENT_TEMPLATE

        # Define rotation for rendering the page
        page_view: Optional[PdfPageView] = page.AcquirePageView(self.zoom, kRotate0)
        if page_view is None:
            raise PdfixFailedToCreateTemplateException(pdfix, "Unable to acquire page view")

        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
                # Render the page as an image
                render_page(pdfix, page, page_view, cast(BinaryIO, temp_file))
                progress_bar.update(render_step_units)
                temp_image_path: str = temp_file.name

                # Run layout analysis
                result: Document = process_image(
                    self.aws_access_key_id, self.aws_secret_access_key, self.aws_region, temp_image_path
                )
                progress_bar.update(ai_step_units)

                # Custom conversion to dict and saving to json file
                convertor: ConvertDocumentToDictionary = ConvertDocumentToDictionary(result, id, page_number)
                convertor.save_as_json()

                # Process the results
                templateJsonCreator.process_page(result, page_number, page_view)
                progress_bar.update(template_step_units)
        except Exception:
            raise
        finally:
            # Release resources
            page_view.Release()
