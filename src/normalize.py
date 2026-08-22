def a_float(valor):
    if valor is None:
        return None

    try:
        return float(valor)
    except (TypeError, ValueError):
        return None

def a_int(valor):
    if valor is None:
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def calcular_porcentaje(parte, total):
    if parte is None or total in (None, 0):
        return None

    return round(
        parte / total * 100,
        1
    )


def porcentaje_a_float(valor):
    if valor is None:
        return None

    if isinstance(valor, str):
        valor = valor.replace("%", "").strip()

    return a_float(valor)


def estadisticas_a_dict(estadisticas):
    return {
        item["type"]: item["value"]
        for item in estadisticas
    }


def normalizar_estadisticas_equipo(bloque):
    if bloque is None:
        return None

    stats = estadisticas_a_dict(
        bloque.get("statistics", [])
    )

    return {
        "shots": {
            "total": stats.get("Total Shots"),
            "on_target": stats.get("Shots on Goal"),
            "off_target": stats.get("Shots off Goal"),
            "blocked": stats.get("Blocked Shots"),
            "inside_box": stats.get("Shots insidebox"),
            "outside_box": stats.get("Shots outsidebox"),
        },

        "possession_pct": porcentaje_a_float(
            stats.get("Ball Possession")
        ),

        "passes": {
            "total": stats.get("Total passes"),
            "accurate": stats.get("Passes accurate"),
            "accuracy_pct": porcentaje_a_float(
                stats.get("Passes %")
            ),
        },

        "fouls": stats.get("Fouls"),
        "corners": stats.get("Corner Kicks"),
        "offsides": stats.get("Offsides"),

        "cards": {
            "yellow": stats.get("Yellow Cards"),
            "red": stats.get("Red Cards"),
        },

        "goalkeeper_saves": stats.get(
            "Goalkeeper Saves"
        ),

        "expected_goals": a_float(
            stats.get("expected_goals")
        ),

        "goals_prevented": a_float(
            stats.get("goals_prevented")
        ),
    }


def buscar_estadisticas_equipo(partido, team_id):
    for bloque in partido.get("statistics", []):
        equipo = bloque.get("team", {})

        if equipo.get("id") == team_id:
            return bloque

    return None

def normalizar_jugador(jugador):
    datos_jugador = jugador.get(
        "player",
        {}
    )

    estadisticas_lista = jugador.get(
        "statistics",
        []
    )

    if not estadisticas_lista:
        return None

    stats = estadisticas_lista[0]

    games = stats.get("games", {})
    shots = stats.get("shots", {})
    goals = stats.get("goals", {})
    passes = stats.get("passes", {})
    tackles = stats.get("tackles", {})
    duels = stats.get("duels", {})
    dribbles = stats.get("dribbles", {})
    fouls = stats.get("fouls", {})
    cards = stats.get("cards", {})
    penalty = stats.get("penalty", {})

    pases_totales = a_int(
        passes.get("total")
    )

    pases_acertados = a_int(
        passes.get("accuracy")
    )

    return {
        "id": datos_jugador.get("id"),
        "name": datos_jugador.get("name"),
        "photo": datos_jugador.get("photo"),

        "minutes": a_int(
            games.get("minutes")
        ),

        "number": a_int(
            games.get("number")
        ),

        "position": games.get("position"),

        "rating": a_float(
            games.get("rating")
        ),

        "captain": games.get("captain"),
        "substitute": games.get("substitute"),

        "shots": {
            "total": a_int(
                shots.get("total")
            ),

            "on_target": a_int(
                shots.get("on")
            ),
        },

        "goals": a_int(
            goals.get("total")
        ),

        "assists": a_int(
            goals.get("assists")
        ),

        # API-Football los mete dentro de goals.*, no
        # en un bloque aparte. Los guardamos en el
        # esquema propio para que la placa de
        # destacados pueda usarlos en arqueros sin
        # volver a leer el JSON crudo.
        "saves": a_int(
            goals.get("saves")
        ),

        "goals_conceded": a_int(
            goals.get("conceded")
        ),

        "passes": {
            "total": pases_totales,
            "accurate": pases_acertados,

            "accuracy_pct": calcular_porcentaje(
                pases_acertados,
                pases_totales
            ),

            "key": a_int(
                passes.get("key")
            ),
        },

        "tackles": {
            "total": a_int(
                tackles.get("total")
            ),

            "blocks": a_int(
                tackles.get("blocks")
            ),

            "interceptions": a_int(
                tackles.get("interceptions")
            ),
        },

        "duels": {
            "total": a_int(
                duels.get("total")
            ),

            "won": a_int(
                duels.get("won")
            ),
        },

        "dribbles": {
            "attempted": a_int(
                dribbles.get("attempts")
            ),

            "successful": a_int(
                dribbles.get("success")
            ),
        },

        "fouls": {
            "drawn": a_int(
                fouls.get("drawn")
            ),

            "committed": a_int(
                fouls.get("committed")
            ),
        },

        "cards": {
            "yellow": a_int(
                cards.get("yellow")
            ),

            "red": a_int(
                cards.get("red")
            ),
        },

        "penalty": {
            "won": a_int(
                penalty.get("won")
            ),

            "scored": a_int(
                penalty.get("scored")
            ),

            "missed": a_int(
                penalty.get("missed")
            ),

            "saved": a_int(
                penalty.get("saved")
            ),
        },
    }

