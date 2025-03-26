class Pointer:
    def __init__(self, var: str, env=None):
        if env is None:
            env = None

        self.env = env
        self.var = var

    @property
    def val(self):
        return self.env[self.var]

    def __str__(self):
        return f'<pointer "{self.var}">'
