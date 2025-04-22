from pulumi_aws import secretsmanager as secretsmanager
import json


def create_secret_manager(project_name: str, db_endpoint: str, db_name: str, db_username: str, db_password: str):
    project_secret = secretsmanager.Secret("project", name=f"{project_name}-secret", description="Secret for FastAPI project", recovery_window_in_days=0)

    project_secret_obj = {
        "db_endpoint": db_endpoint,
        "db_name": db_name,
        "db_username": db_username,
        "db_password": db_password,
        "secret_key": secretsmanager.get_random_password(password_length=16, exclude_punctuation=True).random_password,
        "first_superuser": "chanllenge@devopsdojo.com",
        "first_superuser_password": secretsmanager.get_random_password(password_length=10,exclude_punctuation=True).random_password,
    }

    # Create a secret version with initial values   
    project_secret_version = secretsmanager.SecretVersion("project-secret-version",
        secret_id=project_secret.id,
        secret_string=json.dumps(project_secret_obj)
    )

    return project_secret
