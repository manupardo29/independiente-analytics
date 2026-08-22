"""
Seleccion de destacados y de las estadisticas que los explican.

La visualizacion no deberia conocer estas reglas: aca se arma
una estructura lista para dibujar (quien entra, en que orden,
que hasta 3 frases mostrar). El rating de API-Football decide
QUIEN entra; las estadisticas deciden COMO se justifica.
"""

MIN_MINUTOS = 25
MAX_DESTACADOS = 3
MAX_STATS = 3

# Umbrales simples: evitan destacar un 100% nacido de
# 3/3 pases o un 1/1 en duelos. No son cortes "de elite",
# solo un piso de volumen para que el numero se pueda leer.
PASES_MIN = 20
REGATES_MIN = 4
FALTAS_RECIBIDAS_MIN = 2
TIROS_MIN = 2
TIROS_ARCO_MIN = 2
PASES_CLAVE_PRIMARIO = 2
INTERCEPCIONES_MIN = 2
TACKLES_MIN = 2
BLOQUEOS_MIN = 1
ATAJADAS_MIN = 1

DUELOS_MIN_DEFENSIVO = 8
DUELOS_MIN_OFENSIVO = 12
DUELOS_WIN_PCT_MIN = 60

ROLES_OFENSIVOS = {
    "midfielder_attacking",
    "forward",
}

POSICION_LABEL = {
    "goalkeeper": "ARQUERO",
    "defender": "DEFENSOR",
    "midfielder_central": "MEDIOCAMPISTA",
    "midfielder_attacking": "MEDIAPUNTA",
    "forward": "DELANTERO",
}

# Orden de lectura por rol DESPUES de goles/asistencias.
# No es un ranking propio: solo decide que mirar primero
# cuando hay varias estadisticas validas.
PRIORIDAD_POR_ROL = {
    "goalkeeper": (
        "saves",
        "goals_conceded",
        "passes",
        "key_passes",
    ),
    "defender": (
        "interceptions",
        "tackles",
        "blocks",
        "duels",
        "passes",
        "key_passes",
        "shots",
    ),
    "midfielder_central": (
        "key_passes",
        "passes",
        "interceptions",
        "tackles",
        "duels",
        "shots",
        "fouls_drawn",
        "dribbles",
    ),
    "midfielder_attacking": (
        "key_passes",
        "dribbles",
        "shots",
        "shots_on_target",
        "fouls_drawn",
        "passes",
        "duels",
        "tackles",
    ),
    "forward": (
        "shots",
        "shots_on_target",
        "key_passes",
        "dribbles",
        "duels",
        "fouls_drawn",
        "passes",
    ),
}


def _entero(valor):
    if valor is None:
        return 0

    return int(valor)


def _plural(cantidad, singular, plural):
    if cantidad == 1:
        return singular

    return plural


def indexar_grids(equipo):
    alineacion = equipo.get("lineup") or {}
    titulares = alineacion.get("start_xi") or []

    return {
        jugador["id"]: jugador.get("grid")
        for jugador in titulares
        if jugador.get("id") is not None
    }


def _filas_mediocampo(equipo, grids_titulares):
    alineacion = equipo.get("lineup") or {}
    titulares = alineacion.get("start_xi") or []

    filas = set()

    for titular in titulares:
        if titular.get("position") != "M":
            continue

        grid = titular.get("grid")

        if grid:
            filas.add(grid["row"])

    if filas:
        return sorted(filas)

    # Fallback: filas internas de la formacion (ni la
    # primera -arquero- ni la ultima -punta-).
    filas_todas = sorted({
        grid["row"]
        for grid in grids_titulares.values()
        if grid
    })

    if len(filas_todas) <= 2:
        return filas_todas

    return filas_todas[1:-1]


def _rol_mediocampista(grid, filas_mediocampo):
    if not grid or not filas_mediocampo:
        return "midfielder_central"

    if len(filas_mediocampo) <= 1:
        return "midfielder_central"

    fila = grid["row"]
    corte = (
        filas_mediocampo[0]
        + filas_mediocampo[-1]
    ) / 2

    if fila > corte:
        return "midfielder_attacking"

    return "midfielder_central"


def inferir_rol_jugador(jugador, equipo, grids_titulares):
    position = jugador.get("position")

    if position == "G":
        return "goalkeeper"

    if position == "D":
        return "defender"

    if position == "F":
        return "forward"

    if position != "M":
        return "midfielder_central"

    grid = grids_titulares.get(jugador.get("id"))
    filas_m = _filas_mediocampo(
        equipo,
        grids_titulares
    )

    return _rol_mediocampista(grid, filas_m)


def tiene_impacto_directo(jugador):
    if _entero(jugador.get("goals")) > 0:
        return True

    if _entero(jugador.get("assists")) > 0:
        return True

    if _entero(jugador.get("penalty_saved")) > 0:
        return True

    return False


