"""
Cache local de fotos de jugadores (API-Football).

Flujo:
    player_id -> assets/players/<id>.png
    si no esta y hay URL, se descarga una vez
    si falla, se devuelve None y la placa sigue

No usa el cliente de API-Football: la foto es un archivo
estatico en media.api-sports.io, el mismo patron que el
cache de tipografias en theme.py.
"""

import os
import urllib.request

from PIL import Image


PLAYERS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "assets",
    "players",
)

DOWNLOAD_TIMEOUT = 8


def _ruta_foto(player_id):
    return os.path.join(
        PLAYERS_DIR,
        f"{player_id}.png"
    )


def _archivo_usable(ruta):
    if not os.path.exists(ruta):
        return False

    if os.path.getsize(ruta) <= 0:
        return False

    try:
        with Image.open(ruta) as imagen:
            imagen.verify()

        return True

    except Exception:
        return False


def _es_placeholder_api(ruta):
    """
    API-Football a veces responde 200 con el avatar
    generico (silueta gris, archivo chico, pocos colores).
    Eso no es un fallo de red, pero en un fondo oscuro
    queda peor que el dorsal. Lo tratamos como 'sin foto'.
    """
    try:
        if os.path.getsize(ruta) >= 12000:
            return False

        with Image.open(ruta) as imagen:
            rgb = imagen.convert("RGB")
            colores = rgb.getcolors(maxcolors=512)

        # El avatar generico ronda ~80 colores por el
        # antialiasing; una cara real tiene miles.
        return colores is not None and len(colores) < 200

    except Exception:
        return False


def _descargar_foto(url, ruta):
    os.makedirs(
        PLAYERS_DIR,
        exist_ok=True
    )

    temporal = f"{ruta}.tmp"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "independiente-analytics"
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT
        ) as respuesta:
            datos = respuesta.read()

        if not datos:
            return False

        with open(temporal, "wb") as archivo:
            archivo.write(datos)

        os.replace(temporal, ruta)

        if not _archivo_usable(ruta):
            os.remove(ruta)
            return False

        return True

    except Exception as error:
        print(
            f"[photos] No se pudo descargar "
            f"{url} ({error})"
        )

        if os.path.exists(temporal):
            try:
                os.remove(temporal)
            except OSError:
                pass

        return False


def obtener_foto_jugador(player_id, url):
    """
    Devuelve la ruta local de la foto o None.

    Nunca levanta: una foto faltante no puede tumbar
    la generacion del reporte.
    """
    if not player_id:
        return None

    ruta = _ruta_foto(player_id)

    if _archivo_usable(ruta):
        if _es_placeholder_api(ruta):
            return None

        return ruta

    if os.path.exists(ruta):
        try:
            os.remove(ruta)
        except OSError:
            pass

    if not url:
        return None

    if _descargar_foto(url, ruta):
        return ruta

    return None
