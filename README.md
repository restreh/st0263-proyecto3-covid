# Metadata
<table>
    <tbody>
        <tr>
            <td>Código del curso</td>
            <td>ST0263</td>
        </tr>
        <tr>
            <td>Nombre del curso</td>
            <td>Sistemas Distribuidos</td>
        </tr>
        <tr>
            <td>Estudiantes</td>
            <td>
                <ol>
                <li>Jerónimo Acosta Acevedo(<tt>jacostaa1[at]eafit.edu.co</tt>)</li>
                <li>Juan José Restrepo Higuita (<tt>jjrestre10[at]eafit.edu.co</tt>)</li>
                <li>Luis Miguel Torres Villegas (<tt>lmtorresv[at]eafit.edu.co</tt>)</li>
                </ol>
            </td>
        </tr>
        <tr>
            <td>Profesor</td>
            <td>Edwin Nelson Montoya Múnera (<tt>emontoya[at]eafit.edu.co</tt>)
        </tr>
    </tbody>
</table>

<!--
El objetivo de esta documentación es que cualquier lector con el repo, en
especial el profesor, entienda el alcance de lo desarrollado y que pueda
reproducir sin el estudiante el ambiente de desarrollo y ejecutar y usar la
aplicación sin problemas.
-->

<!--
Renombre este archivo a README.md cuando lo vaya a usar en un caso específico.
-->

# Automatización del proceso de Captura, Ingesta, Procesamiento y Salida de datos accionables para realizar la gestión de datos de Covid en Colombia

## 1. Breve descripción de la actividad
Este proyecto implementa un pipeline batch de captura, ingesta, procesamiento y publicación de datos relacionados con COVID-19 en Colombia, utilizando servicios de cómputo distribuido y almacenamiento en la nube.

### 1.1. Aspectos cumplidos y/o desarrollados de la actividad propuesta por el profesor

-  **Captura e ingesta de datos**
   - Descarga/lectura de datos abiertos de COVID-19 en Colombia.
   - Ingesta de datos hacia un bucket S3 en la zona *raw*.
   - Carga de datos complementarios en una base de datos relacional (RDS).

-  **Procesamiento ETL distribuido**
   - Uso de un clúster EMR con Spark para limpiar, transformar y enriquecer los datos.
   - Escritura de resultados intermedios en una zona *trusted* en S3.

-  **Analítica y resultados refinados**
   - Cálculo de métricas agregadas y/o modelos analíticos simples sobre los datos de COVID-19.
   - Escritura de salidas finales en una zona *refined* en S3, lista para consulta.

-  **Consumo de resultados**
   - Exposición de resultados a través de consultas (por ejemplo, Athena) y un endpoint tipo API (API Gateway + Lambda) para acceso programático.

### 1.2. Aspectos NO cumplidos y/o desarrollados de la actividad propuesta por el profesor

<!-- Requerimientos funcionales y no funcionales -->

## 2. Información general de diseño de alto nivel

### 2.3 Arquitectura
De forma resumida, la arquitectura se compone de las siguientes etapas:

1. **Fuentes de datos**
   - Dataset de casos de COVID-19 en Colombia (datos abiertos).
   - Datos complementarios almacenados en una base relacional (RDS).

2. **Zona de ingesta – S3 raw**
   - Almacenamiento directo de los archivos originales provenientes de las fuentes.
   - Persistencia de los datos tal como llegan (sin transformación).

3. **Procesamiento distribuidor – EMR/Spark**
   - Jobs batch que leen desde S3 raw y desde RDS.
   - Limpieza, filtrado, normalización y combinación de datos.
   - Escritura en la zona S3 trusted.

4. **Zona de análisis – S3 trusted y refined**
   - Trusted: datos limpios y estandarizados, listos para análisis.
   - Refined: resultados agregados, métricas y salidas específicas para consumo.

5. **Capa de consumo**
   - Consultas interactivas (ejemplo: Athena) sobre los datos en S3.
   - API (API Gateway + Lambda) para exponer resultados a aplicaciones externas.

### 2.4 Mejores prácticas utilizadas

En vez de realizar las consultas una a una, se empleó un AWS EMR cluster para el procesamiento de los datasets. Esto se logró con la ayuda de Hadoop Spark, el cual se usó a través de un SDK y la API PySpark.
Los archivos se almacenaron en S3, asegurando consistencia de datos, y las consultas se realizaron a través de AWS Glue, lo cual automatizó la visualización de los datos.

## 3. Descripción del ambiente de desarrollo y técnico

### 3.1 Lenguaje de programación

- Python

### 3.2 Bibliotecas
El codigo no tiene dependencias externas, pero si import

- boto3
- requests
- os
- pyspark

### 3.4 Adicionales

