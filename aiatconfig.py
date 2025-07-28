# aiatconfig.py
import os

class _AiAtConfig:
    _instance = None

    def __init__(self):
        if _AiAtConfig._instance is not None:
            raise RuntimeError("AiatConfig is a singleton - use AiatConfig.get_instance()")
        self.conf_dir = None
        self.conf_dbdir = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = _AiAtConfig()
        return cls._instance

    def set_conf_dir(self, conf_dir):
        self.conf_dir = conf_dir

    def get_conf_dir(self):
        return self.conf_dir

    def set_conf_dbdir(self, dbdir):
        self.conf_dbdir = dbdir

    def get_conf_dbdir(self):
        return self.conf_dbdir

    def get_db_path(self):
        if not self.conf_dbdir:
            return None  # Return None instead of raising an error
        return os.path.join(self.conf_dbdir, "database.db")

# Global singleton instance
AiAtConfig = _AiAtConfig.get_instance()
