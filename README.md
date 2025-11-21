# Pipeline ETL de Datos COVID-19 Colombia

<table>
    <tbody>
        <tr>
            <td>Curso</td>
            <td>ST0263 - Tópicos Especiales en Telemática</td>
        </tr>
        <tr>
            <td>Estudiantes</td>
            <td>
                Jerónimo Acosta Acevedo (<tt>jacostaa1[at]eafit.edu.co</tt>)<br>
                Juan José Restrepo Higuita (<tt>jjrestre10[at]eafit.edu.co</tt>)<br>
                Luis Miguel Torres Villegas (<tt>lmtorresv[at]eafit.edu.co</tt>)
            </td>
        </tr>
        <tr>
            <td>Profesor</td>
            <td>Edwin Montoya Múnera (<tt>emontoya[at]eafit.edu.co</tt>)</td>
        </tr>
    </tbody>
</table>

## 1. Descripción

Pipeline ETL batch para análisis de datos COVID-19 en Colombia mediante
procesamiento distribuido en AWS. Implementa arquitectura medallion
(raw/trusted/refined) con EMR Spark, almacenamiento en S3, base de datos RDS
MySQL y consultas analíticas con Athena.

### 1.1. Aspectos cumplidos

- **Ingesta de datos**: Descarga automática desde API Datos Abiertos Colombia
  (dataset `gt2j-8ykr`) hacia S3 raw zone con límite configurable
  (`ROWS_LIMIT`). Carga de datos demográficos complementarios en RDS MySQL.
- **Procesamiento distribuido**: Tres jobs PySpark en EMR que realizan
  transformaciones ETL, cálculo de indicadores epidemiológicos (casos nuevos,
  acumulados, tasa por 100k) y agregaciones nacionales.
- **Almacenamiento estructurado**: Datos particionados por fecha
  (`anio/mes/dia`) en formato Parquet con compresión Snappy.
- **Capa de consumo**: Consultas SQL interactivas mediante Athena sobre base de
  datos `refined_api_views` generada por AWS Glue Crawler.
- **Analítica con SparkSQL**: 6 queries SQL ejecutadas sobre DataFrames
  registrados como vistas temporales, persistiendo resultados en
  `refined/analytics/` para trazabilidad. Incluye análisis de distribución por
  edades, tendencias mensuales, desglose por género, hitos epidemiológicos y
  suavizado con promedios móviles.
- **API Gateway + Lambda**: Endpoint REST para acceso programático a indicadores
  refinados (en desarrollo). Consumirá mismos datos refined que Athena, pero
  mediante HTTP requests en lugar de queries SQL interactivas.

## 2. Arquitectura

