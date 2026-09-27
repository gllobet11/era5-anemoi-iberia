#!/bin/bash -l
# GRIB → Zarr sobre los 36 meses: un solo job (reescritura atómica completa, D-011/D-015).
#SBATCH --job-name=era5-transform
#SBATCH --output=slurm/logs/transform_%j.out
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --acctg-freq=task=2   # muestreo de memoria cada 2 s (el defecto del clúster es 30 s)
#SBATCH --time=01:00:00
set -euo pipefail
CONFIG=${CONFIG:-configs/iberia.yaml}
module load era5   # en otro HPC: el módulo o entorno del sitio

echo "$(date -Is) job $SLURM_JOB_ID en $(hostname)"
python -m era5_pipeline.cli transform --config "$CONFIG"
