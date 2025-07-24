#!/bin/bash

# Go to test framework directory
cd ../../test-framework

# Run tests with path to folder with configs
./run_tests.sh ../action-autotag-textract-docker/tests/configs
