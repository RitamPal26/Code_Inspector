"""
Application configuration module.

This module handles all configuration settings loaded from environment variables
using Pydantic Settings for type validation and default values.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn

class Settings(BaseSettings):
    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL with asyncpg driver"
    )
    app_name: str = Field(
        default="Code Review Agent Engine",
        description="Application name displayed in API docs"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    max_loop_iterations: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Maximum iterations allowed for loop nodes"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        ge=1000,
        le=65535,
        description="Server port number"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
