def estadisticas_a_dict(estadisticas):
    return {
        item["type"]: item["value"]
        for item in estadisticas
    }


def buscar_bloque_equipo(
    partido,
    bloque_nombre,
    team_id
):
    for bloque in partido.get(
        bloque_nombre,
        []
    ):
        equipo = bloque.get(
            "team",
            {}
        )

        if equipo.get("id") == team_id:
            return bloque

    return None


def contar_eventos(
    partido,
    team_id,
    tipo,
    detalle=None
):
    cantidad = 0

    for evento in partido.get(
        "events",
        []
    ):
        if evento.get(
            "team",
            {}
        ).get("id") != team_id:
            continue

        if evento.get("type") != tipo:
            continue

        if (
            detalle is not None
            and evento.get("detail") != detalle
        ):
            continue

        cantidad += 1

    return cantidad


def max_minutos_titulares(
    bloque_jugadores
):
    if not bloque_jugadores:
        return None

    minutos = []

    for jugador in bloque_jugadores.get(
        "players",
        []
    ):
        estadisticas = jugador.get(
            "statistics",
            []
        )

        if not estadisticas:
            continue

        games = estadisticas[0].get(
            "games",
            {}
        )

        if games.get("substitute"):
            continue

        minutos_jugador = games.get(
            "minutes"
        )

        if minutos_jugador is not None:
            minutos.append(
                minutos_jugador
            )

    if not minutos:
        return None

    return max(minutos)


def validar_equipo(
    partido,
    team_id,
    team_name
):
    problemas = []

    bloque_stats = buscar_bloque_equipo(
        partido,
        "statistics",
        team_id
    )

    bloque_players = buscar_bloque_equipo(
        partido,
        "players",
        team_id
    )

    if bloque_stats is None:
        problemas.append(
            f"{team_name}: faltan estadisticas de equipo"
        )

        return problemas

    stats = estadisticas_a_dict(
        bloque_stats.get(
            "statistics",
            []
        )
    )

    pases = stats.get(
        "Total passes"
    )

    max_minutos = max_minutos_titulares(
        bloque_players
    )

    if (
        pases is not None
        and pases < 50
    ):
        problemas.append(
            f"{team_name}: solo registra "
            f"{pases} pases"
        )

    if (
        max_minutos is not None
        and max_minutos < 45
    ):
        problemas.append(
            f"{team_name}: los titulares "
            f"solo registran hasta "
            f"{max_minutos} minutos"
        )

    amarillas_eventos = contar_eventos(
        partido,
        team_id,
        "Card",
        "Yellow Card"
    )

    amarillas_stats = stats.get(
        "Yellow Cards"
    )

    if (
        amarillas_eventos > 0
        and amarillas_stats != amarillas_eventos
    ):
        problemas.append(
            f"{team_name}: amarillas inconsistentes "
            f"(events={amarillas_eventos}, "
            f"statistics={amarillas_stats})"
        )

    rojas_eventos = contar_eventos(
        partido,
        team_id,
        "Card",
        "Red Card"
    )

    rojas_stats = stats.get(
        "Red Cards"
    )

    if (
        rojas_eventos > 0
        and rojas_stats != rojas_eventos
    ):
        problemas.append(
            f"{team_name}: rojas inconsistentes "
            f"(events={rojas_eventos}, "
            f"statistics={rojas_stats})"
        )

    return problemas


def validar_partido(partido):
    problemas = []

    fixture = partido.get(
        "fixture",
        {}
    )

    estado = fixture.get(
        "status",
        {}
    ).get("short")

    equipos = partido.get(
        "teams",
        {}
    )

    if estado != "FT":
        problemas.append(
            f"El partido no esta finalizado "
            f"(status={estado})"
        )

    for lado in [
        "home",
        "away"
    ]:
        equipo = equipos.get(
            lado,
            {}
        )

        problemas.extend(
            validar_equipo(
                partido,
                equipo.get("id"),
                equipo.get("name")
            )
        )

    return {
        "valid": len(problemas) == 0,
        "issues": problemas,
    }