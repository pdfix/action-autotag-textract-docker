import cv2
from pdfixsdk import (
    GetPdfix,
    PdfPage,
    PdfTagsParams,
    PdsStructElement,
    kRotate0,
    kSaveFull,
)
from tqdm import tqdm

from render_page import render_page
from textract_model import textract_add_elements, textract_model


def autotag_page(page: PdfPage, doc_struct_elem: PdsStructElement) -> None:
    """
    Automatically tags a PDF page by analyzing its layout and mapping the detected elements
    to the document structure.

    Args:
        page (PdfPage): The PDF page to process.
        doc_struct_elem (PdsStructElement): The root structure element where tags will be added.
    """
    pdfix = GetPdfix()

    # Define zoom level and rotation for rendering the page
    zoom = 2.0
    rotate = kRotate0
    page_view = page.AcquirePageView(zoom, rotate)

    try:
        # Render the page as an image
        img_name = render_page(page, page_view)

        # Store image for saving results
        image = cv2.imread(img_name)

        # Run layout analysis
        result = textract_model(img_name)

        # Acquire the page map to store recognized elements
        page_map = page.AcquirePageMap()

        try:
            # Add detected elements to the page map based on the analysis result
            textract_add_elements(page_map, page_view, result, image)

            # Debugging: Save the rendered image for inspection
            cv2.imwrite("tmp_output.jpg", image)

            # Generate structured elements from the page map
            if not page_map.CreateElements():
                raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

            # Create a new structural element for the page
            page_element = doc_struct_elem.AddNewChild("NonStruct", doc_struct_elem.GetNumChildren())

            # Assign recognized elements as tags to the structure element
            if not page_map.AddTags(page_element, False, PdfTagsParams()):
                raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")
        except Exception:
            raise
        finally:
            page_map.Release()
    except Exception:
        raise
    finally:
        page_view.Release()


def autotag_pdf(input: str, output: str, license_name: str, license_key: str) -> None:
    """
    Automatically tags a PDF document by analyzing its structure and applying tags to each page.

    Args:
        input (str): Path to the input PDF file.
        output (str): Path to save the output tagged PDF file.
        name (str): PDFix License Name
        key (str): PDFix License Key
    """
    pdfix = GetPdfix()
    if pdfix is None:
        raise Exception("Pdfix Initialization failed")

    # Authorize PDFix SDK
    if license_name and license_key:
        if not pdfix.GetAccountAuthorization().Authorize(license_name, license_key):
            raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")
    elif license_key:
        if not pdfix.GetStandarsAuthorization().Activate(license_key):
            raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")
    else:
        print("No license name or key provided. Using PDFix SDK trial")

    # Open the document
    doc = pdfix.OpenDoc(input, "")
    if doc is None:
        raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

    # Remove old structure and prepare an empty structure tree
    doc.RemoveTags()
    doc.RemoveStructTree()
    struct_tree = doc.CreateStructTree()
    doc_struct_elem = struct_tree.GetStructElementFromObject(struct_tree.GetObject())
    if doc_struct_elem is None:
        raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

    num_pages = doc.GetNumPages()

    # Process each page
    for i in tqdm(range(0, num_pages), desc="Processing pages"):
        # Acquire the page
        page = doc.AcquirePage(i)
        if page is None:
            raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

        try:
            autotag_page(page, doc_struct_elem)  # Removed unnecessary pdfix argument
        except Exception as e:
            raise e
        finally:
            page.Release()

    # Save the processed document
    if not doc.Save(output, kSaveFull):
        raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")
