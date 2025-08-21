#!/bin/bash
#SBATCH --account=MST113389
#SBATCH --partition=ct112
#SBATCH --job-name=rsync-upload
#SBATCH --output=/home/gauss112/outs/rsync-%j.out
#SBATCH --error=/home/gauss112/outs/rsync-%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --time=96:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=b09501028@ntu.edu.tw

export SSHPASS='SjU5W9ch56wYvhP'

cd /work1/gauss112

echo "Start uploading Folder 'Normal Stress PC' ..."
echo "Start Time: $(date)"

sshpass -e rsync -avz --progress 'Normal Stress PC' b09501028@research.chunyuke.com:~/

echo "Finished uploading: $(date)"
echo "End::end"