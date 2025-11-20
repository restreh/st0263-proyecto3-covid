import os
import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")
SCRIPT_1 = f"s3://{S3_BUCKET}/scripts/steps/step_1_covid_to_trusted.py"
SCRIPT_2 = f"s3://{S3_BUCKET}/scripts/steps/step_2_covid_indicators_refined.py"
SCRIPT_3 = f"s3://{S3_BUCKET}/scripts/steps/step_3_resumen_nacional_diario.py"
INSTANCE_TYPE = "m4.xlarge"

steps = [
    {
        "Name": "etl_trusted",
        "ActionOnFailure": "CONTINUE",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": ["spark-submit", SCRIPT_1],
        },
    },
    {
        "Name": "analytics_refined",
        "ActionOnFailure": "CONTINUE",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": ["spark-submit", SCRIPT_2],
        },
    },
    {
        "Name": "api_views",
        "ActionOnFailure": "CONTINUE",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": ["spark-submit", SCRIPT_3],
        },
    },
]


def run_steps():
    emr = boto3.client("emr", region_name=REGION)

    active_clusters = emr.list_clusters(
        ClusterStates=["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"]
    )

    # Si hay un clúster activo, agregar steps
    if active_clusters["Clusters"]:
        cluster_id = active_clusters["Clusters"][0]["Id"]
        print(f"Clúster activo detectado: {cluster_id}")
        response = emr.add_job_flow_steps(JobFlowId=cluster_id, Steps=steps)
        print(f"Steps añadidos al clúster {cluster_id}: {response['StepIds']}")

    # Si no, crear uno nuevo con los steps
    else:
        print("No se encontró clúster activo. Creando uno nuevo...")
        response = emr.run_job_flow(
            Name="CovidCluster",
            LogUri="s3://{S3_BUCKET}/logs",
            ReleaseLabel="emr-7.11.0",
            ServiceRole="arn:aws:iam::653359214338:role/EMR_DefaultRole",
            JobFlowRole="EMR_EC2_DefaultRole",
            Instances={
                "Ec2SubnetIds": ["subnet-03fa5bdd3d96e5460"],
                "Ec2KeyName": "vockey",
                "EmrManagedMasterSecurityGroup": "sg-00555deb1e1fa0b3d",
                "EmrManagedSlaveSecurityGroup": "sg-0b4708aa5749b3945",
                "InstanceGroups": [
                    {
                        "InstanceCount": 1,
                        "InstanceRole": "TASK",
                        "Name": "Tarea - 1",
                        "InstanceType": INSTANCE_TYPE,
                        "EbsConfiguration": {
                            "EbsBlockDeviceConfigs": [
                                {
                                    "VolumeSpecification": {
                                        "VolumeType": "gp2",
                                        "SizeInGB": 15,
                                    },
                                    "VolumesPerInstance": 2,
                                }
                            ]
                        },
                    },
                    {
                        "InstanceCount": 1,
                        "InstanceRole": "MASTER",
                        "Name": "Principal",
                        "InstanceType": INSTANCE_TYPE,
                        "EbsConfiguration": {
                            "EbsBlockDeviceConfigs": [
                                {
                                    "VolumeSpecification": {
                                        "VolumeType": "gp2",
                                        "SizeInGB": 15,
                                    },
                                    "VolumesPerInstance": 2,
                                }
                            ]
                        },
                    },
                    {
                        "InstanceCount": 1,
                        "InstanceRole": "CORE",
                        "Name": "Central",
                        "InstanceType": INSTANCE_TYPE,
                        "EbsConfiguration": {
                            "EbsBlockDeviceConfigs": [
                                {
                                    "VolumeSpecification": {
                                        "VolumeType": "gp2",
                                        "SizeInGB": 15,
                                    },
                                    "VolumesPerInstance": 2,
                                }
                            ]
                        },
                    },
                ],  # Usa los grupos definidos en la conversión
                "KeepJobFlowAliveWhenNoSteps": True,
                "TerminationProtected": False,
            },
            Applications=[
                {"Name": name}
                for name in [
                    "Flink",
                    "HCatalog",
                    "Hadoop",
                    "Hive",
                    "Hue",
                    "JupyterEnterpriseGateway",
                    "JupyterHub",
                    "Livy",
                    "Spark",
                    "Tez",
                    "Zeppelin",
                ]
            ],
            Configurations=[
                {
                    "Classification": "jupyter-s3-conf",
                    "Properties": {
                        "s3.persistence.bucket": S3_BUCKET,
                        "s3.persistence.enabled": "true",
                    },
                },
                {
                    "Classification": "spark-hive-site",
                    "Properties": {
                        "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
                    },
                },
            ],
            Steps=steps,
            AutoScalingRole="arn:aws:iam::653359214338:role/EMR_AutoScaling_DefaultRole",
            ScaleDownBehavior="TERMINATE_AT_TASK_COMPLETION",
            AutoTerminationPolicy={"IdleTimeout": 3600},
            VisibleToAllUsers=True,
        )
        print(f"Nuevo clúster lanzado con ID: {response['JobFlowId']}")


def main():
    run_steps()

if __name__ == "__main__":
    main()