def es_elegible(jugador):
    if jugador.get("rating") is None:
        return False

    minutos = _entero(jugador.get("minutes"))

    if minutos >= MIN_MINUTOS:
        return True

    # Un suplente de 15-20' que define el partido
    # no deberia quedar afuera por el piso de minutos.
    return tiene_impacto_directo(jugador)


def seleccionar_destacados(
    jugadores,
    cantidad=MAX_DESTACADOS
):
    candidatos = [
        jugador
        for jugador in jugadores
        if es_elegible(jugador)
    ]

    ordenados = sorted(
        candidatos,
        key=lambda jugador: jugador["rating"],
        reverse=True
    )

    return ordenados[:cantidad]


def _duelos_relevantes(jugador, rol):
    total = _entero(jugador.get("duels_total"))
    ganados = _entero(jugador.get("duels_won"))
    win_pct = jugador.get("duel_win_pct")

    minimo = (
        DUELOS_MIN_OFENSIVO
        if rol in ROLES_OFENSIVOS
        else DUELOS_MIN_DEFENSIVO
    )

    if total < minimo:
        return False

    if win_pct is None:
        return False

    # El volumen solo no alcanza: 11/22 (50%) no explica
    # un partido destacado. Pedimos un piso de efectividad
    # para no pintar un duelo promedio como virtud.
    return win_pct >= DUELOS_WIN_PCT_MIN


def _pases_relevantes(jugador):
    return _entero(jugador.get("passes_total")) >= PASES_MIN


def _cumple_primario(clave, jugador, rol):
    if clave == "saves":
        return _entero(jugador.get("saves")) >= ATAJADAS_MIN

    if clave == "goals_conceded":
        return jugador.get("goals_conceded") is not None

    if clave == "passes":
        return _pases_relevantes(jugador)

    if clave == "key_passes":
        return (
            _entero(jugador.get("key_passes"))
            >= PASES_CLAVE_PRIMARIO
        )

    if clave == "dribbles":
        return (
            _entero(jugador.get("dribbles_attempted"))
            >= REGATES_MIN
        )

    if clave == "shots":
        return _entero(jugador.get("shots_total")) >= TIROS_MIN

    if clave == "shots_on_target":
        return (
            _entero(jugador.get("shots_on_target"))
            >= TIROS_ARCO_MIN
        )

    if clave == "fouls_drawn":
        return (
            _entero(jugador.get("fouls_drawn"))
            >= FALTAS_RECIBIDAS_MIN
        )

    if clave == "interceptions":
        return (
            _entero(jugador.get("interceptions"))
            >= INTERCEPCIONES_MIN
        )

    if clave == "tackles":
        # En mediapuntas/delanteros un par de tackles
        # no explica el partido; pedimos volumen alto
        # para no tapar un pase clave o un tiro.
        minimo = (
            5
            if rol in ROLES_OFENSIVOS
            else TACKLES_MIN
        )
        return _entero(jugador.get("tackles")) >= minimo

    if clave == "blocks":
        return _entero(jugador.get("blocks")) >= BLOQUEOS_MIN

    if clave == "duels":
        return _duelos_relevantes(jugador, rol)

    return False


def _cumple_relleno(clave, jugador, rol):
    """
    Segunda pasada, mas permisiva, solo si todavia
    quedan huecos. Sigue sin aceptar muestras ridiculas
    (3/3 pases, 1/1 regates).
    """
    if clave == "key_passes":
        return _entero(jugador.get("key_passes")) >= 1

    if clave == "shots":
        return _entero(jugador.get("shots_total")) >= 1

    if clave == "shots_on_target":
        return _entero(jugador.get("shots_on_target")) >= 1

    if clave == "interceptions":
        return _entero(jugador.get("interceptions")) >= 1

    if clave == "tackles":
        return _entero(jugador.get("tackles")) >= 1

    if clave == "blocks":
        return _entero(jugador.get("blocks")) >= 1

    if clave == "fouls_drawn":
        return (
            _entero(jugador.get("fouls_drawn"))
            >= FALTAS_RECIBIDAS_MIN
        )

    if clave in {
        "passes",
        "dribbles",
        "duels",
        "saves",
        "goals_conceded",
    }:
        return _cumple_primario(clave, jugador, rol)

    return False


