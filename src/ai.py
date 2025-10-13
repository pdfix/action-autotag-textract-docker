import sys

import boto3
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    NoRegionError,
    ParamValidationError,
    PartialCredentialsError,
)
from PIL import Image
from textractcaller import Textract_Features, call_textract
from textractcaller.t_call import Textract_Call_Mode
from textractor.entities.document import Document
from textractor.parsers import response_parser

from exceptions import (
    AmazonTextractCredentialsException,
    AmazonTextractEndpointUnreachableException,
    AmazonTextractGenericException,
    AmazonTextractRegionException,
)


def process_image(aws_access_key_id: str, aws_secret_access_key: str, aws_region: str, image_path: str) -> Document:
    """
    Analyzes the document using Textract and returns the document object.

    Args:
        aws_access_key_id (str): AWS Access Key ID.
        aws_secret_access_key (str): AWS Secret Access Key.
        aws_region (str): AWS Region.
        image_path (str): Path to the image file to be analyzed.

    Returns:
        The document object containing the analysis results.
    """
    try:
        # Create boto3 Textract client
        textract_client = boto3.client(
            "textract",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )

        # Inspired with arguments with what is in extractor.analyze_document only different boto3 client is used
        textract_json = call_textract(
            input_document=image_path,
            features=[Textract_Features.TABLES, Textract_Features.LAYOUT],
            call_mode=Textract_Call_Mode.FORCE_SYNC,
            boto3_textract_client=textract_client,
            job_done_polling_interval=0,
        )

        # Created JSON needs to be further processed by textractor-parser to more useful format
        document = response_parser.parse(textract_json)
        document.response = textract_json

        # Save image so visualization can be done later
        document.pages[0].image = Image.open(image_path)

    except NoCredentialsError as e:
        print(e, file=sys.stderr)
        raise AmazonTextractCredentialsException()
    except PartialCredentialsError as e:
        print(e, file=sys.stderr)
        raise AmazonTextractCredentialsException()
    except NoRegionError as e:
        print(e, file=sys.stderr)
        raise AmazonTextractRegionException()
    except EndpointConnectionError as e:
        print(e, file=sys.stderr)
        raise AmazonTextractEndpointUnreachableException()
    except ParamValidationError as e:
        print(e, file=sys.stderr)
        raise AmazonTextractGenericException()
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ["UnrecognizedClientException", "InvalidClientTokenId", "SignatureDoesNotMatch"]:
            print(e, file=sys.stderr)
            raise AmazonTextractCredentialsException()
        else:
            print(e, file=sys.stderr)
            raise AmazonTextractGenericException()
    except Exception as e:
        print(e, file=sys.stderr)
        raise AmazonTextractGenericException()

    return document
