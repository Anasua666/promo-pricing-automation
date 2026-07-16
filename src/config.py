"""Central config, loaded from environment variables (.env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Bedrock
    bedrock_region: str = os.getenv("BEDROCK_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )

    # DB
    db_connection_string: str = os.getenv("DB_CONNECTION_STRING", "")

    # Filesystem
    submissions_root: str = os.getenv("SUBMISSIONS_ROOT", "./data/submissions")
    fiscal_calendar_xlsx: str = os.getenv(
        "FISCAL_CALENDAR_XLSX", "./data/inputs/fiscal_calendar.xlsx"
    )
    price_file_xlsx: str = os.getenv("PRICE_FILE_XLSX", "./data/inputs/price_file.xlsx")

    # Email
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    email_from: str = os.getenv("EMAIL_FROM", "pricing-automation@example.com")


settings = Settings()
