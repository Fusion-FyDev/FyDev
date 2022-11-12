import collections
import contextlib
import functools
import inspect
import os
import pprint
import sys
import time
import pathlib

from ..util.logger import logger, sp_enable_logging


class Session:
    """ Manager of computing

        TODO (salmon 20190922):
        * setup/dropdown enveriment
        * load/unload modules
        * support docker
        * support pbs,slurm...
        * improve support for graph
        * visualizing state monitor
    """
    MAX_NODES_NUMBER = 128
    DEFAULT_MASK = 0o755

    _default_working_dir = None
    current_job = None

    _stack = []

    @staticmethod
    def current(name=None, *args, **kwargs):
        if len(Session._stack) == 0:
            Session._stack.append(Session(name=name, *args, **kwargs))
            sp_enable_logging(prefix=f"{Session._stack[-1].cwd}/{Session._stack[-1].name}_")
        return Session._stack[-1]

    def __init__(self,  *args, engine=None, envs=None,
                 name=None, label=None, parent=None, attributes=None, working_dir=None,
                 ** kwargs):

        self._envs = envs or {}
        self._name = name or __package__.split('.')[0]
        self._label = label or self._name

        if working_dir is not None:
            working_dir = pathlib.Path(working_dir)
        else:
            if isinstance(parent, Session):
                working_dir = parent.cwd
            else:
                working_dir = pathlib.Path(Session._default_working_dir or pathlib.Path.cwd())

            working_dir = working_dir.expanduser().resolve()

            count = len(list(working_dir.glob(f"{self._name}_*")))

            working_dir /= f"{self._name}_{count}"

        self._working_dir = working_dir

        self._job_count = 0

        logger.info(f"====== Session Start [{self._name} in {self._working_dir}]   ======")

    # def __del__(self):
    #     logger.info(f"====== Session [{self._name}]  Stop  ======")

    def job_id(self, id_hint=None):
        res = f"{self._job_count:03}_{id_hint or ''}"
        self._job_count += 1
        return res

    @property
    def name(self):
        return self._name

    @property
    def envs(self):
        return self._envs

    @property
    def cwd(self):
        return self._working_dir

    @property
    def graph(self):
        return self._graph

    def __enter__(self):
        logger.info(f"======== Session '{self.label}' open ========")
        if self._graph is None:
            self._graph = Graph(name=self.name, label=self.label)
        self._graph.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._graph is not None:
            self._graph.close()
        logger.info(
            f"======== Session '{self.label}' close========[{exc_type}]")

    def submit(self, g):
        self._graph = g

    def run(self, *,
            callback=None,
            exit_if_failed=False,
            display=False,
            wait_time=0,
            envs={},
            **kwargs):

        step_it, cache = self.run_by_step(envs=envs, **kwargs)
        count = 0
        while True:
            try:
                nid, stage, state = next(step_it)
                if SpState.valid in state or SpState.active in state:
                    # if isinstance(display, collections.abc.Mapping):
                    count = count+1
                    with open(f"{envs.setdefault('WORKING_DIR','../output')}/demo{count:04}.svg", "wb") as ofid:
                        ofid.write(self.display(cache=cache))
                       # self.display(cache=cache, **display)

                    if wait_time is not None:
                        time.sleep(wait_time)

                if state is SpState.error and exit_if_failed:
                    step_it.close()

                if callback is not None:
                    callback(self, step_it, nid, stage, state, cache)
            except StopIteration:
                break

    def run_by_step(self, envs={}, **kwargs):
        cache = SpBag()
        return self._engine.traversal(self._graph, cache, envs={**envs, **self._envs}, **kwargs), cache

    def display(self, g=None, *,  cache=None, render=None, backend=None, ** kwargs):
        if g is None:
            g = self._graph

        if render is None:
            render = Render(cache=cache,  envs=self._envs,
                            backend=backend or "GraphvizRender")

        return render.apply(g, **kwargs)

    # def make_working_dir(self, wdir):
    #     wdir = wdir or self.envs.get("WORKING_DIR", "./")

    #     if not isinstance(wdir, pathlib.Path):
    #         wdir = pathlib.Path(wdir)

    #     if not wdir.is_absolute():
    #         cwd = self.envs.get("TEMP_DIR", None)
    #         cwd = pathlib.Path(cwd) if cwd is not None else pathlib.Path.cwd()
    #         wdir = cwd/wdir

    #     try:
    #         if not wdir.exists():
    #             wdir.mkdir(exist_ok=True,
    #                        mode=LocalEngine.DEFAULT_MASK, parents=True)

    #         os.chdir(wdir)
    #     except:
    #         raise FileNotFoundError(f"Can not enter working dir [{wdir}]")
    #     finally:
    #         logger.debug(f"Enter dir [{wdir}]!")

    #     return wdir
