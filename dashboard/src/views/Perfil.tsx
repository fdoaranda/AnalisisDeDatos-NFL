import { useEffect, useMemo, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, ErrorBar, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { ErrorApi, getComparacion } from '../api';
import { etiquetaIC, textoDif, textoTasa } from '../format';
import type { Comparacion, CriterioDistinto, Estimacion, MetricaEquipo } from '../types/api';

const COLOR_EQUIPO = '#1d4ed8';
const COLOR_LIGA = '#64748b';

interface Fila {
  etiqueta: string;
  equipo: number | null; // %
  liga: number | null; // %
  errEquipo: [number, number];
  errLiga: [number, number];
}

function valor(e: Estimacion): number | null {
  return e.estimado === null ? null : e.estimado * 100;
}
function err(e: Estimacion): [number, number] {
  if (e.estimado === null || e.ic_inf === null || e.ic_sup === null) return [0, 0];
  return [(e.estimado - e.ic_inf) * 100, (e.ic_sup - e.estimado) * 100];
}
function aFila(m: MetricaEquipo): Fila {
  return {
    etiqueta: m.etiqueta,
    equipo: valor(m.equipo),
    liga: valor(m.liga),
    errEquipo: err(m.equipo),
    errLiga: err(m.liga),
  };
}

function veredicto(m: MetricaEquipo): { texto: string; clase: string } {
  if (m.diferencia_vs_liga.estimado === null) return { texto: 'Sin datos suficientes', clase: 'text-slate-700' };
  if (!m.distinto_de_liga) return { texto: 'No distinguible de la liga', clase: 'text-slate-700' };
  return m.diferencia_vs_liga.estimado > 0
    ? { texto: 'Disfraza más que la liga', clase: 'text-blue-800' }
    : { texto: 'Disfraza menos que la liga', clase: 'text-rose-800' };
}

export default function Perfil({ equipos, criterio, equipo, onEquipo }: {
  equipos: string[];
  criterio: CriterioDistinto;
  equipo: string;
  onEquipo: (e: string) => void;
}) {
  const ic = etiquetaIC(criterio);
  const [datos, setDatos] = useState<Comparacion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    setError(null);
    getComparacion(equipo)
      .then((d) => { if (vigente) setDatos(d); })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : 'No se pudieron cargar los datos.');
      })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [equipo]);

  const filas = useMemo(() => (datos ? datos.metricas.map(aFila) : []), [datos]);
  const maxY = useMemo(() => {
    if (!datos) return 100;
    const topes = datos.metricas.flatMap((m) => [m.equipo.ic_sup ?? 0, m.liga.ic_sup ?? 0]);
    return Math.min(100, Math.ceil(Math.max(...topes) * 20) * 5);
  }, [datos]);

  return (
    <section aria-labelledby="titulo-perfil">
      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="sel-equipo" className="font-semibold">Equipo:</label>
        <select
          id="sel-equipo"
          value={equipo}
          onChange={(e) => onEquipo(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2"
        >
          {equipos.map((e) => <option key={e} value={e}>{e}</option>)}
        </select>
      </div>

      {cargando && <p className="rounded-md bg-slate-100 p-6 text-center text-slate-700" role="status">Cargando datos…</p>}

      {!cargando && error && (
        <p className="rounded-md border border-red-300 bg-red-50 p-6 text-red-800" role="alert">
          No se pudo mostrar el perfil: {error}
        </p>
      )}

      {!cargando && !error && datos && (
        <>
          <h2 id="titulo-perfil" className="text-2xl font-bold leading-tight text-slate-900 md:text-3xl">{datos.titulo}</h2>

          <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">{datos.equipo} contra la liga, con {ic}</h3>
            <div className="mt-2 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={filas} margin={{ top: 10, right: 16, bottom: 5, left: 8 }}>
                  <CartesianGrid vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="etiqueta" tick={{ fontSize: 12 }} interval={0} />
                  <YAxis
                    domain={[0, maxY]}
                    tickFormatter={(v: number) => `${v}%`}
                    label={{ value: '% de jugadas', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    formatter={(v) => (typeof v === 'number' ? `${v.toFixed(1)}%` : 'sin datos')}
                    cursor={{ fill: '#f1f5f9' }}
                  />
                  <Legend />
                  <Bar dataKey="equipo" name={datos.equipo} fill={COLOR_EQUIPO} isAnimationActive={false}>
                    <ErrorBar dataKey="errEquipo" direction="y" stroke="#0f172a" strokeWidth={1.5} width={5} />
                  </Bar>
                  <Bar dataKey="liga" name="Liga" fill={COLOR_LIGA} isAnimationActive={false}>
                    <ErrorBar dataKey="errLiga" direction="y" stroke="#0f172a" strokeWidth={1.5} width={5} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-slate-600">
              Las líneas negras son el {ic}. {criterio.texto}
            </p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {datos.metricas.map((m) => {
              const v = veredicto(m);
              return (
                <article key={m.metrica} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                  <h3 className="font-semibold text-slate-900">{m.etiqueta}</h3>
                  <p className={`mt-1 font-semibold ${v.clase}`}>{v.texto}</p>
                  <dl className="mt-3 space-y-2 text-sm text-slate-800">
                    <div>
                      <dt className="font-medium text-slate-600">{datos.equipo}</dt>
                      <dd>{textoTasa(m.equipo, ic)}</dd>
                      {m.equipo.nota && <dd className="font-semibold text-amber-700">⚠ {m.equipo.nota}</dd>}
                    </div>
                    <div>
                      <dt className="font-medium text-slate-600">Liga</dt>
                      <dd>{textoTasa(m.liga, ic)}</dd>
                    </div>
                    <div>
                      <dt className="font-medium text-slate-600">Diferencia (ajustada)</dt>
                      <dd>{textoDif(m.diferencia_vs_liga, ic)}</dd>
                      {m.diferencia_vs_liga.nota && (
                        <dd className="text-xs text-slate-600">{m.diferencia_vs_liga.nota}</dd>
                      )}
                    </div>
                    <div>
                      <dt className="font-medium text-slate-600">Lugar entre los {equipos.length} equipos</dt>
                      <dd>{m.posicion}</dd>
                    </div>
                  </dl>
                </article>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
