from copy import copy


class Pointer:
    def __init__(self, var: str, env: dict = None):
        self._env = env
        self.var = var

    @property
    def val(self):
        return self.env[self.var]

    @property
    def env(self):
        return {k: v for k, v in self._env.items() if k[0:2] != "__"}

    def __str__(self):
        return f'<pointer "{self.var}">'
