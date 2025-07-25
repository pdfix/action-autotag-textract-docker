import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import textractor.data.constants as constants
from pdfixsdk import PdfDevRect, PdfPageView, PdfRect, __version__
from textractor.entities.document import Document
from textractor.entities.layout import Layout
from textractor.entities.table import Table
from textractor.entities.table_cell import TableCell


class TemplateJsonCreator:
    """
    Class that prepares each page and in the end creates whole template json file for PDFix-SDK
    """

    # Constants
    CONFIG_FILE = "config.json"

    def __init__(self) -> None:
        """
        Initializes pdfix sdk template json creation by preparing list for each page.
        """
        self.template_json_pages: list = []

    def create_json_dict_for_document(self, zoom: float) -> dict:
        """
        Prepare PDFix SDK json template for whole document.

        Args:
            zoom (float): Zoom level that page was rendered with.

        Returns:
            Template json for whole document
        """
        created_date = date.today().strftime("%Y-%m-%d")
        metadata: dict = {
            "author": f"AutoTag (Textract) {self._get_current_version()}",
            "created": created_date,
            "modified": created_date,
            "notes": f"Created using Amazon Textract and PDFix zoom: {zoom}",
            "sdk_version": __version__,
            # we are creating first one always so it is always "1"
            "version": "1",
        }
        page_map: list = [{"graphic_table_detect": "0", "statement": "$if", "text_table_detect": "0"}]

        return {
            "metadata": metadata,
            "template": {
                "element_create": self.template_json_pages,
                "pagemap": page_map,
            },
        }

    def process_page(self, result: Document, page_number: int, page_view: PdfPageView) -> None:
        """
        Prepare json template for PDFix SDK for one page and save it internally to use later in
        create_json_dict_for_document.

        Args:
            result (Document): AWS Document class containing all data from AI for one page.
            page_number (int): PDF file page number.
            page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
            zoom (float): Zoom level that page was rendered with.
        """
        elements: list = self._create_json_for_elements(result, page_view, page_number)

        json_for_page = {
            "comment": f"Page {page_number}",
            "elements": elements,
            "query": {
                "$and": [{"$page_num": page_number}],
            },
            "statement": "$if",
        }
        self.template_json_pages.append(json_for_page)

    def _get_current_version(self) -> str:
        """
        Read the current version from config.json.

        Returns:
            The current version of the Docker image.
        """
        config_path: Path = Path(__file__).parent.joinpath(f"../{self.CONFIG_FILE}").resolve()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("version", "unknown")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading {self.CONFIG_FILE}: {e}", file=sys.stderr)
            return "unknown"

    def _create_json_for_elements(self, result: Document, page_view: PdfPageView, page_number: int) -> list:
        """
        Prepare initial structural elements for the template based on
        detected regions.

        Args:
            result (Document): AWS Document class containing all data from AI for one page.
            page_view (PdfPageView): The view of the PDF page used for coordinate conversion.
            page_number (int): PDF file page number.

        Returns:
            List of elements with parameters.
        """
        elements: list = []

        page_w = page_view.GetDeviceWidth()
        page_h = page_view.GetDeviceHeight()

        for region in result.layouts:
            if not isinstance(region, Layout):
                continue

            layout: Layout = region
            element: dict[str, Any] = {}

            rect = PdfDevRect()
            offset = 2
            rect.left = int(layout.bbox.x * page_w - offset)
            rect.top = int(layout.bbox.y * page_h - offset)
            rect.right = int((layout.bbox.x + layout.bbox.width) * page_w + offset)
            rect.bottom = int((layout.bbox.y + layout.bbox.height) * page_h + offset)

            bbox = page_view.RectToPage(rect)
            element["bbox"] = [str(bbox.left), str(bbox.bottom), str(bbox.right), str(bbox.top)]
            label = layout.layout_type.split("_")[-1].lower()
            element["comment"] = f"{label} {round(layout.confidence * 100)}%"

            # List of types:
            # https://docs.aws.amazon.com/textract/latest/dg/layoutresponse.html
            match layout.layout_type:
                case constants.LAYOUT_FIGURE:
                    element["type"] = "pde_image"

                case constants.LAYOUT_FOOTER:
                    element["flag"] = "footer|artifact"
                    element["type"] = "pde_text"

                case constants.LAYOUT_HEADER:
                    element["flag"] = "header|artifact"
                    element["type"] = "pde_text"

                case constants.LAYOUT_LIST:
                    # No info about type of list (bullets vs numbers)
                    # element["numbering"] = "Circle"  # "Decimal"
                    list_items = self._create_list_items(layout, page_view)
                    element["element_template"] = {
                        "template": {
                            "element_create": [{"elements": list_items, "statement": "$if"}],
                        },
                    }
                    element["type"] = "pde_list"

                case constants.LAYOUT_PAGE_NUMBER:
                    number_flag = self._is_footer_or_header(page_view, bbox)
                    element["flag"] = f"{number_flag}|artifact"
                    element["type"] = "pde_text"

                case constants.LAYOUT_SECTION_HEADER:
                    element["heading"] = "h1"
                    element["type"] = "pde_text"

                case constants.LAYOUT_TABLE:
                    table_data: Table = layout.children[0]
                    cell_elements: list = self._create_table_cells(table_data, page_view)
                    element["element_template"] = {
                        "template": {
                            "element_create": [{"elements": cell_elements, "query": {}, "statement": "$if"}],
                        },
                    }
                    element["row_num"] = table_data.row_count
                    element["col_num"] = table_data.column_count
                    element["type"] = "pde_table"

                case constants.LAYOUT_TEXT:
                    element["type"] = "pde_text"

                case constants.LAYOUT_TITLE:
                    element["tag"] = "Title"
                    element["type"] = "pde_text"

                case _:
                    element["type"] = "pde_text"

            elements.append(element)

        elements = sorted(elements, key=lambda x: (float(x["bbox"][3]), 1000.0 - float(x["bbox"][0])), reverse=True)

        return elements

    def _create_list_items(self, list_layout: Layout, page_view: PdfPageView) -> list:
        """
        Prepare list item elements.

        Args:
            list_layout (Layout): AWS Textract Layout class containing all data from AI for list.
            page_view (PdfPageView): The view of the PDF page used
                for coordinate conversion.

        Returns:
            List of item elements with parameters.
        """
        items: list = []

        page_w = page_view.GetDeviceWidth()
        page_h = page_view.GetDeviceHeight()

        for region in list_layout.children:
            if not isinstance(region, Layout):
                continue

            layout: Layout = region

            rect = PdfDevRect()
            rect.left = int(layout.bbox.x * page_w)
            rect.top = int(layout.bbox.y * page_h)
            rect.right = int((layout.bbox.x + layout.bbox.width) * page_w)
            rect.bottom = int((layout.bbox.y + layout.bbox.height) * page_h)
            bbox = page_view.RectToPage(rect)

            item: dict = {
                "bbox": [str(bbox.left), str(bbox.bottom), str(bbox.right), str(bbox.top)],
                "comment": f"List Item {round(layout.confidence * 100)}%",
                "type": "pde_text",
            }

            # Only text included so we cannot mark bullets/numbers as:
            # item["label"] = "label"

            items.append(item)

        # TODO sorting

        return items

    def _create_table_cells(self, table_data: Table, page_view: PdfPageView) -> list:
        """
        Prepare table cell elements.

        Args:
            table_data (Table): AWS Textract Table class containing all data from AI for table.
            page_view (PdfPageView): The view of the PDF page used
                for coordinate conversion.

        Returns:
            List of cell elements with parameters.
        """
        cells: list = []

        page_w = page_view.GetDeviceWidth()
        page_h = page_view.GetDeviceHeight()

        for cell_data in table_data.children:
            if not isinstance(cell_data, TableCell):
                continue

            cell: TableCell = cell_data

            cell_position: str = f"[{cell.row_index + 1}, {cell.col_index + 1}]"
            cell_span: str = f"[{cell.row_span}, {cell.col_span}]"

            rect = PdfDevRect()
            rect.left = int(cell.bbox.x * page_w)
            rect.top = int(cell.bbox.y * page_h)
            rect.right = int((cell.bbox.x + cell.bbox.width) * page_w)
            rect.bottom = int((cell.bbox.y + cell.bbox.height) * page_h)
            bbox = page_view.RectToPage(rect)

            create_cell: dict = {
                "bbox": [str(bbox.left), str(bbox.bottom), str(bbox.right), str(bbox.top)],
                "cell_column": str(cell.col_index + 1),
                "cell_column_span": str(cell.col_span),
                "cell_row": str(cell.row_index + 1),
                "cell_row_span": str(cell.row_span),
                "cell_header": cell.is_column_header,
                "comment": f"Cell Pos: {cell_position} Span: {cell_span} Confidence: {round(cell.confidence * 100)}%",
                "type": "pde_cell",
            }

            # # We are not able to acquire this information
            # create_cell["cell_scope"] = "0"

            cells.append(create_cell)

        # Fill table with empty cells
        for row_index in range(table_data.row_count):
            for col_index in range(table_data.column_count):
                if not any(cell.row_index == row_index and cell.col_index == col_index for cell in table_data.children):
                    empty_cell: dict = {
                        "bbox": ["0", "0", "0", "0"],
                        "cell_column": str(col_index + 1),
                        "cell_column_span": "0",
                        "cell_row": str(row_index + 1),
                        "cell_row_span": "0",
                        "cell_header": "false",
                        "comment": f"Cell Pos: [{row_index + 1}, {col_index + 1}] Span: [0, 0] Added by processing",
                        "type": "pde_cell",
                    }
                    cells.append(empty_cell)

        # TODO sorting

        return cells

    def _convert_bool_to_str(self, value: bool) -> str:
        """
        Create value for json as pdfix template expects

        Args:
            value (bool): calue to convert

        Returns:
            Converted bool to string for json purposes
        """
        return "true" if value else "false"

    def _is_footer_or_header(self, page_view: PdfPageView, bbox: PdfRect) -> str:
        """
        According to Y coordinate of bbox return if it is "header" or "footer"

        Args:
            page_view (PdfPageView): Page view to get page heigh
            bbox (PdfRect): Bounding box in PDF coordinates (Y=0 is bottom)

        Returns:
            "header" or "footer"
        """
        page_height = page_view.GetDeviceHeight()
        half_height = page_height / 2
        return "footer" if bbox.top < half_height else "header"
