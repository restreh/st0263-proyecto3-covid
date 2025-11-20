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