### 2.1. Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│ Fuentes de datos                                                │
│  • API Datos Abiertos Colombia (casos COVID-19)                 │
│  • RDS MySQL (demografía por departamento)                      │
└────────────────────┬────────────────────────────────────────────┘
                     │ Ingesta
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ S3: s3://jacostaa1datalake/lake/                                │
│  ├─ raw/covid/         ← CSV original (1M registros)            │
│  ├─ raw/rds/           ← Exportación RDS (poblacion.csv)        │
│  ├─ trusted/covid/     ← Parquet limpio + join demográfico      │
│  ├─ refined/indicadores_departamento/  ← Métricas diarias       │
│  ├─ refined/analytics/ ← Resultados SparkSQL (6 datasets)       │
│  └─ refined/api_views/resumen_nacional_diario/  ← API views     │
└────────────────────┬────────────────────────────────────────────┘
                     │ Procesamiento
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ EMR Cluster (emr-7.11.0, m4.xlarge)                             │
│  • Step 1: raw → trusted (limpieza + join DIVIPOLA)             │
│  • Step 2: trusted → refined (indicadores departamentales)      │
│  • Step 3: refined → api_views (resumen nacional)               │
└────────────────────┬────────────────────────────────────────────┘
                     │ Catalogación
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ AWS Glue Crawler → DB: refined_api_views                        │
│  • Escaneo recursivo de refined/ en S3                          │
│  • Detección automática de esquema Parquet                      │
│  • Registro de particiones por fecha                            │
└────────────────────┬────────────────────────────────────────────┘
                     │ Consulta
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Athena (consultas SQL sobre S3)                                 │
│  • Editor de queries interactivo                                │
│  • Resultados en s3://bucket/athena/                            │
└─────────────────────────────────────────────────────────────────┘
```

<!-- TODO: Image of architecture diagram -->

### 2.2. Ciclo de vida de los datos

1. **Captura**: Script `download_covid_to_s3.py` descarga CSV desde API con
   límite de 1M registros (configurable via `ROWS_LIMIT`). Datos demográficos se
   cargan a RDS MySQL via `upload_csv_to_rds.py`.

2. **Exportación RDS**: Script `export_rds_to_s3.py` extrae tabla `poblacion`
   desde RDS hacia `lake/raw/rds/poblacion.csv`. Esto simula un sistema OLTP del
   cual se extraen datos complementarios.

3. **Transformación ETL**:
   - **Step 1** (`step_1_covid_to_trusted.py`): Lee casos COVID y demografía,
     normaliza departamentos usando códigos DIVIPOLA, agrega columnas de
     particionamiento temporal, escribe Parquet a `trusted/`.
   - **Step 2** (`step_2_covid_indicators_refined.py`): **Procesamiento dual
     DataFrame/SparkSQL**. Primero usa DataFrame API para agregaciones y window
     functions (indicadores departamentales). Luego registra DataFrames como
     vistas SQL temporales y ejecuta 6 queries SparkSQL para análisis
     exploratorio, persistiendo cada resultado como Parquet en
     `refined/analytics/`:
     1. Top 10 departamentos por tasa (CTE + ROW_NUMBER)
     2. Tendencias mensuales (agregación temporal)
     3. Distribución por edades (CASE binning + window percentage)
     4. Desglose por género y letalidad (agregación condicional)
     5. Hitos de 1000 casos (DATEDIFF milestone tracking)
     6. Promedio móvil 7 días nacional (window ROWS BETWEEN)
   - **Step 3** (`step_3_resumen_nacional_diario.py`): Agrega indicadores
     departamentales a nivel nacional.

4. **Catalogación**: Glue Crawler navega `refined/` recursivamente, infiere
   esquemas de Parquet particionados, crea/actualiza tablas en base de datos
   `refined_api_views`.

5. **Consumo dual**:
   - **Athena**: Consultas SQL interactivas sobre tablas
     catalogadas. Ideal para analistas, data scientists, exploración ad-hoc.
   - **API Gateway + Lambda**: Endpoints REST programáticos que
     leerán mismos datos refined. Ideal para aplicaciones web/móviles, dashboards
     automatizados.

   Ambos consumen **el mismo conjunto de datos** en refined zone, sirviendo
   distintos perfiles de usuario.

### 2.3. Patrones implementados

- **Medallion Architecture**: Separación raw (datos brutos) → trusted (limpios)
  → refined (analíticos).
- **Particionamiento por fecha**: Optimización de queries con predicados
  temporales (`WHERE anio=2020 AND mes=12`).
- **Idempotencia**: Steps EMR usan `.mode("overwrite")` permitiendo
  re-ejecuciones sin duplicados.
- **Join por clave normalizada**: Uso de códigos DIVIPOLA (numéricos) en lugar
  de nombres de departamento (inconsistentes) para garantizar 100% de match
  demográfico.
- **Lazy evaluation**: PySpark difiere transformaciones hasta acciones
  (`.write()`, `.show()`) optimizando plan de ejecución.

## 3. Ambiente de desarrollo

### 3.1. Stack tecnológico

| Componente | Versión/Configuración |
|------------|----------------------|
| **Python** | 3.11+ |
| **PySpark** | 4.0.1 (Hadoop 3.4.0) |
| **AWS EMR** | emr-7.11.0 |
| **Instancias EMR** | m4.xlarge (1 master + workers según demanda) |
| **Boto3** | 1.41.0 |
| **Requests** | 2.31.0 |
| **PyMySQL** | 1.1.1 |
| **Pandas** | 2.2.3 |
| **RDS MySQL** | 8.0 (db.t3.micro) |

### 3.2. Dependencias

Archivo `requirements/prod.txt`:

```
boto3==1.41.0     # AWS SDK para Python
requests==2.31.0  # Cliente HTTP para API Datos Abiertos
pymysql==1.1.1    # Conector MySQL para RDS
pandas==2.2.3     # Exportación RDS a CSV/Parquet
```

Dependencias Spark (manejadas por EMR, declaradas en steps para ejecución
local):

```python
# Hadoop AWS para acceso S3 desde PySpark local
org.apache.hadoop:hadoop-aws:3.4.0
com.amazonaws:aws-java-sdk-bundle:1.12.367
```

### 3.3. Estructura del proyecto

```
st0263-proyecto3-covid/
├── .env.example              # Template de variables de entorno
├── run.bash                  # Orquestador del pipeline completo
├── requirements/
│   └── prod.txt              # Dependencias Python
├── data/
│   └── rds_departamento_demografia.csv  # 33 departamentos colombianos
├── scripts/                  # Scripts de ingesta y orquestación
│   ├── download_covid_to_s3.py        # Descarga API → S3 raw
│   ├── upload_csv_to_rds.py           # Carga CSV → RDS MySQL
│   ├── export_rds_to_s3.py            # Exportación RDS → S3 raw
│   └── create_emr_plus_steps.py       # Creación/reutilización cluster EMR
└── steps/                    # Jobs PySpark para EMR
    ├── step_1_covid_to_trusted.py            # ETL raw → trusted
    ├── step_2_covid_indicators_refined.py    # Indicadores departamentales
    └── step_3_resumen_nacional_diario.py     # Agregación nacional
