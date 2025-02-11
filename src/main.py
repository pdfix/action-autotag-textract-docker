from pathlib import Path
import argparse, sys, os, time
from datetime import datetime
from autotag_pdf import autotag_pdf

def get_config(args) -> None:
    with open(
        os.path.join(Path(__file__).parent.absolute(), "../config.json"),
        "r",
        encoding="utf-8",
    ) as f:
        if hasattr(args, "output") and args.output:
            with open(args.output, "w") as out:
                out.write(f.read())
        else:
            print(f.read())

def main() -> None:
    try:
        parser = argparse.ArgumentParser(
            description="Process a PDF file using layout recognition",
        )
        subparsers = parser.add_subparsers(title="Commands", dest="command", required=True)

        # get config subparser
        pars_config = subparsers.add_parser(
            "config",
            help="Extract config file for integration",
        )

        pars_config.add_argument(
            "-o",
            "--output",
            type=str,
            help="Output to save the config JSON file. Application output\
                is used if not provided",
        )
        pars_config.set_defaults(func=get_config)

        pars_autotag = subparsers.add_parser(
            "autotag",
            help="Run autotag",
        )

        pars_autotag.add_argument("-i", "--input", type=str, help="The input PDF file")
        pars_autotag.add_argument(
            "-o",
            "--output",
            type=str,
            help="The output PDF file",
        )
        pars_autotag.add_argument("--name", type=str, help="License Name")
        pars_autotag.add_argument("--key", type=str, help="License Key")
        pars_autotag.set_defaults(func=autotag_pdf)

        args = parser.parse_args()

        # Measure the time it takes to make all requests
        start_time = time.time()  # Record the start time

        dayTyme = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"\nProcessing started at: {dayTyme}")
        
        # Run assigned function
        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_help()    

        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time            
        print(f"\nProcessing finished at: {dayTyme}. Elapsed time: {elapsed_time:.2f} seconds")        

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()