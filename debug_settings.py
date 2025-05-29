#!/usr/bin/env python3

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class TestAuthSettings(BaseSettings):
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        print(f"Parsing cors_origins: {v} (type: {type(v)})")
        if isinstance(v, str):
            result = [origin.strip() for origin in v.split(",") if origin.strip()]
            print(f"Parsed result: {result}")
            return result
        return v

if __name__ == "__main__":
    print("Environment variable CORS_ORIGINS:", os.getenv("CORS_ORIGINS"))
    try:
        settings = TestAuthSettings()
        print("Success! cors_origins:", settings.cors_origins)
    except Exception as e:
        print(f"Error: {e}")
