#!/usr/bin/env bash
USED=(10 11 12 13 )
echo $USED
break
for free in {10..20}; do
    echo $USED || break
done