```

## 4. Configuración y ejecución

### 4.1. Configuración inicial

1. **Clonar repositorio**:
   ```bash
   git clone https://github.com/restreh/st0263-proyecto3-covid.git
   cd st0263-proyecto3-covid
   ```

2. **Crear entorno virtual**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements/prod.txt
   ```

4. **Configurar variables de entorno** (copiar `.env.example` → `.env`):
   ```bash
   export COVID_BUCKET_NAME=jacostaa1datalake  # Bucket S3 destino
   export ROWS_LIMIT=1000000                    # Límite descarga API (1M registros)
   export RDS_HOST=db.xxxxxx.us-east-1.rds.amazonaws.com
   export RDS_USER=admin
   export RDS_PASSWORD=tu_password
   export SPARK_LOCAL=false  # true para pruebas locales, false para EMR
   ```

   **Nota sobre `SPARK_LOCAL`**: Permite ejecutar jobs PySpark localmente para
   pruebas rápidas antes del despliegue a EMR (que toma ~25 min). Configuración
   local usa `local[2]` con 4GB memoria y conectividad S3 via `hadoop-aws`.

5. **Configurar credenciales AWS CLI**:
   ```bash
   aws configure
   # Ingresar Access Key ID, Secret Access Key, región us-east-1
   ```

### 4.2. Preparación de recursos AWS

1. **Crear bucket S3** (si no existe):
   ```bash
   aws s3 mb s3://jacostaa1datalake
   ```

2. **Crear instancia RDS MySQL**:
   - Motor: MySQL 8.0
   - Clase: db.t3.micro (capa gratuita)
   - Crear base de datos: `datos_complementarios`
   - Habilitar acceso público (para pruebas) o configurar VPC security group

3. **Cargar datos demográficos a RDS**:
   ```bash
   python3 scripts/upload_csv_to_rds.py
   ```
   Crea tabla `poblacion` con 33 registros (departamentos colombianos +
   población).

### 4.3. Ejecución del pipeline completo

**Opción A: Script automatizado** (recomendado)
```bash
./run.bash
```

