"""
Retos al toolkit: simulaciones/casos con respuesta CONOCIDA.
Ejecutar desde la carpeta tools/:  python test_retos.py
Un reto que falla = el agente podría inducir a error. Todo se reporta, no se esconde.
"""
import math
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
import stats_toolkit as st

try:
    import scipy.stats as sps  # solo como referencia independiente si existe
except Exception:  # pragma: no cover
    sps = None

R = []


def check(name, ok, detail=""):
    R.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'} | {name} | {detail}", flush=True)


def missing(fn):
    if not hasattr(st, fn):
        check(f"[falta función] {fn}", False, "el agente la menciona o la necesita pero no existe")
        return True
    return False


T0 = time.time()

# ---- R1: cobertura bootstrap iid (normal vs sesgada) ----------------------------------
rng = np.random.default_rng(11)


def coverage(gen, true, nsim=500, n=30, nboot=400):
    hit = 0
    for i in range(nsim):
        r = st.bootstrap_ci(gen(n), n_boot=nboot, seed=i)
        hit += r["ic_inf"] <= true <= r["ic_sup"]
    return hit / nsim


c = coverage(lambda n: rng.normal(0, 1, n), 0.0)
check("R1a bootstrap iid normal n=30 cubre ~95%", 0.92 <= c <= 0.98, f"cobertura={c:.3f}")
def cov_m(method, nsim=800, n=30, nboot=500):
    hit = 0
    for i in range(nsim):
        r = st.bootstrap_ci(rng.lognormal(0, 1, n), n_boot=nboot, seed=i, method=method)
        hit += r["ic_inf"] <= math.exp(0.5) <= r["ic_sup"]
    return hit / nsim


c_def, c_pct = cov_m("auto"), cov_m("percentile")
check("R1b media de datos MUY sesgados n=30: IC por defecto (bootstrap-t) cubre >=89%", c_def >= 0.89,
      f"defecto={c_def:.3f} | percentil={c_pct:.3f} (ningún bootstrap llega a 95% aquí: limitación real)")

# ---- R2: datos agrupados: bootstrap por filas vs por grupos ---------------------------
G, M = 20, 20
hit_naive = hit_cluster = 0
nsim = 300
has_cluster = hasattr(st, "cluster_bootstrap_ci")
for i in range(nsim):
    g = np.repeat(np.arange(G), M)
    v = rng.normal(0, 1, G)[g] + rng.normal(0, 1, G * M)
    r = st.bootstrap_ci(v, n_boot=300, seed=i)
    hit_naive += r["ic_inf"] <= 0 <= r["ic_sup"]
    if has_cluster:
        rc = st.cluster_bootstrap_ci(v, g, n_boot=300, seed=i)
        hit_cluster += rc["ic_inf"] <= 0 <= rc["ic_sup"]
check("R2a bootstrap por FILAS con datos agrupados (debe fallar: demuestra el riesgo)",
      hit_naive / nsim < 0.7, f"cobertura={hit_naive/nsim:.3f} (nominal 0.95)")
if not missing("cluster_bootstrap_ci"):
    check("R2b cluster_bootstrap_ci cubre >=88% con 20 grupos", hit_cluster / nsim >= 0.88,
          f"cobertura={hit_cluster/nsim:.3f}")

# ---- R3: Wilson ------------------------------------------------------------------------
w0 = st.wilson_interval(0, 10)
check("R3a Wilson 0/10 -> límite sup = z²/(n+z²)", abs(w0["ic_sup"] - 3.8416 / 13.8416) < 1e-3
      and w0["ic_inf"] < 1e-9, f"{w0['ic_inf']:.4f}-{w0['ic_sup']:.4f}")
n, p = 20, 0.05
hits_w = hits_wald = 0
xs = rng.binomial(n, p, 4000)
for x in xs:
    wi = st.wilson_interval(int(x), n)
    hits_w += wi["ic_inf"] <= p <= wi["ic_sup"]
    ph = x / n
    se = math.sqrt(ph * (1 - ph) / n)
    hits_wald += (ph - 1.96 * se) <= p <= (ph + 1.96 * se)
check("R3b Wilson supera claramente al Wald con p=0.05,n=20", hits_w / 4000 > hits_wald / 4000 + 0.05,
      f"Wilson={hits_w/4000:.3f} Wald={hits_wald/4000:.3f}")

