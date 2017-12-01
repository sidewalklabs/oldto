#!/bin/bash
git ls-files oldtoronto .py | grep -v '_test' | grep -v '.md5' |  xargs vulture whitelist.py
