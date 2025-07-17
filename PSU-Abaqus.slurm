#!/bin/bash
#SBATCH --account=MST113389
#SBATCH --partition=ct112
#SBATCH --job-name=Abaqus_Job
#SBATCH --output=/home/gauss112/Abaqus-%j.out
#SBATCH --error=/home/gauss112/Abaqus-%j.err
#SBATCH --ntasks=1
#SBATCH --time=48:00:00
#SBATCH --mem-per-cpu=16G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=b09501028@ntu.edu.tw


cd /home/gauss112/abaqus
source /etc/profile.d/modules.sh
module load apps/abaqus/2024
abaqus cae noGUI=PSU-Make.py
echo "8cpu" | absub BlockJob MST113389
echo "Abaqus job submitted at $(date)"