# ---- R4: permutación: error tipo I y potencia -----------------------------------------
rej = 0
rej_t = 0
pw = 0
pw_t = 0
nsim = 300
for i in range(nsim):
    a = rng.normal(0, 1, 15)
    b = rng.normal(0, 1, 15)
    rej += st.permutation_test(a, b, n_perm=300, seed=i)["p_valor"] < 0.05
    b2 = rng.normal(0.8, 1, 15)
    pw += st.permutation_test(a, b2, n_perm=300, seed=i)["p_valor"] < 0.05
    if sps is not None:
        rej_t += sps.ttest_ind(a, b).pvalue < 0.05
        pw_t += sps.ttest_ind(a, b2).pvalue < 0.05
check("R4a permutación bajo H0 rechaza ~5%", 0.025 <= rej / nsim <= 0.08, f"tasa={rej/nsim:.3f}")
if sps is not None:
    check("R4b potencia permutación ≈ t-test (d=0.8,n=15)", abs(pw - pw_t) / nsim < 0.08,
          f"perm={pw/nsim:.3f} t={pw_t/nsim:.3f}")

# ---- R5: Benjamini-Hochberg controla FDR; p crudo no ---------------------------------
fdp_bh = []
fdp_raw = []
for rep in range(150):
    m0, m1 = 900, 100
    z = np.concatenate([rng.normal(0, 1, m0), rng.normal(3, 1, m1)])
    pv = np.array([math.erfc(abs(v) / math.sqrt(2)) for v in z])
    truth_null = np.arange(m0 + m1) < m0
    bh = st.benjamini_hochberg(pv, q=0.05)
    sig = bh["significativo"].to_numpy()
    fdp_bh.append((sig & truth_null).sum() / max(sig.sum(), 1))
    sig_r = pv < 0.05
    fdp_raw.append((sig_r & truth_null).sum() / max(sig_r.sum(), 1))
check("R5a BH: FDR promedio <= ~5%", np.mean(fdp_bh) <= 0.065, f"FDP BH={np.mean(fdp_bh):.3f}")
check("R5b p<0.05 sin corrección: FDR alto (demuestra por qué corregir)", np.mean(fdp_raw) > 0.2,
      f"FDP crudo={np.mean(fdp_raw):.3f}")
try:
    out = st.benjamini_hochberg([0.001, np.nan, 0.04, 0.5])
    ok = out["p_ajustado_BH"].notna().sum() == 3 and abs(out["p_ajustado_BH"].iloc[0] - 0.003) < 1e-9
    check("R5c BH con NaN en los p-valores no corrompe el resto", ok, out["p_ajustado_BH"].round(4).tolist())
except Exception as e:
    check("R5c BH con NaN", False, repr(e))

# ---- R6: OLS vs referencia, cobertura con n pequeño -----------------------------------
x = rng.normal(size=40)
yv = 1 + 2 * x + rng.normal(size=40)
res = st.ols(pd.DataFrame({"x": x}), pd.Series(yv))
slope, intercept = np.polyfit(x, yv, 1)
check("R6a OLS coincide con np.polyfit", abs(res.loc["x", "coef"] - slope) < 1e-9
      and abs(res.loc["const", "coef"] - intercept) < 1e-9)
if sps is not None:
    lr = sps.linregress(x, yv)
    check("R6b OLS error estándar coincide con scipy.linregress", abs(res.loc["x", "ee"] - lr.stderr) < 1e-9,
          f"ours={res.loc['x','ee']:.6f} scipy={lr.stderr:.6f}")
hit = 0
nsim = 2000
for i in range(nsim):
    xs_ = rng.normal(size=12)
    ys_ = 1 + 2 * xs_ + rng.normal(size=12)
    r = st.ols(pd.DataFrame({"x": xs_}), pd.Series(ys_))
    hit += r.loc["x", "ic95_inf"] <= 2 <= r.loc["x", "ic95_sup"]
check("R6c IC95 de pendiente con n=12 cubre ~95% (z=1.96 debería subcubrir)", 0.93 <= hit / nsim <= 0.97,
      f"cobertura={hit/nsim:.3f}")