Ejecuta secuencialmente:
1. Descarga casos COVID desde API → `s3://bucket/lake/raw/covid/casos_covid.csv`
2. Exporta tabla RDS → `s3://bucket/lake/raw/rds/poblacion.csv`
3. Sube scripts PySpark → `s3://bucket/steps/`
4. Crea/reutiliza cluster EMR y ejecuta 3 steps Spark
5. Cluster se auto-termina tras 1 hora inactivo

**Opción B: Ejecución manual paso a paso**

1. **Ingesta**:
   ```bash
   python3 scripts/download_covid_to_s3.py  # API → S3 raw
   python3 scripts/export_rds_to_s3.py      # RDS → S3 raw
   ```

2. **Subir scripts a S3**:
   ```bash
   aws s3 cp steps/ s3://jacostaa1datalake/steps/ --recursive --exclude "*" --include "*.py"
   ```

3. **Ejecutar procesamiento EMR**:
   ```bash
   python3 scripts/create_emr_plus_steps.py
   ```

   Este script:
   - Busca cluster EMR activo (estado WAITING/RUNNING)
   - Si existe, agrega steps; si no, crea cluster nuevo con configuración:
     - Release: emr-7.11.0
     - Aplicaciones: Spark, Hadoop, Hive (Glue Catalog integration)
     - Steps: `spark-submit` secuencial de 3 scripts
     - Auto-terminación: 3600 segundos inactividad

   Monitorear progreso en consola EMR → Steps. Tiempo esperado: 20-25 min.

4. **Catalogar con Glue Crawler**:
   - Consola AWS Glue → Crawlers → Crear crawler
   - Data source: `s3://jacostaa1datalake/lake/refined/`
   - Recursivo: Sí
   - Target database: `refined_api_views` (crear si no existe)
   - Ejecutar crawler (detecta tablas `indicadores_departamento`,
     `resumen_nacional_diario`)

5. **Consultar con Athena**:
   ```sql
   -- Configurar output location en Athena settings:
   -- s3://jacostaa1datalake/athena/

   USE refined_api_views;

   -- Top 10 departamentos por tasa de casos
   SELECT nombre_departamento,
          CAST(casos_por_100k AS DECIMAL(10,2)) as tasa,
          casos_acumulados
   FROM indicadores_departamento
   WHERE anio=2020 AND mes=12 AND dia=31
   ORDER BY casos_por_100k DESC
   LIMIT 10;

   -- Resumen nacional últimos 7 días
   SELECT fecha, casos_nuevos_nacional, casos_acumulados_nacional
   FROM resumen_nacional_diario
   ORDER BY fecha DESC
   LIMIT 7;
   ```

<!-- TODO: Image of Athena query results -->

### 4.4. Ejecución local de steps (desarrollo)

Para probar transformaciones sin desplegar a EMR:

```bash
export SPARK_LOCAL=true
export COVID_BUCKET_NAME=jacostaa1datalake

# Ejecutar step individual (requiere datos en S3)
python3 steps/step_1_covid_to_trusted.py
python3 steps/step_2_covid_indicators_refined.py
python3 steps/step_3_resumen_nacional_diario.py

# Deshabilitar queries SQL analíticas (opcional, acelera ejecución)
export RUN_SQL_ANALYTICS=false
```

Configuración local automática:
- Master: `local[2]` (2 cores para reducir presión de memoria)
- Driver memory: 4GB
- Shuffle partitions: 8 (reducido desde default 200)
- Filesystem: S3A con credenciales AWS CLI

## 5. Detalles técnicos

### 5.1. Transformaciones PySpark

**Step 1: raw → trusted** (`step_1_covid_to_trusted.py`)
- Lee `lake/raw/covid/casos_covid.csv` (1M registros) y
  `lake/raw/rds/poblacion.csv` (33 departamentos)
