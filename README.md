# Independiente Analytics

Pipeline de Football Analytics en Python que convierte los datos de
un partido (via [API-Football](https://www.api-football.com/)) en un
reporte post-partido automatizado — métricas propias y visualizaciones
1080x1350 pensadas para un carrusel de Instagram.

La identidad visual y el caso de uso principal están centrados en
Club Atlético Independiente, pero la arquitectura no depende de eso:
el pipeline arranca de un `fixture_id` y funciona con cualquier
partido que tenga datos suficientemente completos.

## Filosofía

- **Un dato, un gráfico.** Cada placa responde una sola pregunta
  concreta sobre el partido — no se busca poner todas las
  estadísticas disponibles en una imagen.
- **Validar antes de generar.** Un fixture marcado como `FT` no
  garantiza que las estadísticas estén completas. Si los datos
  parecen inconsistentes, el pipeline se detiene antes de generar
  nada — mejor no publicar una placa que publicar una con datos
  incorrectos.
- **No fabricar lo que los datos no dan.** No usamos coordenadas de
  pases, tracking ni posiciones promedio porque API-Football no las
  provee. Ninguna visualización simula ese tipo de dato.
- **Diseño, no decoración.** Fondo oscuro, pocos colores, jerarquía
  clara, lectura rápida desde el celular.

## Pipeline

```
API-Football
    │
    ▼
data/raw/fixture_<id>.json        (JSON crudo del proveedor)
    │
    ▼
validation.py                     (¿los datos son coherentes?)
    │
    ▼
normalize.py                      (esquema propio, independiente del proveedor)
    │
    ▼
data/normalized/fixture_<id>.json
    │
    ▼
metrics.py                        (métricas derivadas)
    │
    ▼
visualizations.py
    │
    ▼
outputs/figures/*.png             (1080x1350, listas para Instagram)
```

## Setup

```bash
git clone <este-repo>
cd independiente-analytics
pip install -r requirements.txt
cp .env.example .env
```

Completá `.env` con tu API key de API-Football:

```
API_FOOTBALL_KEY=tu_key_aca
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
```

La primera vez que corras el pipeline con conexión a internet,
`theme.py` descarga y cachea la tipografía (Barlow Condensed) en
`assets/fonts/`. Si no hay conexión, cae automáticamente a la fuente
por defecto de matplotlib sin romper nada.

## Uso

```bash
python generate_match.py <fixture_id>
```

Ejemplo, con el fixture de desarrollo incluido en el repo:

```bash
python generate_match.py 1493077
```

Esto:

1. Carga `data/raw/fixture_<id>.json`.
2. Valida que los datos sean coherentes (si no, corta acá e imprime
   por qué).
3. Normaliza el partido a nuestro propio esquema.
4. Calcula las métricas derivadas.
5. Guarda el partido normalizado en `data/normalized/`.
6. Genera las 3 placas en `outputs/figures/`.
7. Imprime en consola las métricas y el Top 5 por rating de cada
   equipo.

### Iterar rápido sobre el diseño de las placas

Si ya tenés un fixture normalizado y solo querés retocar diseño sin
volver a pegarle a la API ni revalidar:

```bash
python scripts/preview.py <fixture_id>
```

Regenera las 3 placas importando las funciones reales de
`src/visualizations.py` — nunca las duplica, así no hay riesgo de
que un fix quede aplicado en un lado y en otro no.

## Estructura del repositorio

```
independiente-analytics/
├── assets/
│   ├── independiente_logo.png
│   └── fonts/                  (cache de tipografía, no se versiona)
├── data/
│   ├── raw/                    (JSON crudo de API-Football, no se versiona)
│   └── normalized/             (partidos ya normalizados)
├── outputs/
│   └── figures/                (placas generadas)
├── scripts/
│   └── preview.py              (scratchpad para iterar diseño)
├── src/
│   ├── api_football.py         (cliente de API-Football)
│   ├── metrics.py               (métricas derivadas)
│   ├── normalize.py             (JSON crudo -> esquema propio)
│   ├── storage.py               (leer/guardar JSON)
│   ├── theme.py                 (colores, tipografía, identidad visual)
│   ├── validation.py            (¿se puede generar este partido?)
│   └── visualizations.py        (las placas en sí)
├── generate_match.py            (entry point)
├── requirements.txt
└── .env.example
```

## Estado del carrusel

| # | Placa | Estado |
|---|-------|--------|
| 1 | Comparación general | Terminada |
| 2 | Ataque y calidad de ocasiones | Terminada |
| 3 | XI inicial y ratings | Terminada |
| 4 | Rendimiento individual | Planeada |
| 5 | Pase y creación | Planeada |
| 6 | Timeline del partido | Planeada |

No todos los partidos necesitan exactamente las mismas placas —
según la historia del encuentro puede tener sentido agregar
defensa, rendimiento del arquero, impacto de suplentes, disciplina o
pelota parada.

## Limitaciones conocidas

API-Football da buenos datos agregados, pero no es un dataset de
eventos espaciales. Hoy no hay coordenadas reales de tiros, pases,
recuperaciones ni posiciones de jugadores durante el partido — por
eso el proyecto no genera shot maps, pass maps, heatmaps ni mapas de
Voronoi. Un posible proyecto futuro (fuera del scope actual) es
combinar esto con un pipeline de computer vision (YOLO + tracking +
homografía) para derivar datos espaciales a partir de video.
