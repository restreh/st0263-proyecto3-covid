# Trabajo 3 – Automatización del proceso de Captura, Ingesta, Procesamiento y Salida de datos

## Contexto del curso

El trabajo 3 de la materia ST0263 – Tópicos Especiales en Telemática / Sistemas Distribuidos (2025-2) se centra en diseñar e implementar un pipeline *batch* completo de datos, aplicado a un caso realista de analítica de datos en la nube. El enfoque está en usar servicios de cómputo distribuido y almacenamiento masivo para transformar datos crudos en información accionable para la toma de decisiones.

## Objetivo general del trabajo

Automatizar el flujo de datos de extremo a extremo, desde las fuentes de información hasta las salidas refinadas listas para análisis, cubriendo las etapas de:

- Captura de datos desde una o varias fuentes externas.
- Ingesta y almacenamiento inicial en una zona *raw*.
- Procesamiento distribuido (ETL) para limpieza, transformación y enriquecimiento.
- Generación de salidas analíticas (*trusted* y *refined*) y exposición para consumo mediante consultas o APIs.

## Alcance técnico mínimo

El enunciado exige, como mínimo, los siguientes componentes:

1. **Fuentes de datos**
   - Dataset principal de casos de COVID-19 en Colombia (fuente abierta, por ejemplo, datos del Ministerio de Salud o datos abiertos del gobierno).
   - Datos complementarios en una base de datos relacional (por ejemplo, información demográfica, hospitalaria o similar) alojada en un motor tipo RDS.

2. **Almacenamiento en S3 organizado por zonas**
   - Zona **raw**: almacenamiento de datos tal como llegan desde las fuentes, sin transformar.
   - Zona **trusted**: datos limpios, validados y estandarizados, listos para análisis.
   - Zona **refined**: resultados finales (agregados, métricas, indicadores, salidas analíticas).

3. **Procesamiento distribuido con EMR y Spark**
   - Uso de un clúster EMR para ejecutar *jobs* de Spark en modo batch.
   - Implementación de *steps* en EMR para orquestar las diferentes fases de procesamiento (lectura desde raw/RDS, transformaciones, escritura en trusted/refined).
   - Manejo de formatos de datos adecuados (por ejemplo, CSV/JSON en raw, Parquet u otro formato columnar en trusted/refined).

4. **Capa de consumo de datos**
   - Posibilidad de consultar los datos refinados con herramientas de consulta sobre S3 (por ejemplo, Athena).
   - Exposición de resultados a través de alguna interfaz programática (por ejemplo, una API apoyada en Lambda + API Gateway) o, al menos, definición clara de cómo se consumirían los datos desde aplicaciones externas.

## Requerimientos funcionales clave

Del enunciado se derivan los siguientes requerimientos funcionales principales:

- Implementar un flujo reproducible que pueda ejecutarse de manera periódica (por ejemplo, diariamente) para actualizar los datos.
- Permitir el cruce de información entre la fuente principal de COVID-19 y la información complementaria en la base relacional.
- Generar indicadores o métricas que sean útiles para análisis (por ejemplo, casos por departamento, tasas relativas a población, tendencias en el tiempo, etc.).
- Mantener la trazabilidad entre las diferentes zonas (raw → trusted → refined), de forma que se pueda identificar el origen de los datos procesados.

## Requerimientos no funcionales y consideraciones

- Uso de servicios de nube orientados a datos masivos y procesamiento distribuido (EMR, S3, RDS, etc.).
- Organización clara de los *buckets* y rutas en S3 por zona y, preferiblemente, por particiones lógicas (fecha, región, etc.).
- Automatización mediante scripts, *steps* de EMR o herramientas de orquestación disponibles en el entorno del curso.
- Buenas prácticas de versionamiento del código y documentación en un repositorio Git.

## Entregables esperados (según el enunciado)

De forma resumida, el trabajo debe entregar:

- Un **repositorio Git** con:
  - Código de ingestión (conexión a datos abiertos y a la base relacional).
  - Código de procesamiento (scripts Spark/EMR y lógica ETL).
  - Estructura de carpetas organizada (ingestion, processing, infra, api, docs, etc.).
  - Archivos de configuración o scripts necesarios para crear/usar los recursos en la nube.

- Una **documentación técnica** donde se explique:
  - La arquitectura general del pipeline.
  - Las decisiones de diseño tomadas (estructuras de datos, particionamiento, formatos, etc.).
  - El flujo de ejecución desde la captura hasta las salidas refinadas.
  - Cómo ejecutar el pipeline paso a paso.

- Evidencia de funcionamiento del pipeline (por ejemplo, capturas de pantalla, consultas de verificación o pruebas) que demuestren que el proceso de captura, ingesta, procesamiento y salida de datos está automatizado y produce resultados coherentes.

Este resumen sintetiza los puntos esenciales del enunciado para guiar la implementación del proyecto.