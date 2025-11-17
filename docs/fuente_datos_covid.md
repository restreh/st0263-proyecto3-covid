# Fuente de datos principal de COVID-19 en Colombia

## 1. Identificación del dataset

- **Nombre oficial del dataset:** Casos positivos de COVID-19 en Colombia  
- **Plataforma:** Datos Abiertos Colombia (datos.gov.co)  
- **Entidad responsable:** Instituto Nacional de Salud (INS)  
- **URL de la ficha del dataset:**  
  - https://www.datos.gov.co/Salud-y-Protecci-n-Social/Casos-positivos-de-COVID-19-en-Colombia-/gt2j-8ykr  

Este dataset contiene el registro de casos positivos de COVID-19 reportados en Colombia por el INS a través de la plataforma de datos abiertos del gobierno. :contentReference[oaicite:0]{index=0}  

## 2. Acceso programático (API)

La plataforma usa Socrata, que expone el dataset mediante endpoints de tipo API. El identificador del conjunto de datos es `gt2j-8ykr`. :contentReference[oaicite:1]{index=1}  

Los endpoints típicos de acceso son:

- **API JSON (básico):**  
  `https://www.datos.gov.co/resource/gt2j-8ykr.json`

- **API CSV (básico):**  
  `https://www.datos.gov.co/resource/gt2j-8ykr.csv`

Parámetros comunes que se pueden usar sobre estos endpoints (se configurarán más adelante en los scripts de ingestión):

- `$select` → seleccionar columnas o aplicar agregaciones.  
- `$where` → filtrar filas.  
- `$limit` y `$offset` → paginar resultados cuando el número de registros es muy grande.  
- `$order` → ordenar resultados.

La autenticación y los límites de consumo dependen de la configuración pública del portal de datos abiertos; para el alcance del proyecto se asumirá uso sin token personalizado, con los límites por defecto de la plataforma.

## 3. Estructura básica de campos relevantes

El dataset incluye muchos campos. Para el proyecto se priorizan algunos que son críticos para el análisis:

- **Identificación y fechas**
  - `id_de_caso` → identificador único del caso. :contentReference[oaicite:2]{index=2}  
  - `fecha_reporte_web` → fecha de reporte del caso en la plataforma. :contentReference[oaicite:3]{index=3}  
  - `fecha_de_notificaci_n` → fecha de notificación del caso. :contentReference[oaicite:4]{index=4}  
  - `fecha_inicio_sintomas` → fecha de inicio de síntomas. :contentReference[oaicite:5]{index=5}  
  - `fecha_diagnostico` → fecha de diagnóstico del caso. :contentReference[oaicite:6]{index=6}  

- **Ubicación geográfica**
  - `departamento` → código DIVIPOLA del departamento. :contentReference[oaicite:7]{index=7}  
  - `departamento_nom` → nombre del departamento. :contentReference[oaicite:8]{index=8}  
  - `ciudad_municipio` → código del municipio. :contentReference[oaicite:9]{index=9}  
  - `ciudad_municipio_nom` → nombre del municipio. :contentReference[oaicite:10]{index=10}  

- **Características del caso**
  - `edad` → edad de la persona. :contentReference[oaicite:11]{index=11}  
  - `unidad_medida` → unidad de medida de la edad (años, meses, etc.). :contentReference[oaicite:12]{index=12}  
  - `sexo` → sexo de la persona. :contentReference[oaicite:13]{index=13}  
  - `fuente_tipo_contagio` → tipo de contagio (relacionado, importado, en estudio, etc.). :contentReference[oaicite:14]{index=14}  

- **Estado y evolución del caso**
  - `ubicacion` → ubicación actual del caso (casa, hospital, UCI, etc.). :contentReference[oaicite:15]{index=15}  
  - `estado` → estado del caso (activo, recuperado, fallecido, etc.). :contentReference[oaicite:16]{index=16}  
  - `recuperado` → marca de recuperación. :contentReference[oaicite:17]{index=17}  
  - `fecha_muerte` → fecha de muerte (si aplica). :contentReference[oaicite:18]{index=18}  
  - `fecha_recuperado` → fecha de recuperación (si aplica). :contentReference[oaicite:19]{index=19}  

- **Información adicional**
  - `pais_viajo_1_cod` y `pais_viajo_1_nom` → información asociada a viajes al exterior. :contentReference[oaicite:20]{index=20}  
  - `per_etn_` y `nom_grupo_` → pertenencia étnica y nombre del grupo étnico. :contentReference[oaicite:21]{index=21}  

## 4. Frecuencia de actualización

Según la descripción del dataset en Datos Abiertos Colombia, la actualización pasó a ser semanal cuando el comportamiento de la transmisión entró en una zona considerada de seguridad, manteniendo un monitoreo continuo de positividad y otros indicadores. :contentReference[oaicite:22]{index=22}  

Para el proyecto, se asumirá que:

- El dataset se consulta en modo histórico completo para la primera carga.  
- Las actualizaciones posteriores se podrían hacer de forma incremental usando filtros por fecha de reporte o notificación.

## 5. Decisiones de uso en el proyecto

- Este dataset será la **fuente principal** para la construcción de métricas de casos por departamento, región y país.  
- El campo de departamento (`departamento` y `departamento_nom`) se usará para enlazar con las tablas de RDS (`departamento_demografia` y `departamento_capacidad_hospitalaria`).  
- Las fechas (`fecha_reporte_web`, `fecha_de_notificaci_n`, `fecha_inicio_sintomas`, `fecha_diagnostico`) se utilizarán para construir series de tiempo y particiones por año/mes/día en S3.  
- Los campos de estado (`estado`, `recuperado`, `fecha_muerte`, `fecha_recuperado`) permitirán derivar indicadores como:
  - Casos activos.  
  - Casos recuperados.  
  - Fallecidos por periodo y por departamento.  

Este documento funcionará como referencia para los scripts de ingestión, para el diseño de las transformaciones en Spark y para la interpretación de las métricas generadas en las zonas `trusted` y `refined`.
