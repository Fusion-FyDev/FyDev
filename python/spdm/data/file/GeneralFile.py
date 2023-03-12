from ..File import File


class GeneralFile(File):
    def __init__(self,   *args,  **kwargs):
        super().__init__(*args, **kwargs)


__SP_EXPORT__ = GeneralFile
