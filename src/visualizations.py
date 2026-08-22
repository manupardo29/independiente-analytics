from pathlib import Path

import matplotlib.pyplot as plt

from mplsoccer import VerticalPitch

from matplotlib.patches import FancyBboxPatch, Rectangle

from src.theme import (
    ACCENT,
    ACCOUNT_HANDLE,
    BACKGROUND,
    DIVIDER,
    MUTED_TEXT,
    PANEL,
    RATING_AVERAGE,
    RATING_BAD,
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_NA,
    RATING_TEXT_DARK,
    RATING_TEXT_LIGHT,
    SECONDARY,
    TEXT,
    TRACK,
    aplicar_tema,
)

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image, ImageDraw

from src.player_highlights import construir_destacados
from src.player_photos import obtener_foto_jugador

INDEPENDIENTE_ID = 453

def agregar_marca_de_cuenta(fig):
    """
    Handle de la cuenta, consistente en todas las placas.

    Usa fig.text() (coordenadas de figura 0-1) en vez de
    ax.text() a proposito: cada placa arma sus ejes distinto
    (una sola ax en unas, ax_header + ax_pitch en la del XI),
    y fig.text() funciona igual sin importar esa estructura -
    asi no hay que adaptar esta funcion cada vez que se agregue
    una placa nueva.

    Sirve para que una captura o repost por fuera de Instagram
    (donde no se ve el @ de la cuenta que publico) siga
    identificando la fuente.
    """
    fig.text(
        0.5,
        0.035,
        ACCOUNT_HANDLE,
        ha="center",
        va="bottom",
        fontsize=13,
        fontweight="bold",
        color=MUTED_TEXT,
        alpha=0.8,
    )

def obtener_colores_equipos(home, away):
    if home["id"] == INDEPENDIENTE_ID:
        return ACCENT, SECONDARY

    if away["id"] == INDEPENDIENTE_ID:
        return SECONDARY, ACCENT

    # Fallback para fixtures de desarrollo
    return ACCENT, SECONDARY

def obtener_equipo_destacado(
    partido
):
    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    if home["id"] == INDEPENDIENTE_ID:
        return home

    if away["id"] == INDEPENDIENTE_ID:
        return away

    # Fallback para fixtures de desarrollo
    return home

def buscar_datos_jugador(
    equipo,
    player_id
):
    for jugador in equipo["players"]:
        if jugador["id"] == player_id:
            return jugador

    return None

def obtener_estilo_rating(rating):
    if rating is None:
        return RATING_NA, RATING_TEXT_LIGHT

    if rating < 6.0:
        return RATING_BAD, RATING_TEXT_LIGHT

    if rating < 7.0:
        return RATING_AVERAGE, RATING_TEXT_DARK

    if rating < 8.0:
        return RATING_GOOD, RATING_TEXT_LIGHT

    return RATING_EXCELLENT, RATING_TEXT_LIGHT

def calcular_apellidos_duplicados(jugadores):
    """
    Devuelve el set de apellidos que se repiten entre los
    jugadores dados. Se usa para saber a quien hay que
    desambiguar con la inicial y a quien no - por default
    mostramos solo apellido (mas corto = mas legible en
    Instagram), la inicial es la excepcion, no la regla.
    """
    conteo = {}

    for jugador in jugadores:
        nombre = jugador.get("name")

        if not nombre:
            continue

        apellido = nombre.split()[-1]

        conteo[apellido] = (
            conteo.get(apellido, 0) + 1
        )

    return {
        apellido
        for apellido, cantidad in conteo.items()
        if cantidad > 1
    }


def acortar_nombre(nombre, apellidos_duplicados=None):
    if not nombre:
        return "N/D"

    partes = nombre.split()
    apellido = partes[-1]

    if len(partes) == 1:
        return apellido

    hay_colision = (
        apellidos_duplicados is not None
        and apellido in apellidos_duplicados
    )

    if not hay_colision:
        return apellido

    nombre_corto = (
        f"{partes[0][0]}. "
        f"{apellido}"
    )

    if len(nombre_corto) <= 15:
        return nombre_corto

    return apellido

def obtener_fontsize_nombre(cantidad_fila):
    """
    Fontsize del apellido segun cuantos jugadores comparten
    la fila. Con mas jugadores hay menos espacio horizontal
    por jugador (ver obtener_posiciones_alineacion), asi que
    en filas de 4-5 hay que achicar la fuente para no pisar
    al vecino. Numeros calculados a mano contra el ancho real
    de la cancha renderizada (~576px) y el apellido mas largo
    del roster (12 caracteres, ej "Breitenbruch").
    """
    if cantidad_fila <= 3:
        return 12

    if cantidad_fila == 4:
        return 10

    return 9

