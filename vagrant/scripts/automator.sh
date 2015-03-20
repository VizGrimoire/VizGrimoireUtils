#!/bin/bash

for f in $( ls automator/*.sh ) ; do
    bash ${f}
done