## 4. Cómo correr el programa

### 4.1 Compilación

### 4.2 Ejecución

## 5. Detalles de desarrollo

## 6. Detalles técnicos

## 7. Configuración de entorno del proyecto

<!-- Por ejemplo, direcciones IPs, puertos, conexión a bases de datos, variables de ambiente, parámetros, etc. -->

<!-- Opcional: Detalles de la organización del código por carpetas o descripción de algún archivo.
(Estructura de directorios y archivos importante del proyecto. Usar el comando 'tree' en sistemas Linux.) -->

La estructura mínima del repositorio al inicio del proyecto es:

```
st0263-proyecto3-covid/
├── README.md
├── docs/
│   ├── enunciado_resumen.md
│   ├── modelo_datos.md
│   └── arquitectura.md
├── ingestion/
├── processing/
├── infra/
└── api/
```
## 8. Resultados o capturas de pantalla

<!-- Esta sección es opcional. -->

## 9. Guía de cómo un usuario utilizaría el software o la aplicación

## 10. Información adicional

<!-- Cualquier cosa que considere relevante. -->

## 11. Referencias

<!--
Debemos siempre reconocer los créditos de partes del código que reutilizaremos,
así como referencias a youtube, o referencias bibliográficas utilizadas para
desarrollar el proyecto o la actividad.

* [Nombre de la página](sitio-1-url)
* [Nombre de la página](sitio-2-url)
* …
*
* [Nombre de la página](sitio-N-url)
-->

<details>
<summary>
Arquitectura
</summary>

--- ARQUITECTURA COMIENZA

# Arquitectura general del pipeline de datos

Este documento describe la arquitectura técnica del pipeline batch de datos COVID-19 en Colombia, incluyendo las fuentes de datos, las zonas de almacenamiento en S3, los procesos de cómputo distribuido y la capa de consumo.

---

## 1. Componentes principales

La arquitectura se organiza alrededor de los siguientes componentes:

1. **Fuentes de datos**
   - Dataset de casos de COVID-19 en Colombia (datos abiertos).
   - Base de datos relacional (RDS) con tablas demográficas y de capacidad hospitalaria por departamento.

2. **Almacenamiento en S3**
   - Buckets o bucket principal para el proyecto, organizado en tres zonas:
     - `raw`
     - `trusted`
     - `refined`

3. **Cómputo distribuido**
   - Clúster EMR ejecutando Spark para:
     - Ingestar datos desde las fuentes.
     - Realizar procesos ETL batch.
     - Generar salidas analíticas.

4. **Base de datos relacional (RDS)**
   - Motor relacional (por ejemplo, MySQL o PostgreSQL) que almacena:

5. **Capa de consumo**
   - Servicio de consultas sobre S3 (por ejemplo, Athena).
   - API basada en Lambda + API Gateway que expone ciertos resultados refinados.

---

## 2. Vista de alto nivel del flujo de datos

El flujo de datos se puede describir en cinco etapas principales:

1. **Captura**
   - Lectura/descarga del dataset de COVID-19 desde la fuente oficial de datos abiertos.
   - Inserción de datos complementarios en RDS (población, capacidad hospitalaria, etc.).

2. **Ingesta**
   - Almacenamiento de los archivos de COVID-19 en el bucket S3 en la zona `raw`.
   - Exportación de extractos desde RDS a archivos (por ejemplo, CSV) almacenados también en la zona `raw`.

3. **Procesamiento ETL**
   - Jobs Spark en EMR que:
     - Leen datos desde `raw/covid` y `raw/rds`.
     - Limpian, normalizan y enriquecen los datos.
     - Escriben resultados intermedios en la zona `trusted`.

4. **Analítica y refinamiento**
   - Jobs Spark adicionales que leen desde `trusted` y calculan:
     - Métricas por departamento, región y país.
     - Indicadores relativos a la población y a la capacidad hospitalaria.
   - Los resultados finales se almacenan en la zona `refined`.

5. **Consumo**
   - Consultas interactivas sobre las tablas/archivos refinados en S3.
   - API que expone ciertos indicadores listos para usar en aplicaciones externas.

---

## 3. Diagrama lógico del pipeline

Diagrama textual simplificado del flujo:

