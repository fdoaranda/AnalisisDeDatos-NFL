"""Esquemas pydantic v2 del contrato (docs/api.md)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MetricaId = Literal["muestra_no_manda", "blitz_escondido", "rotacion_cascara"]
MetodoEstimacion = Literal["cluster_bootstrap_partido", "estratificada_cluster_partido_bonferroni"]


class Estimacion(BaseModel):
    estimado: float | None = Field(description="Proporción 0-1 (o diferencia en proporción)")
    ic_inf: float | None
    ic_sup: float | None
    n: int = Field(description="Jugadas en el denominador")
    metodo: MetodoEstimacion
    nota: str | None = None


# ------------------------------------------------------------------ /api/meta
class MetricaInfo(BaseModel):
    id: MetricaId
    etiqueta: str
    descripcion: str


class Umbrales(BaseModel):
    linea_profundidad_yd: float
    linea_ancho_yd: float
    safety_profundo_yd: float


class CriterioDistinto(BaseModel):
    nivel_ic_mostrado: float = Field(description="Nivel de ic_inf/ic_sup que se muestran (0.95)")
    nivel_ic_decision: float = Field(description="Nivel del IC que decide distinto_de_liga (1 - 0.05/m)")
    n_comparaciones: int = Field(description="m = equipos comparados por métrica")
    metodo: Literal["Bonferroni"]
    texto: str = Field(description="Definición lista para mostrar")


class Meta(BaseModel):
    fuente: str
    temporada: int
    semanas: tuple[int, int]
    partidos: int
    jugadas: int
    equipos: list[str]
    metricas: list[MetricaInfo]
    umbrales: Umbrales
    limitaciones: list[str]
    criterio_distinto: CriterioDistinto
    generado: str


# ------------------------------------------------------------------ /api/resumen
class EquipoRanking(BaseModel):
    equipo: str
    posicion: int = Field(description="1 = el que más disfraza (orden por tasa encogida)")
    tasa: Estimacion
    diferencia_vs_liga: Estimacion
    distinto_de_liga: bool = Field(description="El IC por partido de la diferencia ajustada al nivel "
                                               "Bonferroni 1 - 0.05/m (m = equipos de la métrica) no incluye 0")
    q_bh: float | None = Field(None, description="Opcional y orientativo: Benjamini-Hochberg sobre un EE que "
                                                 "supone independencia entre jugadas. No usar como significancia.")
    q_bh_nota: str | None = None


class Resumen(BaseModel):
    metrica: MetricaId
    titulo: str
    liga: Estimacion
    equipos: list[EquipoRanking]


# ------------------------------------------------------------------ /api/comparacion
class MetricaEquipo(BaseModel):
    metrica: MetricaId
    etiqueta: str
    equipo: Estimacion
    liga: Estimacion
    diferencia_vs_liga: Estimacion
    posicion: int
    distinto_de_liga: bool


class Comparacion(BaseModel):
    equipo: str
    titulo: str
    metricas: list[MetricaEquipo]


# ------------------------------------------------------------------ /api/serie
class PuntoSituacion(BaseModel):
    situacion: str
    equipo: Estimacion
    liga: Estimacion


class Serie(BaseModel):
    equipo: str
    metrica: Literal["muestra_no_manda", "blitz_escondido"]
    titulo: str
    eje_x: str
    eje_y: str
    puntos: list[PuntoSituacion]


# ------------------------------------------------------------------ comunes
class Health(BaseModel):
    status: Literal["ok"]


class ErrorDetalle(BaseModel):
    codigo: Literal["parametro_invalido", "sin_datos", "interno"]
    mensaje: str


class ErrorRespuesta(BaseModel):
    error: ErrorDetalle
