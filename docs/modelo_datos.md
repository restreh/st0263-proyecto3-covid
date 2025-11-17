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

---

## 2. Modelo relacional en RDS

El modelo relacional mínimo propuesto incluye dos tablas: una de demografía por departamento y otra de capacidad hospitalaria por departamento y fecha. El objetivo es poder calcular métricas relativas (por ejemplo, casos por 100.000 habitantes) y relacionarlas con la infraestructura disponible.

### 2.1. Tabla `departamento_demografia`

Información demográfica básica por departamento.

- Nombre de la tabla: `departamento_demografia`

Campos:

| Columna              | Tipo          | Descripción                                                            |
|----------------------|---------------|------------------------------------------------------------------------|
| `codigo_departamento`| VARCHAR(5)    | Código del departamento (por ejemplo, código DANE). **PK**            |
| `nombre_departamento`| VARCHAR(100)  | Nombre del departamento (mayúsculas sostenidas).                       |
| `region`             | VARCHAR(50)   | Región del país a la que se asocia el departamento (ej. ANDINA).      |
| `poblacion`          | BIGINT        | Población estimada del departamento.                                   |
| `anio_corte`         | INT           | Año de referencia de la población (ej. 2020).                          |

Restricciones principales:

- **Clave primaria (PK)**: `codigo_departamento`
- Se recomienda índice adicional en `region` para consultas analíticas por región.

### 2.2. Tabla `departamento_capacidad_hospitalaria`

Información resumida de capacidad hospitalaria por departamento y fecha, enfocada en unidades de cuidado intensivo (UCI).

- Nombre de la tabla: `departamento_capacidad_hospitalaria`

Campos:

| Columna                | Tipo          | Descripción                                                                      |
|------------------------|---------------|----------------------------------------------------------------------------------|
| `id_capacidad`         | BIGINT        | Identificador único de la fila. **PK**                                          |
| `fecha`                | DATE          | Fecha del registro de la capacidad.                                             |
| `codigo_departamento`  | VARCHAR(5)    | Código del departamento. **FK** a `departamento_demografia.codigo_departamento` |
| `camas_uci_totales`    | INT           | Número total de camas UCI disponibles.                                          |
| `camas_uci_ocupadas`   | INT           | Número de camas UCI ocupadas en la fecha dada.                                  |
| `fuente`               | VARCHAR(100)  | Fuente del dato (nombre del informe, entidad, etc.).                            |

Restricciones principales:

- **Clave primaria (PK)**: `id_capacidad`
- **Clave foránea (FK)**: `codigo_departamento` → `departamento_demografia.codigo_departamento`
- Índices recomendados:
  - Índice compuesto en (`fecha`, `codigo_departamento`) para consultas por rango de fechas y departamento.

### 2.3. Relación con el dataset principal de COVID-19

El dataset principal de COVID-19 (almacenado en S3) suele tener campos como:

- Fecha del diagnóstico / notificación.
- Departamento de residencia o departamento de ocurrencia.
- Estado del caso (activo, recuperado, fallecido).
- Edad, sexo, tipo de caso, etc.

Para el cruce con RDS se usará:

- El código o nombre del departamento, estandarizado para enlazar con `codigo_departamento` o `nombre_departamento` de la tabla `departamento_demografia`.

En el proceso de ETL en Spark se definirá una lógica de normalización para que el campo de departamento del dataset COVID-19 quede alineado con el código de departamento usado en RDS.

---

## 3. Modelo de datos en S3

Los datos en S3 se organizarán en tres zonas: **raw**, **trusted** y **refined**. Cada zona tendrá una estructura de carpetas coherente y, en lo posible, se utilizará particionamiento por fecha y departamento.

Supondremos un bucket general llamado:

- `st0263-proyecto3-covid19`

### 3.1. Zona raw

Objetivo: almacenar los datos tal como llegan, sin transformar.

Ruta base:

- `s3://st0263-proyecto3-covid19/raw/`

Subcarpetas principales:

1. Datos de COVID-19:
   - `raw/covid/`  
   Ejemplos de rutas:
   - `raw/covid/casos_covid_2020-01-01.csv`
   - `raw/covid/casos_covid_2020-01-02.csv`
   - `raw/covid/casos_covid_historico.csv`

2. Exportaciones desde RDS (copias de seguridad o extractos para procesamiento distribuido):
   - `raw/rds/`  
   Ejemplos de rutas:
   - `raw/rds/departamento_demografia.csv`
   - `raw/rds/departamento_capacidad_hospitalaria.csv`

Formato de archivos recomendado en raw:

- CSV o JSON, de acuerdo con el formato de descarga de la fuente oficial.

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
