#!/bin/bash

# Go to test framework directory
cd ../../test-framework

# Create outputs for tests
./create_outputs.sh ../action-autotag-textract-docker/tests/configs/test_autotag.json
./create_outputs.sh ../action-autotag-textract-docker/tests/configs/test_template.json