- **Join crítico**: Usa códigos DIVIPOLA numéricos en lugar de nombres de
  departamento
  ```python
  # COVID CSV: columna 'departamento' = código DIVIPOLA (ej: "76" para Valle)
  # Demografía: columna 'codigo_departamento' = código DIVIPOLA
  col("covid.departamento").cast("string") == col("demog.codigo_departamento").cast("string")
  ```
  Esto garantiza 100% de matches vs. ~80% con nombres (inconsistencias: "VALLE"
  vs "Valle del Cauca", "Bogotá D.C." vs "Bogotá").
- Agrega columnas de particionamiento: `anio`, `mes`, `dia` extraídas de
  `fecha_reporte_web`
- Escribe Parquet particionado:
  `lake/trusted/covid/anio=2020/mes=12/dia=31/*.parquet`

**Step 2: trusted → refined (procesamiento dual DataFrame/SparkSQL)**
(`step_2_covid_indicators_refined.py`)

Este step demuestra **dos paradigmas complementarios de procesamiento Spark**:

**A. DataFrame API (transformaciones principales)**:
- Agrega casos diarios por departamento con `groupBy(fecha, codigo_departamento)`
- Window function para acumulados:
  ```python
  Window.partitionBy("codigo_departamento").orderBy("fecha")
  # Ejemplo: Antioquia 2020-03-10
  # casos_nuevos=11, casos_acumulados=68 (5+12+8+32+11)
  ```
- Calcula tasa por 100k habitantes: `(casos_acumulados * 100000) / poblacion`
- Escribe resultado principal a `refined/indicadores_departamento/`

**B. SparkSQL (análisis exploratorio con persistencia)**:

Registra DataFrames como vistas temporales (`createOrReplaceTempView`) y ejecuta
6 queries SQL complejas, **persistiendo cada resultado como Parquet** en
`refined/analytics/` para trazabilidad y reutilización:

1. **`top_departamentos_tasa/`**: Top 10 departamentos por casos por 100k
   (última fecha disponible). Usa CTE + `ROW_NUMBER()` window function.

2. **`tendencias_mensuales/`**: Casos mensuales agregados por año, con conteo
   de departamentos afectados y promedio diario. Análisis temporal macro.

3. **`distribucion_edad/`**: Distribución de casos por grupo etario (0-17, 18-29,
   30-49, 50-64, 65+) con porcentajes. Usa `CASE` para binning + window
   aggregation para calcular porcentaje del total.

4. **`desglose_genero/`**: Total casos, fallecidos, recuperados y tasa de
   letalidad por género. Agregación condicional con `SUM(CASE WHEN...)`.

5. **`hitos_1000_casos/`**: Primera fecha en que cada departamento alcanzó 1000
   casos acumulados, con días transcurridos desde primer caso nacional
   (2020-03-06). Milestone tracking con CTEs + `DATEDIFF()`.

6. **`promedio_movil_7dias/`**: Serie temporal nacional con suavizado mediante
   promedio móvil de 7 días. Window function `ROWS BETWEEN 6 PRECEDING AND
   CURRENT ROW`.

**Ventajas del enfoque dual**:
- DataFrame API: Eficiente para transformaciones complejas con schema inferido
- SparkSQL: Expresividad SQL para análisis ad-hoc, CTEs, window functions
  anidadas
- Persistencia: Resultados SQL almacenados permiten auditoría y consultas
  posteriores sin re-ejecutar análisis completos

**Step 3: refined/indicadores_departamento →
refined/api_views/resumen_nacional_diario**
(`step_3_resumen_nacional_diario.py`)
- Agrega indicadores departamentales a nivel nacional por fecha
- Suma casos nuevos y acumulados de todos los departamentos
- Calcula tasa nacional promedio ponderada por población
- Salida lista para API: un registro por fecha con métricas nacionales

### 5.2. Optimizaciones

- **Formato Parquet**: Compresión columnar (Snappy) reduce tamaño ~80% vs CSV
- **Particionamiento por fecha**: Queries con predicado temporal (`WHERE
  anio=2020`) solo leen particiones relevantes (partition pruning)
- **Reparticionamiento pre-escritura**: `.repartition(8, "anio", "mes", "dia")`
  distribuye uniformemente datos entre archivos, evitando small files problem
