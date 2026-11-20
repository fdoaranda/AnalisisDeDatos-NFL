"""API del Índice de disfraz defensivo (contrato: docs/api.md).

Desarrollo, desde la raíz del proyecto:
    .venv\\Scripts\\uvicorn backend.main:app --reload --port 8000
Swagger: http://localhost:8000/docs
"""
from __future__ import annotations

import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import analisis
from .modelos import Comparacion, ErrorRespuesta, Health, Meta, Resumen, Serie

log = logging.getLogger("uvicorn.error")


class JSONUtf8(JSONResponse):
    """JSON con charset explícito para que ningún cliente adivine la codificación."""
    media_type = "application/json; charset=utf-8"


class ErrorApi(Exception):
    def __init__(self, status: int, codigo: str, mensaje: str):
        self.status, self.codigo, self.mensaje = status, codigo, mensaje


def _error(status: int, codigo: str, mensaje: str) -> JSONResponse:
    return JSONUtf8(status_code=status, content={"error": {"codigo": codigo, "mensaje": mensaje}})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga y calcula una sola vez al arrancar; las peticiones leen de memoria."""
    st = app.state
    st.error_carga, st.resumenes, st.series, st.lock_series = None, {}, {}, threading.Lock()
    t0 = time.time()
    try:
        df = analisis.cargar_jugadas()
        st.jugadas = df
        st.meta = Meta.model_validate(analisis.calcular_meta(df))
        crudos = {m: analisis.calcular_resumen(df, m) for m in analisis.METRICAS}
        st.resumenes = {m: Resumen.model_validate(r) for m, r in crudos.items()}
        st.comparaciones = {e: Comparacion.model_validate(analisis.calcular_comparacion(crudos, e))
                            for e in st.meta.equipos}
        st.liga_situacion = {m: analisis.liga_por_situacion(df, m) for m in analisis.METRICAS_SERIE}
        log.info("Datos listos: %d jugadas, %.1f s", len(df), time.time() - t0)
    except Exception as e:  # la app arranca igual; los endpoints de datos responden 500 con el motivo
        st.error_carga = str(e)
        log.exception("No se pudieron cargar los datos")
    yield


app = FastAPI(title="Índice de disfraz defensivo", version="0.1.0", lifespan=lifespan,
              default_response_class=JSONUtf8,
              description="Lo que la defensa muestra al snap contra lo que juega. NFL 2021, semanas 1-8.")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["GET"], allow_headers=["*"])

ERRORES = {400: {"model": ErrorRespuesta}, 404: {"model": ErrorRespuesta}, 500: {"model": ErrorRespuesta}}


@app.exception_handler(ErrorApi)
async def _manejar_error_api(_: Request, e: ErrorApi):
    return _error(e.status, e.codigo, e.mensaje)


@app.exception_handler(RequestValidationError)
async def _manejar_validacion(_: Request, e: RequestValidationError):
    campos = ", ".join(str(err["loc"][-1]) for err in e.errors())
    return _error(400, "parametro_invalido", f"Parámetro inválido o faltante: {campos}.")


@app.exception_handler(StarletteHTTPException)
async def _manejar_http(request: Request, e: StarletteHTTPException):
    if e.status_code == 404:
        return _error(404, "sin_datos", f"La ruta {request.url.path} no existe.")
    return _error(e.status_code, "parametro_invalido", str(e.detail))


@app.exception_handler(Exception)
async def _manejar_interno(_: Request, e: Exception):
    log.exception("Error interno", exc_info=e)
    return _error(500, "interno", "Error interno del servidor.")


# ----------------------------------------------------------------------------- validaciones
def _datos_listos(request: Request) -> None:
    if request.app.state.error_carga is not None:
        raise ErrorApi(500, "interno", "Los datos precalculados no están disponibles. "
                                       "Genera backend/datos/jugadas_disfraz.csv con tools/precalcular_jugadas.py.")


def _validar_metrica(metrica: str | None, validas: list[str]) -> str:
    lista = ", ".join(validas)
    if not metrica:
        raise ErrorApi(400, "parametro_invalido", f"Falta el parámetro 'metrica'. Usa una de: {lista}.")
    if metrica not in validas:
        raise ErrorApi(400, "parametro_invalido", f"La métrica '{metrica}' no existe aquí. Usa una de: {lista}.")
    return metrica


def _validar_equipo(request: Request, equipo: str | None) -> str:
    if not equipo:
        raise ErrorApi(400, "parametro_invalido", "Falta el parámetro 'equipo' (abreviatura, por ejemplo KC).")
    eq = equipo.strip().upper()
    if eq not in request.app.state.meta.equipos:
        raise ErrorApi(400, "parametro_invalido", f"El equipo '{equipo}' no existe. Usa uno de /api/meta.")
    return eq


# ----------------------------------------------------------------------------- endpoints
@app.get("/health", response_model=Health, summary="Estado del servidor")
def health() -> Health:
    return Health(status="ok")


@app.get("/api/meta", response_model=Meta, responses=ERRORES,
         summary="Qué datos hay: temporada, equipos, métricas, umbrales y limitaciones")
def meta(request: Request) -> Meta:
    _datos_listos(request)
    return request.app.state.meta


@app.get("/api/resumen", response_model=Resumen, responses=ERRORES,
         summary="Ranking de los 32 equipos en una métrica de disfraz (Vista 1)")
def resumen(request: Request,
            metrica: str | None = Query(None, description="muestra_no_manda | blitz_escondido | rotacion_cascara")
            ) -> Resumen:
    _datos_listos(request)
    return request.app.state.resumenes[_validar_metrica(metrica, list(analisis.METRICAS))]


@app.get("/api/comparacion", response_model=Comparacion, responses=ERRORES,
         summary="Perfil de un equipo en las 3 métricas contra la liga (Vista 2)")
def comparacion(request: Request,
                equipo: str | None = Query(None, description="Abreviatura del equipo, por ejemplo KC")
                ) -> Comparacion:
    _datos_listos(request)
    return request.app.state.comparaciones[_validar_equipo(request, equipo)]


@app.get("/api/serie", response_model=Serie, responses=ERRORES,
         summary="Equipo contra la liga por situación de down y yardas por ganar (Vista 3)")
def serie(request: Request,
          equipo: str | None = Query(None, description="Abreviatura del equipo, por ejemplo KC"),
          metrica: str | None = Query(None, description="muestra_no_manda | blitz_escondido")
          ) -> Serie:
    _datos_listos(request)
    eq = _validar_equipo(request, equipo)
    m = _validar_metrica(metrica, analisis.METRICAS_SERIE)
    st = request.app.state
    clave = (eq, m)
    with st.lock_series:
        if clave not in st.series:
            st.series[clave] = Serie.model_validate(
                analisis.calcular_serie(st.jugadas, st.liga_situacion[m], eq, m))
        return st.series[clave]
