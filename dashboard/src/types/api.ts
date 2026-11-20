// Copiado de docs/api.md. Si cambia el contrato, cambia aquí también.
export type MetricaId = 'muestra_no_manda' | 'blitz_escondido' | 'rotacion_cascara';
export type MetodoEstimacion = 'cluster_bootstrap_partido' | 'estratificada_cluster_partido_bonferroni';

export interface Estimacion {
  estimado: number | null;
  ic_inf: number | null;
  ic_sup: number | null;
  n: number;
  metodo: MetodoEstimacion;
  nota: string | null;
}

export interface ApiError {
  error: { codigo: 'parametro_invalido' | 'sin_datos' | 'interno'; mensaje: string };
}

export interface Health { status: 'ok' }

export interface MetricaInfo { id: MetricaId; etiqueta: string; descripcion: string }

export interface Meta {
  fuente: string;
  temporada: number;
  semanas: [number, number];
  partidos: number;
  jugadas: number;
  equipos: string[];
  metricas: MetricaInfo[];
  umbrales: { linea_profundidad_yd: number; linea_ancho_yd: number; safety_profundo_yd: number };
  limitaciones: string[];
  criterio_distinto: CriterioDistinto;
  generado: string;
}

// Definición de "distinto de la liga" (de /api/meta): el dashboard no escribe niveles ni textos a mano.
export interface CriterioDistinto {
  nivel_ic_mostrado: number;   // 0.95: nivel de ic_inf/ic_sup
  nivel_ic_decision: number;   // 1 - 0.05/m: decide distinto_de_liga
  n_comparaciones: number;     // m
  metodo: 'Bonferroni';
  texto: string;
}

export interface EquipoRanking {
  equipo: string;
  posicion: number;
  tasa: Estimacion;
  diferencia_vs_liga: Estimacion;
  distinto_de_liga: boolean;          // IC de decisión (Bonferroni) sin 0: el ÚNICO indicador de "distinto"
  q_bh?: number | null;               // orientativo; el dashboard no lo muestra
  q_bh_nota?: string | null;
}

export interface Resumen {
  metrica: MetricaId;
  titulo: string;
  liga: Estimacion;
  equipos: EquipoRanking[];
}

export interface MetricaEquipo {
  metrica: MetricaId;
  etiqueta: string;
  equipo: Estimacion;
  liga: Estimacion;
  diferencia_vs_liga: Estimacion;
  posicion: number;
  distinto_de_liga: boolean;
}

export interface Comparacion {
  equipo: string;
  titulo: string;
  metricas: MetricaEquipo[];
}

export interface PuntoSituacion {
  situacion: string;
  equipo: Estimacion;
  liga: Estimacion;
}

export interface Serie {
  equipo: string;
  metrica: Exclude<MetricaId, 'rotacion_cascara'>;
  titulo: string;
  eje_x: string;
  eje_y: string;
  puntos: PuntoSituacion[];
}