```text
[Fuentes de datos]
    |
    | 1) Dataset COVID (datos abiertos)
    | 2) Tablas RDS (demografía, capacidad hospitalaria)
    v
+--------------------+
|  Ingesta / Raw     |
+--------------------+
| S3 raw             |
|  - raw/covid       |
|  - raw/rds         |
+--------------------+
    |
    | Lectura por Spark en EMR
    v
+--------------------+
|  Procesamiento     |
|  ETL (EMR/Spark)   |
+--------------------+
    |
    | Escritura de datos limpios
    v
+--------------------+
|  S3 trusted        |
|  - covid limpio    |
|  - demografía std  |
|  - capacidad std   |
+--------------------+
    |
    | Lectura para analítica
    v
+--------------------+
|  Analítica / ML    |
|  (EMR/Spark)       |
+--------------------+
    |
    | Escritura de métricas
    v
+--------------------+
|  S3 refined        |
|  - indicadores     |
|  - vistas API      |
+--------------------+
    |
    | 1) Consultas (Athena)
    | 2) API (Lambda + API GW)
    v
[Consumo externo]
```

---

## 4. Detalle por componente

### 4.1. Fuentes de datos

* **Dataset COVID-19**

  * Formato de origen: CSV o similar.
  * Ubicación de destino inicial: `s3://<bucket>/raw/covid/`.
  * Contenido principal: fecha, departamento, estado del caso, edad, sexo, tipo de caso, etc.

* **Base de datos RDS**

  * Tablas:

    * `departamento_demografia`
    * `departamento_capacidad_hospitalaria`
  * Uso principal: enriquecer los datos de COVID-19 con población y capacidad hospitalaria por departamento.

### 4.2. Almacenamiento en S3

* **Zona raw**

  * Propósito: conservar datos tal cual llegan.
  * Carpetas:

    * `raw/covid/`
    * `raw/rds/`

* **Zona trusted**

  * Propósito: datos limpios y normalizados.
  * Carpetas:

    * `trusted/covid/`
    * `trusted/demografia/`
    * `trusted/capacidad_hospitalaria/`

* **Zona refined**

  * Propósito: salidas analíticas finales.
  * Carpetas:

    * `refined/indicadores_departamento/`
    * `refined/indicadores_region/`
    * `refined/indicadores_pais/`
    * `refined/api_views/`

### 4.3. EMR y jobs de Spark

* Se define un clúster EMR que:

  * Accede al bucket S3 (zonas raw/trusted/refined).
  * Tiene permisos de lectura/escritura sobre S3 y acceso a RDS.
* Los jobs de Spark se organizan en dos grupos:

  1. **ETL hacia trusted**:

     * Limpieza y normalización del dataset COVID.
     * Integración con RDS para agregar códigos y población por departamento.
  2. **Analítica hacia refined**:

     * Cálculo de métricas diarias y acumuladas.
     * Cálculo de tasas por población.
     * Cálculo de indicadores relacionados con capacidad hospitalaria.

### 4.4. RDS

* Motor relacional (MySQL/PostgreSQL).
* Tablas con claves primarias y foráneas bien definidas.
* Lectura y escritura:

  * Carga inicial de datos demográficos y de capacidad hospitalaria.
  * Lecturas periódicas desde Spark para enriquecer los datos.

### 4.5. Capa de consumo

* **Consultas sobre S3**:

  * Herramienta tipo Athena para ejecutar consultas SQL sobre los datos en `trusted` y `refined`.
* **API**:

  * Lambda que lee datos refinados (directamente de S3 o vía consultas).
  * API Gateway que define los endpoints para:

    * Obtener indicadores por departamento.
    * Obtener un resumen nacional diario.
    * Otras vistas que se definan durante el desarrollo.

---

## 5. Frecuencia y orquestación del pipeline

* **Frecuencia de ejecución**:

  * El pipeline está diseñado para ejecutarse en modo batch, por ejemplo, una vez al día.
* **Orquestación**:

  * Las ejecuciones pueden dispararse:

    * Manualmente durante el desarrollo.
    * Mediante programación usando los mecanismos disponibles en el entorno (por ejemplo, steps encadenados en EMR o scripts de automatización).
* **Trazabilidad**:

  * Los datos en S3 se organizan por fecha de proceso y/o fecha de los datos.
  * Se conservan los datos originales en `raw` para permitir reprocesos si es necesario.

## 7. Ubicación de scripts de procesamiento en S3

Los scripts de Spark que se ejecutan en EMR se almacenan en:

- `s3://st0263-proyecto3-covid19/scripts/etl_trusted/covid_to_trusted.py`

## 8. Endpoint API Gateway

La capa de consumo expone un endpoint HTTP público usando API Gateway y Lambda:

- URL base (Invoke URL): `https://n0znyvjr0k.execute-api.us-east-1.amazonaws.com/prod`
- Endpoint de resumen nacional diario:
  - `GET /resumen-nacional`
  - `GET /resumen-nacional?fecha=YYYY-MM-DD`

La Lambda `covid_resumen_nacional` ejecuta consultas en Athena sobre la tabla
`covid_analytics.resumen_nacional_diario` y devuelve un JSON con:

