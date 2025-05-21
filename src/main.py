import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from autotag_pdf import autotag_pdf


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
            case "input":
                parser.add_argument("--input", "-i", type=str, required=True, help="The input PDF file")
            case "key":
                parser.add_argument("--key", type=str, help="PDFix license key")
            case "name":
                parser.add_argument("--name", type=str, help="PDFix license name")
            case "output":
                parser.add_argument("--output", "-o", type=str, required=required_output, help=output_help)


def run_config_subcommand(args) -> None:
    get_pdfix_config(args.output)


def get_pdfix_config(path: str) -> None:
    """
    If Path is not provided, output content of config.
    If Path is provided, copy config to destination path.

    Args:
        path (string): Destination path for config.json file
    """
    config_path = os.path.join(Path(__file__).parent.absolute(), "../config.json")

    with open(config_path, "r", encoding="utf-8") as file:
        if path is None:
            print(file.read())
        else:
            with open(path, "w") as out:
                out.write(file.read())


def run_autotag_subcommand(args) -> None:
    autotag_pdf(args.input, args.output, args.name, args.key)


def main() -> None:
    try:
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
            "Output to save the config JSON file. Application output" + "is used if not provided",
        )
        config_subparser.set_defaults(func=run_config_subcommand)

        # Autotag subparser
        autotag_subparser = subparsers.add_parser(
            "autotag",
            help="Run autotag PDF document",
        )
        set_arguments(autotag_subparser, ["name", "key", "input", "output"], True, "The output PDF file")
        autotag_subparser.set_defaults(func=run_autotag_subcommand)

        # Parse arguments
        args = parser.parse_args()

        # Measure the time it takes to make all requests
        start_time = time.time()  # Record the start time

        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"\nProcessing started at: {current_time}")

        # Run subcommand
        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_help()

        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"\nProcessing finished at: {current_time}. Elapsed time: {elapsed_time:.2f} seconds")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
