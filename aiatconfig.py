# aiatconfig.py
import os
from PySide6.QtCore import QSettings

class _AiAtConfig:
    _instance = None

    def __init__(self):
        if _AiAtConfig._instance is not None:
            raise RuntimeError("AiatConfig is a singleton - use AiatConfig.get_instance()")
        self.conf_dir = None
        self.conf_dbdir = None
        self.deepseek_api_key = None
        self.jwt_secret = None
        self.llm_provider = None
        self.settings = None  # Initialize to None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = _AiAtConfig()
        return cls._instance

    def set_conf_dir(self, conf_dir):
        self.conf_dir = conf_dir
        print("dir " , conf_dir )
        self.initialize_config()

    def get_conf_dir(self):
        return self.conf_dir

    def initialize_config(self):
        # Create QSettings instance here
        settings_path = os.path.join(self.conf_dir, "settings.ini")
        self.settings = QSettings(settings_path, QSettings.IniFormat)
        
        # Set default values if they don't exist
        defaults = {
            "Database/url": f"sqlite:///{self.get_db_path()}",
            "JWT/secret": "super_secret_key",
            "LLM/provider": "dummy",
            "DeepSeek/api_key": ""
        }
        
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)
        
        self.settings.sync()
        
        # Load values into instance
        self.jwt_secret = self.settings.value("JWT/secret")
        self.llm_provider = self.settings.value("LLM/provider")
        self.deepseek_api_key = self.settings.value("DeepSeek/api_key")

    def set_conf_dbdir(self, dbdir):
        self.conf_dbdir = dbdir
        os.makedirs(self.conf_dbdir, exist_ok=True)

    def get_conf_dbdir(self):
        return self.conf_dbdir

    def get_db_path(self):
        if not self.conf_dbdir:
            return os.path.join(os.getcwd(), "database.db")
        return os.path.join(self.conf_dbdir, "database.db")

    def get_db_url(self):
        # Ensure settings is initialized
        if not self.settings:
            self.initialize_config()
        return self.settings.value("Database/url")

    def get_jwt_secret(self):
        if not self.settings:
            self.initialize_config()
        return self.jwt_secret

    def get_llm_provider(self):
        if not self.settings:
            self.initialize_config()
        return self.llm_provider

    def set_deepseek_api_key(self, key):
        if not self.settings:
            self.initialize_config()
        self.deepseek_api_key = key
        self.settings.setValue("DeepSeek/api_key", key)
        self.settings.sync()

    def get_deepseek_api_key(self):
        if not self.settings:
            self.initialize_config()
        return self.deepseek_api_key

# Global singleton instance
AiAtConfig = _AiAtConfig.get_instance()