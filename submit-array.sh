#!/bin/bash

CHUNK_SIZE=10
TOTAL=100

for (( i=0; i<${TOTAL}; i+=${CHUNK_SIZE} )); do
    from=$i
    to=$((i + CHUNK_SIZE - 1))
    echo "Submitting rupture chunk: ${from} ~ ${to}"
    sbatch --export=INDEX_FROM=${from},INDEX_TO=${to} PSU-Run-Array.slurm
done