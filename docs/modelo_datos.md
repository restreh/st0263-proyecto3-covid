# Modelo de datos del proyecto

Este documento describe el modelo de datos propuesto para el Proyecto 3, incluyendo el modelo relacional en RDS y la organización de los datos en S3 (zonas *raw*, *trusted* y *refined*).

---

## 1. Visión general

El pipeline utilizará dos tipos de almacenamiento de datos:

1. **Base de datos relacional (RDS)**
   - Contendrá información complementaria a los casos de COVID-19, principalmente datos demográficos y de capacidad hospitalaria por departamento.
   - Se usará para enriquecer los datos del dataset principal de COVID-19 durante el procesamiento en Spark.

2. **Almacenamiento en S3**
   - Contendrá el dataset principal de COVID-19 y todos los resultados intermedios y finales.
   - Se dividirá en tres zonas lógicas: **raw**, **trusted** y **refined**.

### 3.2. Zona trusted

Objetivo: almacenar datos limpios, normalizados y listos para análisis.

Ruta base:

- `s3://st0263-proyecto3-covid19/trusted/`

Subcarpetas y particiones sugeridas:

1. Datos de casos COVID-19 limpios:
   - `trusted/covid/`
   - Con particiones por año, mes, día, y departamento si es posible.
   Ejemplo de rutas:
   - `trusted/covid/anio=2020/mes=01/dia=01/part-0000.snappy.parquet`
   - `trusted/covid/anio=2020/mes=01/dia=02/part-0001.snappy.parquet`
   - `trusted/covid/anio=2020/mes=01/dia=01/departamento=05/part-0000.snappy.parquet`

2. Datos complementarios estandarizados (a partir de RDS):
   - `trusted/demografia/`
   - `trusted/capacidad_hospitalaria/`

Formato de archivos recomendado en trusted:

- Parquet (columnar, comprimido), para optimizar consultas y procesamiento.

### 3.3. Zona refined

Objetivo: almacenar salidas analíticas finales, métricas agregadas e indicadores.

Ruta base:

- `s3://st0263-proyecto3-covid19/refined/`

Subcarpetas típicas:

1. Indicadores por departamento y fecha:
   - `refined/indicadores_departamento/`
   Ejemplo de métricas:
   - Casos nuevos diarios por departamento.
   - Casos acumulados por departamento.
   - Casos por 100.000 habitantes.
   - Porcentaje de ocupación UCI aproximado (combinando información COVID + capacidad).

   Ejemplo de rutas:
   - `refined/indicadores_departamento/anio=2020/mes=01/dia=01/part-0000.snappy.parquet`

2. Indicadores regionales o nacionales:
   - `refined/indicadores_region/`
   - `refined/indicadores_pais/`

3. Tablas específicas para consumo por API:
   - `refined/api_views/`
   Ejemplos:
   - `refined/api_views/top_departamentos_casos_diarios/`
   - `refined/api_views/resumen_nacional_diario/`

Formato de archivos recomendado en refined:

- Parquet para análisis,
- Opcionalmente, copias en CSV/JSON si se requiere para consumo directo desde otras herramientas.

---

## 4. Resumen de entidades principales

- **RDS**
  - `departamento_demografia`
  - `departamento_capacidad_hospitalaria`

- **S3**
  - Zona `raw`
    - `raw/covid/`
    - `raw/rds/`
  - Zona `trusted`
    - `trusted/covid/`
    - `trusted/demografia/`
    - `trusted/capacidad_hospitalaria/`
  - Zona `refined`
    - `refined/indicadores_departamento/`
    - `refined/indicadores_region/`
    - `refined/indicadores_pais/`
    - `refined/api_views/`

Este modelo servirá como base para el diseño de los procesos de ingestión, transformación y publicación de datos en el proyecto.
