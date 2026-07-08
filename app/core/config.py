"""
App settings + tenant registry.

In production the tenant table would live in Mongo, not hardcoded — but
keeping it explicit here makes multi-tenant routing easy to follow and test.
"""


from dataclasses import dataclass
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    pinecone_api_key: str = ""
    pinecone_index_name: str = "sales-agent"
    
    mongodb_uri:str = ""
    mongodb_db_name: str = "sales_agent"
    
    google_service_account_json: str = ""
    google_calendar_id: str = ""
    
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""

    ollama_base_url: str = "http://localhost:11434/v1"
    
    openai_api_key: str = ""
    openai_model: str = ""

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


@dataclass(frozen=True)
class TenantConfig:
    org_id: str
    branch_id: str
    display_name: str
    pinecone_namespace: str      # isolates vector search per branch
    google_calendar_id: str      # branch-specific Google Calendar ID
    from_email: str              # "reply-from" address for confirmations
    sales_rep_name: str = "Alex"  # persona name used in lead-capture flow


# Tenant registry 
TENANTS: dict[tuple[str, str], TenantConfig] = {
    ("org_1", "branch_a"): TenantConfig(
        org_id="org_1",
        branch_id="branch_a",
        display_name="Cafe 24 AJNG-  KTM Branch",
        pinecone_namespace="org_1__branch_a",
        google_calendar_id="206a991a8081eb369e5cc6e8921b4a212a4667fd538828c0cf4e9d1a2ac04077@group.calendar.google.com",
        from_email="noreply@anujnandagorkhali.com.np",
    ),
    ("org_1", "branch_b"): TenantConfig(
        org_id="org_1",
        branch_id="branch_b",
        display_name="AJNG Corp — PKR Branch",
        pinecone_namespace="org_1__branch_b",
        google_calendar_id="206a991a8081eb369e5cc6e8921b4a212a4667fd538828c0cf4e9d1a2ac04077@group.calendar.google.com",
        from_email="noreply@anujnandagorkhali.com.np",
    ),
    ("org_2", "branch_a"): TenantConfig(
        org_id="org_2",
        branch_id="branch_a",
        display_name="AJNG2 Inc — Main Branch",
        pinecone_namespace="org_2__branch_a",
        google_calendar_id="206a991a8081eb369e5cc6e8921b4a212a4667fd538828c0cf4e9d1a2ac04077@group.calendar.google.com",
        from_email="noreply@anujnandagorkhali.com.np",
    ),
}


def get_tenant(org_id: str, branch_id: str) -> TenantConfig:
    tenant = TENANTS.get((org_id, branch_id))
    if tenant is None:
        raise ValueError(
            f"Unknown tenant orgId={org_id!r} branchId={branch_id!r}. "
            "Register it in core.config.TENANTS before routing queries to it."
        )
    return tenant


if __name__=="__main__":
    print(settings.smtp_host)