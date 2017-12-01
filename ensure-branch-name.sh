#!/bin/bash
#
# This script ensures that the remote tracking branch for the current branch
# has an associated Jira issue. It looks for the characters "AP".

local_branch=$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)

if [[ $local_branch != *'AP'* ]]; then
  >&2 cat <<END
Remote branch ($local_branch) must be linked to a Jira issue via AP-nnn.
To rename your branch:

  git branch -m $local_branch $local_branch-AP-nnn

or skip this check via

  git push --no-verify

END
  exit 1
fi
