#!/bin/bash -l
# QC del Zarr final. Sale con código 1 si algún check crítico falla → job FAILED.
#SBATCH --job-name=era5-qc
#SBATCH --output=slurm/logs/qc_%j.out
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:15:00
set -euo pipefail
CONFIG=${CONFIG:-configs/iberia.yaml}
ZARR=${ZARR:-data/zarr/iberia.zarr}
module load era5   # en otro HPC: el módulo o entorno del sitio

echo "$(date -Is) job $SLURM_JOB_ID en $(hostname)"
python -m era5_pipeline.cli qc --zarr "$ZARR" --config "$CONFIG"