- `fecha`
- `casos_nuevos_nacional`
- `casos_acumulados_nacional`
- `poblacion_total_aprox`
- `casos_por_100k_nacional`

--- ARQUITECTURA TERMINA
</details>

<details>
<summary>
Ejecución pipeline
</summary>
--- EJECUCIÓN PIPELINE COMIENZA

# Guía de ejecución del pipeline completo

Este documento describe, paso a paso, cómo ejecutar el pipeline de datos COVID-19 desde la captura hasta el consumo por API.

---

## 1. Prerrequisitos

1. Cuenta activa en el entorno de AWS Academy del curso.
2. Bucket S3 creado:
   - `st0263-proyecto3-covid19`
   - Con las carpetas:
     - `raw/`
     - `trusted/`
     - `refined/`
3. Dataset COVID configurado:
   - Fuente: Datos Abiertos Colombia, dataset `gt2j-8ykr`.
4. Tablas de tipo "RDS" emuladas como CSV en S3:
   - `raw/rds/departamento_demografia.csv`
   - `raw/rds/departamento_capacidad_hospitalaria.csv`
5. Tabla de Athena creada:
   - `covid_analytics.indicadores_departamento`
   - `covid_analytics.resumen_nacional_diario`
6. Lambda y API Gateway configurados para exponer:
   - `GET https://n0znyvjr0k.execute-api.us-east-1.amazonaws.com/prod/resumen-nacional`
   - `GET https://n0znyvjr0k.execute-api.us-east-1.amazonaws.com/prod/resumen-nacional?fecha=YYYY-MM-DD`

---

## 2. Preparar entorno local (una sola vez)

En la máquina local o en una VM del lab:

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/TU_USUARIO/st0263-proyecto3-covid.git
   cd st0263-proyecto3-covid
   ```

2. Crear y activar entorno virtual de Python (en Windows):

   ```bash
   python -m venv venv
   venv\Scripts\activate.bat
   ```

3. Instalar dependencias:

   ```bash
   pip install requests boto3
   ```

4. Configurar credenciales de AWS CLI (si no se ha hecho antes):

   ```bash
   aws configure
   ```

### 4.2. Ejecutar ETL `raw -> trusted` (casos COVID enriquecidos)

Agregar un step:

* **Step type**: `Custom JAR`

* **Name**: `covid-raw-to-trusted`

* **JAR**: `command-runner.jar`

* **Arguments**:

  ```text
  spark-submit s3://st0263-proyecto3-covid19/scripts/etl_trusted/covid_to_trusted.py
  ```

* **Action on failure**: `Cancel and wait`

Esperar a que el step termine en **Completed**.

Resultado esperado en S3:

* `s3://st0263-proyecto3-covid19/trusted/covid/anio=.../mes=.../dia=.../*.parquet`

### 4.3. Ejecutar analítica `trusted -> refined/indicadores_departamento`

Agregar un step:

* **Step type**: `Custom JAR`
* **Name**: `covid-trusted-to-refined-indicadores`
* **JAR**: `command-runner.jar`
* **Arguments**:

  ```text
  spark-submit s3://st0263-proyecto3-covid19/scripts/analytics_refined/covid_indicators_refined.py
  ```

Esperar **Completed**.

Resultado esperado en S3:

* `s3://st0263-proyecto3-covid19/refined/indicadores_departamento/anio=.../mes=.../dia=.../*.parquet`

### 4.4. Ejecutar vista API `refined/indicadores_departamento -> refined/api_views/resumen_nacional_diario`

Agregar un step:

* **Step type**: `Custom JAR`
* **Name**: `covid-resumen-nacional-diario`
* **JAR**: `command-runner.jar`
* **Arguments**:

  ```text
  spark-submit s3://st0263-proyecto3-covid19/scripts/api_views/resumen_nacional_diario.py
  ```

Esperar **Completed**.

Resultado esperado en S3:

* `s3://st0263-proyecto3-covid19/refined/api_views/resumen_nacional_diario/anio=.../mes=.../dia=.../*.parquet`

### 4.5. Terminar el clúster EMR

Cuando todos los steps terminen correctamente, terminar el clúster:

* En EMR → seleccionar `covid-emr-cluster` → **Terminate**.

---

## 5. Actualizar particiones en Athena

En el editor de consultas de Athena:

1. Seleccionar base de datos:

   ```sql
   USE covid_analytics;
   ```

2. Reparar particiones de indicadores por departamento:

   ```sql
   MSCK REPAIR TABLE indicadores_departamento;
   ```

3. Reparar particiones de resumen nacional diario:

   ```sql
   MSCK REPAIR TABLE resumen_nacional_diario;
   ```

4. Probar consultas:

   ```sql
   SELECT * FROM indicadores_departamento ORDER BY fecha, codigo_departamento LIMIT 50;

   SELECT * FROM resumen_nacional_diario ORDER BY fecha LIMIT 50;
   ```

