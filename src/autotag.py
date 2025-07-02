import json
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Optional, cast

import cv2
from pdfixsdk import (
    GetPdfix,
    PdfDoc,
    PdfDocTemplate,
    Pdfix,
    PdfPage,
    PdfPageView,
    PdfTagsParams,
    kDataFormatJson,
    kRotate0,
    kSaveFull,
)
from PIL import Image
from textractor.entities.document import Document
from tqdm import tqdm

from ai import process_image
from convertor import ConvertDocumentToDictionary
from exceptions import PdfixException
from page_renderer import render_page
from template_json import TemplateJsonCreator
from utils_sdk import authorize_sdk, json_to_raw_data
from visualisation import VisualizeAmazonResults


class AutotagUsingAmazonTextractRecognition:
    """
    Class that takes care of Autotagging provided PDF document using AWS Textract Engine.
    """

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
        Initialize class for tagging pdf.

        Args:
            aws_access_key_id (str): AWS Access Key ID.
            aws_secret_access_key (str): AWS Secret Access Key.
            aws_region (str): AWS Region.
            license_name (Optional[str]): Pdfix SDK license name (e-mail).
            license_key (Optional[str]): Pdfix SDK license key.
            input_path (str): Path to PDF document.
            output_path (str): Path where tagged PDF should be saved.
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
        Automatically tags a PDF document.
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

        # Process each page
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

        # Save template to file
        template_path: Path = Path(__file__).parent.joinpath("../output/{id}-template_json.json").resolve()
        with open(template_path, "w") as file:
            file.write(json.dumps(template_json_dict, indent=2))

        # Autotag document
        self._autotag_using_template(doc, template_json_dict, pdfix)

        # Save the processed document
        if not doc.Save(self.output_path_str, kSaveFull):
            raise PdfixException(pdfix, "Unable to save PDF")

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

        # Define zoom level and rotation for rendering the page
        page_view: PdfPageView = page.AcquirePageView(self.zoom, kRotate0)
        if page_view is None:
            raise PdfixException(pdfix, "Unable to acquire page view")

        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
                # Render the page as an image
                render_page(pdfix, page, page_view, cast(BinaryIO, temp_file))
                temp_image_path = temp_file.name

                # Run layout analysis
                result = process_image(
                    self.aws_access_key_id, self.aws_secret_access_key, self.aws_region, temp_image_path
                )

                # Store image for saving results
                image = cv2.imread(temp_image_path)

                # Custom visualization of the results
                custom_visualizer = VisualizeAmazonResults(result, image, id, page_number)
                custom_visualizer.visualize(page_view)

                # Amazon built-in visualization
                self._visualize_page(result, id, page_number)

                # Custom conversion to dict and saving to json file
                convertor = ConvertDocumentToDictionary(result, id, page_number)
                convertor.save_as_json()

                # Process the results
                templateJsonCreator.process_page(result, page_number, page_view)
        except Exception:
            raise
        finally:
            page_view.Release()

    def _visualize_page(
        self,
        document: Document,
        id: str,
        page_number: int,
    ) -> None:
        """
        Visualize the results of the layout analysis on the PDF page.

        Args:
            document (Document): The result of the layout analysis.
            id (str): PDF document name.
            page_number (int): PDF file page number.
        """
        images: Any = document.layouts.visualize(True, False, True, 0.5)

        if isinstance(images, Image.Image):
            image_path: Path = (
                Path(__file__).parent.joinpath(f"../output/{id}-{page_number}-aws_result_0.jpg").resolve()
            )
            images.save(image_path)
        elif isinstance(images, list) and len(images) > 0:
            for index, image in enumerate(images):
                if isinstance(image, Image.Image):
                    image_path = (
                        Path(__file__).parent.joinpath(f"../output/{id}-{page_number}-aws_result_{index}.jpg").resolve()
                    )
                    image.save(image_path)
                else:
                    print(f"Expected Image and instead got: {type(images)}")

    def _autotag_using_template(self, doc: PdfDoc, template_json_dict: dict, pdfix: Pdfix) -> None:
        """
        Autotag opened document using template and remove previous tags and structures.

        Args:
            doc (PdfDoc): Opened document to tag.
            template_json_dict (dict): Template for tagging.
            pdfix (Pdfix): Pdfix SDK.
        """
        # Remove old structure and prepare an empty structure tree
        if not doc.RemoveTags():
            raise PdfixException(pdfix, "Failed to remove tags from doc")
        if not doc.RemoveStructTree():
            raise PdfixException(pdfix, "Failed to remove structure from doc")

        # Convert template json to memory stream
        memory_stream = pdfix.CreateMemStream()
        if memory_stream is None:
            raise PdfixException(pdfix, "Unable to create memory stream")

        try:
            raw_data, raw_data_size = json_to_raw_data(template_json_dict)
            if not memory_stream.Write(0, raw_data, raw_data_size):
                raise PdfixException(pdfix, "Unable to write template data into memory")

            doc_template: PdfDocTemplate = doc.GetTemplate()
            if not doc_template.LoadFromStream(memory_stream, kDataFormatJson):
                raise PdfixException(pdfix, "Unable save template into document")
        except Exception:
            raise
        finally:
            memory_stream.Destroy()

        # Autotag document
        tagsParams = PdfTagsParams()
        if not doc.AddTags(tagsParams):
            raise PdfixException(pdfix, "Failed to tag document")
