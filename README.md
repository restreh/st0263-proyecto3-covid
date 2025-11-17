# Proyecto 3 – Pipeline batch de datos COVID-19 en Colombia

## Curso y contexto

- Curso: ST0263 – Sistemas Distribuidos  
- Semestre: 7  
- Estudiante: Juan José Restrepo Higuita  

Este proyecto implementa un pipeline batch de captura, ingesta, procesamiento y publicación de datos relacionados con COVID-19 en Colombia, utilizando servicios de cómputo distribuido y almacenamiento en la nube.

## Objetivo general

Diseñar e implementar un flujo batch que tome datos de COVID-19 como fuente principal, los ingrese a una zona de almacenamiento en la nube, los transforme mediante procesos distribuidos y exponga resultados listos para análisis y consumo por aplicaciones cliente.

## Alcance inicial

El alcance mínimo del proyecto incluye:

1. **Captura e ingesta de datos**
   - Descarga/lectura de datos abiertos de COVID-19 en Colombia.
   - Ingesta de datos hacia un bucket S3 en la zona *raw*.
   - Carga de datos complementarios en una base de datos relacional (RDS).

2. **Procesamiento ETL distribuido**
   - Uso de un clúster EMR con Spark para limpiar, transformar y enriquecer los datos.
   - Escritura de resultados intermedios en una zona *trusted* en S3.

3. **Analítica y resultados refinados**
   - Cálculo de métricas agregadas y/o modelos analíticos simples sobre los datos de COVID-19.
   - Escritura de salidas finales en una zona *refined* en S3, lista para consulta.

4. **Consumo de resultados**
   - Exposición de resultados a través de consultas (por ejemplo, Athena) y un endpoint tipo API (API Gateway + Lambda) para acceso programático.

## Arquitectura general (visión de alto nivel)

De forma resumida, la arquitectura se compone de las siguientes etapas:

1. **Fuentes de datos**
   - Dataset de casos COVID-19 en Colombia (datos abiertos).
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

## Estructura inicial del repositorio

La estructura mínima del repositorio al inicio del proyecto es:

```text
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
