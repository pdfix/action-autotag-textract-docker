import tempfile

from pdfixsdk import (
    GetPdfix,
    PdfImageParams,
    PdfPage,
    PdfPageRenderParams,
    PdfPageView,
    kImageDIBFormatArgb,
    kImageFormatJpg,
    kPsTruncate,
)


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

    try:
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

            try:
                # Set image parameters (format and quality)
                image_params = PdfImageParams()
                image_params.format = kImageFormatJpg
                image_params.quality = 100

                # Save the image to the file stream
                if not page_image.SaveToStream(file_stream, image_params):
                    raise RuntimeError(f"{pdfix.GetError()} [{pdfix.GetErrorType()}]")
            except Exception:
                raise
            finally:
                file_stream.Close()

            # Return the saved image
            return temp_file.name
    except Exception:
        raise
    finally:
        page_image.Destroy()
