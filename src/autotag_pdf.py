import tempfile

import cv2
from pdfixsdk import (
    GetPdfix,
    PdfImageParams,
    PdfPage,
    PdfPageRenderParams,
    PdfPageView,
    PdfTagsParams,
    PdsStructElement,
    kImageDIBFormatArgb,
    kImageFormatJpg,
    kPsTruncate,
    kRotate0,
    kSaveFull,
)
from tqdm import tqdm

from textract_model import textract_add_elements, textract_model


def render_page(pdf_page: PdfPage, page_view: PdfPageView) -> str:
    """
    Renders the PDF page into image

    Args:
        pdf_page (PdfPage): The page to render.
        page_view (PdfPageView): The view of the PDF page used for coordinate conversion.

    Returns:
        The path to the rendered image temporary file.
    """
    # Initialize PDFix instance
    pdfix = GetPdfix()

    # Get the dimensions of the page view (device width and height)
    page_width = page_view.GetDeviceWidth()
    page_height = page_view.GetDeviceHeight()

    # Create an image with the specified dimensions and ARGB format
    page_image = pdfix.CreateImage(page_width, page_height, kImageDIBFormatArgb)
    if page_image is None:
        raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

    # Set up rendering parameters
    render_params = PdfPageRenderParams()
    render_params.image = page_image
    render_params.matrix = page_view.GetDeviceMatrix()

    # Render the page content onto the image
    if not pdf_page.DrawContent(render_params):
        raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

    # Save the rendered image to a temporary file in JPG format
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        file_stream = pdfix.CreateFileStream(temp_file.name, kPsTruncate)

        # Set image parameters (format and quality)
        image_params = PdfImageParams()
        image_params.format = kImageFormatJpg
        image_params.quality = 100

        # Save the image to the file stream
        if not page_image.SaveToStream(file_stream, image_params):
            raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

        # Clean up resources
        file_stream.Destroy()
        page_image.Destroy()

        # Return the saved image
        return temp_file.name


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

    # Render the page as an image
    img_name = render_page(page, page_view)

    # Store image for saving results
    image = cv2.imread(img_name)

    # Run layout analysis
    result = textract_model(img_name)

    # Acquire the page map to store recognized elements
    page_map = page.AcquirePageMap()

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

    # Release resources
    page_map.Release()
    page_view.Release()


def autotag_pdf(args) -> None:
    """
    Automatically tags a PDF document by analyzing its structure and applying tags to each page.

    Args:
        args (): arguments passed by argparse
            input (str): Path to the input PDF file.
            output (str): Path to save the output tagged PDF file.
            name (str): PDFix License Name
            key (str): PDFix License Key
    """
    pdfix = GetPdfix()
    if pdfix is None:
        raise Exception("Pdfix Initialization failed")

    # pdfix authorization
    if hasattr(args, "key") and args.key:
        if hasattr(args, "name") and args.name:
            if not pdfix.GetAccountAuthorization().Authorize(args.name, args.key):
                raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")
        else:
            if not pdfix.GetStandardAuthorization().Activate(args.key):
                raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")

    # Open the document
    doc = pdfix.OpenDoc(args.input, "")
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

        page.Release()

    # Save the processed document
    if not doc.Save(args.output, kSaveFull):
        raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")
