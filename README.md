# PDF Accesibility Amazon Textract

A Docker image that automatically tags a PDF file or creates template layout json for it using Amazon Textract.

## Table of Contents

- [Autotag Textract](#autotag-textract)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [Run a Docker Container ](#run-docker-container)
    - [Run Docker Container for Autotagging](#run-docker-container-for-autotagging)
    - [Run Docker Container for Template JSON Creation](#run-docker-container-for-template-json-creation)
    - [Exporting Configuration for Integration](#exporting-configuration-for-integration)
  - [License](#license)
  - [Help \& Support](#help--support)

## Getting Started

To use this Docker application, you'll need to have Docker installed on your system. If Docker is not installed, please follow the instructions on the [official Docker website](https://docs.docker.com/get-docker/) to install it.

## Run a Docker Container

The first run will pull the docker image, which may take some time. Make your own image for more advanced use.

### Run Docker Container for Autotagging

To run docker container as CLI you should share the folder with PDF to process using `-v` parameter. In this example it's current folder.

```bash
docker run -v ~/.aws:/root/.aws -v $(pwd):/data -w /data --rm pdfix/autotag-textract:latest tag --aws_id ${AWS_ID} --aws_secret ${AWS_SECRET} --aws_region ${AWS_REGION} --name ${LICENSE_NAME} --key ${LICENSE_KEY} -i /data/input.pdf -o /data/output.pdf
```

These arguments are required and are used to identify AWS account used for Textract.

```bash
--aws_id ${AWS_ID} --aws_secret ${AWS_SECRET} --aws_region ${AWS_REGION}
```

These arguments are for an account-based PDFix license.

```bash
--name ${LICENSE_NAME} --key ${LICENSE_KEY}
```

Contact support for more information.

For more detailed information about the available command-line arguments, you can run the following command:

```bash
docker run --rm pdfix/autotag-textract:latest --help
```

### Run Docker Container for Template JSON Creation

Automatically creates layout template json using AWS Textract, saving it as JSON file.

```bash
docker run -v ~/.aws:/root/.aws -v $(pwd):/data -w /data --rm pdfix/autotag-textract:latest template -i /data/document.pdf -o /data/template.json
```

### Exporting Configuration for Integration

To export the configuration JSON file, use the following command:

```bash
docker run -v $(pwd):/data -w /data --rm pdfix/autotag-textract:latest config -o config.json
```

## License

- [PDFix license](https://pdfix.net/terms)
- [Amazon Textract](https://github.com/aws-samples/amazon-textract-textractor/blob/master/LICENSE)

The trial version of the PDFix SDK may apply a watermark on the page and redact random parts of the PDF including the scanned image in the background. Contact us to get an evaluation or production license.

## Help & Support

To obtain a PDFix SDK license or report an issue please contact us at support@pdfix.net.
For more information visit https://pdfix.net