- **Cache de datos locales**: Script `download_covid_to_s3.py` verifica
  existencia de CSV local antes de descargar (skip si existe)
- **Verificación S3 pre-upload**: `head_object()` evita re-upload de archivos
  existentes
- **Cluster reuse**: `create_emr_plus_steps.py` busca clusters activos antes de
  crear nuevos (ahorro tiempo/costo)

### 5.3. Catalogación con Glue Crawler

Para las búsquedas con Athena, se configuró un crawler que toma los datos
hallados en la carpeta `refined/` dentro del datalake en S3 y los convierte en
tablas de AWS Glue. Esto se logra gracias a que el crawler puede navegar S3 de
manera recursiva, y obtiene los datos de los diferentes directorios generados
por los scripts de PySpark. Una vez los datos están en la base de datos
`refined_api_views`, estos se pueden visualizar usando consultas con el editor
de queries de Athena.

Configuración del crawler:
- **Data source**: `s3://jacostaa1datalake/lake/refined/`
- **Crawler behavior**: Recursive scan, create table for each top-level
  partition
- **Schema inference**: Automático desde metadatos Parquet (columnas + tipos)
- **Partition detection**: Heurística basada en patrón `key=value` en rutas S3
- **Update behavior**: Add new partitions, update schema if changed
- **Schedule**: On-demand (manual post-EMR) o programado (diario post-ETL)

Resultado: Tablas `indicadores_departamento` y `resumen_nacional_diario` con
particiones `anio`, `mes`, `dia` registradas automáticamente.

## 6. Esquema de datos

### 6.1. Raw zone

**`lake/raw/covid/casos_covid.csv`** (1M registros)
- Fuente: API Datos Abiertos Colombia (`gt2j-8ykr`)
- Columnas clave: `id_de_caso`, `fecha_reporte_web`, `departamento` (código
  DIVIPOLA), `departamento_nom`, `edad`, `sexo`, `estado`, `recuperado`

**`lake/raw/rds/poblacion.csv`** (33 registros)
- Fuente: Exportación tabla RDS MySQL
- Columnas: `codigo_departamento`, `departamento`, `poblacion`
- Propósito: Enriquecimiento demográfico para cálculo de tasas

### 6.2. Trusted zone

**`lake/trusted/covid/`** (Parquet particionado)
- Schema: Todos los campos originales COVID + campos demográficos (`poblacion`,
  `departamento_nombre_normalizado`) + particiones (`anio`, `mes`, `dia`)
- Join: Por código DIVIPOLA (garantiza 100% match)
- Formato: Parquet Snappy, ~1M registros, particionado por `anio/mes/dia`

### 6.3. Refined zone

**`lake/refined/indicadores_departamento/`**
```
fecha: date
anio, mes, dia: int (particiones)
codigo_departamento: string (DIVIPOLA)
nombre_departamento: string
poblacion: bigint
casos_nuevos: bigint (conteo diario)
casos_acumulados: bigint (running sum)
casos_por_100k: double (tasa epidemiológica)
```

**`lake/refined/api_views/resumen_nacional_diario/`**
```
fecha: date
anio, mes, dia: int (particiones)
casos_nuevos_nacional: bigint
casos_acumulados_nacional: bigint
poblacion_total_aprox: bigint
casos_por_100k_nacional: double
```

**`lake/refined/analytics/`** (Resultados SparkSQL)

Directorio con 6 subdirectorios, cada uno conteniendo resultados de queries SQL
ejecutadas en step 2:

1. **`top_departamentos_tasa/`** - Top 10 departamentos por tasa (10 registros)
   ```
   nombre_departamento: string
   tasa_por_100k: decimal(10,2)
   casos_totales: bigint
   ultima_actualizacion: date
   ```

2. **`tendencias_mensuales/`** - Agregación mensual (~24 registros por 2 años)
   ```
   anio, mes: int
   casos_mensuales: bigint
   departamentos_afectados: bigint
   promedio_diario: double
   ```

