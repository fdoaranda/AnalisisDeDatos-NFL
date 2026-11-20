import { useEffect, useMemo, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, ErrorBar, ReferenceArea, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { ErrorApi, getResumen } from '../api';
import { entero, etiquetaIC, pct, pocosDatos, textoDif, textoTasa } from '../format';
import type { CriterioDistinto, EquipoRanking, MetricaId, MetricaInfo, Resumen } from '../types/api';

const COLOR_DISTINTO = '#1d4ed8'; // azul: distinto_de_liga (criterio de /api/meta)
const COLOR_NORMAL = '#64748b'; // gris: no distinguible de la liga
const COLOR_POCOS = '#d97706'; // ámbar: la API marca "pocos datos" en la nota
const COLOR_LIGA = '#dc2626';

interface Fila {
  equipo: string;
  valor: number; // % (0-100)
  error: [number, number]; // [abajo, arriba] en puntos de %
  fila: EquipoRanking;
}

function colorDe(e: EquipoRanking): string {
  if (pocosDatos(e.tasa)) return COLOR_POCOS;
  return e.distinto_de_liga ? COLOR_DISTINTO : COLOR_NORMAL;
}

function aFila(e: EquipoRanking): Fila {
  const { estimado, ic_inf, ic_sup } = e.tasa;
  if (estimado === null || ic_inf === null || ic_sup === null) {
    return { equipo: e.equipo, valor: 0, error: [0, 0], fila: e };
  }
  return {
    equipo: e.equipo,
    valor: estimado * 100,
    error: [(estimado - ic_inf) * 100, (ic_sup - estimado) * 100],
    fila: e,
  };
}

function Tip({ active, payload, total, ic }: {
  active?: boolean;
  payload?: ReadonlyArray<{ payload: Fila }>;
  total: number;
  ic: string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const e = payload[0].payload.fila;
  return (
    <div className="max-w-xs rounded-md border border-slate-300 bg-white p-3 text-sm shadow">
      <p className="font-bold">{e.equipo} · lugar {e.posicion} de {total}</p>
      <p>Tasa: {textoTasa(e.tasa, ic)}</p>
      <p>Diferencia vs. liga: {textoDif(e.diferencia_vs_liga, ic)}</p>
      <p>{e.distinto_de_liga ? 'Distinto de la liga' : 'No distinguible de la liga'}</p>
      {e.tasa.nota && <p className="mt-1 font-semibold text-amber-700">⚠ {e.tasa.nota}</p>}
    </div>
  );
}

function Kpi({ titulo, valor, detalle }: { titulo: string; valor: string; detalle: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-600">{titulo}</p>
      <p className="mt-1 text-3xl font-bold text-slate-900">{valor}</p>
      <p className="mt-1 text-sm text-slate-600">{detalle}</p>
    </div>
  );
}

export default function Hallazgo({ metricas, criterio }: { metricas: MetricaInfo[]; criterio: CriterioDistinto }) {
  const ic = etiquetaIC(criterio);
  const [metrica, setMetrica] = useState<MetricaId>(metricas[0].id);
  const [datos, setDatos] = useState<Resumen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    setError(null);
    getResumen(metrica)
      .then((d) => { if (vigente) setDatos(d); })
      .catch((e: unknown) => {
        if (vigente) setError(e instanceof ErrorApi ? e.message : 'No se pudieron cargar los datos.');
      })
      .finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [metrica]);

  const info = metricas.find((m) => m.id === metrica);
  const filas = useMemo(() => (datos ? datos.equipos.map(aFila) : []), [datos]);
  const maxX = useMemo(() => {
    if (!datos) return 100;
    const topes = datos.equipos.map((e) => e.tasa.ic_sup ?? 0);
    return Math.min(100, Math.ceil(Math.max(...topes, datos.liga.ic_sup ?? 0) * 20) * 5);
  }, [datos]);

  return (
    <section aria-labelledby="titulo-hallazgo">
      <div role="tablist" aria-label="Métrica" className="mb-4 flex flex-wrap gap-2">
        {metricas.map((m) => (
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

      {cargando && <p className="rounded-md bg-slate-100 p-6 text-center text-slate-700" role="status">Cargando datos…</p>}

      {!cargando && error && (
        <p className="rounded-md border border-red-300 bg-red-50 p-6 text-red-800" role="alert">
          No se pudo mostrar el hallazgo: {error}
        </p>
      )}

      {!cargando && !error && datos && (
        <>
          <h2 id="titulo-hallazgo" className="text-2xl font-bold leading-tight text-slate-900 md:text-3xl">
            {datos.titulo}
          </h2>
          {info && <p className="mt-1 text-slate-600">Cómo se mide: {info.descripcion}.</p>}

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <Kpi
              titulo={`Primero del ranking: ${datos.equipos[0].equipo}`}
              valor={pct(datos.equipos[0].tasa.estimado)}
              detalle={`${ic}: ${pct(datos.equipos[0].tasa.ic_inf)}–${pct(datos.equipos[0].tasa.ic_sup)} · n = ${entero(datos.equipos[0].tasa.n)}`}
            />
            <Kpi
              titulo="Promedio de la liga"
              valor={pct(datos.liga.estimado)}
              detalle={`${ic}: ${pct(datos.liga.ic_inf)}–${pct(datos.liga.ic_sup)} · n = ${entero(datos.liga.n)}`}
            />
            <Kpi
              titulo="Equipos distintos de la liga"
              valor={`${datos.equipos.filter((e) => e.distinto_de_liga).length} de ${datos.equipos.length}`}
              detalle={criterio.texto}
            />
          </div>

          <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">Ranking de los {datos.equipos.length} equipos, con {ic}</h3>
            <ul className="my-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-700">
              <li><span className="mr-1 inline-block h-3 w-3 align-middle" style={{ background: COLOR_DISTINTO }} />Distinto de la liga</li>
              <li><span className="mr-1 inline-block h-3 w-3 align-middle" style={{ background: COLOR_NORMAL }} />No distinguible de la liga</li>
              <li><span className="mr-1 inline-block h-3 w-3 align-middle" style={{ background: COLOR_POCOS }} />Pocos datos</li>
              <li><span className="mr-1 inline-block h-3 w-0 border-l-2 border-dashed align-middle" style={{ borderColor: COLOR_LIGA }} />Liga (franja = su IC)</li>
            </ul>
            <div style={{ height: filas.length * 24 + 60 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={filas} margin={{ top: 5, right: 24, bottom: 25, left: 8 }}>
                  <CartesianGrid horizontal={false} stroke="#e2e8f0" />
                  <XAxis
                    type="number"
                    domain={[0, maxX]}
                    tickFormatter={(v: number) => `${v}%`}
                    label={{ value: '% de jugadas de pase', position: 'insideBottom', offset: -15 }}
                  />
                  <YAxis type="category" dataKey="equipo" width={44} interval={0} tick={{ fontSize: 12 }} />
                  <Tooltip content={<Tip total={datos.equipos.length} ic={ic} />} cursor={{ fill: '#f1f5f9' }} />
                  {datos.liga.ic_inf !== null && datos.liga.ic_sup !== null && (
                    <ReferenceArea x1={datos.liga.ic_inf * 100} x2={datos.liga.ic_sup * 100} fill={COLOR_LIGA} fillOpacity={0.15} />
                  )}
                  {datos.liga.estimado !== null && (
                    <ReferenceLine x={datos.liga.estimado * 100} stroke={COLOR_LIGA} strokeDasharray="5 4" strokeWidth={2} />
                  )}
                  <Bar dataKey="valor" isAnimationActive={false}>
                    {filas.map((f) => (
                      <Cell key={f.equipo} fill={colorDe(f.fila)} />
                    ))}
                    <ErrorBar dataKey="error" direction="x" stroke="#0f172a" strokeWidth={1.5} width={5} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-slate-600">
              Las barras de error son el {ic} de cada equipo; la franja roja es el {ic} de la liga. {criterio.texto}
            </p>
          </div>

          <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
            <table className="w-full min-w-[720px] text-left text-sm">
              <caption className="p-3 text-left font-semibold text-slate-900">Detalle por equipo (cifra, {ic} y n)</caption>
              <thead className="bg-slate-100 text-slate-700">
                <tr>
                  <th className="px-3 py-2">#</th>
                  <th className="px-3 py-2">Equipo</th>
                  <th className="px-3 py-2">Tasa</th>
                  <th className="px-3 py-2">Diferencia vs. liga (ajustada)</th>
                  <th className="px-3 py-2">¿Distinto de la liga?</th>
                </tr>
              </thead>
              <tbody>
                {datos.equipos.map((e) => (
                  <tr key={e.equipo} className="border-t border-slate-200 align-top">
                    <td className="px-3 py-2">{e.posicion}</td>
                    <td className="px-3 py-2 font-semibold">{e.equipo}</td>
                    <td className="px-3 py-2">
                      {textoTasa(e.tasa, ic)}
                      {e.tasa.nota && <span className="block font-semibold text-amber-700">⚠ {e.tasa.nota}</span>}
                    </td>
                    <td className="px-3 py-2">
                      {textoDif(e.diferencia_vs_liga, ic)}
                      {e.diferencia_vs_liga.nota && (
                        <span className="block text-xs text-slate-600">{e.diferencia_vs_liga.nota}</span>
                      )}
                    </td>
                    <td className="px-3 py-2">{e.distinto_de_liga ? 'Sí' : 'No'}</td>
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