---

## 6. Consumir el resumen nacional por API

### 6.1. Último día disponible

Request:

```text
GET https://n0znyvjr0k.execute-api.us-east-1.amazonaws.com/prod/resumen-nacional
```

Respuesta (ejemplo):

```json
{
  "fecha": "2023-10-04",
  "casos_nuevos_nacional": 1,
  "casos_acumulados_nacional": 91712,
  "poblacion_total_aprox": null,
  "casos_por_100k_nacional": null
}
```

### 6.2. Fecha específica

Request:

```text
GET https://n0znyvjr0k.execute-api.us-east-1.amazonaws.com/prod/resumen-nacional?fecha=2023-10-04
```

Respuesta esperada: igual formato que el caso anterior, pero para la fecha solicitada. Si no hay datos para esa fecha, la API devuelve un 404 con mensaje de error.

---

## 7. Resumen del flujo

1. Ingesta COVID + CSV “RDS” → `raw/` (scripts Python locales).
2. EMR + Spark:

   * `raw -> trusted` (enriquecimiento y limpieza).
   * `trusted -> refined/indicadores_departamento` (métricas por departamento).
   * `refined/indicadores_departamento -> refined/api_views/resumen_nacional_diario` (resumen nacional).
3. Athena:

   * Tablas externas sobre `refined/`.
   * Consultas SQL interactivas.
4. Lambda + API Gateway:

   * Exponen resumen nacional diario como JSON a través de un endpoint HTTP.


--- EJECUCIÓN PIPELINE TERMINA
</details>

<details>
<summary>
Fuente de datos
</summary>

--- FUENTE DE DATOS COMIENZA

# Fuente de datos principal de COVID-19 en Colombia

## 1. Identificación del dataset

- **Nombre oficial del dataset:** Casos positivos de COVID-19 en Colombia
- **Plataforma:** Datos Abiertos Colombia (datos.gov.co)
- **Entidad responsable:** Instituto Nacional de Salud (INS)
- **URL de la ficha del dataset:** <https://www.datos.gov.co/Salud-y-Protecci-n-Social/Casos-positivos-de-COVID-19-en-Colombia-/gt2j-8ykr>

Este dataset contiene el registro de casos positivos de COVID-19 reportados en
Colombia por el INS a través de la plataforma de datos abiertos del gobierno.

## 2. Acceso programático (API)

La plataforma usa Socrata, que expone el dataset mediante endpoints de tipo API.
El identificador del conjunto de datos es `gt2j-8ykr`. Los endpoints típicos de
acceso son: `https://www.datos.gov.co/resource/gt2j-8ykr.csv`

Parámetros comunes que se pueden usar sobre estos endpoints (se configurarán más
adelante en los scripts de ingestión):

- `$select` → seleccionar columnas o aplicar agregaciones.
- `$where` → filtrar filas.
- `$limit` y `$offset` → paginar resultados cuando el número de registros es muy
  grande.
- `$order` → ordenar resultados.

La autenticación y los límites de consumo dependen de la configuración pública
del portal de datos abiertos; para el alcance del proyecto se asumirá uso sin
token personalizado, con los límites por defecto de la plataforma.

## 4. Frecuencia de actualización

Según la descripción del dataset en Datos Abiertos Colombia, la actualización
pasó a ser semanal cuando el comportamiento de la transmisión entró en una zona
considerada de seguridad, manteniendo un monitoreo continuo de positividad y
otros indicadores.

Para el proyecto, se asumirá que:

- El dataset se consulta en modo histórico completo para la primera carga.
- Las actualizaciones posteriores se podrían hacer de forma incremental usando
  filtros por fecha de reporte o notificación.

## 5. Decisiones de uso en el proyecto

- Este dataset será la **fuente principal** para la construcción de métricas de
  casos por departamento, región y país.
- El campo de departamento (`departamento` y `departamento_nom`) se usará para
  enlazar con las tablas de RDS (`departamento_demografia` y
  `departamento_capacidad_hospitalaria`).
- Las fechas (`fecha_reporte_web`, `fecha_de_notificaci_n`,
  `fecha_inicio_sintomas`, `fecha_diagnostico`) se utilizarán para construir
  series de tiempo y particiones por año/mes/día en S3.
- Los campos de estado (`estado`, `recuperado`, `fecha_muerte`,
  `fecha_recuperado`) permitirán derivar indicadores como:
  - Casos activos.
  - Casos recuperados.
  - Fallecidos por periodo y por departamento.

Este documento funcionará como referencia para los scripts de ingestión, para el
diseño de las transformaciones en Spark y para la interpretación de las métricas
generadas en las zonas `trusted` y `refined`.


