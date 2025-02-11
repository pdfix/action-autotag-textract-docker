from textractor import Textractor
from textractor.data.constants import TextractFeatures, Direction, DirectionalFinderType
from PIL import Image
import cv2
from pdfixsdk import *


def textract_model(image: str):
    extractor = Textractor(profile_name="default")
    image = Image.open(image)
    document = extractor.analyze_document(
        file_source=image,
        features=[TextractFeatures.TABLES, TextractFeatures.LAYOUT],
        save_image=True,
    )

    return document


def textract_add_elements(page_map, page_view, document, image):
    """
    Adds initial structural elements to the page map based on detected regions.

    Args:
        page_map (PdePageMap): The page map where elements will be added.
        page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
        document (): A document returned by textract.
        image (any): The image representation of the page for visualization.
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

        cv2.rectangle(
            image, (rect.left, rect.top), (rect.right, rect.bottom), (0, 255, 0), 2
        )

        # Determine element type
        element_type = kPdeText  # Default to text
        region_type = region.layout_type
        if region_type == "LAYOUT_TABLE":
            element_type = kPdeTable
        elif region_type == "LAYOUT_FIGURE":
            element_type = kPdeImage
        elif region_type == "LAYOUT_LIST":
            element_type = kPdeList

        element = page_map.CreateElement(element_type, None)
        element.SetBBox(bbox)

        if region_type == "LAYOUT_HEADER":
            element.SetTextStyle(kTextH1)
        elif region_type == "LAYOUT_SECTION_HEADER":
            element.SetTextStyle(kTextH2)
        elif region_type == "LAYOUT_TABLE":
            update_table_cells(element, page_view, region, image)


def update_table_cells(pdf_element: PdeElement, page_view: PdfPageView, region, image):
    """
    Updates the table element with detected cells

    Args:
        pdf_element (PdeElement): The table element to edit.
        page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
        region (): The data containing the textract table region.
        image (any): The image representation of the page for visualization.
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
        cv2.rectangle(
            image, (rect.left, rect.top), (rect.right, rect.bottom), (255, 0, 0), 1
        )

        # Convert cell rectangle to page coordinates
        bbox = page_view.RectToPage(rect)

        # Create a new cell element and set its properties
        cell_element = PdeCell(page_map.CreateElement(kPdeCell, table).obj)
        cell_element.SetColNum(cell.col_index - 1)
        cell_element.SetRowNum(cell.row_index - 1)
        cell_element.SetBBox(bbox)
        cell_element.SetColSpan(1)
        cell_element.SetRowSpan(1)
