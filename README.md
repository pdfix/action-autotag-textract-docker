# Autotag Textract

A Docker image that automatically tags a PDF file using AWS Textract.

## Table of Contents

- [Autotag Textract](#autotag-textract)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [Run using Command Line Interface](#run-using-command-line-interface)
  - [Run using REST API](#run-using-rest-api)
    - [Exporting Configuration for Integration](#exporting-configuration-for-integration)
  - [License](#license)
  - [Help \& Support](#help--support)

## Getting Started

To use this Docker application, you'll need to have Docker installed on your system. If Docker is not installed, please follow the instructions on the [official Docker website](https://docs.docker.com/get-docker/) to install it.


## Run using Command Line Interface

To run docker container as CLI you should share the folder with PDF to process using `-i` parameter. In this example it's current folder.

```bash
docker run -v $(pwd):/data -w /data --rm pdfix/autotag-textract:latest autotag -i input.pdf -o output.pdf
```

The first run will pull the docker image, which may take some time. Make your own image for more advanced use.

For more detailed information about the available command-line arguments, you can run the following command:

```bash
docker run --rm pdfix/autotag-textract:latest --help
```

## Run using REST API
Comming soon. Please contact us.

### Exporting Configuration for Integration
To export the configuration JSON file, use the following command:
```bash
docker run -v $(pwd):/data -w /data --rm pdfix/autotag-textract:latest config -o config.json
```

## License
- PDFix license https://pdfix.net/terms
- AWS Textract 

The trial version of the PDFix SDK may apply a watermark on the page and redact random parts of the PDF including the scanned image in the background. Contact us to get an evaluation or production license.

## Help & Support
To obtain a PDFix SDK license or report an issue please contact us at support@pdfix.net.
For more information visit https://pdfix.net
