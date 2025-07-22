#!/bin/bash

module load apps/abaqus/2024
cd /home/gauss112/abaqus
abaqus cae
rm -rf ./*rpy*
rm -rf ./*.inp
rm -rf ~/abaqus_2024.gpr
