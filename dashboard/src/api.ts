import type {
  ApiError, Comparacion, Estimacion, Meta, MetricaEquipo, MetricaId, PuntoSituacion, Resumen, Serie,
} from './types/api';
import metaMock from './mocks/meta.json';
import errorMock from './mocks/error.json';
import resumenMuestra from './mocks/resumen_muestra_no_manda.json';
import resumenBlitz from './mocks/resumen_blitz_escondido.json';
import resumenRotacion from './mocks/resumen_rotacion_cascara.json';

// Mocks activos salvo que VITE_USE_MOCKS sea 'false'. Al integrar: VITE_USE_MOCKS=false.
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false';
// Prefijo opcional (vacío = ruta relativa, sin diagonal inicial).
const BASE = import.meta.env.VITE_API_URL ?? '';

export class ErrorApi extends Error {
  codigo: string;
  constructor(codigo: string, mensaje: string) {
    super(mensaje);
    this.codigo = codigo;
  }
}

const esperar = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Agrega ?error=1 a la URL de la página para ver el estado de error con mocks.
function forzarError(): boolean {
  return new URLSearchParams(window.location.search).has('error');
}

async function getJson<T>(ruta: string, mock: () => unknown): Promise<T> {
  if (USE_MOCKS) {
    await esperar(300);
    if (forzarError()) {
      const e = errorMock as ApiError;
      throw new ErrorApi(e.error.codigo, e.error.mensaje);
    }
    return mock() as T;
  }
  let resp: Response;
  try {
    resp = await fetch(BASE + ruta);
  } catch {
    throw new ErrorApi('red', 'No se pudo conectar con el servidor.');
  }
  const cuerpo = await resp.json().catch(() => null);
  if (!resp.ok) {
    const e = cuerpo as ApiError | null;
    throw new ErrorApi(e?.error?.codigo ?? 'interno', e?.error?.mensaje ?? 'Error inesperado del servidor.');
  }
  return cuerpo as T;
}

export const getMeta = () => getJson<Meta>('api/meta', () => metaMock);

const MOCK_RESUMEN: Record<MetricaId, unknown> = {
  muestra_no_manda: resumenMuestra,
  blitz_escondido: resumenBlitz,
  rotacion_cascara: resumenRotacion,
};

// Mock de /api/comparacion: se arma con los mocks de /api/resumen para que las cifras coincidan entre vistas.
function mockComparacion(equipo: string): Comparacion {
  const meta = metaMock as unknown as Meta;
  if (!meta.equipos.includes(equipo)) {
    throw new ErrorApi('parametro_invalido', `El equipo '${equipo}' no existe. Usa uno de /api/meta.`);
  }
  const metricas: MetricaEquipo[] = meta.metricas.map((m) => {
    const r = MOCK_RESUMEN[m.id] as Resumen;
    const fila = r.equipos.find((e) => e.equipo === equipo)!;
    return {
      metrica: m.id,
      etiqueta: m.etiqueta,
      equipo: fila.tasa,
      liga: r.liga,
      diferencia_vs_liga: fila.diferencia_vs_liga,
      posicion: fila.posicion,
      distinto_de_liga: fila.distinto_de_liga,
    };
  });
  const mas = metricas.filter((m) => m.distinto_de_liga && (m.diferencia_vs_liga.estimado ?? 0) > 0).length;
  return { equipo, titulo: `${equipo} disfraza más que la liga en ${mas} de 3 métricas`, metricas };
}

export const getComparacion = (equipo: string) =>
  getJson<Comparacion>(`api/comparacion?equipo=${encodeURIComponent(equipo)}`, () => mockComparacion(equipo));

// Mock de /api/serie: 7 situaciones en orden fijo, derivadas de las cifras de /api/resumen (inventadas).
const SITUACIONES = [
  '1er down',
  '2do y corto (1-3)',
  '2do y medio (4-7)',
  '2do y largo (8+)',
  '3ro/4to y corto (1-3)',
  '3ro/4to y medio (4-7)',
  '3ro/4to y largo (8+)',
];
const PARTE_N = [0.3, 0.08, 0.1, 0.1, 0.1, 0.14, 0.18];
const FACTOR = [0.6, 0.8, 0.9, 1.1, 1.0, 1.2, 1.5];
const FRASE: Record<string, string> = {
  muestra_no_manda: 'simula más el blitz',
  blitz_escondido: 'esconde más el blitz',
};

