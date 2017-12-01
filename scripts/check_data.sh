#!/bin/bash
for md5_file in $(find . -maxdepth 2 -name '.md5'); do
  if [ -n "$(diff <(md5sum ${md5_file/.md5/}) $md5_file)" ]
  then
    exit 1
  fi
done