def obtener_posiciones_alineacion(
    start_xi
):
    jugadores_validos = [
        jugador
        for jugador in start_xi
        if jugador.get("grid")
    ]

    if not jugadores_validos:
        return []

    max_fila = max(
        jugador["grid"]["row"]
        for jugador in jugadores_validos
    )

    posiciones = []

    for jugador in jugadores_validos:
        fila = jugador["grid"]["row"]
        columna = jugador["grid"]["column"]

        jugadores_fila = [
            otro
            for otro in jugadores_validos
            if otro["grid"]["row"] == fila
        ]

        cantidad_fila = len(
            jugadores_fila
        )

        # Profundidad:
        # arquero cerca de x=8,
        # delanteros cerca de x=108.
        if max_fila == 1:
            x = 60
        else:
            x_min = 14
            x_max = 106

            x = (
                x_min
                + (
                    (fila - 1)
                    / (max_fila - 1)
                )
                * (x_max - x_min)
            )

        # Ancho de cancha
        y = (
            80
            * columna
            / (cantidad_fila + 1)
        )

        posiciones.append(
            {
                "player": jugador,
                "x": x,
                "y": y,
                "cantidad_fila": cantidad_fila,
            }
        )

    return posiciones

def formatear_valor(valor, tipo):
    if valor is None:
        return "N/D"

    if tipo == "int":
        return str(int(valor))

    if tipo == "pct":
        return f"{valor:.0f}%"

    if tipo == "decimal":
        return f"{valor:.2f}"

    return str(valor)

def formatear_decimal(
    valor,
    decimales
):
    if valor is None:
        return "N/D"

    return f"{valor:.{decimales}f}"

def formatear_decimal_con_signo(
    valor,
    decimales
):
    if valor is None:
        return "N/D"

    return f"{valor:+.{decimales}f}"

def calcular_barras_comparacion(valor_home, valor_away):
    """
    Escala home/away a fracciones para dibujar_barra_comparacion.

    SIEMPRE "share del combinado" (home / (home+away)), nunca
    valor/100 - un valor/100 infla o desinfla el llenado
    combinado de la barra segun si home+away suma cerca de
    100 o no (ej: dos porcentajes independientes como
    precision de tiro o conversion de gol casi nunca suman
    100), lo que hace que dos filas con la MISMA diferencia
    relativa entre equipos se vean con barras de "tamaño"
    muy distinto. Esta es la unica funcion que decide esa
    escala - evita que una placa nueva reintroduzca el bug
    a mano en otro lado.
    """
    home_num = (
        float(valor_home)
        if valor_home is not None
        else 0
    )

    away_num = (
        float(valor_away)
        if valor_away is not None
        else 0
    )

    total = home_num + away_num

    if total > 0:
        return home_num / total, away_num / total

    return 0, 0

def dibujar_barra_comparacion(
    ax,
    y,
    valor_home,
    valor_away,
    color_home,
    color_away,
    altura=0.22
):
    radio_maximo = 0.07

    # Pista completa de fondo
    pista = FancyBboxPatch(
        (-1, y - altura / 2),
        2,
        altura,
        boxstyle=(
            f"round,pad=0,"
            f"rounding_size={radio_maximo}"
        ),
        facecolor=TRACK,
        edgecolor="none",
        zorder=1,
    )

    ax.add_patch(
        pista
    )

    # Barra local
    if valor_home > 0:
        radio_home = min(
            radio_maximo,
            valor_home / 2,
            altura / 2,
        )

        barra_home = FancyBboxPatch(
            (
                -valor_home,
                y - altura / 2
            ),
            valor_home,
            altura,
            boxstyle=(
                f"round,pad=0,"
                f"rounding_size={radio_home}"
            ),
            facecolor=color_home,
            edgecolor="none",
            zorder=2,
        )

        ax.add_patch(
            barra_home
        )

        ancho_centro_home = min(
            0.08,
            valor_home / 2
        )

        centro_home = Rectangle(
            (
                -ancho_centro_home,
                y - altura / 2
            ),
            ancho_centro_home,
            altura,
            facecolor=color_home,
            edgecolor="none",
            zorder=3,
        )

        ax.add_patch(
            centro_home
        )

    # Barra visitante
    if valor_away > 0:
        radio_away = min(
            radio_maximo,
            valor_away / 2,
            altura / 2,
        )

        barra_away = FancyBboxPatch(
            (
                0,
                y - altura / 2
            ),
            valor_away,
            altura,
            boxstyle=(
                f"round,pad=0,"
                f"rounding_size={radio_away}"
            ),
            facecolor=color_away,
            edgecolor="none",
            zorder=2,
        )

        ax.add_patch(
            barra_away
        )

        ancho_centro_away = min(
            0.08,
            valor_away / 2
        )

        centro_away = Rectangle(
            (
                0,
                y - altura / 2
            ),
            ancho_centro_away,
            altura,
            facecolor=color_away,
            edgecolor="none",
            zorder=3,
        )

        ax.add_patch(
            centro_away
        )

