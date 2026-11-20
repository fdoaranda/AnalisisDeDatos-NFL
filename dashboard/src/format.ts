import type { CriterioDistinto, Estimacion } from './types/api';

export const pct = (x: number | null, dec = 1): string =>
  x === null ? 'sin datos' : `${(x * 100).toFixed(dec)}%`;

// Diferencia en puntos porcentuales, con signo.
export const pp = (x: number | null, dec = 1): string =>
  x === null ? 'sin datos' : `${x >= 0 ? '+' : '−'}${Math.abs(x * 100).toFixed(dec)} pp`;

export const entero = (n: number): string => n.toLocaleString('es-MX');

// Etiqueta del intervalo que se muestra, a partir de /api/meta (p. ej. "IC 95%").
export const etiquetaIC = (c: CriterioDistinto): string => `IC ${pct(c.nivel_ic_mostrado, 0)}`;

// "31.0% (IC 95%: 23.5%–38.5%, n = 245)"
export function textoTasa(e: Estimacion, ic: string): string {
  if (e.estimado === null || e.ic_inf === null || e.ic_sup === null) return `sin datos (n = ${entero(e.n)})`;
  return `${pct(e.estimado)} (${ic}: ${pct(e.ic_inf)}–${pct(e.ic_sup)}, n = ${entero(e.n)})`;
}

// "+11.5 pp (IC 95%: +4.0 a +19.0 pp, n = 8,498)"
export function textoDif(e: Estimacion, ic: string): string {
  if (e.estimado === null || e.ic_inf === null || e.ic_sup === null) return `sin datos (n = ${entero(e.n)})`;
  return `${pp(e.estimado)} (${ic}: ${pp(e.ic_inf)} a ${pp(e.ic_sup)}, n = ${entero(e.n)})`;
}

// El backend marca así las cifras con n chico (docs/api.md, campo `nota`).
export const pocosDatos = (e: Estimacion): boolean => (e.nota ?? '').includes('pocos datos');
