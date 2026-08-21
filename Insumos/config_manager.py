class ConfigManager:

    def __init__(self, configuracion):

        self._config = configuracion

    def get(self, nombre, default=None):

        return self._config.get(
            nombre,
            default
        )

    def get_int(self, nombre):

        return int(
            self._config[nombre]
        )

    def get_bool(self, nombre):

        return bool(
            self._config[nombre]
        )

    def get_str(self, nombre):

        return str(
            self._config[nombre]
        )