def _formatear_stat(clave, jugador):
    if clave == "goals":
        n = _entero(jugador.get("goals"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(n, "gol", "goles"),
        }

    if clave == "assists":
        n = _entero(jugador.get("assists"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(
                n,
                "asistencia",
                "asistencias"
            ),
        }

    if clave == "penalty_saved":
        n = _entero(jugador.get("penalty_saved"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(
                n,
                "penal atajado",
                "penales atajados"
            ),
        }

    if clave == "saves":
        n = _entero(jugador.get("saves"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(n, "atajada", "atajadas"),
        }

    if clave == "goals_conceded":
        n = _entero(jugador.get("goals_conceded"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(
                n,
                "gol recibido",
                "goles recibidos"
            ),
        }

    if clave == "key_passes":
        n = _entero(jugador.get("key_passes"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(
                n,
                "pase clave",
                "pases clave"
            ),
        }

    if clave == "passes":
        total = _entero(jugador.get("passes_total"))
        acertados = _entero(jugador.get("passes_accurate"))
        pct = jugador.get("pass_accuracy_pct")
        pct_txt = (
            f"{pct:.0f}%"
            if pct is not None
            else "N/D"
        )
        return {
            "key": clave,
            "value": f"{acertados}/{total}",
            "label": f"pases · {pct_txt}",
        }

    if clave == "dribbles":
        ok = _entero(jugador.get("dribbles_successful"))
        intentos = _entero(jugador.get("dribbles_attempted"))
        return {
            "key": clave,
            "value": f"{ok}/{intentos}",
            "label": "regates",
        }

    if clave == "duels":
        ok = _entero(jugador.get("duels_won"))
        total = _entero(jugador.get("duels_total"))
        return {
            "key": clave,
            "value": f"{ok}/{total}",
            "label": "duelos",
        }

    if clave == "shots":
        n = _entero(jugador.get("shots_total"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(n, "tiro", "tiros"),
        }

    if clave == "shots_on_target":
        n = _entero(jugador.get("shots_on_target"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(
                n,
                "tiro al arco",
                "tiros al arco"
            ),
        }

    if clave == "fouls_drawn":
        n = _entero(jugador.get("fouls_drawn"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(
                n,
                "falta recibida",
                "faltas recibidas"
            ),
        }

    if clave == "interceptions":
        n = _entero(jugador.get("interceptions"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(
                n,
                "intercepción",
                "intercepciones"
            ),
        }

    if clave == "tackles":
        n = _entero(jugador.get("tackles"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(n, "tackle", "tackles"),
        }

    if clave == "blocks":
        n = _entero(jugador.get("blocks"))
        return {
            "key": clave,
            "value": str(n),
            "label": _plural(n, "bloqueo", "bloqueos"),
        }

    return None


def elegir_stats_jugador(jugador, rol):
    elegidas = []
    usadas = set()

    impacto = []

    if _entero(jugador.get("goals")) > 0:
        impacto.append("goals")

    if _entero(jugador.get("assists")) > 0:
        impacto.append("assists")

    if _entero(jugador.get("penalty_saved")) > 0:
        impacto.append("penalty_saved")

    for clave in impacto:
        stat = _formatear_stat(clave, jugador)

        if stat:
            elegidas.append(stat)
            usadas.add(clave)

    prioridad = PRIORIDAD_POR_ROL.get(
        rol,
        PRIORIDAD_POR_ROL["midfielder_central"]
    )

    def agregar_si(filtro):
        for clave in prioridad:
            if len(elegidas) >= MAX_STATS:
                return

            if clave in usadas:
                continue

            # Si ya mostramos tiros, el on-target suelto
            # no aporta salvo que tenga volumen propio.
            if (
                clave == "shots_on_target"
                and "shots" in usadas
                and _entero(jugador.get("shots_on_target")) < TIROS_ARCO_MIN
            ):
                continue

            if filtro(clave, jugador, rol):
                stat = _formatear_stat(clave, jugador)

                if stat:
                    elegidas.append(stat)
                    usadas.add(clave)

    agregar_si(_cumple_primario)

    if len(elegidas) < MAX_STATS:
        agregar_si(_cumple_relleno)

    return elegidas


def _nombre_visible(nombre):
    if not nombre:
        return "N/D"

    return nombre.upper()


def armar_vista_jugador(jugador, rol, es_figura):
    return {
        "id": jugador.get("id"),
        "name": jugador.get("name"),
        "display_name": _nombre_visible(
            jugador.get("name")
        ),
        "photo": jugador.get("photo"),
        "number": jugador.get("number"),
        "position": jugador.get("position"),
        "role": rol,
        "position_label": POSICION_LABEL.get(
            rol,
            "N/D"
        ),
        "minutes": jugador.get("minutes"),
        "rating": jugador.get("rating"),
        "stats": elegir_stats_jugador(jugador, rol),
        "es_figura": es_figura,
    }


def construir_destacados(equipo, jugadores_metricas):
    grids = indexar_grids(equipo)
    seleccionados = seleccionar_destacados(
        jugadores_metricas
    )

    vistas = []

    for indice, jugador in enumerate(seleccionados):
        rol = inferir_rol_jugador(
            jugador,
            equipo,
            grids
        )

        vistas.append(
            armar_vista_jugador(
                jugador,
                rol,
                es_figura=(indice == 0),
            )
        )

    return vistas
