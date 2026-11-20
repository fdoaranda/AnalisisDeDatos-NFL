import { useEffect, useState } from 'react';
import { ErrorApi, getMeta } from './api';
import { entero } from './format';
import Hallazgo from './views/Hallazgo';
import Perfil from './views/Perfil';
import Situacion from './views/Situacion';
import type { Meta } from './types/api';

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [vista, setVista] = useState<'hallazgo' | 'perfil' | 'situacion'>('hallazgo');
  const [equipo, setEquipo] = useState('KC');

  useEffect(() => {
    getMeta()
      .then(setMeta)
      .catch((e: unknown) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar la información.'));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-4">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-800">Índice de disfraz defensivo</p>
          <p className="text-slate-600">¿Qué defensas de la NFL disfrazan más sus intenciones antes del snap?</p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">
        {error && <p className="rounded-md border border-red-300 bg-red-50 p-6 text-red-800" role="alert">{error}</p>}
        {!error && !meta && <p className="rounded-md bg-slate-100 p-6 text-center text-slate-700" role="status">Cargando…</p>}
        {meta && (
          <>
            <nav aria-label="Vistas" className="mb-5 flex gap-4 border-b border-slate-200">
              {([['hallazgo', 'Hallazgo'], ['perfil', 'Perfil del equipo'], ['situacion', 'Por situación']] as const).map(([id, nombre]) => (
                <button
                  key={id}
                  onClick={() => setVista(id)}
                  aria-current={vista === id ? 'page' : undefined}
                  className={`-mb-px border-b-2 px-1 pb-2 font-semibold ${
                    vista === id ? 'border-blue-800 text-blue-800' : 'border-transparent text-slate-700 hover:text-slate-900'
                  }`}
                >
                  {nombre}
                </button>
              ))}
            </nav>
            {vista === 'hallazgo' && <Hallazgo metricas={meta.metricas} criterio={meta.criterio_distinto} />}
            {vista === 'perfil' && (
              <Perfil equipos={meta.equipos} criterio={meta.criterio_distinto} equipo={equipo} onEquipo={setEquipo} />
            )}
            {vista === 'situacion' && (
              <Situacion
                metricas={meta.metricas}
                equipos={meta.equipos}
                criterio={meta.criterio_distinto}
                equipo={equipo}
                onEquipo={setEquipo}
              />
            )}
          </>
        )}
      </main>

      {meta && (
        <footer className="mx-auto max-w-5xl px-4 pb-10 text-sm text-slate-600">
          <p className="font-semibold">Fuente: {meta.fuente}</p>
          <p>{entero(meta.partidos)} partidos · {entero(meta.jugadas)} jugadas</p>
          <ul className="mt-2 list-disc pl-5">
            {meta.limitaciones.map((l) => <li key={l}>{l}</li>)}
          </ul>
        </footer>
      )}
    </div>
  );
}