function est(p: number | null, n: number, metodo: Estimacion['metodo']): Estimacion {
  const nota = n < 30 ? 'pocos datos: interpretar con cautela' : null;
  if (p === null || n === 0) return { estimado: null, ic_inf: null, ic_sup: null, n: 0, metodo, nota };
  const se = Math.sqrt((p * (1 - p)) / n) * 1.3;
  const r = (x: number) => Math.round(x * 1000) / 1000;
  return { estimado: r(p), ic_inf: r(Math.max(0, p - 1.96 * se)), ic_sup: r(Math.min(1, p + 1.96 * se)), n, metodo, nota };
}

function mockSerie(equipo: string, metrica: string): Serie {
  const meta = metaMock as unknown as Meta;
  if (!meta.equipos.includes(equipo)) {
    throw new ErrorApi('parametro_invalido', `El equipo '${equipo}' no existe. Usa uno de /api/meta.`);
  }
  if (metrica !== 'muestra_no_manda' && metrica !== 'blitz_escondido') {
    throw new ErrorApi('parametro_invalido', `La métrica '${metrica}' no tiene serie por situación.`);
  }
  const r = MOCK_RESUMEN[metrica] as Resumen;
  const fila = r.equipos.find((e) => e.equipo === equipo)!;
  const pLiga = r.liga.estimado ?? 0;
  const pEq = fila.tasa.estimado ?? 0;
  const puntos: PuntoSituacion[] = SITUACIONES.map((situacion, i) => {
    const ligaSit = Math.min(0.9, pLiga * FACTOR[i]);
    const jitter = 1 + 0.25 * Math.sin(equipo.charCodeAt(0) * (i + 3) + equipo.charCodeAt(1));
    const eqSit = Math.min(0.9, ligaSit * (pEq / pLiga) * jitter);
    let nEq = Math.round(fila.tasa.n * PARTE_N[i]);
    if (equipo === 'NYJ' && i === 1) nEq = 0; // caso feo: situación sin jugadas del equipo
    return {
      situacion,
      equipo: est(nEq === 0 ? null : eqSit, nEq, 'cluster_bootstrap_partido'),
      liga: est(ligaSit, Math.round(r.liga.n * PARTE_N[i]), 'cluster_bootstrap_partido'),
    };
  });
  const pct = (x: number) => `${Math.round(x * 100)}%`;
  let mejor: PuntoSituacion | null = null;
  for (const p of puntos) {
    if (p.equipo.estimado === null || p.liga.estimado === null || p.equipo.n < 30) continue;
    if (!mejor || p.equipo.estimado - p.liga.estimado > (mejor.equipo.estimado ?? 0) - (mejor.liga.estimado ?? 0)) mejor = p;
  }
  const titulo = mejor
    ? `${equipo} ${FRASE[metrica]} en ${mejor.situacion}: ${pct(mejor.equipo.estimado!)} contra ${pct(mejor.liga.estimado!)} de la liga`
    : `${equipo}: sin situaciones con datos suficientes`;
  return {
    equipo,
    metrica,
    titulo,
    eje_x: 'Situación (down y yardas por ganar)',
    eje_y: '% de jugadas de pase',
    puntos,
  };
}

export const getSerie = (equipo: string, metrica: Serie['metrica']) =>
  getJson<Serie>(
    `api/serie?equipo=${encodeURIComponent(equipo)}&metrica=${encodeURIComponent(metrica)}`,
    () => mockSerie(equipo, metrica),
  );

export const getResumen = (metrica: MetricaId) =>
  getJson<Resumen>(`api/resumen?metrica=${encodeURIComponent(metrica)}`, () => MOCK_RESUMEN[metrica]);
