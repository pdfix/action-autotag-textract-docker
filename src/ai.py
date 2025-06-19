from PIL import Image
from textractor import Textractor
from textractor.data.constants import TextractFeatures
from textractor.entities.document import Document


def process_image(image_path: str) -> Document:
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
