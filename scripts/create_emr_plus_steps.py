import os

import boto3

# Constants - AWS configuration
REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("COVID_BUCKET_NAME", "jacostaa1datalake")

# Constants - EMR configuration
INSTANCE_TYPE = "m4.xlarge"
CLUSTER_NAME = "CovidCluster"
EMR_VERSION = "emr-7.11.0"
IDLE_TIMEOUT = 3600  # 1 hour

# Constants - IAM roles (AWS Academy specific)
SERVICE_ROLE = "arn:aws:iam::653359214338:role/EMR_DefaultRole"
JOB_FLOW_ROLE = "arn:aws:iam::653359214338:role/EMR_EC2_DefaultRole"
AUTOSCALING_ROLE = "arn:aws:iam::653359214338:role/EMR_AutoScaling_DefaultRole"

# Constants - Network configuration (AWS Academy specific)
SUBNET_ID = "subnet-03fa5bdd3d96e5460"
EC2_KEY_NAME = "vockey"
MASTER_SECURITY_GROUP = "sg-046af1dd4f143bf9c"
SLAVE_SECURITY_GROUP = "sg-00555deb1e1fa0b3d"

# Constants - Spark job scripts
SCRIPT_1 = f"s3://{S3_BUCKET}/scripts/steps/step_1_covid_to_trusted.py"
SCRIPT_2 = f"s3://{S3_BUCKET}/scripts/steps/step_2_covid_indicators_refined.py"
SCRIPT_3 = f"s3://{S3_BUCKET}/scripts/steps/step_3_resumen_nacional_diario.py"

# EMR steps definition
STEPS = [
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


def find_active_cluster(emr):
    """
    Find an active EMR cluster if one exists.

    Args:
        emr: Boto3 EMR client

    Returns:
        Cluster ID if found, None otherwise
    """
    active_clusters = emr.list_clusters(
        ClusterStates=["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"]
    )

    if active_clusters["Clusters"]:
        cluster_id = active_clusters["Clusters"][0]["Id"]
        print(f"cluster: found active cluster {cluster_id}")
        return cluster_id

    print("cluster: no active cluster found")
    return None


def add_steps_to_cluster(emr, cluster_id: str) -> None:
    """
    Add processing steps to an existing EMR cluster.

    Args:
        emr: Boto3 EMR client
        cluster_id: ID of the cluster to add steps to
    """
    print(f"adding {len(STEPS)} steps to cluster {cluster_id}")
    response = emr.add_job_flow_steps(JobFlowId=cluster_id, Steps=STEPS)
    print(f"steps added: {response['StepIds']}")


def create_cluster_with_steps(emr) -> str:
    """
    Create a new EMR cluster with processing steps.

    Args:
        emr: Boto3 EMR client

    Returns:
        ID of the newly created cluster
    """
    print(f"creating new emr cluster: {CLUSTER_NAME}")

    response = emr.run_job_flow(
        Name=CLUSTER_NAME,
        LogUri=f"s3://{S3_BUCKET}/logs",
        ReleaseLabel=EMR_VERSION,
        ServiceRole=SERVICE_ROLE,
        JobFlowRole=JOB_FLOW_ROLE,
        Instances={
            "Ec2SubnetIds": [SUBNET_ID],
            "Ec2KeyName": EC2_KEY_NAME,
            "EmrManagedMasterSecurityGroup": MASTER_SECURITY_GROUP,
            "EmrManagedSlaveSecurityGroup": SLAVE_SECURITY_GROUP,
            "InstanceGroups": [
                {
                    "InstanceCount": 1,
                    "InstanceRole": "TASK",
                    "Name": "Task",
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
                    "Name": "Master",
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
                    "Name": "Core",
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
            ],
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
        Steps=STEPS,
        AutoScalingRole=AUTOSCALING_ROLE,
        ScaleDownBehavior="TERMINATE_AT_TASK_COMPLETION",
        AutoTerminationPolicy={"IdleTimeout": IDLE_TIMEOUT},
        VisibleToAllUsers=True,
    )

    cluster_id = response["JobFlowId"]
    print(f"cluster created: {cluster_id}")
    return cluster_id


def main() -> None:
    """
    Create or reuse EMR cluster and run Spark processing steps.

    Steps:
    1. Check if an active EMR cluster exists
    2. If yes, add processing steps to existing cluster
    3. If no, create new cluster with steps included
    """
    print(f"config: region={REGION}, bucket={S3_BUCKET}")
    print(f"config: instance_type={INSTANCE_TYPE}, emr_version={EMR_VERSION}")

    emr = boto3.client("emr", region_name=REGION)

    # Try to reuse existing cluster
    cluster_id = find_active_cluster(emr)

    if cluster_id:
        add_steps_to_cluster(emr, cluster_id)
    else:
        create_cluster_with_steps(emr)

    print("emr orchestration: done")


if __name__ == "__main__":
    main()
