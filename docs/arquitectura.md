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
     - Tabla `departamento_demografia`.
     - Tabla `departamento_capacidad_hospitalaria`.

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

---

## 6. Resumen

La arquitectura define un flujo completo:

* Fuentes (COVID + RDS)
* S3 `raw`
* EMR/Spark (ETL)
* S3 `trusted`
* EMR/Spark (analítica)
* S3 `refined`
* Consumo (Athena + API)

Esta estructura soporta el objetivo del proyecto de automatizar un pipeline batch de datos COVID-19 en la nube, con separación clara de responsabilidades por zona y servicio.

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
