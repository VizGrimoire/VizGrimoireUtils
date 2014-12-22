#!/bin/bash

export AUTOMATOR_SCRIPTS="${SCRIPTS_PATH}/automator"

for f in $( ls ${AUTOMATOR_SCRIPTS}/*.sh ) ; do
    bash ${f}
done