3. **`distribucion_edad/`** - Grupos etarios (~6 registros)
   ```
   grupo_edad: string ("0-17 años", "18-29 años", etc.)
   total_casos: bigint
   porcentaje: double
   ```

4. **`desglose_genero/`** - Análisis por sexo (~3 registros: M, F, No reportado)
   ```
   sexo: string
   total_casos: bigint
   fallecidos: bigint
   recuperados: bigint
   tasa_letalidad: double
   ```

5. **`hitos_1000_casos/`** - Milestone tracking (~33 registros máximo)
   ```
   nombre_departamento: string
   fecha_milestone_1000: date
   dias_desde_primer_caso: int
   ```

6. **`promedio_movil_7dias/`** - Serie temporal suavizada (todos los días con
   datos)
   ```
   fecha: date
   casos_nuevos_nacional: bigint
   promedio_movil_7dias: double
   ```

## 7. Variables de entorno

Archivo `.env.example` (template de configuración):

| Variable | Valor por defecto | Descripción |
|----------|------------------|-------------|
| `COVID_BUCKET_NAME` | `jacostaa1datalake` | Bucket S3 para almacenamiento del datalake |
| `ROWS_LIMIT` | `1000000` | Límite de registros descargados desde API Datos Abiertos (1M para producción, 50k para desarrollo rápido) |
| `DATA_FILENAME` | `casos_covid.csv` | Nombre del archivo CSV descargado |
| `AWS_REGION` | `us-east-1` | Región AWS para servicios (EMR, RDS, S3) |
| `SPARK_LOCAL` | `false` | `true` para ejecución local PySpark (pruebas), `false` para EMR |
| `RUN_SQL_ANALYTICS` | `true` | `false` para omitir queries SparkSQL en step 2 (acelera ejecución) |
| `RDS_HOST` | - | Endpoint RDS MySQL (ej: `db.xxxxx.us-east-1.rds.amazonaws.com`) |
| `RDS_USER` | `admin` | Usuario MySQL |
| `RDS_PASSWORD` | - | Contraseña MySQL |
| `RDS_DATABASE` | `datos_complementarios` | Base de datos donde reside tabla `poblacion` |

## 8. Organización del datalake S3

```
s3://jacostaa1datalake/
├── lake/                      # Zona de datos (separado de logs/scripts)
│   ├── raw/                   # Datos sin procesar
│   │   ├── covid/
│   │   │   └── casos_covid.csv
│   │   └── rds/
│   │       └── poblacion.csv
│   ├── trusted/               # Datos limpios y normalizados
│   │   └── covid/
│   │       └── anio=2020/mes=12/dia=31/*.parquet
│   └── refined/               # Datos analíticos finales
│       ├── indicadores_departamento/
│       │   └── anio=2020/mes=12/dia=31/*.parquet
│       ├── analytics/         # Resultados SparkSQL (step 2)
│       │   ├── top_departamentos_tasa/*.parquet
│       │   ├── tendencias_mensuales/*.parquet
│       │   ├── distribucion_edad/*.parquet
│       │   ├── desglose_genero/*.parquet
│       │   ├── hitos_1000_casos/*.parquet
│       │   └── promedio_movil_7dias/*.parquet
│       └── api_views/
│           └── resumen_nacional_diario/
│               └── anio=2020/mes=12/dia=31/*.parquet
├── steps/                     # Scripts PySpark subidos por run.bash
│   ├── step_1_covid_to_trusted.py
│   ├── step_2_covid_indicators_refined.py
│   └── step_3_resumen_nacional_diario.py
└── athena/                    # Resultados de queries Athena
    └── Unsaved/2024-11-20/*.csv
```

## 9. Resultados

<!-- TODO: Image of EMR cluster steps completion -->

<!-- TODO: Image of Glue Crawler execution -->

<!-- TODO: Image of Athena query showing top departments by case rate -->

### 9.1. Métricas del pipeline

