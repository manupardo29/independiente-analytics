import json
from pathlib import Path


def guardar_json(datos, ruta):
    ruta = Path(ruta)

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    return ruta

def cargar_json(ruta):
    ruta = Path(ruta)

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:
        return json.load(archivo)