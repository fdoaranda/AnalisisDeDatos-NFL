"""
stats_toolkit.py - Herramientas estadísticas con SOLO numpy + pandas.

Por qué: el stack del hackathon fija pandas 2.2.3 y numpy 2.1.3 (no garantiza scipy,
statsmodels ni scikit-learn). Todo aquí funciona con esas dos librerías.

Uso: copiar a backend/analytics/ y hacer `from stats_toolkit import *`.
Todas las funciones con azar reciben `seed` para que los resultados sean reproducibles.
"""
from __future__ import annotations

import math
from typing import Callable, Iterable

import numpy as np
import pandas as pd

__all__ = [
    "audit_dataframe", "bootstrap_ci", "cluster_bootstrap_ci", "permutation_test", "cohens_d",
    "wilson_interval", "shrink_rates", "benjamini_hochberg", "ols", "t_crit",
    "stratified_comparison", "diagnose_relationship",
    "group_kfold_indices", "time_split", "calibration_table", "brier_score",
]


# --------------------------------------------------------------------------- #
# 0. Distribuciones auxiliares exactas (sin scipy)
# --------------------------------------------------------------------------- #
def _norm_cdf(z: float) -> float:
    return 0.5 * math.erfc(-z / math.sqrt(2))


def _norm_ppf(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _betacf(a: float, b: float, x: float, maxit: int = 300, eps: float = 3e-14) -> float:
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, maxit + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = d if abs(d) > tiny else tiny
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        d = 1.0 / d; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = d if abs(d) > tiny else tiny
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        d = 1.0 / d; de = d * c; h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Función beta incompleta regularizada I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def _t_cdf(t: float, df: float) -> float:
    p = 0.5 * _betai(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - p if t > 0 else p


def t_crit(df: float, level: float = 0.95) -> float:
    """Valor crítico bilateral de la t de Student (exacto, sin scipy). t_crit(10) = 2.228."""
    if df < 1:
        raise ValueError("df debe ser >= 1")
    target = 0.5 + level / 2.0
    lo, hi = 0.0, 1e5
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _t_cdf(mid, df) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# --------------------------------------------------------------------------- #
# 1. Auditoría de calidad (NO modifica el DataFrame)
# --------------------------------------------------------------------------- #
def audit_dataframe(df: pd.DataFrame, key: list[str] | None = None) -> dict:
    """Reporte de calidad: forma, nulos, constantes, duplicados, rangos, cardinalidad.

    key: columnas que deberían identificar una fila de forma única (ej. ['gameId','playId']).
    Devuelve un dict; imprime nada. El analista debe LEER el resultado antes de limpiar.
    """
    rep: dict = {"filas": int(len(df)), "columnas": int(df.shape[1])}
    cols = []
    for c in df.columns:
        s = df[c]
        info = {
            "columna": c,
            "dtype": str(s.dtype),
            "nulos": int(s.isna().sum()),
            "pct_nulos": round(float(s.isna().mean() * 100), 2),
            "unicos": int(s.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(s):
            sn = s.dropna()
            if len(sn):
                info.update(min=float(sn.min()), p50=float(sn.median()), max=float(sn.max()),
                            media=float(sn.mean()), std=float(sn.std(ddof=1)) if len(sn) > 1 else 0.0)
        info["constante"] = info["unicos"] <= 1
        cols.append(info)
    rep["detalle_columnas"] = cols
    rep["filas_duplicadas_exactas"] = int(df.duplicated().sum())
    if key:
        rep["llave"] = key
        rep["duplicados_en_llave"] = int(df.duplicated(subset=key).sum())
    rep["columnas_constantes"] = [c["columna"] for c in cols if c["constante"]]
    rep["columnas_con_>20%_nulos"] = [c["columna"] for c in cols if c["pct_nulos"] > 20]
    return rep


# --------------------------------------------------------------------------- #
# 2. Incertidumbre: bootstrap, permutación, proporciones
# --------------------------------------------------------------------------- #
def bootstrap_ci(x: Iterable[float], stat: Callable[[np.ndarray], float] = np.mean,
                 n_boot: int = 5000, alpha: float = 0.05, seed: int = 0,
                 method: str = "auto") -> dict:
    """Intervalo de confianza bootstrap para cualquier estadístico.

    method="auto" (por defecto): bootstrap-t (studentizado) si stat es np.mean, percentil en
    los demás casos. "percentile": simple. "bca": corrige sesgo/asimetría. "t": solo la media.
    Evidencia (1500 simulaciones, datos lognormales muy sesgados, media, cobertura nominal 95%):
    n=30 -> percentil 0.877, BCa 0.883, bootstrap-t 0.920; n=100 -> 0.911, 0.912, 0.932.
    Con datos muy sesgados y n pequeño NINGÚN IC bootstrap llega a 95%: dilo en el reporte.
    OJO: asume observaciones INDEPENDIENTES. Si hay agrupación (varias filas por partido,
    jugador, sesión) usa cluster_bootstrap_ci(); con filas agrupadas este IC es demasiado
    estrecho (en pruebas: cobertura real ~40-47% en vez de 95%).
    """
    x = np.asarray(list(x), dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        raise ValueError("Se necesitan al menos 2 observaciones válidas.")
    if method not in ("auto", "bca", "percentile", "t"):
        raise ValueError("method debe ser 'auto', 'bca', 'percentile' o 't'")
    if method == "auto":
        method = "t" if stat is np.mean else "percentile"
    if method == "t" and stat is not np.mean:
        raise ValueError("method='t' solo aplica a la media (stat=np.mean).")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    est = float(stat(x))
    if method == "t":
        n = len(x)
        se = float(x.std(ddof=1) / math.sqrt(n))
        xb = x[idx]
        s_b = xb.std(axis=1, ddof=1) / math.sqrt(n)
        with np.errstate(divide="ignore", invalid="ignore"):
            tstar = (xb.mean(axis=1) - est) / np.where(s_b > 0, s_b, np.nan)
        if se == 0 or np.isnan(tstar).all():
            return {"estimado": est, "ic_inf": est, "ic_sup": est, "n": int(n), "n_boot": n_boot,
                    "nivel": 1 - alpha, "metodo": "t"}
        q_hi_t, q_lo_t = np.nanquantile(tstar, [1 - alpha / 2, alpha / 2])
        return {"estimado": est, "ic_inf": float(est - q_hi_t * se), "ic_sup": float(est - q_lo_t * se),
                "n": int(n), "n_boot": n_boot, "nivel": 1 - alpha, "metodo": "t"}
    boots = np.array([stat(x[i]) for i in idx])
    q_lo, q_hi = alpha / 2, 1 - alpha / 2
    if method == "bca":
        prop = (np.sum(boots < est) + 0.5 * np.sum(boots == est)) / n_boot
        prop = min(max(prop, 0.5 / n_boot), 1 - 0.5 / n_boot)
        z0 = _norm_ppf(prop)
        jack = np.array([stat(np.delete(x, i)) for i in range(len(x))])
        d = jack.mean() - jack
        denom = 6.0 * (np.sum(d ** 2) ** 1.5)
        a = float(np.sum(d ** 3) / denom) if denom > 0 else 0.0

        def adj(zq: float) -> float:
            den = 1.0 - a * (z0 + zq)
            if den <= 1e-9:
                return 0.999 if zq > 0 else 0.001
            return min(max(_norm_cdf(z0 + (z0 + zq) / den), 1e-4), 1 - 1e-4)

        q_lo, q_hi = adj(_norm_ppf(alpha / 2)), adj(_norm_ppf(1 - alpha / 2))
    lo, hi = np.quantile(boots, [q_lo, q_hi])
    return {"estimado": est, "ic_inf": float(lo), "ic_sup": float(hi),
            "n": int(len(x)), "n_boot": n_boot, "nivel": 1 - alpha, "metodo": method}


def cluster_bootstrap_ci(values: Iterable[float], groups: Iterable, stat: Callable[[np.ndarray], float] = np.mean,
                         n_boot: int = 2000, alpha: float = 0.05, seed: int = 0) -> dict:
    """Bootstrap por GRUPOS: remuestrea grupos completos (partidos, jugadores, sesiones...).

    Úsalo siempre que varias filas pertenezcan a la misma unidad (no son independientes).
    El n efectivo es el número de grupos. Método percentil. Con <20 grupos el IC suele
    quedar algo corto: el resultado trae una advertencia.
    """
    v = pd.Series(list(values), dtype=float).reset_index(drop=True)
    g = pd.Series(list(groups)).reset_index(drop=True)
    if len(v) != len(g):
        raise ValueError("values y groups deben tener la misma longitud.")
    ok = v.notna() & g.notna()
    v, g = v[ok].to_numpy(), g[ok]
    codes, uniq = pd.factorize(g)
    n_g = len(uniq)
    if n_g < 2:
        raise ValueError("Se necesitan al menos 2 grupos.")
    parts = [v[codes == k] for k in range(n_g)]
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, n_g, n_g)
        boots[b] = stat(np.concatenate([parts[k] for k in pick]))
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    out = {"estimado": float(stat(v)), "ic_inf": float(lo), "ic_sup": float(hi),
           "n_filas": int(len(v)), "n_grupos": int(n_g), "n_boot": n_boot, "nivel": 1 - alpha}
    if n_g < 20:
        out["advertencia"] = f"solo {n_g} grupos: el IC puede ser demasiado estrecho; interprétalo con cautela"
    return out


def permutation_test(a: Iterable[float], b: Iterable[float],
                     stat: Callable[[np.ndarray, np.ndarray], float] | None = None,
                     n_perm: int = 10000, seed: int = 0) -> dict:
    """Prueba de permutación de dos muestras (bilateral). Por defecto: diferencia de medias.

    p-valor con corrección (k+1)/(n+1) para que nunca sea exactamente 0.
    """
    a = np.asarray(list(a), dtype=float); a = a[~np.isnan(a)]
    b = np.asarray(list(b), dtype=float); b = b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2:
        raise ValueError("Cada grupo necesita al menos 2 observaciones válidas.")
    stat = stat or (lambda u, v: float(np.mean(u) - np.mean(v)))
    obs = stat(a, b)
    pool = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        if abs(stat(pool[:len(a)], pool[len(a):])) >= abs(obs) - 1e-12:
            count += 1
    p = (count + 1) / (n_perm + 1)
    return {"diferencia_observada": float(obs), "p_valor": float(p),
            "n_a": int(len(a)), "n_b": int(len(b)), "n_perm": n_perm}


def cohens_d(a: Iterable[float], b: Iterable[float]) -> float:
    """Tamaño de efecto estandarizado (desviación agrupada). Reporta SIEMPRE junto al p-valor."""
    a = np.asarray(list(a), dtype=float); a = a[~np.isnan(a)]
    b = np.asarray(list(b), dtype=float); b = b[~np.isnan(b)]
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        raise ValueError("Cada grupo necesita al menos 2 observaciones válidas.")
    sp = math.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return float((a.mean() - b.mean()) / sp) if sp > 0 else float("nan")


def wilson_interval(successes: int, n: int, z: float = 1.96) -> dict:
    """IC de Wilson para una proporción (mucho mejor que la normal con n pequeño o p extremo)."""
    if n <= 0:
        raise ValueError("n debe ser > 0")
    p = successes / n
    denom = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / denom
    mitad = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return {"proporcion": p, "ic_inf": centro - mitad, "ic_sup": centro + mitad, "n": n}


def shrink_rates(successes: pd.Series, n: pd.Series, prior_strength: float | None = None) -> pd.DataFrame:
    """Encogimiento empírico tipo Beta-Binomial (Bayes empírico) para tasas con n desigual.

    Evita rankings engañosos donde 3/3 = 100% supera a 90/100. Estima una media global y,
    si no se da prior_strength, una fuerza del prior por método de momentos (simple y
    transparente; no es el único método). Devuelve tasa cruda y tasa encogida.
    """
    s = successes.astype(float); m = n.astype(float)
    ok = m > 0
    raw = s / m.where(ok)
    mu = float(s[ok].sum() / m[ok].sum())
    if prior_strength is None:
        if int(ok.sum()) < 10:
            raise ValueError("Con menos de 10 grupos el prior estimado es inestable: "
                             "pasa prior_strength explícito (p. ej. 10-30) y justifícalo.")
        var_obs = float(np.average((raw[ok] - mu) ** 2, weights=m[ok]))
        var_bin = mu * (1 - mu) * float(np.average(1 / m[ok], weights=m[ok]))
        extra = max(var_obs - var_bin, 1e-9)           # varianza real entre grupos
        prior_strength = min(max(mu * (1 - mu) / extra - 1, 1.0), 10_000.0)
    a0, b0 = mu * prior_strength, (1 - mu) * prior_strength
    shrunk = (s + a0) / (m + a0 + b0)
    return pd.DataFrame({"n": m, "tasa_cruda": raw, "tasa_encogida": shrunk,
                         "media_global": mu, "fuerza_prior": prior_strength})


def benjamini_hochberg(pvalues: Iterable[float], q: float = 0.05) -> pd.DataFrame:
    """Control de tasa de falsos descubrimientos (FDR). Úsalo si pruebas muchas hipótesis."""
    p = np.asarray(list(pvalues), dtype=float)
    valid = ~np.isnan(p)
    pv = p[valid]
    m = len(pv)
    out = np.full(len(p), np.nan)
    if m:
        order = np.argsort(pv)
        ranked = pv[order]
        adj = np.minimum.accumulate((ranked * m / np.arange(1, m + 1))[::-1])[::-1]
        adj = np.minimum(adj, 1.0)
        tmp = np.empty(m); tmp[order] = adj
        out[valid] = tmp
    return pd.DataFrame({"p": p, "p_ajustado_BH": out, "significativo": out <= q})


# --------------------------------------------------------------------------- #
# 3. Regresión lineal (OLS) con errores estándar clásicos
# --------------------------------------------------------------------------- #
def ols(X: pd.DataFrame, y: pd.Series, add_const: bool = True,
        cluster: pd.Series | None = None) -> pd.DataFrame:
    """OLS con numpy. Devuelve coeficiente, error estándar, t e IC95 con la t de Student exacta.

    cluster=<Serie con el id de grupo>: errores estándar robustos por grupo (CR1) y t con
    G-1 grados de libertad. ÚSALO cuando varias filas comparten partido/jugador/sesión;
    sin él los EE son demasiado pequeños (en pruebas, cobertura ~74% en vez de 95%).
    No sustituye a statsmodels (sin errores HC para heterocedasticidad sin grupos).
    """
    Xd = X.copy()
    if add_const:
        Xd.insert(0, "const", 1.0)
    mask = Xd.notna().all(axis=1) & y.notna()
    cl_all = None
    if cluster is not None:
        if len(cluster) != len(X):
            raise ValueError("cluster debe tener la misma longitud que X.")
        cl_all = pd.Series(np.asarray(cluster), index=X.index)  # alineación por posición
        mask = mask & cl_all.notna()
    A = Xd.loc[mask].to_numpy(dtype=float)
    b = y.loc[mask].to_numpy(dtype=float)
    n, k = A.shape
    if n <= k:
        raise ValueError("Menos observaciones que parámetros.")
    beta, *_ = np.linalg.lstsq(A, b, rcond=None)
    resid = b - A @ beta
    bread = np.linalg.pinv(A.T @ A)
    if cl_all is None:
        cov = float(resid @ resid / (n - k)) * bread
        df = n - k
    else:
        codes, uniq = pd.factorize(cl_all.loc[mask].to_numpy())
        n_g = len(uniq)
        if n_g < 3:
            raise ValueError("Se necesitan al menos 3 grupos para errores agrupados.")
        meat = np.zeros((k, k))
        for gi in range(n_g):
            s = A[codes == gi].T @ resid[codes == gi]
            meat += np.outer(s, s)
        cov = (n_g / (n_g - 1)) * ((n - 1) / (n - k)) * bread @ meat @ bread
        df = n_g - 1
    se = np.sqrt(np.diag(cov))
    tc = t_crit(df)
    out = pd.DataFrame({"coef": beta, "ee": se, "t": beta / se,
                        "ic95_inf": beta - tc * se, "ic95_sup": beta + tc * se},
                       index=Xd.columns)
    out.attrs["n"] = int(n)
    out.attrs["gl"] = float(df)
    out.attrs["r2"] = float(1 - (resid @ resid) / ((b - b.mean()) @ (b - b.mean())))
    return out


# --------------------------------------------------------------------------- #
# 4. Validación sin fuga de información
# --------------------------------------------------------------------------- #
def group_kfold_indices(groups: pd.Series, k: int = 5, seed: int = 0):
    """Genera (train_idx, test_idx) donde un mismo grupo NUNCA queda en ambos lados.

    Obligatorio cuando las filas no son independientes (varias jugadas del mismo partido,
    varios cuadros del mismo evento, etc.). Una división aleatoria por filas infla el desempeño.
    """
    g = pd.Series(groups).reset_index(drop=True)
    uniq = g.unique()
    if k > len(uniq):
        raise ValueError(f"k={k} es mayor que el número de grupos ({len(uniq)}).")
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    folds = np.array_split(uniq, k)
    for f in folds:
        test_mask = g.isin(f).to_numpy()
        yield np.where(~test_mask)[0], np.where(test_mask)[0]


def time_split(df: pd.DataFrame, time_col: str, test_frac: float = 0.2):
    """Separa por tiempo (entrena en el pasado, prueba en el futuro). Evita fuga temporal."""
    d = df.sort_values(time_col)
    cut = int(len(d) * (1 - test_frac))
    return d.iloc[:cut], d.iloc[cut:]


# --------------------------------------------------------------------------- #
# 5. Calibración de probabilidades
# --------------------------------------------------------------------------- #
def _check_prob_inputs(p: Iterable[float], y: Iterable[int]):
    p = np.asarray(list(p), dtype=float); y = np.asarray(list(y), dtype=float)
    if len(p) != len(y):
        raise ValueError("p y y deben tener la misma longitud.")
    if np.isnan(p).any() or ((p < 0) | (p > 1)).any():
        raise ValueError("Las probabilidades deben estar en [0, 1] y sin NaN (no se descartan en silencio).")
    if not np.isin(y, [0.0, 1.0]).all():
        raise ValueError("y debe contener solo 0 y 1.")
    return p, y


def brier_score(p: Iterable[float], y: Iterable[int]) -> float:
    p, y = _check_prob_inputs(p, y)
    return float(np.mean((p - y) ** 2))


def calibration_table(p: Iterable[float], y: Iterable[int], bins: int = 10) -> pd.DataFrame:
    """Compara probabilidad predicha vs frecuencia observada por intervalos.

    Un modelo que dice 70% debería acertar ~70% de las veces. Reporta n por intervalo:
    intervalos con pocos datos no son evidencia.
    """
    p_arr, y_arr = _check_prob_inputs(p, y)
    d = pd.DataFrame({"p": p_arr, "y": y_arr})
    d["bin"] = pd.cut(d["p"], np.linspace(0, 1, bins + 1), include_lowest=True)
    t = d.groupby("bin", observed=True).agg(n=("y", "size"), p_media=("p", "mean"),
                                           frec_observada=("y", "mean")).reset_index()
    return t


# --------------------------------------------------------------------------- #
# 6. Comparar opciones A vs B sin caer en Simpson / confusión observada
# --------------------------------------------------------------------------- #
def stratified_comparison(df: pd.DataFrame, treat: str, outcome: str, strata: list[str],
                          min_per_arm: int = 5, z: float = 1.96) -> dict:
    """Compara dos opciones (treat = 1 vs 0) DENTRO de contextos comparables (estratos).

    - diferencia_ingenua: promedio de 1 menos promedio de 0, sin ajustar (suele engañar).
    - diferencia_ajustada: promedio de las diferencias por estrato, ponderado por el tamaño
      del estrato, SOLO entre estratos donde hay al menos min_per_arm casos de cada opción.
    - Los estratos sin ambas opciones se EXCLUYEN y se reportan (falta de solapamiento =
      no hay comparación posible ahí; no extrapoles).
    LÍMITE: ajusta solo por las variables de `strata`. Confusores no medidos siguen
    sesgando el resultado y no se pueden corregir con datos. Requiere outcome numérico
    (0/1 o continuo) y treat con valores 0/1.
    """
    strata = list(strata)
    d = df[[treat, outcome] + strata].dropna()
    if not set(pd.unique(d[treat])).issubset({0, 1}):
        raise ValueError("treat debe contener solo 0 y 1.")
    if min_per_arm < 2:
        raise ValueError("min_per_arm debe ser >= 2 (se necesita varianza por grupo).")
    naive = float(d.loc[d[treat] == 1, outcome].mean() - d.loc[d[treat] == 0, outcome].mean())
    rows = []
    for key, g in d.groupby(strata, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        a = g.loc[g[treat] == 1, outcome]
        b = g.loc[g[treat] == 0, outcome]
        ee = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)) if len(a) > 1 and len(b) > 1 else float("nan")
        rows.append({"estrato": key[0] if len(key) == 1 else key, "n": len(g), "n_opcion1": len(a),
                     "n_opcion0": len(b), "media_opcion1": a.mean() if len(a) else float("nan"),
                     "media_opcion0": b.mean() if len(b) else float("nan"),
                     "diferencia": (a.mean() - b.mean()) if len(a) and len(b) else float("nan"), "ee": ee})
    tab = pd.DataFrame(rows)
    use = (tab["n_opcion1"] >= min_per_arm) & (tab["n_opcion0"] >= min_per_arm)
    excl = tab.loc[~use, "estrato"].tolist()
    if not use.any():
        raise ValueError("Ningún estrato tiene ambas opciones: no hay solapamiento, no se puede comparar.")
    tu = tab[use]
    w = tu["n"] / tu["n"].sum()
    adj = float((w * tu["diferencia"]).sum())
    ee = float(math.sqrt(((w ** 2) * (tu["ee"] ** 2)).sum()))
    return {"diferencia_ingenua": naive, "diferencia_ajustada": adj, "ee": ee,
            "ic95_inf": adj - z * ee, "ic95_sup": adj + z * ee, "tabla": tab,
            "estratos_excluidos": excl,
            "pct_filas_excluidas": float(100 * tab.loc[~use, "n"].sum() / tab["n"].sum()),
            "nota": "Ajustado solo por las variables de estrato dadas; confusores no medidos siguen sesgando."}


# --------------------------------------------------------------------------- #
# 7. Diagnóstico rápido de una relación x-y (anti-Anscombe)
# --------------------------------------------------------------------------- #
def diagnose_relationship(x: Iterable[float], y: Iterable[float]) -> dict:
    """Revisa una relación x-y más allá de la correlación: curvatura, atípicos, apalancamiento.

    Umbrales HEURÍSTICOS (son para revisar la gráfica, no para decidir): apalancamiento h>0.5,
    residuo studentizado |r|>2.5, término cuadrático con |t| mayor que el crítico al 99%.
    """
    xa = np.asarray(list(x), dtype=float); ya = np.asarray(list(y), dtype=float)
    m = np.isfinite(xa) & np.isfinite(ya)
    xa, ya = xa[m], ya[m]
    n = len(xa)
    if n < 5:
        raise ValueError("Se necesitan al menos 5 puntos válidos.")
    if xa.std() == 0 or ya.std() == 0:
        return {"n": n, "alertas": ["variable constante: no hay relación que evaluar"]}
    A = np.column_stack([np.ones(n), xa])
    beta, *_ = np.linalg.lstsq(A, ya, rcond=None)
    resid = ya - A @ beta
    h = np.einsum("ij,jk,ik->i", A, np.linalg.pinv(A.T @ A), A)
    s2 = float(resid @ resid / (n - 2))
    stud = resid / np.sqrt(s2 * np.clip(1 - h, 1e-12, None)) if s2 > 0 else np.zeros(n)
    pear = float(np.corrcoef(xa, ya)[0, 1])
    spear = float(np.corrcoef(pd.Series(xa).rank().to_numpy(), pd.Series(ya).rank().to_numpy())[0, 1])  # Spearman = Pearson de rangos (sin scipy)
    alertas = []
    t_quad = float("nan")
    A2 = np.column_stack([np.ones(n), xa, xa ** 2])
    if n > 4 and np.linalg.matrix_rank(A2) == 3:
        b2, *_ = np.linalg.lstsq(A2, ya, rcond=None)
        r2_ = ya - A2 @ b2
        s2b = float(r2_ @ r2_ / (n - 3))
        se_q = math.sqrt(max(s2b * np.linalg.pinv(A2.T @ A2)[2, 2], 0.0))
        t_quad = float(b2[2] / se_q) if se_q > 0 else float("inf")
        if abs(t_quad) > t_crit(n - 3, 0.99):
            alertas.append(f"curvatura: el término cuadrático es claro (t={t_quad:.1f}); la relación no es lineal")
    if h.max() > 0.5:
        alertas.append(f"apalancamiento: un punto (índice {int(h.argmax())}, h={h.max():.2f}) domina el ajuste")
    big = np.where(np.abs(stud) > 2.5)[0]
    if len(big):
        alertas.append(f"atípico: {len(big)} punto(s) con residuo studentizado |r|>2.5 (índices {big.tolist()})")
    return {"n": n, "pearson": pear, "spearman": spear, "pendiente": float(beta[1]),
            "intercepto": float(beta[0]), "max_apalancamiento": float(h.max()),
            "max_residuo_studentizado": float(np.abs(stud).max()), "t_cuadratico": t_quad,
            "alertas": alertas}


if __name__ == "__main__":
    # Autopruebas rápidas (python stats_toolkit.py)
    rng = np.random.default_rng(1)
    a = rng.normal(0.5, 1, 200); b = rng.normal(0.0, 1, 200)
    print("bootstrap:", bootstrap_ci(a))
    print("permutacion:", permutation_test(a, b, n_perm=2000))
    print("cohens_d:", round(cohens_d(a, b), 3))
    print("wilson 3/3:", wilson_interval(3, 3))
    ns = pd.Series(rng.integers(3, 300, 40)); true_p = rng.beta(20, 20, 40)
    ss = pd.Series(rng.binomial(ns, true_p))
    sh = shrink_rates(ss, ns)
    err_raw = float(np.mean((sh["tasa_cruda"] - true_p) ** 2))
    err_shr = float(np.mean((sh["tasa_encogida"] - true_p) ** 2))
    print("encogimiento: error crudo", round(err_raw, 5), "vs encogido", round(err_shr, 5))
    assert err_shr < err_raw, "el encogimiento debería reducir el error"
    try:
        shrink_rates(pd.Series([3, 90]), pd.Series([3, 100])); raise SystemExit("debió fallar")
    except ValueError:
        print("guarda de <10 grupos OK")
    print(shrink_rates(pd.Series([3, 90]), pd.Series([3, 100]), prior_strength=20).round(3))
    print(benjamini_hochberg([0.001, 0.02, 0.04, 0.3, 0.8]))
    X = pd.DataFrame({"x": rng.normal(size=300)}); y = 2 * X["x"] + 1 + rng.normal(size=300)
    print(ols(X, y).round(3))
    g = pd.Series(np.repeat(np.arange(10), 5))
    for tr, te in group_kfold_indices(g, k=5):
        assert set(g.iloc[tr]).isdisjoint(set(g.iloc[te]))
    p = rng.uniform(size=2000); yy = (rng.uniform(size=2000) < p).astype(int)
    print("brier:", round(brier_score(p, yy), 4)); print(calibration_table(p, yy, 5))
    print(audit_dataframe(pd.DataFrame({"a": [1, 1, None], "b": ["x", "x", "y"]}), key=["a"])["duplicados_en_llave"])
    print("OK")
