import json
from pathlib import Path
from typing import Any

from textractor.data.constants import (
    LAYOUT_LIST,
    LAYOUT_TABLE,
)
from textractor.entities.bbox import BoundingBox
from textractor.entities.document import Document
from textractor.entities.layout import Layout
from textractor.entities.page import Page
from textractor.entities.table import Table
from textractor.entities.table_cell import TableCell


class ConvertDocumentToDictionary:
    """
    Converts a Amazon Textract Document to a dictionary and save it as json.
    """

    def __init__(self, document: Document, id: str, page_number: int) -> None:
        """
        Initializes the ConvertDocumentToDictionary instance.

        Args:
            document (Document): The document to be converted.
            id (str): PDF document name.
            page_number (int): PDF file page number.
        """
        self.document = document
        self.id = id
        self.page_number = page_number

    def save_as_json(self) -> None:
        """
        Save the Document as dictionary into JSON file.
        """
        dictionary = self._convert()
        path: Path = Path(__file__).parent.joinpath(f"../output/{self.id}-{self.page_number}.json").resolve()

        with open(path, "w", encoding="utf-8") as result_file:
            json.dump(dictionary, result_file, indent=2)

    def _convert(self) -> dict:
        """
        Convert the document to a dictionary format.
        """
        return self._convert_object(self.document, True)

    def _convert_object(self, object_to_convert: Any, include_children: bool = True) -> Any:
        if isinstance(object_to_convert, BoundingBox):
            return {
                "x": object_to_convert.x,
                "y": object_to_convert.y,
                "width": object_to_convert.width,
                "height": object_to_convert.height,
            }

        if isinstance(object_to_convert, Document):
            return {
                "pages": [self._convert_object(page) for page in object_to_convert.pages],
            }

        if isinstance(object_to_convert, Page):
            return {
                "layout": [self._convert_object(layout) for layout in object_to_convert.layouts],
            }

        if isinstance(object_to_convert, Layout):
            result = {
                "bbox": self._convert_object(object_to_convert.bbox),
                "layout_type": object_to_convert.layout_type,
                "confidence": object_to_convert.confidence,
            }
            if include_children:
                if object_to_convert.layout_type == LAYOUT_TABLE or object_to_convert.layout_type == LAYOUT_LIST:
                    result["children"] = [self._convert_object(child) for child in object_to_convert.children]
            return result

        if isinstance(object_to_convert, Table):
            return {
                "column_count": object_to_convert.column_count,
                "row_count": object_to_convert.row_count,
                "bbox": self._convert_object(object_to_convert.bbox),
                "children": [self._convert_object(child) for child in object_to_convert.children],
            }

        if isinstance(object_to_convert, TableCell):
            return {
                "col_index": object_to_convert.col_index,
                "row_index": object_to_convert.row_index,
                "col_span": object_to_convert.col_span,
                "row_span": object_to_convert.row_span,
                "bbox": self._convert_object(object_to_convert.bbox),
                "text": object_to_convert.text,
                "confidence": object_to_convert.confidence,
                "is_column_header": object_to_convert.is_column_header,
                "is_title": object_to_convert.is_title,
                "is_summary": object_to_convert.is_summary,
            }

        if isinstance(object_to_convert, dict):
            return {key: self._convert_object(value, include_children) for key, value in object_to_convert.items()}

        if isinstance(object_to_convert, list):
            return [self._convert_object(item) for item in object_to_convert]

        return object_to_convert
