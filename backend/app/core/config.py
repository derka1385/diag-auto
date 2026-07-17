from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./diagnostic.db"
    cors_origins: str = "http://localhost:3000"
    llm_provider: str = "mock"
    max_upload_bytes: int = 1_048_576
    log_level: str = "INFO"
    vin_encryption_key: str = ""
    vin_fingerprint_secret: str = ""
    vin_provider: str = "mock"
    nhtsa_vpic_enabled: bool = False
    vin_provider_timeout_seconds: float = 10
    vin_cache_ttl_days: int = 30
    vin_retention_days: int = 365
    vin_rate_limit_per_minute: int = 30
    registration_provider: str = "mock"
    registration_api_url: str = ""
    registration_api_key: str = ""
    registration_api_timeout_seconds: float = 12
    vehicle_provider_primary: str = "mock"
    vehicle_provider_fallbacks: str = ""
    aaa_data_api_url: str = ""
    aaa_data_api_key: str = ""
    tecalliance_api_url: str = ""
    tecalliance_api_key: str = ""
    auto_ways_api_url: str = ""
    auto_ways_api_key: str = ""
    vehicle_lookup_timeout_ms: int = 8000
    vehicle_lookup_cache_ttl_seconds: int = 86400
    vehicle_lookup_enable_mock: bool = False
    vehicle_confidence_reliable: float = .90
    vehicle_confidence_recommended: float = .70
    vehicle_confidence_ambiguous: float = .40
    gemini_api_key: str = ""
    gemini_model_fast: str = "gemini-3.1-flash-lite"
    gemini_model_reasoning: str = "gemini-3.5-flash"
    gemini_timeout_seconds: float = 45
    gemini_max_output_tokens: int = 8192
    gemini_rate_limit_per_minute: int = 10
    diagnostic_image_dir: str = "./private_images"
    diagnostic_image_retention_days: int = 90
    max_diagnostic_images: int = 8
    max_image_bytes: int = 8_000_000
    max_image_total_bytes: int = 24_000_000
    max_image_dimension: int = 2400
    keep_original_images: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
