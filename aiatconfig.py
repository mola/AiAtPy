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

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = _AiAtConfig()
        return cls._instance

    def set_conf_dir(self, conf_dir):
        self.conf_dir = conf_dir
        self.initialize_config()

    def get_conf_dir(self):
        return self.conf_dir

    def initialize_config(self): # add this method
        settings = QSettings(os.path.join(self.conf_dir, "settings.ini"), QSettings.IniFormat)
        self.deepseek_api_key = settings.value("DeepSeek/API_KEY")

    def set_conf_dbdir(self, dbdir):
        self.conf_dbdir = dbdir

    def get_conf_dbdir(self):
        return self.conf_dbdir

    def get_db_path(self):
        if not self.conf_dbdir:
            return None  # Return None instead of raising an error
        return os.path.join(self.conf_dbdir, "database.db")

    def set_deepseek_api_key(self, key): # add this method
        self.deepseek_api_key = key

    def get_deepseek_api_key(self): # add this method
        return self.deepseek_api_key

# Global singleton instance
AiAtConfig = _AiAtConfig.get_instance()
