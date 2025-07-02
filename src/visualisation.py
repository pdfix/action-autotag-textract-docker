from pathlib import Path

import cv2
from pdfixsdk import PdfDevRect, PdfPageView
from textractor.data.constants import (
    LAYOUT_LIST,
    LAYOUT_TABLE,
)
from textractor.entities.document import Document
from textractor.entities.layout import Layout


class VisualizeAmazonResults:
    """
    Visualizes the results of Amazon Textract layout recognition on a PDF page.
    This is done without highlighting words or lines.
    This class focuses on layouts and sublayouts like tables and lists.
    """

    def __init__(self, result: Document, image: cv2.typing.MatLike, id: str, page_number: int) -> None:
        """
        Initializes the VisualizeAmazonResults instance.

        Args:
            result (Document): The document containing the layout recognition results.
            image (cv2.typing.MatLike): The image where the results will be visualized.
            id (string): PDF document name.
            page_number (int): PDF file page number.
        """
        self.document = result
        self.image = image
        self.id = id
        self.page_number = page_number

    def visualize(self, page_view: PdfPageView) -> None:
        """
        Visualize layout, table and list on rendered PDF page.

        Args:
            page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
        """
        page_w = page_view.GetDeviceWidth()
        page_h = page_view.GetDeviceHeight()

        # Draw into image layouts, tables and lists
        for layout in self.document.layouts:
            rect = PdfDevRect()
            offset = 2
            rect.left = int(layout.bbox.x * page_w - offset)
            rect.top = int(layout.bbox.y * page_h - offset)
            rect.right = int((layout.bbox.x + layout.bbox.width) * page_w + offset)
            rect.bottom = int((layout.bbox.y + layout.bbox.height) * page_h + offset)

            layout_type = layout.layout_type
            if layout_type == LAYOUT_TABLE:
                self._visualize_table_cells(page_view, layout)
                rect.top -= 6
                rect.bottom -= 6
            if layout_type == LAYOUT_LIST:
                self._visualize_list_items(page_view, layout)
                rect.top -= 6
                rect.bottom -= 6

            green_color = (0, 255, 0)
            black_color = (0, 0, 0)
            thickness = 2
            cv2.rectangle(self.image, (rect.left, rect.top), (rect.right, rect.bottom), green_color, thickness)
            self._print_text(rect, layout.layout_type, layout.confidence, black_color, green_color)

        # Save the image to filesystem
        path: Path = Path(__file__).parent.joinpath(f"../output/{self.id}-{self.page_number}.jpg").resolve()
        cv2.imwrite(path, self.image)

    def _visualize_table_cells(self, page_view: PdfPageView, table_layout: Layout) -> None:
        """
        Visualizes cells from table in the image.

        Args:
            page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
            table_layout (Layout): The data containing the textract table region.
        """
        # Get information about table
        table_data = table_layout.children[0]

        page_w = page_view.GetDeviceWidth()
        page_h = page_view.GetDeviceHeight()

        # Loop through each cell's bounding box in the region
        for cell in table_data.children:
            rect = PdfDevRect()
            rect.left = int(cell.bbox.x * page_w)
            rect.top = int(cell.bbox.y * page_h)
            rect.right = int((cell.bbox.x + cell.bbox.width) * page_w)
            rect.bottom = int((cell.bbox.y + cell.bbox.height) * page_h)

            # Draw the cell rectangle on the image for visualization (optional step)
            blue_color = (255, 0, 0)
            white_color = (255, 255, 255)
            cv2.rectangle(self.image, (rect.left, rect.top), (rect.right, rect.bottom), blue_color, 2)
            self._print_text(rect, "Cell", cell.confidence, white_color, blue_color)

    def _visualize_list_items(self, page_view: PdfPageView, list_layout: Layout) -> None:
        """
        Visualizes items from list in the image.

        Args:
            page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
            list_layout (Layout): The data containing the textract list region.
        """
        page_w = page_view.GetDeviceWidth()
        page_h = page_view.GetDeviceHeight()

        for item in list_layout.children:
            rect = PdfDevRect()
            rect.left = int(item.bbox.x * page_w)
            rect.top = int(item.bbox.y * page_h)
            rect.right = int((item.bbox.x + item.bbox.width) * page_w)
            rect.bottom = int((item.bbox.y + item.bbox.height) * page_h)

            red_color = (0, 0, 255)
            black_color = (0, 0, 0)
            cv2.rectangle(self.image, (rect.left, rect.top), (rect.right, rect.bottom), red_color, 2)
            self._print_text(rect, "Item", item.confidence, black_color, red_color)

    def _print_text(
        self, rect: PdfDevRect, type_text: str, confidence: float, text_color: tuple, bg_color: tuple
    ) -> None:
        """ "
        Prints text on the image with a background rectangle.

        Args:
            rect (PdfDevRect): The rectangle where the text will be printed.
            type_text (str): Text to print (e.g., "Cell", "Item", "LAYOUT_TABLE").
            confidence (float): The confidence score of the text recognition.
            text_color (tuple): The color of the text in BGR format.
            bg_color (tuple): The background color of the text rectangle in BGR format.
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thickness = 1

        original_position = (rect.left + 2, rect.top + 10)

        short_type = type_text.split("_")[-1]
        percentage = int(confidence * 100)
        text = f"{short_type} {percentage}%"

        (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
        border = 2
        top_left = (original_position[0] - border, original_position[1] - text_h - border)
        bottom_right = (original_position[0] + text_w + border, original_position[1] + baseline + border)

        bg_rect_thickness = -1  # Fill the rectangle
        cv2.rectangle(self.image, top_left, bottom_right, bg_color, bg_rect_thickness)
        cv2.putText(self.image, text, original_position, font, scale, text_color, thickness)
