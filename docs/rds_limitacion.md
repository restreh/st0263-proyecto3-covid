# Limitación de uso de RDS en el entorno del curso

En el entorno de AWS Academy del curso ST0263 no se cuenta con permisos para ejecutar la acción `rds:CreateDBInstance`, por lo que no es posible crear una instancia real de Amazon RDS para este proyecto.

Sin embargo, el modelo relacional definido (tablas `departamento_demografia` y `departamento_capacidad_hospitalaria`) sigue siendo válido a nivel lógico. Para efectos prácticos de implementación:

- Las tablas se materializan como archivos CSV en S3 bajo `raw/rds/`.
- Los procesos de Spark en EMR leerán estos CSV como si fueran extractos exportados desde una base relacional.
- El cruce entre el dataset principal de COVID-19 y los datos demográficos / hospitalarios se realizará directamente en Spark, respetando la estructura de columnas del modelo relacional.

De esta forma, se conserva el diseño conceptual que integra una fuente relacional con el dataset principal, pero adaptado a las restricciones de permisos del entorno.