def dibujar_tarjeta_metrica(
    ax,
    x,
    y,
    ancho,
    alto,
    etiqueta,
    valor_home,
    valor_away,
    color_home,
    color_away,
):
    tarjeta = FancyBboxPatch(
        (
            x - ancho / 2,
            y - alto / 2
        ),
        ancho,
        alto,
        boxstyle=(
            "round,pad=0,"
            "rounding_size=0.06"
        ),
        facecolor=PANEL,
        edgecolor="none",
        zorder=1,
    )

    ax.add_patch(
        tarjeta
    )

    ax.text(
        x,
        y + 0.17,
        etiqueta,
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=MUTED_TEXT,
        zorder=2,
    )

    ax.text(
        x - ancho * 0.23,
        y - 0.10,
        valor_home,
        ha="center",
        va="center",
        fontsize=23,
        fontweight="bold",
        color=color_home,
        zorder=2,
    )

    ax.text(
        x,
        y - 0.10,
        "|",
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
        alpha=0.35,
        zorder=2,
    )

    ax.text(
        x + ancho * 0.23,
        y - 0.10,
        valor_away,
        ha="center",
        va="center",
        fontsize=23,
        fontweight="bold",
        color=color_away,
        zorder=2,
    )

def crear_comparacion_general(
    partido,
    ruta_salida
):
    aplicar_tema()

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    color_home, color_away = obtener_colores_equipos(
        home,
        away
    )

    home_stats = home["statistics"]
    away_stats = away["statistics"]

    score = partido["match"]["score"]

    competencia = partido[
        "match"
    ]["competition"]

    estadisticas = [
        (
            "POSESION",
            home_stats["possession_pct"],
            away_stats["possession_pct"],
            "pct",
        ),
        (
            "TIROS",
            home_stats["shots"]["total"],
            away_stats["shots"]["total"],
            "int",
        ),
        (
            "TIROS AL ARCO",
            home_stats["shots"]["on_target"],
            away_stats["shots"]["on_target"],
            "int",
        ),
        (
            "xG",
            home_stats["expected_goals"],
            away_stats["expected_goals"],
            "decimal",
        ),
        (
            "PASES",
            home_stats["passes"]["total"],
            away_stats["passes"]["total"],
            "int",
        ),
        (
            "PRECISION DE PASE",
            home_stats["passes"]["accuracy_pct"],
            away_stats["passes"]["accuracy_pct"],
            "pct",
        ),
    ]

    fig, ax = plt.subplots(
        figsize=(10.8, 13.5),
        dpi=100
    )

    fig.subplots_adjust(
        left=0.06,
        right=0.94,
        top=0.95,
        bottom=0.06
    )

    logo = Image.open(
    "assets/independiente_logo.png"
    )

    imagen_logo = OffsetImage(
        logo,
        zoom=0.68,
        alpha=0.025
    )

    watermark = AnnotationBbox(
        imagen_logo,
        (0, 2.5),
        frameon=False,
        zorder=0
    )

    ax.add_artist(
        watermark
    )

    fig.patch.set_facecolor(
        BACKGROUND
    )

    ax.set_facecolor(
        BACKGROUND
    )

    cantidad = len(
        estadisticas
    )

    ax.set_xlim(
        -1.22,
        1.22
    )

    ax.set_ylim(
        -0.35,
        cantidad + 1.3
    )

    ax.axis("off")

    # Encabezado

    ax.text(
        -1.02,
        cantidad + 0.9,
        home["name"],
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if home["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        1.02,
        cantidad + 0.9,
        away["name"],
        ha="right",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if away["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        0,
        cantidad + 0.9,
        (
            f"{score['home']} "
            f"- "
            f"{score['away']}"
        ),
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )

    ax.text(
        0,
        cantidad + 0.45,
        (
            f"{competencia['name']} "
            f"| {competencia['round']}"
        ),
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
    )

    ax.plot(
        [-0.18, 0.18],
        [cantidad + 0.22, cantidad + 0.22],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
        zorder=4,
    )

    # Estadisticas

    for indice, estadistica in enumerate(
        estadisticas
    ):
        (
            nombre,
            valor_home,
            valor_away,
            tipo,
        ) = estadistica

        y = cantidad - 1 - indice

        # Todas las filas a la misma escala - ver
        # calcular_barras_comparacion para el detalle de
        # por que valor/100 rompe la comparacion entre filas.
        home_bar, away_bar = calcular_barras_comparacion(
            valor_home,
            valor_away
        )

        dibujar_barra_comparacion(
            ax,
            y,
            home_bar,
            away_bar,
            color_home,
            color_away,
            altura=0.28,
        )

        ax.text(
            0,
            y + 0.29,
            nombre,
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color=MUTED_TEXT,
        )

        ax.text(
            -1.07,
            y,
            formatear_valor(
                valor_home,
                tipo
            ),
            ha="right",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )

        ax.text(
            1.07,
            y,
            formatear_valor(
                valor_away,
                tipo
            ),
            ha="left",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )


    agregar_marca_de_cuenta(fig)

    ruta = Path(
        ruta_salida
    )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        ruta,
        dpi=100,
        facecolor=BACKGROUND,
    )

    plt.close(
        fig
    )

    return ruta

def crear_perfil_ofensivo(
    partido,
    metricas,
    ruta_salida
):
    aplicar_tema()

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    color_home, color_away = obtener_colores_equipos(
        home,
        away
    )

    home_stats = home["statistics"]
    away_stats = away["statistics"]

    home_metricas = metricas["home"]
    away_metricas = metricas["away"]

    score = partido["match"]["score"]

    competencia = partido[
        "match"
    ]["competition"]

    fig, ax = plt.subplots(
        figsize=(10.8, 13.5),
        dpi=100
    )

    fig.subplots_adjust(
        left=0.06,
        right=0.94,
        top=0.95,
        bottom=0.06
    )

    fig.patch.set_facecolor(
        BACKGROUND
    )

    ax.set_facecolor(
        BACKGROUND
    )

    ax.set_xlim(
        -1.22,
        1.22
    )

    ax.set_ylim(
        -0.35,
        7.3
    )

    ax.axis("off")

    logo = Image.open(
        "assets/independiente_logo.png"
    )

    imagen_logo = OffsetImage(
        logo,
        zoom=0.68,
        alpha=0.025
    )

    watermark = AnnotationBbox(
        imagen_logo,
        (0, 2.45),
        frameon=False,
        zorder=0
    )

    ax.add_artist(
        watermark
    )

    ax.text(
        -1.02,
        6.9,
        home["name"],
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if home["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        1.02,
        6.9,
        away["name"],
        ha="right",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if away["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        0,
        6.9,
        (
            f"{score['home']} "
            f"- "
            f"{score['away']}"
        ),
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )

    ax.text(
        0,
        6.45,
        (
            f"{competencia['name']} "
            f"| {competencia['round']}"
        ),
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
    )

    ax.plot(
        [-0.18, 0.18],
        [6.22, 6.22],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
        zorder=4,
    )

    ax.text(
        0,
        5.65,
        "ATAQUE Y CALIDAD DE OCASIONES",
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color=TEXT,
    )

    dibujar_tarjeta_metrica(
        ax,
        x=-0.76,
        y=4.85,
        ancho=0.66,
        alto=0.72,
        etiqueta="TIROS",
        valor_home=str(
            home_stats["shots"]["total"]
        ),
        valor_away=str(
            away_stats["shots"]["total"]
        ),
        color_home=color_home,
        color_away=color_away,
    )

    dibujar_tarjeta_metrica(
        ax,
        x=0,
        y=4.85,
        ancho=0.66,
        alto=0.72,
        etiqueta="xG",
        valor_home=formatear_decimal(
            home_stats["expected_goals"],
            2
        ),
        valor_away=formatear_decimal(
            away_stats["expected_goals"],
            2
        ),
        color_home=color_home,
        color_away=color_away,
    )

    dibujar_tarjeta_metrica(
        ax,
        x=0.76,
        y=4.85,
        ancho=0.66,
        alto=0.72,
        etiqueta="xG POR TIRO",
        valor_home=formatear_decimal(
            home_metricas["xg_per_shot"],
            2
        ),
        valor_away=formatear_decimal(
            away_metricas["xg_per_shot"],
            2
        ),
        color_home=color_home,
        color_away=color_away,
    )

    estadisticas_pct = [
        (
            "TIROS DENTRO DEL AREA",
            home_metricas["inside_box_pct"],
            away_metricas["inside_box_pct"],
        ),
        (
            "PRECISION DE TIRO",
            home_metricas["shot_accuracy_pct"],
            away_metricas["shot_accuracy_pct"],
        ),
        (
            "CONVERSION DE GOL",
            home_metricas["goal_conversion_pct"],
            away_metricas["goal_conversion_pct"],
        ),
    ]

    posiciones_y = [
        3.65,
        2.55,
        1.45,
    ]

    for (
        nombre,
        valor_home,
        valor_away
    ), y in zip(
        estadisticas_pct,
        posiciones_y
    ):
        # Mismo criterio que en crear_comparacion_general:
        # share del combinado, nunca valor/100 (estos 3 son
        # porcentajes independientes que no suman 100, asi
        # que valor/100 los dejaba con "tamaños" de barra
        # inconsistentes entre si - CONVERSION DE GOL
        # llegaba a verse casi vacia con esto).
        home_bar, away_bar = calcular_barras_comparacion(
            valor_home,
            valor_away
        )

        dibujar_barra_comparacion(
            ax,
            y,
            home_bar,
            away_bar,
            color_home,
            color_away,
            altura=0.28,
        )

        ax.text(
            0,
            y + 0.31,
            nombre,
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color=MUTED_TEXT,
        )

        ax.text(
            -1.07,
            y,
            (
                f"{valor_home:.1f}%"
                if valor_home is not None
                else "N/D"
            ),
            ha="right",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )

        ax.text(
            1.07,
            y,
            (
                f"{valor_away:.1f}%"
                if valor_away is not None
                else "N/D"
            ),
            ha="left",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )

    # Cierre de la placa: GOLES - xG (sobre/bajo rendimiento).
    # Ya estaba calculado en metrics.py pero no se mostraba en
    # ningun lado - ademas de sumar informacion real (en vez
    # de dejar el espacio vacio), es un buen cierre narrativo
    # para una placa sobre "calidad de ocasiones": volumen ->
    # calidad -> precision -> efectividad -> y aca, si esa
    # efectividad estuvo por encima o por debajo de lo
    # esperado segun el xG generado.
    y_cierre = 0.55

    ax.plot(
        [-0.18, 0.18],
        [y_cierre + 0.5, y_cierre + 0.5],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
        zorder=4,
    )

    dibujar_tarjeta_metrica(
        ax,
        x=0,
        y=y_cierre,
        ancho=1.9,
        alto=0.72,
        etiqueta="GOLES - xG  (sobre / bajo rendimiento)",
        valor_home=formatear_decimal_con_signo(
            home_metricas["goals_minus_xg"],
            2
        ),
        valor_away=formatear_decimal_con_signo(
            away_metricas["goals_minus_xg"],
            2
        ),
        color_home=color_home,
        color_away=color_away,
    )

    agregar_marca_de_cuenta(fig)

    ruta = Path(
        ruta_salida
    )
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        ruta,
        dpi=100,
        facecolor=BACKGROUND,
    )

    plt.close(
        fig
    )

    return ruta

def crear_xi_ratings(
    partido,
    ruta_salida
):
    aplicar_tema()

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    equipo = obtener_equipo_destacado(
        partido
    )

    alineacion = equipo.get(
        "lineup"
    )

    if not alineacion:
        return None

    titulares = alineacion.get(
        "start_xi",
        []
    )

    apellidos_duplicados = calcular_apellidos_duplicados(
        titulares
    )

    posiciones = obtener_posiciones_alineacion(
        titulares
    )

    if not posiciones:
        return None

    score = partido["match"]["score"]

    competencia = partido[
        "match"
    ]["competition"]

    formacion = alineacion.get(
        "formation"
    )

    entrenador = alineacion.get(
        "coach",
        {}
    )

    fig = plt.figure(
        figsize=(10.8, 13.5),
        dpi=100,
        facecolor=BACKGROUND,
    )

    # Encabezado
    ax_header = fig.add_axes(
        [0.06, 0.76, 0.88, 0.19]
    )

    ax_header.set_facecolor(
        BACKGROUND
    )

    ax_header.set_xlim(
        -1.22,
        1.22
    )

    ax_header.set_ylim(
        0,
        1
    )

    ax_header.axis(
        "off"
    )

    ax_header.text(
        -1.02,
        0.82,
        home["name"],
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if home["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax_header.text(
        1.02,
        0.82,
        away["name"],
        ha="right",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if away["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax_header.text(
        0,
        0.82,
        (
            f"{score['home']} "
            f"- "
            f"{score['away']}"
        ),
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )

    ax_header.text(
        0,
        0.55,
        (
            f"{competencia['name']} "
            f"| {competencia['round']}"
        ),
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
    )

    ax_header.plot(
        [-0.18, 0.18],
        [0.40, 0.40],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
    )

    ax_header.text(
        0,
        0.15,
        "XI INICIAL Y RATINGS",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color=TEXT,
    )

    fig.text(
        0.5,
        0.745,
        (
            f"{equipo['name']}  |  "
            f"{formacion}  |  "
            f"DT: {entrenador.get('name', 'N/D')}"
        ),
        ha="center",
        va="center",
        fontsize=14,
        color=MUTED_TEXT,
    )

    ax_pitch = fig.add_axes(
        [0.12, 0.07, 0.76, 0.64]
    )

    pitch = VerticalPitch(
        pitch_type="statsbomb",
        pitch_color=PANEL,
        line_color=DIVIDER,
        linewidth=1.5,
        corner_arcs=True,
        goal_type="box",
    )

    pitch.draw(
        ax=ax_pitch
    )

    for posicion in posiciones:
        jugador_lineup = posicion[
            "player"
        ]

        x = posicion["x"]
        y = posicion["y"]

        datos = buscar_datos_jugador(
            equipo,
            jugador_lineup["id"]
        )

        rating = (
            datos["rating"]
            if datos
            else None
        )

        numero = jugador_lineup.get(
            "number"
        )

        nombre = acortar_nombre(
            jugador_lineup.get(
                "name"
            ),
            apellidos_duplicados
        )

        color_rating, color_texto_rating = (
            obtener_estilo_rating(
                rating
            )
        )

        # Circulo del jugador
        pitch.scatter(
            x,
            y,
            s=1050,
            color=TRACK,
            edgecolors=ACCENT,
            linewidth=2.2,
            zorder=3,
            ax=ax_pitch,
        )

        # Dorsal
        pitch.annotate(
            str(numero)
            if numero is not None
            else "-",
            xy=(x, y),
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold",
            color=TEXT,
            zorder=4,
            ax=ax_pitch,
        )

        # Rating
        texto_rating = (
            f"{rating:.1f}"
            if rating is not None
            else "N/D"
        )

        # OJO: pitch.annotate() de mplsoccer invierte SIEMPRE
        # el tuple de xytext en VerticalPitch (x,y) -> (y,x),
        # sin mirar textcoords. Por eso el offset real que
        # necesitamos "hacia abajo" (0, -18) hay que pasarlo
        # pre-invertido como (-18, 0) para que, tras el swap
        # interno de mplsoccer, termine siendo (0, -18).
        pitch.annotate(
            texto_rating,
            xy=(x, y),
            xytext=(-18, 0),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=color_texto_rating,
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": color_rating,
                "edgecolor": PANEL,
                "linewidth": 1.4,
            },
            zorder=6,
            ax=ax_pitch,
        )

        # Nombre debajo del jugador
        # Mismo tema: pre-invertimos (0, -32) -> (-32, 0)
        # para que mplsoccer lo vuelva a invertir y quede
        # realmente 32pts hacia abajo (debajo del rating).
        #
        # El fontsize es dinamico (obtener_fontsize_nombre):
        # en filas de 4-5 jugadores hay menos espacio
        # horizontal, asi que ahi la fuente es mas chica para
        # no pisar el nombre del vecino - ver el comentario de
        # esa funcion para la cuenta completa.
        pitch.annotate(
            nombre,
            xy=(x, y),
            xytext=(-32, 0),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=obtener_fontsize_nombre(
                posicion["cantidad_fila"]
            ),
            fontweight="bold",
            color=TEXT,
            zorder=5,
            ax=ax_pitch,
        )

    agregar_marca_de_cuenta(fig)

    ruta = Path(
        ruta_salida
    )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        ruta,
        dpi=100,
        facecolor=BACKGROUND,
    )

    plt.close(
        fig
    )

    return ruta

def obtener_lado_destacado(partido):
    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    if home["id"] == INDEPENDIENTE_ID:
        return "home"

    if away["id"] == INDEPENDIENTE_ID:
        return "away"

    # Fallback para fixtures de desarrollo
    return "home"

FOTO_PIXELES = 108
FOTO_TAMANO_PREP = 216


def _color_hex_a_rgba(hex_color, alpha=255):
    valor = hex_color.lstrip("#")

    return (
        int(valor[0:2], 16),
        int(valor[2:4], 16),
        int(valor[4:6], 16),
        alpha,
    )


def preparar_foto_circular(ruta, tamano=FOTO_TAMANO_PREP):
    imagen = Image.open(ruta).convert("RGBA")

    ancho, alto = imagen.size
    lado = min(ancho, alto)
    left = (ancho - lado) // 2
    top = (alto - lado) // 2

    imagen = imagen.crop(
        (left, top, left + lado, top + lado)
    )
    imagen = imagen.resize(
        (tamano, tamano),
        Image.Resampling.LANCZOS
    )

    mascara = Image.new("L", (tamano, tamano), 0)
    ImageDraw.Draw(mascara).ellipse(
        (1, 1, tamano - 2, tamano - 2),
        fill=255
    )

    # Fondo PANEL para que una foto con transparencia
    # no "rompa" el circulo sobre el watermark.
    fondo = Image.new(
        "RGBA",
        (tamano, tamano),
        _color_hex_a_rgba(PANEL)
    )
    fondo.paste(imagen, (0, 0), imagen)
    fondo.putalpha(mascara)

    return fondo


def _fontsize_nombre_destacado(nombre):
    largo = len(nombre or "")

    if largo > 20:
        return 15

    if largo > 16:
        return 17

    return 19


def dibujar_foto_o_dorsal(ax, x, y, destacado):
    """
    Foto circular recortada, o el dorsal si no hay foto.

    scatter() para el anillo: un Circle() en este ax se
    achata porque X e Y no tienen la misma escala (el
    mismo motivo que en la placa anterior).
    """
    ruta_foto = obtener_foto_jugador(
        destacado.get("id"),
        destacado.get("photo"),
    )

    ax.scatter(
        x,
        y,
        s=2350,
        color=TRACK,
        edgecolors=ACCENT,
        linewidth=2.2,
        zorder=2,
    )

    if ruta_foto:
        try:
            foto = preparar_foto_circular(ruta_foto)
            zoom = FOTO_PIXELES / max(foto.size)

            caja = AnnotationBbox(
                OffsetImage(foto, zoom=zoom),
                (x, y),
                frameon=False,
                pad=0,
                zorder=3,
            )
            ax.add_artist(caja)
            return
        except Exception as error:
            print(
                f"[visualizations] No se pudo usar la "
                f"foto de {destacado.get('name')}: {error}"
            )

    ax.text(
        x,
        y,
        str(destacado["number"])
        if destacado.get("number") is not None
        else "-",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color=TEXT,
        zorder=3,
    )


def dibujar_tarjeta_destacado(ax, y, alto, destacado):
    ancho = 2.2
    x_foto = -ancho / 2 + 0.36
    x_texto = x_foto + 0.38

    tarjeta = FancyBboxPatch(
        (
            -ancho / 2,
            y - alto / 2
        ),
        ancho,
        alto,
        boxstyle=(
            "round,pad=0,"
            "rounding_size=0.06"
        ),
        facecolor=PANEL,
        edgecolor="none",
        zorder=1,
    )

    ax.add_patch(tarjeta)

    dibujar_foto_o_dorsal(
        ax,
        x_foto,
        y,
        destacado
    )

    nombre = destacado["display_name"]
    minutos = destacado.get("minutes")
    minutos_txt = (
        f"{int(minutos)}'"
        if minutos is not None
        else ""
    )

    meta = destacado["position_label"]

    if minutos_txt:
        meta = f"{meta}  ·  {minutos_txt}"

    ax.text(
        x_texto,
        y + 0.48,
        nombre,
        ha="left",
        va="center",
        fontsize=_fontsize_nombre_destacado(nombre),
        fontweight="bold",
        color=TEXT,
        zorder=2,
    )

    ax.text(
        x_texto,
        y + 0.26,
        meta,
        ha="left",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=MUTED_TEXT,
        zorder=2,
    )

    color_rating, color_texto_rating = (
        obtener_estilo_rating(
            destacado["rating"]
        )
    )

    ax.add_patch(
        FancyBboxPatch(
            (
                ancho / 2 - 0.46,
                y + alto / 2 - 0.36
            ),
            0.34,
            0.24,
            boxstyle=(
                "round,pad=0,"
                "rounding_size=0.05"
            ),
            facecolor=color_rating,
            edgecolor="none",
            zorder=2,
        )
    )

    ax.text(
        ancho / 2 - 0.29,
        y + alto / 2 - 0.24,
        formatear_decimal(
            destacado["rating"],
            1
        ),
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=color_texto_rating,
        zorder=3,
    )

    if destacado.get("es_figura"):
        ax.text(
            ancho / 2 - 0.12,
            y + alto / 2 - 0.50,
            "FIGURA",
            ha="right",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=ACCENT,
            zorder=3,
        )

    stats = destacado.get("stats") or []
    y_stats = [0.02, -0.22, -0.46]
    x_label = x_texto + 0.50

    for stat, y_stat in zip(stats, y_stats):
        ax.text(
            x_texto,
            y + y_stat,
            stat["value"],
            ha="left",
            va="center",
            fontsize=16,
            fontweight="bold",
            color=ACCENT,
            zorder=2,
        )

        ax.text(
            x_label,
            y + y_stat,
            stat["label"],
            ha="left",
            va="center",
            fontsize=13,
            fontweight="bold",
            color=MUTED_TEXT,
            zorder=2,
        )

def crear_rendimiento_individual(
    partido,
    metricas,
    ruta_salida
):
    aplicar_tema()

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    lado_destacado = obtener_lado_destacado(
        partido
    )

    equipo_destacado = partido["teams"][
        lado_destacado
    ]

    jugadores_equipo = metricas["players"][
        lado_destacado
    ]

    destacados = construir_destacados(
        equipo_destacado,
        jugadores_equipo
    )

    if not destacados:
        return None

    score = partido["match"]["score"]

    competencia = partido[
        "match"
    ]["competition"]

    fig, ax = plt.subplots(
        figsize=(10.8, 13.5),
        dpi=100
    )

    fig.subplots_adjust(
        left=0.06,
        right=0.94,
        top=0.95,
        bottom=0.06
    )

    fig.patch.set_facecolor(
        BACKGROUND
    )

    ax.set_facecolor(
        BACKGROUND
    )

    ax.set_xlim(
        -1.22,
        1.22
    )

    ax.set_ylim(
        -0.35,
        7.3
    )

    ax.axis("off")

    logo = Image.open(
        "assets/independiente_logo.png"
    )

    imagen_logo = OffsetImage(
        logo,
        zoom=0.68,
        alpha=0.025
    )

    watermark = AnnotationBbox(
        imagen_logo,
        (0, 2.45),
        frameon=False,
        zorder=0
    )

    ax.add_artist(
        watermark
    )

    ax.text(
        -1.02,
        6.9,
        home["name"],
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if home["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        1.02,
        6.9,
        away["name"],
        ha="right",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if away["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        0,
        6.9,
        (
            f"{score['home']} "
            f"- "
            f"{score['away']}"
        ),
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )

    ax.text(
        0,
        6.45,
        (
            f"{competencia['name']} "
            f"| {competencia['round']}"
        ),
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
    )

    ax.plot(
        [-0.18, 0.18],
        [6.22, 6.22],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
        zorder=4,
    )

    ax.text(
        0,
        5.65,
        "RENDIMIENTOS DESTACADOS",
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color=TEXT,
    )

    ax.text(
        0,
        5.28,
        f"Los destacados de {equipo_destacado['name']}",
        ha="center",
        va="center",
        fontsize=14,
        color=MUTED_TEXT,
    )

    alto_tarjeta = 1.52
    gap = 0.16

    y_inicial = 4.30

    for indice, destacado in enumerate(destacados):
        y = y_inicial - indice * (alto_tarjeta + gap)

        dibujar_tarjeta_destacado(
            ax,
            y,
            alto_tarjeta,
            destacado,
        )

    agregar_marca_de_cuenta(fig)

    ruta = Path(
        ruta_salida
    )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        ruta,
        dpi=100,
        facecolor=BACKGROUND,
    )

    plt.close(
        fig
    )

    return ruta
