import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    # Production specific config
    pass


config_by_name = {"dev": DevelopmentConfig, "test": TestingConfig, "prod": ProductionConfig}