def normalizar_jugadores_equipo(
    partido,
    team_id
):
    for bloque in partido.get(
        "players",
        []
    ):
        equipo = bloque.get(
            "team",
            {}
        )

        if equipo.get("id") == team_id:
            jugadores = []

            for jugador in bloque.get(
                "players",
                []
            ):
                jugador_normalizado = (
                    normalizar_jugador(
                        jugador
                    )
                )

                if jugador_normalizado:
                    jugadores.append(
                        jugador_normalizado
                    )

            return jugadores

    return []

def normalizar_grid(grid):
    if not grid:
        return None

    try:
        fila, columna = grid.split(":")

        return {
            "row": int(fila),
            "column": int(columna),
        }

    except (ValueError, AttributeError):
        return None


def normalizar_jugador_alineacion(item):
    jugador = item.get("player", {})

    return {
        "id": jugador.get("id"),
        "name": jugador.get("name"),
        "number": a_int(
            jugador.get("number")
        ),
        "position": jugador.get("pos"),
        "grid": normalizar_grid(
            jugador.get("grid")
        ),
    }


def buscar_alineacion_equipo(
    partido,
    team_id
):
    for bloque in partido.get(
        "lineups",
        []
    ):
        equipo = bloque.get(
            "team",
            {}
        )

        if equipo.get("id") == team_id:
            return bloque

    return None


def normalizar_alineacion_equipo(
    partido,
    team_id
):
    alineacion = buscar_alineacion_equipo(
        partido,
        team_id
    )

    if alineacion is None:
        return None

    entrenador = alineacion.get(
        "coach",
        {}
    )

    return {
        "formation": alineacion.get(
            "formation"
        ),

        "coach": {
            "id": entrenador.get("id"),
            "name": entrenador.get("name"),
            "photo": entrenador.get("photo"),
        },

        "start_xi": [
            normalizar_jugador_alineacion(
                jugador
            )
            for jugador
            in alineacion.get(
                "startXI",
                []
            )
        ],

        "substitutes": [
            normalizar_jugador_alineacion(
                jugador
            )
            for jugador
            in alineacion.get(
                "substitutes",
                []
            )
        ],
    }

def normalizar_persona_evento(persona):
    if not persona:
        return None

    if (
        persona.get("id") is None
        and persona.get("name") is None
    ):
        return None

    return {
        "id": persona.get("id"),
        "name": persona.get("name"),
    }


def normalizar_evento(evento):
    tiempo = evento.get("time", {})
    equipo = evento.get("team", {})

    tipo_original = evento.get("type")

    tipos = {
        "Goal": "goal",
        "Card": "card",
        "subst": "substitution",
        "Var": "var",
    }

    tipo = tipos.get(
        tipo_original,
        tipo_original
    )

    resultado = {
        "minute": a_int(
            tiempo.get("elapsed")
        ),

        "extra": a_int(
            tiempo.get("extra")
        ),

        "team": {
            "id": equipo.get("id"),
            "name": equipo.get("name"),
        },

        "type": tipo,

        "detail": evento.get(
            "detail"
        ),

        "comments": evento.get(
            "comments"
        ),
    }

    if tipo == "substitution":
        resultado["player_out"] = (
            normalizar_persona_evento(
                evento.get("player")
            )
        )

        resultado["player_in"] = (
            normalizar_persona_evento(
                evento.get("assist")
            )
        )

    else:
        resultado["player"] = (
            normalizar_persona_evento(
                evento.get("player")
            )
        )

        resultado["assist"] = (
            normalizar_persona_evento(
                evento.get("assist")
            )
        )

    return resultado


def normalizar_eventos(partido):
    return [
        normalizar_evento(evento)
        for evento
        in partido.get("events", [])
    ]

def normalizar_equipo(partido, lado):
    equipo = partido["teams"][lado]

    bloque_estadisticas = buscar_estadisticas_equipo(
        partido,
        equipo["id"]
    )

    return {
        "id": equipo["id"],
        "name": equipo["name"],
        "logo": equipo.get("logo"),
        "winner": equipo.get("winner"),
        "statistics": normalizar_estadisticas_equipo(
            bloque_estadisticas
        ),
        "players": normalizar_jugadores_equipo(
            partido,
            equipo["id"]
        ),
        "lineup": normalizar_alineacion_equipo(
            partido,
            equipo["id"]
        ),
    }

def normalizar_partido(partido):
    fixture = partido["fixture"]
    liga = partido["league"]
    goles = partido["goals"]
    score = partido["score"]

    return {
        "source": {
            "provider": "api_football",
            "fixture_id": fixture["id"],
        },

        "match": {
            "date": fixture.get("date"),
            "status": fixture["status"].get("short"),
            "elapsed": fixture["status"].get("elapsed"),
            "extra": fixture["status"].get("extra"),
            "referee": fixture.get("referee"),

            "venue": {
                "name": fixture.get(
                    "venue",
                    {}
                ).get("name"),

                "city": fixture.get(
                    "venue",
                    {}
                ).get("city"),
            },

            "competition": {
                "id": liga.get("id"),
                "name": liga.get("name"),
                "country": liga.get("country"),
                "season": liga.get("season"),
                "round": liga.get("round"),
            },

            "score": {
                "home": goles.get("home"),
                "away": goles.get("away"),

                "halftime": {
                    "home": score.get(
                        "halftime",
                        {}
                    ).get("home"),

                    "away": score.get(
                        "halftime",
                        {}
                    ).get("away"),
                },
            },
        },

        "teams": {
            "home": normalizar_equipo(
                partido,
                "home"
            ),

            "away": normalizar_equipo(
                partido,
                "away"
            ),
        },

        "events": normalizar_eventos(
            partido
        ),
    }