# ---- R6d: OLS con errores correlacionados dentro de grupos ----------------------------
Gc, Mc = 25, 10
hit_n = hit_c = 0
nsim = 800
has_cr = "cluster" in st.ols.__code__.co_varnames
for i in range(nsim):
    g = np.repeat(np.arange(Gc), Mc)
    xv = rng.normal(0, 1, Gc)[g] + rng.normal(0, 1, Gc * Mc)
    e = rng.normal(0, 1, Gc)[g] + rng.normal(0, 1, Gc * Mc)
    yv_ = 1 + 2 * xv + e
    X = pd.DataFrame({"x": xv})
    r = st.ols(X, pd.Series(yv_))
    hit_n += r.loc["x", "ic95_inf"] <= 2 <= r.loc["x", "ic95_sup"]
    if has_cr:
        rc = st.ols(X, pd.Series(yv_), cluster=pd.Series(g))
        hit_c += rc.loc["x", "ic95_inf"] <= 2 <= rc.loc["x", "ic95_sup"]
check("R6d OLS clásico con datos agrupados subcubre (demuestra el riesgo)", hit_n / nsim < 0.88,
      f"cobertura={hit_n/nsim:.3f}")
check("R6e OLS con errores agrupados (cluster=) cubre >=90%", has_cr and hit_c / nsim >= 0.90,
      f"cobertura={(hit_c/nsim) if has_cr else float('nan'):.3f}" if has_cr else "no existe la opción cluster=")

# ---- R7: encogimiento ------------------------------------------------------------------
for label, a_, b_ in [("heterogéneo", 20, 20), ("casi homogéneo", 500, 500)]:
    ns = pd.Series(rng.integers(3, 300, 60))
    tp = rng.beta(a_, b_, 60)
    ss = pd.Series(rng.binomial(ns, tp))
    sh = st.shrink_rates(ss, ns)
    er, es = np.mean((sh["tasa_cruda"] - tp) ** 2), np.mean((sh["tasa_encogida"] - tp) ** 2)
    check(f"R7 encogimiento ({label}) no empeora al estimador crudo", es <= er * 1.02, f"crudo={er:.5f} encogido={es:.5f}")
try:
    sh0 = st.shrink_rates(pd.Series([0] * 5 + [3, 5, 8, 9, 10] * 3), pd.Series([0] * 5 + [10] * 15))
    check("R7c grupos con n=0 no producen NaN en la tasa encogida", sh0["tasa_encogida"].notna().all())
except Exception as e:
    check("R7c grupos con n=0", False, repr(e))

# ---- R8: fuga de información por grupos -------------------------------------------------
Gn, Mn = 60, 10
g = np.repeat(np.arange(Gn), Mn)
fingerprint = rng.normal(0, 1, Gn)[g]
y = rng.normal(0, 1, Gn)[g] + rng.normal(0, 0.5, Gn * Mn)


def r2_1nn(train, test):
    d = np.abs(fingerprint[test][:, None] - fingerprint[train][None, :])
    pred = y[train][d.argmin(axis=1)]
    return 1 - ((y[test] - pred) ** 2).sum() / ((y[test] - y[test].mean()) ** 2).sum()


idx = rng.permutation(len(y))
tr, te = idx[: int(0.8 * len(y))], idx[int(0.8 * len(y)):]
r2_rand = r2_1nn(tr, te)
r2_grp = np.mean([r2_1nn(a, b) for a, b in st.group_kfold_indices(pd.Series(g), k=5, seed=1)])
check("R8 partición aleatoria infla el R² por fuga (brecha > 1 punto de R²); GroupKFold lo desinfla", r2_rand - r2_grp > 1.0 and r2_rand > 0.3 and r2_grp < 0.2,
      f"R2 aleatorio={r2_rand:.2f} | R2 por grupos={r2_grp:.2f}")

# ---- R9: calibración: entradas inválidas -----------------------------------------------
try:
    st.calibration_table([1.2, 0.5, 0.3], [1, 0, 1], bins=2)
    check("R9 calibration_table rechaza probabilidades fuera de [0,1]", False, "las descarta en silencio")
except ValueError:
    check("R9 calibration_table rechaza probabilidades fuera de [0,1]", True)

# ---- R10: casos borde -------------------------------------------------------------------
try:
    r = st.bootstrap_ci([5.0] * 10)
    check("R10a bootstrap con datos constantes no revienta", r["ic_inf"] == r["ic_sup"] == 5.0)
except Exception as e:
    check("R10a bootstrap constante", False, repr(e))
d = st.cohens_d([1, 1, 1], [1, 1, 1])
check("R10b cohens_d con varianza 0 devuelve NaN (no error ni inf)", isinstance(d, float) and math.isnan(d))
try:
    rep = st.audit_dataframe(pd.DataFrame({"b": [True, False, True], "f": [np.nan] * 3,
                                           "t": pd.to_datetime(["2024-01-01"] * 3), "s": ["a", "b", None]}))
    check("R10c audit_dataframe con bool/NaN/fecha/texto", rep["filas"] == 3 and "f" in rep["columnas_constantes"])
