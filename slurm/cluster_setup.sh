#!/bin/bash
# Prepara el clúster simulado como lo tendría un HPC. Idempotente; ejecutar en el host tras `compose up`.
#  1. Usuario `era5` con el UID/GID del host en login y nodos (los ficheros de data/ no son de root).
#  2. Contabilidad de memoria (jobacct_gather/linux) → MaxRSS en sacct/sstat.
#  3. Entorno micromamba en /gpfs/apps/envs/era5 desde environment.yml + modulefile Lmod `era5`.
set -euo pipefail
PROJ=/gpfs/projects/era5-anemoi-iberia
APPS=/gpfs/apps
WORKERS=$(docker ps -a --format '{{.Names}}' | grep -- '-cpu-worker-' | sort)
NODES="slurmctld $WORKERS"
# el entrypoint de slurm-docker-cluster puede tumbar un worker si arranca antes de que el DNS de
# Docker resuelva a los demás (carrera al recrearlos a la vez): arrancarlos de nuevo basta
docker start $WORKERS >/dev/null

for c in $NODES; do
  docker exec "$c" bash -c "getent group $(id -g) >/dev/null || groupadd -g $(id -g) era5
    id -u era5 &>/dev/null || useradd -u $(id -u) -g $(id -g) -M -d /home/era5 era5
    chown era5: /home/era5"
done

# /etc/slurm es un volumen compartido por todos los contenedores: basta editarlo en el login.
if ! docker exec slurmctld grep -q '^JobAcctGatherType=jobacct_gather/linux' /etc/slurm/slurm.conf; then
  docker exec slurmctld sed -i 's|^#\?JobAcctGatherType=.*|JobAcctGatherType=jobacct_gather/linux|' /etc/slurm/slurm.conf
  # cambiar el plugin de gather exige reiniciar los demonios, no basta `scontrol reconfigure`
  docker restart slurmctld >/dev/null
  until docker exec slurmctld scontrol ping &>/dev/null; do sleep 2; done
  docker restart $WORKERS >/dev/null
fi

# Entorno: lo instala el usuario del proyecto (el `pip install -e .` escribe egg-info en el repo).
docker exec slurmctld chown era5: "$APPS"
docker exec -u era5 -w "$PROJ" slurmctld bash -c "
  set -e
  if [ ! -x $APPS/envs/era5/bin/python ]; then
    mkdir -p $APPS/bin
    curl -sSL https://micro.mamba.pm/api/micromamba/linux-64/2.3.2 | tar -xj -C $APPS bin/micromamba
    MAMBA_ROOT_PREFIX=$APPS/mamba $APPS/bin/micromamba create -y -q -p $APPS/envs/era5 -f environment.yml
    MAMBA_ROOT_PREFIX=$APPS/mamba $APPS/bin/micromamba clean -afy -q
  fi"

# /opt/modulefiles es otro volumen compartido y ya está en el MODULEPATH de la imagen.
docker exec -i slurmctld bash -c "mkdir -p /opt/modulefiles/era5 && cat > /opt/modulefiles/era5/1.0.lua" <<LUA
whatis("era5-anemoi-iberia: entorno micromamba de environment.yml (Python, eccodes, CDO, NCO, anemoi)")
prepend_path("PATH", "$APPS/envs/era5/bin")
LUA

N_WORKERS=$(echo "$WORKERS" | wc -w)
until [ "$(docker exec slurmctld sinfo -h -N -t idle -o %N | wc -l)" -eq "$N_WORKERS" ]; do sleep 2; done
docker exec -u era5 -w "$PROJ" slurmctld bash -lc 'module load era5 && srun -N'"$N_WORKERS"' bash -lc "module load era5 && echo \$(hostname): \$(python -c \"import era5_pipeline\" && cdo --version 2>&1 | head -1)"'
