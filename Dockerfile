# Imagen reproducible del pipeline: mismo environment.yml que local y CI (D-003)
FROM mambaorg/micromamba:2.3.2
# COPY antes de WORKDIR: así /app se crea con dueño $MAMBA_USER (pip escribe temporales ahí)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml pyproject.toml /app/
WORKDIR /app
COPY --chown=$MAMBA_USER:$MAMBA_USER src ./src
RUN micromamba install -y -n base -f environment.yml && micromamba clean -afy
COPY --chown=$MAMBA_USER:$MAMBA_USER configs ./configs
COPY --chown=$MAMBA_USER:$MAMBA_USER tests ./tests
# el entrypoint de la imagen base activa el entorno; datos y ~/.cdsapirc se montan en ejecución
CMD ["python", "-m", "era5_pipeline.cli", "--help"]
