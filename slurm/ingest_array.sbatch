#!/bin/bash -l
# Ingesta ERA5: una tarea del job array por mes del periodo de la config.
# El rango (--array=0-N%P) lo pone submit.sh a partir de configs/, no se fija aquí.
#SBATCH --job-name=era5-ingest
#SBATCH --output=slurm/logs/ingest_%A_%a.out
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=12:00:00
set -euo pipefail
CONFIG=${CONFIG:-configs/iberia.yaml}
module load era5   # en otro HPC: el módulo o entorno del sitio

MONTH=$(python -m era5_pipeline.cli months --config "$CONFIG" | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
echo "$(date -Is) job ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} en $(hostname): mes $MONTH"
python -m era5_pipeline.cli ingest --config "$CONFIG" --month "$MONTH"
