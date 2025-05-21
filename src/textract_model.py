import cv2
from pdfixsdk import (
    PdeCell,
    PdeElement,
    PdePageMap,
    PdeTable,
    PdfDevRect,
    PdfPageView,
    kPdeCell,
    kPdeFooter,
    kPdeHeader,
    kPdeImage,
    kPdeList,
    kPdeTable,
    kPdeText,
    kTextH1,
)
from PIL import Image
from textractor import Textractor
from textractor.data.constants import (
    LAYOUT_FIGURE,
    LAYOUT_FOOTER,
    LAYOUT_HEADER,
    LAYOUT_LIST,
    LAYOUT_PAGE_NUMBER,
    LAYOUT_SECTION_HEADER,
    LAYOUT_TABLE,
    LAYOUT_TITLE,
    TextractFeatures,
)
from textractor.entities.document import Document
from textractor.entities.layout import Layout


def textract_model(image_path: str) -> Document:
    """
    Analyzes the document using Textract and returns the document object.

    Args:
        image_path (str): Path to the image file to be analyzed.

    Returns:
        The document object containing the analysis results.
    """
    extractor = Textractor(profile_name="default")
    image = Image.open(image_path)
    document = extractor.analyze_document(
        file_source=image,
        features=[TextractFeatures.TABLES, TextractFeatures.LAYOUT],
        save_image=True,
    )

    return document


def textract_add_elements(
    page_map: PdePageMap, page_view: PdfPageView, document: Document, image: cv2.typing.MatLike
) -> None:
    """
    Adds initial structural elements to the page map based on detected regions.

    Args:
        page_map (PdePageMap): The page map where elements will be added.
        page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
        document (): A document returned by textract.
        image (cv2.typing.MatLike): The image representation of the page for visualization.
    """
    page_w = page_view.GetDeviceWidth()
    page_h = page_view.GetDeviceHeight()

    for region in document.layouts:
        rect = PdfDevRect()
        rect.left = int(region.bbox.x * page_w - 2)
        rect.top = int(region.bbox.y * page_h - 2)
        rect.right = int((region.bbox.x + region.bbox.width) * page_w + 2)
        rect.bottom = int((region.bbox.y + region.bbox.height) * page_h + 2)
        bbox = page_view.RectToPage(rect)

        cv2.rectangle(image, (rect.left, rect.top), (rect.right, rect.bottom), (0, 255, 0), 2)

        element = page_map.CreateElement(convert_region_type_to_element_type(region.layout_type), None)
        element.SetBBox(bbox)

        region_type = region.layout_type
        if region_type == LAYOUT_TITLE:
            element.SetTextStyle(kTextH1)  # TODO maybe set as document title
        elif region_type == LAYOUT_SECTION_HEADER:
            element.SetTextStyle(kTextH1)
        elif region_type == LAYOUT_TABLE:
            update_table_cells(element, page_view, region, image)


def convert_region_type_to_element_type(region_type: str) -> int:
    """
    Converts a Textract region type to a PDFix element type.

    Args:
        region_type (str): The Textract region type.

    Returns:
        int: The corresponding PDFix element type.
    """
    if region_type == LAYOUT_FOOTER:
        return kPdeFooter
    elif region_type == LAYOUT_HEADER:
        return kPdeHeader
    elif region_type == LAYOUT_FIGURE:
        return kPdeImage
    elif region_type == LAYOUT_LIST:
        return kPdeList
    elif region_type == LAYOUT_PAGE_NUMBER:
        return kPdeFooter
    elif region_type == LAYOUT_TABLE:
        return kPdeTable

    # Default to text
    return kPdeText


def update_table_cells(
    pdf_element: PdeElement, page_view: PdfPageView, region: Layout, image: cv2.typing.MatLike
) -> None:
    """
    Updates the table element with detected cells

    Args:
        pdf_element (PdeElement): The table element to edit.
        page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
        region (Layout): The data containing the textract table region.
        image (cv2.typing.MatLike): The image representation of the page for visualization.
    """
    # Return early if no cells exist in the region
    layout_table = region.children[0]

    # Get the page map and create the table object
    page_map = pdf_element.GetPageMap()
    table = PdeTable(pdf_element.obj)

    table.SetNumCols(layout_table.column_count)
    table.SetNumRows(layout_table.row_count)

    page_w = page_view.GetDeviceWidth()
    page_h = page_view.GetDeviceHeight()

    # Loop through each cell's bounding box in the region
    for cell in layout_table.children:
        rect = PdfDevRect()
        rect.left = int(cell.bbox.x * page_w)
        rect.top = int(cell.bbox.y * page_h)
        rect.right = int((cell.bbox.x + cell.bbox.width) * page_w)
        rect.bottom = int((cell.bbox.y + cell.bbox.height) * page_h)
        bbox = page_view.RectToPage(rect)

        # Draw the cell rectangle on the image for visualization (optional step)
        cv2.rectangle(image, (rect.left, rect.top), (rect.right, rect.bottom), (255, 0, 0), 1)

        # Convert cell rectangle to page coordinates
        bbox = page_view.RectToPage(rect)

        # Create a new cell element and set its properties
        cell_element = PdeCell(page_map.CreateElement(kPdeCell, table).obj)
        cell_element.SetColNum(cell.col_index - 1)
        cell_element.SetRowNum(cell.row_index - 1)
        cell_element.SetBBox(bbox)
        cell_element.SetColSpan(1)
        cell_element.SetRowSpan(1)
