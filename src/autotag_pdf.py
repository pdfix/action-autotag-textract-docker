import tempfile
from typing import BinaryIO, cast

import cv2
from pdfixsdk import (
    GetPdfix,
    PdePageMap,
    Pdfix,
    PdfPage,
    PdfPageView,
    PdfTagsParams,
    PdsStructElement,
    kRotate0,
    kSaveFull,
)
from tqdm import tqdm

from exceptions import PdfixException
from page_renderer import render_page
from textract_model import textract_add_elements, textract_model
from utils_sdk import authorize_sdk


def autotag_pdf(input: str, output: str, license_name: str, license_key: str, zoom: float) -> None:
    """
    Automatically tags a PDF document by analyzing its structure and applying tags to each page.

    Args:
        input (str): Path to the input PDF file.
        output (str): Path to save the output tagged PDF file.
        name (str): PDFix License Name.
        key (str): PDFix License Key.
        zoom (float): Render at zoom level.
    """
    pdfix = GetPdfix()
    if pdfix is None:
        raise Exception("Pdfix Initialization failed")

    # Authorize PDFix SDK
    authorize_sdk(pdfix, license_name, license_key)

    # Open the document
    doc = pdfix.OpenDoc(input, "")
    if doc is None:
        raise PdfixException(pdfix, "Unable to open PDF")

    # Remove old structure and prepare an empty structure tree
    doc.RemoveTags()
    doc.RemoveStructTree()
    struct_tree = doc.CreateStructTree()
    doc_struct_elem = struct_tree.GetStructElementFromObject(struct_tree.GetObject())
    if doc_struct_elem is None:
        raise PdfixException(pdfix, "Unable to acquire document structured element")

    num_pages = doc.GetNumPages()

    # Process each page
    for i in tqdm(range(0, num_pages), desc="Processing pages"):
        # Acquire the page
        page: PdfPage = doc.AcquirePage(i)
        if page is None:
            raise PdfixException(pdfix, "Unable to acquire the page")

        try:
            autotag_page(pdfix, page, doc_struct_elem, zoom)  # Removed unnecessary pdfix argument
        except Exception:
            raise
        finally:
            page.Release()

    # Save the processed document
    if not doc.Save(output, kSaveFull):
        raise PdfixException(pdfix, "Unable to save PDF")


def autotag_page(pdfix: Pdfix, page: PdfPage, doc_struct_elem: PdsStructElement, zoom: float) -> None:
    """
    Automatically tags a PDF page by analyzing its layout and mapping the detected elements
    to the document structure.

    Args:
        pdfix (Pdfix): Pdfix SDK.
        page (PdfPage): The PDF page to process.
        doc_struct_elem (PdsStructElement): The root structure element where tags will be added.
        zoom (float): Render at zoom level.
    """
    # Define zoom level and rotation for rendering the page
    page_view: PdfPageView = page.AcquirePageView(zoom, kRotate0)
    if page_view is None:
        raise PdfixException(pdfix, "Unable to acquire page view")

    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
            # Render the page as an image
            render_page(pdfix, page, page_view, cast(BinaryIO, temp_file))
            img_name = temp_file.name

            # Store image for saving results
            image = cv2.imread(img_name)

            # Run layout analysis
            result = textract_model(img_name)

        # Acquire the page map to store recognized elements
        page_map: PdePageMap = page.AcquirePageMap()
        if page_map is None:
            raise PdfixException(pdfix, "Unable to acquire page map")

        try:
            # Add detected elements to the page map based on the analysis result
            textract_add_elements(page_map, page_view, result, image)

            # Debugging: Save the rendered image for inspection
            cv2.imwrite("tmp_output.jpg", image)

            # Generate structured elements from the page map
            if not page_map.CreateElements():
                raise PdfixException(pdfix, "Failed to generate structured element")

            # Create a new structural element for the page
            page_element = doc_struct_elem.AddNewChild("NonStruct", doc_struct_elem.GetNumChildren())

            # Assign recognized elements as tags to the structure element
            if not page_map.AddTags(page_element, False, PdfTagsParams()):
                raise PdfixException(pdfix, "Failed to tags document")
        except Exception:
            raise
        finally:
            page_map.Release()
    except Exception:
        raise
    finally:
        page_view.Release()
