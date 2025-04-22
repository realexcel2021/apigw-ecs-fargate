from pulumi_aws import rds, ec2, secretsmanager


def create_db_cluster(db_subnet_group_name: str, availability_zones: list, vpc_id: str, db_security_group_id: str, db_name: str, db_username: str, db_password: str):

    default = rds.Cluster("app-cluster",
        cluster_identifier="fastapi-cluster",
        engine=rds.EngineType.AURORA_POSTGRESQL,
        engine_mode="provisioned",
        engine_version="15.3",
        publicly_accessible=False,
        availability_zones=availability_zones,
        database_name=f"{db_name}",
        master_username=f"{db_username}",
        master_password=f"{db_password}",
        skip_final_snapshot=True, # for demo environment
        backup_retention_period=2,

        apply_immediately=True,

        db_cluster_instance_class="db.t3.medium",

        cluster_members = [
            "fastapi-cluster-instance-1",
            "fastapi-cluster-instance-2"
        ],

        db_subnet_group_name=db_subnet_group_name,
        vpc_security_group_ids=[db_security_group_id],
        preferred_backup_window="07:00-09:00")
    
    return {
        "cluster_endpoint": default.endpoint,
        "cluster_reader_endpoint": default.reader_endpoint
    }