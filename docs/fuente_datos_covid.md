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
