import type { Estimacion } from './types/api';

export const pct = (x: number | null, dec = 1): string =>
  x === null ? 'sin datos' : `${(x * 100).toFixed(dec)}%`;

// Diferencia en puntos porcentuales, con signo.
export const pp = (x: number | null, dec = 1): string =>
  x === null ? 'sin datos' : `${x >= 0 ? '+' : '−'}${Math.abs(x * 100).toFixed(dec)} pp`;

export const entero = (n: number): string => n.toLocaleString('es-MX');

// "31.0% (IC 95%: 23.5%–38.5%, n = 245)"
export function textoTasa(e: Estimacion): string {
  if (e.estimado === null || e.ic_inf === null || e.ic_sup === null) return `sin datos (n = ${entero(e.n)})`;
  return `${pct(e.estimado)} (IC 95%: ${pct(e.ic_inf)}–${pct(e.ic_sup)}, n = ${entero(e.n)})`;
}

// "+11.5 pp (IC 95%: +4.0 a +19.0 pp, n = 8,498)"
export function textoDif(e: Estimacion): string {
  if (e.estimado === null || e.ic_inf === null || e.ic_sup === null) return `sin datos (n = ${entero(e.n)})`;
  return `${pp(e.estimado)} (IC 95%: ${pp(e.ic_inf)} a ${pp(e.ic_sup)}, n = ${entero(e.n)})`;
}
