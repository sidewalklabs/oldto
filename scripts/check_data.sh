#!/bin/bash
set -o errexit

for md5_file in $(find . -maxdepth 2 -name '*.md5'); do
  md5sum --check $md5_file
done
