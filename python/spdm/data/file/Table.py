import numpy as np
from spdm.util.logger import logger

from ..File import File


class FileTable(File):
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self, data=None, *args, **kwargs):
        raise NotImplementedError

    @property
    def root(self):
        if self._data is None:
            count = 0
            head = None
            with self.path.open() as fp:
                for l in fp.readlines():
                    count = count+1
                    head = l.strip()
                    if not not head and head[0] != '#':
                        break

            if not head:
                raise ValueError(f"Can not find title!")

            head = head.split()

            data = np.loadtxt(self.path, comments='#', skiprows=count)

            if len(head) != data.shape[-1]:
                raise RuntimeError(f"Illegal file format: number of title != number of  data column")

            self._data = {title: data[:, idx] for idx, title in enumerate(head)}

        return super().root


__SP_EXPORT__ = FileTable
