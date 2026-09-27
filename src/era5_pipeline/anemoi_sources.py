"""Fuente anemoi `grib-hourly-accum`: `grib` que sí atiende a los intervalos de `accumulate`.

En anemoi-datasets 0.5.44 `GribSource` no implementa `execute_intervals`: la llamada cae en
`execute_valid_dates` con solo los `valid_time` objetivo (T), así que `accumulate` recibe 1 de las
6 horas de `tp` y falla con "Accumulator not complete". Aquí se piden los `valid_time` de todos los
intervalos horarios que el covering necesita (T-5h..T). Registrada por entry point (pyproject).
"""

from anemoi.datasets.create.arguments import ValidDates
from anemoi.datasets.create.sources.grib import GribSource


class GribHourlyAccumSource(GribSource):
    def execute_intervals(self, argument):
        return self.execute_valid_dates(ValidDates(sorted({i.max for i in argument.intervals})))
