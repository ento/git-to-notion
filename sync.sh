#!/usr/bin/env bash
# Git to Notion
#       -p 1b3e1e3e265c809e9f36e7f016f20b54 \

# docs
#exec python sync.py  ../main/docs/ \
#       -p 1b7e1e3e265c80ceb883c0c58b8fb180 \
#       -u https://github.com/StriveTalent/strive \
#       -b dev

# test
exec python sync.py  ../main/docs/ \
       -p 212e1e3e265c8092b455dcd4e865ab29 \
       -u https://github.com/StriveTalent/strive \
       -b dev \
       --build-dir test
