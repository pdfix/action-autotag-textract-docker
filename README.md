# PDF Accessibility Amazon Textract

A Docker image that automatically tags a PDF or creates a layout template JSON using Amazon Textract.

## Table of Contents

- [PDF Accessibility Amazon Textract](#pdf-accessibility-amazon-textract)
  - [Getting started](#getting-started)
  - [Usage](#usage)
  - [Commands](#commands)
  - [Arguments](#arguments)
  - [Examples](#examples)
  - [Help \& support](#help--support)
  - [Licenses](#licenses)

## Getting started

You need Docker installed. The first run downloads the image and may take longer than later runs.

## Usage

Mount a folder into the container and run a subcommand:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/autotag-textract:latest <command> [options]
```

## Commands

- `tag`: Tag a PDF using Amazon Textract layout recognition
- `template`: Create a layout template JSON for later tagging

## Arguments

### Common (used by `tag` and `template`)

| Option | Required | Type / expected value | Description |
|---|:---:|---|---|
| `--aws_id` | yes | String (AWS Access Key ID) | AWS Access Key ID |
| `--aws_secret` | yes | String (AWS Secret Access Key) | AWS Secret Access Key |
| `--aws_region` | yes | String (AWS region code, e.g. `us-east-1`) | AWS region |
| `--name` | no | String (PDFix account license name) | PDFix license name |
| `--key` | no | String (PDFix account license key) | PDFix license key |
| `--zoom` | no | Float, range **1.0–10.0** (default **2.0**) | Page render zoom |

### `tag`

| Option | Required | Type / expected value | Description |
|---|:---:|---|---|
| `--input`, `-i` | yes | Path to an existing `.pdf` file | Input PDF |
| `--output`, `-o` | yes | Path for the output `.pdf` file | Output PDF |

### `template`

| Option | Required | Type / expected value | Description |
|---|:---:|---|---|
| `--input`, `-i` | yes | Path to an existing `.pdf` file | Input PDF |
| `--output`, `-o` | yes | Path ending in `.json` | Output JSON layout template |

## Examples

Tag a PDF:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/autotag-textract:latest \
  tag --aws_id "${AWS_ID}" --aws_secret "${AWS_SECRET}" --aws_region "${AWS_REGION}" \
  --name "${LICENSE_NAME}" --key "${LICENSE_KEY}" \
  -i /data/input.pdf -o /data/output.pdf
```

Create a layout template JSON:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/autotag-textract:latest \
  template --aws_id "${AWS_ID}" --aws_secret "${AWS_SECRET}" --aws_region "${AWS_REGION}" \
  -i /data/document.pdf -o /data/template.json
```

## Help & support

For PDFix SDK licensing or issues, contact `support@pdfix.net`.

## Licenses

- [PDFix Terms](https://pdfix.net/terms)
- [Amazon Textract Textractor License](https://github.com/aws-samples/amazon-textract-textractor/blob/master/LICENSE)

Trial versions of the PDFix SDK may apply watermarks and redact random content in the output PDF.
