import { useEffect, useMemo, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, ErrorBar, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { ErrorApi, getSerie } from '../api';
import { etiquetaIC, textoTasa } from '../format';
import type { CriterioDistinto, Estimacion, MetricaInfo, Serie } from '../types/api';

const COLOR_EQUIPO = '#1d4ed8';
const COLOR_LIGA = '#64748b';

type MetricaFrente = Serie['metrica'];

interface Fila {
  situacion: string;
  equipo: number | null;
  liga: number | null;
  errEquipo: [number, number];
  errLiga: [number, number];
}

const valor = (e: Estimacion): number | null => (e.estimado === null ? null : e.estimado * 100);
function err(e: Estimacion): [number, number] {
  if (e.estimado === null || e.ic_inf === null || e.ic_sup === null) return [0, 0];
  return [(e.estimado - e.ic_inf) * 100, (e.ic_sup - e.estimado) * 100];
}

export default function Situacion({ metricas, equipos, criterio, equipo, onEquipo }: {
  metricas: MetricaInfo[];
  equipos: string[];
  criterio: CriterioDistinto;
  equipo: string;
  onEquipo: (e: string) => void;
}) {
  const ic = etiquetaIC(criterio);
  const frente = metricas.filter((m): m is MetricaInfo & { id: MetricaFrente } => m.id !== 'rotacion_cascara');
  const [metrica, setMetrica] = useState<MetricaFrente>(frente[0].id);
  const [datos, setDatos] = useState<Serie | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    setError(null);
    getSerie(equipo, metrica)
      .then((d) => { if (vigente) setDatos(d); })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : 'No se pudieron cargar los datos.');
      })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [equipo, metrica]);

  const filas: Fila[] = useMemo(
    () => (datos ? datos.puntos.map((p) => ({
      situacion: p.situacion,
      equipo: valor(p.equipo),
      liga: valor(p.liga),
      errEquipo: err(p.equipo),
      errLiga: err(p.liga),
    })) : []),
    [datos],
  );
  const maxY = useMemo(() => {
    if (!datos) return 100;
    const topes = datos.puntos.flatMap((p) => [p.equipo.ic_sup ?? 0, p.liga.ic_sup ?? 0]);
    return Math.min(100, Math.ceil(Math.max(...topes) * 20) * 5);
  }, [datos]);

  return (
    <section aria-labelledby="titulo-situacion">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label htmlFor="sel-equipo-s" className="font-semibold">Equipo:</label>
        <select
          id="sel-equipo-s"
          value={equipo}
          onChange={(e) => onEquipo(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2"
        >
          {equipos.map((e) => <option key={e} value={e}>{e}</option>)}
        </select>
        <div role="tablist" aria-label="Métrica" className="flex flex-wrap gap-2">
          {frente.map((m) => (
            <button
              key={m.id}
              role="tab"
              aria-selected={m.id === metrica}
              onClick={() => setMetrica(m.id)}
              className={`rounded-full border px-4 py-2 text-sm font-semibold ${
                m.id === metrica
                  ? 'border-blue-800 bg-blue-800 text-white'
                  : 'border-slate-300 bg-white text-slate-800 hover:bg-slate-100'
              }`}
            >
              {m.etiqueta}
            </button>
          ))}
        </div>
      </div>

      {cargando && <p className="rounded-md bg-slate-100 p-6 text-center text-slate-700" role="status">Cargando datos…</p>}

      {!cargando && error && (
        <p className="rounded-md border border-red-300 bg-red-50 p-6 text-red-800" role="alert">
          No se pudo mostrar la vista por situación: {error}
        </p>
      )}

      {!cargando && !error && datos && (
        <>
          <h2 id="titulo-situacion" className="text-2xl font-bold leading-tight text-slate-900 md:text-3xl">{datos.titulo}</h2>
          <p className="mt-1 text-slate-600">
            {metricas.find((m) => m.id === datos.metrica)?.descripcion}.
          </p>

          <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">{datos.equipo} contra la liga, por situación, con {ic}</h3>
            <div className="mt-2 h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={filas} margin={{ top: 10, right: 16, bottom: 30, left: 8 }}>
                  <CartesianGrid vertical={false} stroke="#e2e8f0" />
                  <XAxis
                    dataKey="situacion"
                    interval={0}
                    tick={{ fontSize: 11 }}
                    height={70}
                    angle={-25}
                    textAnchor="end"
                    label={{ value: datos.eje_x, position: 'insideBottom', offset: -25 }}
                  />
                  <YAxis
                    domain={[0, maxY]}
                    tickFormatter={(v: number) => `${v}%`}
                    label={{ value: datos.eje_y, angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    formatter={(v) => (typeof v === 'number' ? `${v.toFixed(1)}%` : 'sin datos')}
                    cursor={{ fill: '#f1f5f9' }}
                  />
                  <Legend verticalAlign="top" />
                  <Bar dataKey="equipo" name={datos.equipo} fill={COLOR_EQUIPO} isAnimationActive={false}>
                    <ErrorBar dataKey="errEquipo" direction="y" stroke="#0f172a" strokeWidth={1.5} width={4} />
                  </Bar>
                  <Bar dataKey="liga" name="Liga" fill={COLOR_LIGA} isAnimationActive={false}>
                    <ErrorBar dataKey="errLiga" direction="y" stroke="#0f172a" strokeWidth={1.5} width={4} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-slate-600">
              Las líneas negras son el {ic}. Una barra faltante significa que el equipo no tuvo jugadas en esa situación. Las barras con n pequeño tienen intervalos muy anchos.
            </p>
          </div>

          <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
            <table className="w-full min-w-[640px] text-left text-sm">
              <caption className="p-3 text-left font-semibold text-slate-900">Detalle por situación (cifra, {ic} y n)</caption>
              <thead className="bg-slate-100 text-slate-700">
                <tr>
                  <th className="px-3 py-2">Situación</th>
                  <th className="px-3 py-2">{datos.equipo}</th>
                  <th className="px-3 py-2">Liga</th>
                </tr>
              </thead>
              <tbody>
                {datos.puntos.map((p) => (
                  <tr key={p.situacion} className="border-t border-slate-200 align-top">
                    <td className="px-3 py-2 font-semibold">{p.situacion}</td>
                    <td className="px-3 py-2">
                      {textoTasa(p.equipo, ic)}
                      {p.equipo.nota && <span className="block font-semibold text-amber-700">⚠ {p.equipo.nota}</span>}
                    </td>
                    <td className="px-3 py-2">
                      {textoTasa(p.liga, ic)}
                      {p.liga.nota && <span className="block font-semibold text-amber-700">⚠ {p.liga.nota}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