except Exception as e:
    check("R10c audit_dataframe tipos mixtos", False, repr(e))
try:
    st.audit_dataframe(pd.DataFrame())
    check("R10d audit_dataframe con DataFrame vacío", True)
except Exception as e:
    check("R10d audit_dataframe con DataFrame vacío", False, repr(e))

# ---- R11: Simpson y confusión ------------------------------------------------------------
if not missing("stratified_comparison"):
    n_e = n_h = 10000
    ctx = np.array(["facil"] * n_e + ["dificil"] * n_h)
    tprob = np.where(ctx == "facil", 0.1, 0.9)
    tr_ = (rng.uniform(size=len(ctx)) < tprob).astype(int)
    base = np.where(ctx == "facil", 0.90, 0.30)
    out = (rng.uniform(size=len(ctx)) < base + 0.05 * tr_).astype(int)
    df = pd.DataFrame({"B": tr_, "exito": out, "ctx": ctx})
    res = st.stratified_comparison(df, "B", "exito", ["ctx"])
    check("R11a Simpson: la diferencia ingenua es NEGATIVA (engaña)", res["diferencia_ingenua"] < -0.2,
          f"ingenua={res['diferencia_ingenua']:.3f}")
    check("R11b estratificada recupera ≈ +0.05 y su IC excluye la ingenua", abs(res["diferencia_ajustada"] - 0.05) < 0.03
          and res["ic95_inf"] < 0.05 < res["ic95_sup"], f"ajustada={res['diferencia_ajustada']:.3f} "
          f"IC=({res['ic95_inf']:.3f},{res['ic95_sup']:.3f})")
    # positividad: un estrato donde solo hay una opción
    df2 = pd.concat([df, pd.DataFrame({"B": [1] * 200, "exito": [1] * 200, "ctx": ["solo_B"] * 200})], ignore_index=True)
    res2 = st.stratified_comparison(df2, "B", "exito", ["ctx"])
    check("R11c detecta falta de solapamiento y excluye el estrato", "solo_B" in str(res2["estratos_excluidos"]),
          f"excluidos={res2['estratos_excluidos']}")

# ---- R12: Anscombe -----------------------------------------------------------------------
ax = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
ays = [[8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68],
       [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74],
       [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]]
x4 = [8] * 7 + [19] + [8] * 3
y4 = [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]
sets = [(ax, ays[0]), (ax, ays[1]), (ax, ays[2]), (x4, y4)]
cors = [np.corrcoef(a, b)[0, 1] for a, b in sets]
check("R12a datos de Anscombe bien cargados (r≈0.816 en los 4)", all(abs(c - 0.816) < 0.002 for c in cors),
      [round(c, 3) for c in cors])
sp = float(np.corrcoef(pd.Series(ax).rank().to_numpy(), pd.Series(ays[0]).rank().to_numpy())[0, 1])
check("R12b Spearman por rangos (sin scipy) válido", not math.isnan(sp) and 0.7 < sp < 0.9, f"rho={sp:.3f}")
if not missing("diagnose_relationship"):
    flags = [st.diagnose_relationship(a, b)["alertas"] for a, b in sets]
    check("R12c set1 (lineal sano) sin alertas", flags[0] == [], flags[0])
    check("R12d set2 (curva) alerta de curvatura", any("curvatura" in f for f in flags[1]), flags[1])
    check("R12e set3 (outlier) alerta de atípico", any("atípico" in f for f in flags[2]), flags[2])
    check("R12f set4 (un punto manda) alerta de apalancamiento", any("apalancamiento" in f for f in flags[3]), flags[3])

# ---- R13: valor crítico t exacto --------------------------------------------------------------
if not missing("t_crit"):
    table = {1: 12.706, 2: 4.303, 5: 2.571, 10: 2.228, 20: 2.086, 30: 2.042, 120: 1.980}
    errs = {k: abs(st.t_crit(k) - v) for k, v in table.items()}
    check("R13 t_crit coincide con tablas t(0.975)", max(errs.values()) < 0.002, {k: round(v, 4) for k, v in errs.items()})

fails = [n for n, ok in R if not ok]
print(f"\nRESUMEN: {len(R)-len(fails)}/{len(R)} pasan en {time.time()-T0:.0f}s")
for n in fails:
    print("  FALLA:", n)
sys.exit(1 if fails else 0)
