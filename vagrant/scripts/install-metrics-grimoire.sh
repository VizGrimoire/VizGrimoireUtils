#!/bin/bash

export MG_SCRIPTS="${SCRIPTS_PATH}/metrics-grimoire"

for f in $( ls ${MG_SCRIPTS}/*.sh ) ; do
    bash ${f}
done
