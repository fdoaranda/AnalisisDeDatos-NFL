health: {'status': 'ok'}
meta: NFL Big Data Bowl: tracking + PFF, temporada 2021, semanas 1-8 | partidos=122 jugadas=8498 equipos=32
criterio: Distinto de la liga = el IC de decisión de 99.84 % por partido (Bonferroni, 32 equipos) de la diferencia ajustada no incluye el 0. Las barras muestran el IC de 95 %.
umbrales: {'linea_profundidad_yd': 2.0, 'linea_ancho_yd': 8.0, 'safety_profundo_yd': 10.0}

## rotacion_cascara
titulo: Con 2 safeties profundos al snap, MIA juega cobertura de un safety en 65 % de las jugadas; la liga, en 36 %
liga: 35.6 % [IC 32.8–38.5] n=3293
  distinto ARRIBA #2 MIA: tasa 65.0 % [IC 54.1–77.3] n=80 | dif +34.9 pp [IC +17.7 a +48.8] n=2205
  distinto ABAJO #30 TB: tasa 11.6 % [IC 8.8–14.9] n=95 | dif -25.1 pp [IC -32.2 a -17.6] n=2384
  distinto ABAJO #31 HOU: tasa 7.7 % [IC 3.9–13.6] n=104 | dif -31.0 pp [IC -35.5 a -25.9] n=2273
  distinto ABAJO #32 MIN: tasa 2.5 % [IC 0.0–6.2] n=80 | dif -34.7 pp [IC -39.3 a -28.7] n=2384
  MIA #2: tasa 65.0 % [IC 54.1–77.3] n=80 | dif +34.9 pp [IC +17.7 a +48.8] n=2205 | distinto=True
  SF #7: tasa 47.4 % [IC 17.0–65.3] n=78 | dif +9.2 pp [IC -18.5 a +26.6] n=2200 | distinto=False
  CLE #8: tasa 46.6 % [IC 36.2–60.2] n=133 | dif +13.8 pp [IC +4.6 a +25.1] n=2368 | distinto=False
  NYJ #25: tasa 23.1 % [IC 9.0–39.6] n=52 | dif -12.3 pp [IC -27.6 a +1.5] n=1773 | distinto=False

## muestra_no_manda
titulo: Ningún equipo muestra blitz sin mandarlo claramente más que la liga (19 %)
liga: 19.5 % [IC 18.2–20.7] n=8498
  distinto ABAJO #26 LV: tasa 13.9 % [IC 11.8–15.9] n=273 | dif -4.3 pp [IC -7.7 a -2.5] n=7324
  distinto ABAJO #27 NYJ: tasa 11.0 % [IC 7.3–14.6] n=246 | dif -10.7 pp [IC -14.5 a -7.7] n=6983
  distinto ABAJO #31 CLE: tasa 7.7 % [IC 5.4–10.2] n=259 | dif -13.5 pp [IC -17.1 a -9.8] n=7420
  distinto ABAJO #32 SF: tasa 5.7 % [IC 3.8–8.7] n=228 | dif -12.7 pp [IC -15.6 a -7.1] n=6673
  MIA #1: tasa 32.9 % [IC 25.2–40.4] n=295 | dif +14.1 pp [IC +5.2 a +23.4] n=7113 | distinto=False
  SF #32: tasa 5.7 % [IC 3.8–8.7] n=228 | dif -12.7 pp [IC -15.6 a -7.1] n=6673 | distinto=True
  CLE #31: tasa 7.7 % [IC 5.4–10.2] n=259 | dif -13.5 pp [IC -17.1 a -9.8] n=7420 | distinto=True
  NYJ #27: tasa 11.0 % [IC 7.3–14.6] n=246 | dif -10.7 pp [IC -14.5 a -7.7] n=6983 | distinto=True

## blitz_escondido
titulo: Ningún equipo esconde el blitz claramente más que la liga (9 %)
liga: 8.8 % [IC 8.1–9.6] n=8498
  distinto ABAJO #30 BUF: tasa 4.4 % [IC 2.0–7.2] n=248 | dif -4.1 pp [IC -7.6 a -1.4] n=6622
  MIA #26: tasa 6.8 % [IC 4.0–9.3] n=295 | dif -2.5 pp [IC -5.4 a +0.1] n=7113 | distinto=False
  SF #4: tasa 13.2 % [IC 7.7–20.4] n=228 | dif +5.8 pp [IC -0.9 a +13.2] n=6673 | distinto=False
  CLE #5: tasa 12.7 % [IC 8.8–16.6] n=259 | dif +4.0 pp [IC -1.8 a +11.2] n=7420 | distinto=False
  NYJ #3: tasa 13.8 % [IC 9.4–18.9] n=246 | dif +5.2 pp [IC +1.6 a +9.5] n=6983 | distinto=False

## comparacion MIA
titulo: MIA disfraza claramente más que la liga en 1 de 3 métricas
  muestra_no_manda: equipo 32.9 % [IC 25.2–40.4] n=295 | liga 19.5 % [IC 18.2–20.7] n=8498 | distinto=False
  blitz_escondido: equipo 6.8 % [IC 4.0–9.3] n=295 | liga 8.8 % [IC 8.1–9.6] n=8498 | distinto=False
  rotacion_cascara: equipo 65.0 % [IC 54.1–77.3] n=80 | liga 35.6 % [IC 32.8–38.5] n=3293 | distinto=True

OK
