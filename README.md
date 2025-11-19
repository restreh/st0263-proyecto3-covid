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
            <td><a href="https://scholar.google.com/citations?user=BhCMq0oAAAAJ&hl=es">Edwin Nelson Montoya Múnera</a> (<tt>emontoya[at]eafit.edu.co</tt>)
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