--- FUENTE DE DATOS TERMINA
</details>

<details>
<summary>
Modelo de datos
</summary>

--- MODELO DE DATOS COMIENZA


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

Este modelo servirá como base para el diseño de los procesos de ingestión,
transformación y publicación de datos en el proyecto.

--- MODELO DE DATOS TERMINA

</details>

<details>
<summary>
Reporte antiguo en LaTeX
</summary>

--- REPORTE ANTIGUO EN LATEX COMIENZA


Introducción
============

Este proyecto implementa un *pipeline* batch de datos para el análisis
de casos de COVID-19 en Colombia, utilizando servicios de cómputo
distribuido y almacenamiento en la nube sobre Amazon Web Services (AWS).
El flujo cubre las etapas de captura, ingesta, procesamiento, generación
de resultados analíticos y exposición de estos resultados a través de
una API HTTP.

El *dataset* principal corresponde a los casos positivos de COVID-19
reportados en Colombia mediante datos abiertos, complementados con
información demográfica y de capacidad hospitalaria simulada, organizada
lógicamente como si proviniera de una base de datos relacional.

Objetivos
=========

Objetivo general
----------------

Diseñar e implementar un *pipeline* batch automatizado que tome datos de
COVID-19 como fuente principal, los ingrese a un almacenamiento en la
nube organizado por zonas, los procese de manera distribuida y produzca
salidas refinadas listas para análisis y consumo programático.

Objetivos específicos
---------------------

-   Capturar y almacenar el *dataset* de casos de COVID-19 de Colombia
    en una zona *raw* en Amazon S3.

-   Emular una fuente relacional (tipo Amazon RDS) mediante archivos CSV
    con datos demográficos y de capacidad hospitalaria.

-   Implementar procesos ETL en EMR/Spark para limpiar, normalizar y
    enriquecer los datos, generando una zona *trusted*.

-   Calcular métricas agregadas por departamento y generar indicadores
    en una zona *refined*.

-   Construir vistas analíticas específicas para consumo por API
    (resumen nacional diario).

-   Exponer los resultados a través de Amazon Athena y de un endpoint
    HTTP basado en AWS Lambda y Amazon API Gateway.

-   Documentar la arquitectura, las decisiones de diseño y los pasos de
    ejecución del *pipeline*.

Descripción de datos y modelo
=============================

Dataset principal de COVID-19
-----------------------------

El *dataset* principal se obtiene de Datos Abiertos Colombia
(`datos.gov.co`):

-   Nombre: *Casos positivos de COVID-19 en Colombia*.

-   Identificador: `gt2j-8ykr`.

-   Endpoint CSV (Socrata):
    <https://www.datos.gov.co/resource/gt2j-8ykr.csv>.

Campos relevantes utilizados en el proyecto:

-   Fechas:

    -   `fecha_reporte_web`

    -   `fecha_de_notificaci_n`

    -   `fecha_inicio_sintomas`

    -   `fecha_diagnostico`

-   Ubicación:

    -   `departamento`, `departamento_nom`

    -   `ciudad_municipio`, `ciudad_municipio_nom`

-   Características:

    -   `edad`, `unidad_medida`, `sexo`

    -   `fuente_tipo_contagio`

-   Estado:

    -   `ubicacion`, `estado`, `recuperado`

    -   `fecha_muerte`, `fecha_recuperado`

Datos relacionales emulados
---------------------------

Se define un modelo relacional lógico con dos tablas:

#### Tabla `departamento_demografia`

-   `codigo_departamento` (PK)

-   `nombre_departamento`

-   `region`

-   `poblacion`

-   `anio_corte`

#### Tabla `departamento_capacidad_hospitalaria`

-   `id_capacidad` (PK)

-   `fecha`

-   `codigo_departamento` (FK a `departamento_demografia`)

-   `camas_uci_totales`

-   `camas_uci_ocupadas`

-   `fuente`

Por restricciones de permisos en el entorno de AWS Academy no se crea
una instancia real de Amazon RDS, sino que estas tablas se materializan
como archivos CSV locales:

-   `data/rds/departamento_demografia.csv`

-   `data/rds/departamento_capacidad_hospitalaria.csv`

Estos archivos se suben a S3 bajo:

-   `s3://st0263-proyecto3-covid19/raw/rds/`

y son leídos por Spark como extractos de una base de datos relacional.

Organización en S3
------------------

El *bucket* principal del proyecto es:

-   `st0263-proyecto3-covid19`

Se definen tres zonas lógicas:

-   **`raw/`**:

    -   `raw/covid/` CSV descargados desde Datos Abiertos.

    -   `raw/rds/` CSV que emulan las tablas relacionales.

