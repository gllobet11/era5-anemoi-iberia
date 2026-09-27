#!/bin/bash -l
# Encadena ingest (job array por mes) → transform → qc con --dependency=afterok.
# Uso, desde la raíz del repo en el nodo de login:  slurm/submit.sh
set -euo pipefail
export CONFIG=${CONFIG:-configs/iberia.yaml}
MAX_PARALLEL=${MAX_PARALLEL:-4}   # tareas de ingest simultáneas: la cola del CDS manda (D-009)

module load era5
N=$(python -m era5_pipeline.cli months --config "$CONFIG" | wc -l)
mkdir -p slurm/logs   # Slurm no crea el directorio de --output: sin él el job falla sin log

ING=$(sbatch --parsable --array="0-$((N - 1))%$MAX_PARALLEL" slurm/ingest_array.sbatch)
TRF=$(sbatch --parsable --dependency="afterok:$ING" slurm/transform.sbatch)
QC=$(sbatch --parsable --dependency="afterok:$TRF" slurm/qc.sbatch)
echo "ingest=$ING (array 0-$((N - 1))) transform=$TRF qc=$QC"
