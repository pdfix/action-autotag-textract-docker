import argparse
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from autotag import AutotagUsingAmazonTextractRecognition
from create_template import CreateTemplateJsonUsingAmazonTextract
from image_update import DockerImageContainerUpdateChecker


def set_arguments(
    parser: argparse.ArgumentParser, names: list, required_output: bool = True, output_help: str = ""
) -> None:
    """
    Set arguments for the parser based on the provided names and options.

    Args:
        parser (argparse.ArgumentParser): The argument parser to set arguments for.
        names (list): List of argument names to set.
        required_output (bool): Whether the output argument is required. Defaults to True.
        output_help (str): Help for output argument. Defaults to "".
    """
    for name in names:
        match name:
            case "aws-id":
                parser.add_argument("--aws_id", type=str, required=True, help="AWS Access Key ID.")
            case "aws-secret":
                parser.add_argument("--aws_secret", type=str, required=True, help="AWS Secret Access Key.")
            case "aws-region":
                parser.add_argument("--aws_region", type=str, required=True, help="AWS Region.")
            case "input":
                parser.add_argument("--input", "-i", type=str, required=True, help="The input PDF file.")
            case "key":
                parser.add_argument("--key", type=str, default="", nargs="?", help="PDFix license key.")
            case "name":
                parser.add_argument("--name", type=str, default="", nargs="?", help="PDFix license name.")
            case "output":
                parser.add_argument("--output", "-o", type=str, required=required_output, help=output_help)
            case "zoom":
                parser.add_argument(
                    "--zoom", type=float, default=2.0, help="Zoom level for the PDF page rendering (default: 2.0)."
                )


def run_config_subcommand(args) -> None:
    get_pdfix_config(args.output)


def get_pdfix_config(path: str) -> None:
    """
    If Path is not provided, output content of config.
    If Path is provided, copy config to destination path.

    Args:
        path (string): Destination path for config.json file
    """
    config_path: Path = Path(__file__).parent.joinpath("../config.json").resolve()

    with open(config_path, "r", encoding="utf-8") as file:
        if path is None:
            print(file.read())
        else:
            with open(path, "w") as out:
                out.write(file.read())


def run_autotag_subcommand(args) -> None:
    autotagging_pdf(
        args.aws_id, args.aws_secret, args.aws_region, args.name, args.key, args.input, args.output, args.zoom
    )


def autotagging_pdf(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_region: str,
    license_name: Optional[str],
    license_key: Optional[str],
    input_path: str,
    output_path: str,
    zoom: float,
) -> None:
    """
    Autotagging PDF document with provided arguments

    Args:
        aws_access_key_id (str): AWS Access Key ID.
        aws_secret_access_key (str): AWS Secret Access Key.
        aws_region (str): AWS Region.
        license_name (Optional[str]): Name used in authorization in PDFix-SDK.
        license_key (Optional[str]): Key used in authorization in PDFix-SDK.
        input_path (str): Path to PDF document.
        output_path (str): Path to PDF document.
        zoom (float): Zoom level for rendering the page.
    """
    if zoom < 1.0 or zoom > 10.0:
        raise Exception("Zoom level must between 1.0 and 10.0")

    if input_path.lower().endswith(".pdf") and output_path.lower().endswith(".pdf"):
        autotag = AutotagUsingAmazonTextractRecognition(
            aws_access_key_id,
            aws_secret_access_key,
            aws_region,
            license_name,
            license_key,
            input_path,
            output_path,
            zoom,
        )
        autotag.process_file()
    else:
        raise Exception("Input and output file must be PDF documents")


def run_template_subcommand(args) -> None:
    create_template_json(
        args.aws_id, args.aws_secret, args.aws_region, args.name, args.key, args.input, args.output, args.zoom
    )


def create_template_json(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_region: str,
    license_name: Optional[str],
    license_key: Optional[str],
    input_path: str,
    output_path: str,
    zoom: float,
) -> None:
    """
    Creating template json for PDF document using provided arguments

    Args:
        aws_access_key_id (str): AWS Access Key ID.
        aws_secret_access_key (str): AWS Secret Access Key.
        aws_region (str): AWS Region.
        license_name (Optional[str]): Name used in authorization in PDFix-SDK.
        license_key (Optional[str]): Key used in authorization in PDFix-SDK.
        input_path (str): Path to PDF document.
        output_path (str): Path to JSON file.
        zoom (float): Zoom level for rendering the page.
    """
    if zoom < 1.0 or zoom > 10.0:
        raise Exception("Zoom level must between 1.0 and 10.0")

    if input_path.lower().endswith(".pdf") and output_path.lower().endswith(".json"):
        template_creator = CreateTemplateJsonUsingAmazonTextract(
            aws_access_key_id,
            aws_secret_access_key,
            aws_region,
            license_name,
            license_key,
            input_path,
            output_path,
            zoom,
        )
        template_creator.process_file()
    else:
        raise Exception("Input file must be PDF and output file must be JSON")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Autotag PDF file using layout recognition",
    )

    subparsers = parser.add_subparsers(title="Commands", dest="command", required=True)

    # Config subparser
    config_subparser = subparsers.add_parser(
        "config",
        help="Extract config file for integration",
    )
    set_arguments(
        config_subparser,
        ["output"],
        False,
        "Output to save the config JSON file. Application output is used if not provided.",
    )
    config_subparser.set_defaults(func=run_config_subcommand)

    # Autotag subparser
    autotag_subparser = subparsers.add_parser(
        "tag",
        help="Run autotag PDF document",
    )
    set_arguments(
        autotag_subparser,
        ["aws-id", "aws-secret", "aws-region", "name", "key", "input", "output", "zoom"],
        True,
        "The output PDF file.",
    )
    autotag_subparser.set_defaults(func=run_autotag_subcommand)

    # Template subparser
    template_subparser = subparsers.add_parser(
        "template",
        help="Create layout template JSON.",
    )
    set_arguments(
        template_subparser,
        ["aws-id", "aws-secret", "aws-region", "name", "key", "input", "output", "zoom"],
        True,
        "The output JSON file.",
    )
    template_subparser.set_defaults(func=run_template_subcommand)

    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code == 0:
            # This happens when --help is used, exit gracefully
            sys.exit(0)
        print("Failed to parse arguments. Please check the usage and try again.", file=sys.stderr)
        sys.exit(e.code)

    if hasattr(args, "func"):
        # Check for updates only when help is not checked
        update_checker = DockerImageContainerUpdateChecker()
        # Check it in separate thread not to be delayed when there is slow or no internet connection
        update_thread = threading.Thread(target=update_checker.check_for_image_updates)
        update_thread.start()

        # Measure the time it takes to make all requests
        start_time = time.time()  # Record the start time
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"\nProcessing started at: {current_time}")

        # Run subcommand
        try:
            args.func(args)
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
            print(f"Failed to run the program: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            end_time = time.time()  # Record the end time
            elapsed_time = end_time - start_time  # Calculate the elapsed time
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            print(f"\nProcessing finished at: {current_time}. Elapsed time: {elapsed_time:.2f} seconds")

            # Make sure to let update thread finish before exiting
            update_thread.join()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