- **Volumen procesado**: 1M registros COVID-19 (CSV 350MB → Parquet 45MB
  comprimido)
- **Tiempo ejecución EMR**: ~20-25 minutos (3 steps secuenciales)
- **Particiones generadas**: ~300 particiones fecha (anio/mes/dia desde marzo
  2020)
- **Costo aproximado**: $2-3 USD por ejecución completa (EMR 1hr + S3 storage)

### 9.2. Queries ejemplo Athena

**Top 10 departamentos con mayor tasa de contagio (últimos datos)**
```sql
WITH latest AS (
    SELECT codigo_departamento, nombre_departamento,
           casos_por_100k, casos_acumulados,
           ROW_NUMBER() OVER (PARTITION BY codigo_departamento ORDER BY fecha DESC) as rn
    FROM refined_api_views.indicadores_departamento
)
SELECT nombre_departamento, ROUND(casos_por_100k, 2) as tasa, casos_acumulados
FROM latest
WHERE rn=1 AND casos_por_100k IS NOT NULL
ORDER BY casos_por_100k DESC
LIMIT 10;
```

**Evolución nacional últimos 30 días**
```sql
SELECT fecha, casos_nuevos_nacional, casos_acumulados_nacional,
       ROUND(casos_por_100k_nacional, 2) as tasa_nacional
FROM refined_api_views.resumen_nacional_diario
WHERE fecha >= DATE_ADD('day', -30, CURRENT_DATE)
ORDER BY fecha DESC;
```

## 10. Justificación de decisiones técnicas

### 10.1. ¿Por qué RDS si solo se usa CSV?

Requisito del proyecto: simular sistema OLTP con datos complementarios en base
relacional. Flujo real:
1. CSV → RDS MySQL (tabla `poblacion`)
2. Query desde RDS → exportación a S3 raw
3. Spark lee desde S3 (no directamente desde RDS)

Esto emula arquitectura típica donde sistemas transaccionales (RDS) alimentan
data lakes (S3) mediante exports periódicos.

### 10.2. ¿Por qué join por DIVIPOLA y no por nombre?

Nombres de departamento inconsistentes entre fuentes:
- API COVID: "VALLE", "BOGOTA", "ATLANTICO" (mayúsculas, sin tildes)
- Datos demográficos: "Valle del Cauca", "Bogotá D.C.", "Atlántico"

Códigos DIVIPOLA (estándar DANE Colombia) son numéricos y únicos: "76", "11",
"08". Garantizan 100% de matches vs ~80% con normalización de strings.

### 10.3. ¿Por qué Parquet sobre CSV?

- Compresión: 80% reducción tamaño (350MB → 45MB)
- Columnar: Queries leen solo columnas necesarias
- Schema embebido: Tipos de datos preservados
- Partition pruning: Athena/Spark omiten particiones irrelevantes

### 10.4. ¿Por qué EMR y no Lambda?

Volumen de datos (1M registros) y operaciones (joins, window functions,
agregaciones) exceden límites Lambda (15 min timeout, 10GB memoria). EMR escala
horizontalmente con múltiples workers.

## 11. Referencias

- [Datos Abiertos Colombia -
  COVID-19](https://www.datos.gov.co/Salud-y-Protecci-n-Social/Casos-positivos-de-COVID-19-en-Colombia-/gt2j-8ykr):
  Dataset oficial casos positivos Colombia
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/): Guías
  PySpark, SQL, optimización
- [AWS EMR Best
  Practices](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan.html):
  Configuración clusters, auto-scaling, cost optimization
- [Parquet Format Specification](https://parquet.apache.org/docs/):
  Especificación técnica formato columnar
- [AWS Glue
  Crawler](https://docs.aws.amazon.com/glue/latest/dg/add-crawler.html):
  Catalogación automática data lakes
- [Códigos DIVIPOLA -
  DANE](https://www.dane.gov.co/index.php/sistema-estadistico-nacional-sen/nomenclaturas-y-clasificaciones/codigos-divipola):
  Estándar colombiano códigos territoriales