-   **`trusted/`**:

    -   `trusted/covid/` casos de COVID limpios y enriquecidos, en
        formato Parquet particionado por año, mes y día.

    -   `trusted/demografia/` y `trusted/capacidad_hospitalaria/`
        (planificados para extensión).

-   **`refined/`**:

    -   `refined/indicadores_departamento/` métricas diarias por
        departamento.

    -   `refined/api_views/resumen_nacional_diario/` resumen nacional
        diario para consumo por API.

Arquitectura del pipeline
=========================

Componentes de AWS utilizados
-----------------------------

-   **Amazon S3**: almacenamiento por zonas (*raw*, *trusted*,
    *refined*).

-   **Amazon EMR sobre EC2**: clúster con Apache Spark para
    procesamiento batch.

-   **Amazon Athena**: consultas SQL sobre datos en S3 (zonas
    *refined*).

-   **AWS Lambda**: función `covid_resumen_nacional` que consulta
    Athena.

-   **Amazon API Gateway**: API HTTP que expone el resumen nacional
    diario.

-   **AWS CLI y `boto3`**: ingesta y automatización desde scripts
    Python.

Flujo de datos
--------------

El flujo se organiza en las siguientes etapas:

### Captura e ingesta

-   Script `ingestion/covid_api/download_covid_to_s3.py`:

    -   Descarga un CSV del dataset `gt2j-8ykr` desde Datos Abiertos.

    -   Almacena el archivo en `raw/covid/` dentro del *bucket* S3.

-   Script `ingestion/upload_rds_csv_to_s3.py`:

    -   Sube los CSV locales de `data/rds/` a `raw/rds/`.

### Procesamiento ETL `raw` $\rightarrow$ `trusted`

-   Script de Spark: `processing/etl_trusted/covid_to_trusted.py`.

-   Ejecución en EMR mediante un *step* que corre:

    -   `spark-submit s3://st0263-proyecto3-covid19/scripts/etl_trusted/`\
        `covid_to_trusted.py`

-   Funcionalidad principal:

    -   Lectura de `raw/covid/*.csv` y
        `raw/rds/departamento_demografia.csv`.

    -   Normalización de nombres de departamento.

    -   *Join* con datos demográficos.

    -   Conversión de fechas y creación de columnas `anio`, `mes`,
        `dia`.

    -   Escritura de datos limpios y enriquecidos en `trusted/covid/` en
        formato Parquet particionado.

### Analítica `trusted` $\rightarrow$ `refined/indicadores_departamento`

-   Script de Spark:
    `processing/analytics_refined/covid_indicators_refined.py`.

-   *Step* en EMR que ejecuta:

    -   `spark-submit s3://st0263-proyecto3-covid19/scripts/analytics_refined/`\
        `covid_indicators_refined.py`

-   Funcionalidad:

    -   Lectura de `trusted/covid/`.

    -   Agregación por fecha y departamento para obtener:

        -   `casos_nuevos`

        -   `casos_acumulados` (usando una ventana por departamento y
            fecha)

        -   `casos_por_100k` (cuando hay población disponible)

    -   Escritura en `refined/indicadores_departamento/` en formato
        Parquet particionado.

### Vista para API `refined/indicadores_departamento` $\rightarrow$ `refined/api_views`

-   Script de Spark: `processing/api_views/resumen_nacional_diario.py`.

-   *Step* en EMR que ejecuta:

    -   `spark-submit s3://st0263-proyecto3-covid19/scripts/api_views/`\
        `resumen_nacional_diario.py`

-   Funcionalidad:

    -   Agregación de indicadores por departamento a nivel nacional para
        cada fecha.

    -   Cálculo de:

        -   `casos_nuevos_nacional`

        -   `casos_acumulados_nacional`

        -   `poblacion_total_aprox`

        -   `casos_por_100k_nacional`

    -   Escritura de la vista en
        `refined/api_views/resumen_nacional_diario/` en formato Parquet
        particionado.

Capa de consumo: Athena y API
-----------------------------

### Athena

-   Base de datos: `covid_analytics`.

-   Tablas externas definidas:

    -   `indicadores_departamento` sobre
        `refined/indicadores_departamento/`.

    -   `resumen_nacional_diario` sobre
        `refined/api_views/resumen_nacional_diario/`.

-   Particiones registradas mediante:

    -   `MSCK REPAIR TABLE indicadores_departamento;`

    -   `MSCK REPAIR TABLE resumen_nacional_diario;`

### Lambda y API Gateway

#### Lambda

-   Función: `covid_resumen_nacional`.

-   Rol de ejecución: `LabRole` del entorno del laboratorio.

-   Lógica:

    -   Recibe eventos con `queryStringParameters`.

    -   Si se indica `fecha=YYYY-MM-DD`, consulta en Athena la tabla
        `resumen_nacional_diario` para esa fecha.

    -   Si no se indica fecha, obtiene la última fecha disponible.

    -   Devuelve un JSON con:

        -   `fecha`

        -   `casos_nuevos_nacional`

        -   `casos_acumulados_nacional`

        -   `poblacion_total_aprox`

        -   `casos_por_100k_nacional`

#### API Gateway

-   Tipo: HTTP API.

-   Nombre: `st0263-proyecto3-covid-api`.

-   *Stage*: `prod`.

-   URL base:

    -   <https://n0znyvjr0k.execute-api.us-east-1.amazonaws.com/prod>

-   Rutas:

    -   `GET /resumen-nacional`

    -   `GET /resumen-nacional?fecha=YYYY-MM-DD`

Ejecución del pipeline
======================

La ejecución completa del flujo, desde la captura hasta el consumo, se
resume en los siguientes pasos:

1.  Preparar el entorno local:

    1.  Clonar el repositorio del proyecto.

    2.  Crear y activar un entorno virtual de Python.

    3.  Instalar `requests` y `boto3`.

    4.  Configurar credenciales con `aws configure`.

2.  Ejecutar la ingesta:

    1.  `python ingestion/covid_api/download_covid_to_s3.py`

    2.  `python ingestion/upload_rds_csv_to_s3.py`

3.  Crear el clúster EMR y lanzar los *steps* de Spark:

    1.  ETL `raw` $\rightarrow$ `trusted` con `covid_to_trusted.py`.

    2.  `trusted` $\rightarrow$ `refined/indicadores_departamento` con
        `covid_indicators_refined.py`.

    3.  `refined/indicadores_departamento` $\rightarrow$
        `refined/api_views/resumen_nacional_diario` con
        `resumen_nacional_diario.py`.

4.  Actualizar las particiones de las tablas externas en Athena.

5.  Consumir los resultados:

    1.  Ejecutar consultas SQL en Athena.

    2.  Consumir la API HTTP:

        -   `GET /resumen-nacional`

        -   `GET /resumen-nacional?fecha=YYYY-MM-DD`

Limitaciones y adaptaciones al entorno
======================================

-   No se crea una instancia real de Amazon RDS debido a restricciones
    IAM (`rds:CreateDBInstance` no permitido). Se emula la fuente
    relacional mediante CSV en `raw/rds/`, integrados desde Spark.

-   La creación de roles IAM personalizados está limitada. Se reutiliza
    `LabRole` como rol de ejecución para Lambda.

-   La orquestación del *pipeline* se realiza mediante ejecución manual
    de *steps* de EMR. En un entorno productivo podría automatizarse con
    servicios adicionales (por ejemplo, Step Functions o herramientas
    externas de orquestación), que aquí no se utilizan para ajustarse al
    entorno del laboratorio.

Resultados
==========

-   Datos de COVID-19 cargados en S3 en la zona `raw/covid`.

-   Datos demográficos y de capacidad hospitalaria cargados en
    `raw/rds`.

-   Zona `trusted/covid` con datos limpios y enriquecidos, particionados
    por fecha.

-   Zona `refined/indicadores_departamento` con indicadores diarios por
    departamento.

-   Vista `refined/api_views/resumen_nacional_diario` con el resumen
    nacional diario.

-   Tablas externas en Athena que permiten analizar los indicadores por
    departamento, región y país, así como el comportamiento agregado
    nacional.

-   API HTTP operativa que devuelve un resumen nacional diario en
    formato JSON, listo para ser consumido por aplicaciones cliente o
    paneles de visualización.

Conclusiones
============

-   Es posible construir un *pipeline* batch completo sobre AWS
    combinando S3, EMR, Athena, Lambda y API Gateway, incluso con
    restricciones de permisos, siempre que se adapten las fuentes de
    datos y la forma de integración.

-   La separación en zonas *raw*, *trusted* y *refined* facilita la
    trazabilidad, permite reprocesos y clarifica las responsabilidades
    de cada etapa del flujo de datos.

-   El uso de Spark en EMR permite procesar volúmenes grandes de
    información de forma distribuida, aplicar transformaciones complejas
    y generar indicadores analíticos en formatos eficientes (Parquet).

-   Athena ofrece una capa de consulta flexible sobre S3 sin administrar
    servidores adicionales, lo que simplifica la exposición de datos
    tanto para usuarios SQL como para servicios *serverless*.

-   La combinación de Lambda y API Gateway permite exponer vistas
    analíticas específicas como servicios HTTP, acercando el *pipeline*
    de datos a aplicaciones externas y facilitando la integración con
    otros sistemas.


--- REPORTE ANTIGUO EN LATEX TERMINA

</details>
