import collections
from spdm.data.Node import Dict
import pathlib
import pprint

import numpy as np
import scipy.integrate
from spdm.util.logger import logger

from ..Document import Document
from ..File import File


def sp_read_geqdsk(file):
    """
    :param file: input file / file path
    :return: profile object
    """

    description = file.read(48)
    idum = int(file.read(4))
    nw = int(file.read(4))
    nh = int(file.read(4))
    file.readline()

    rdim = float(file.read(16))
    zdim = float(file.read(16))
    rcentr = float(file.read(16))
    rleft = float(file.read(16))
    zmid = float(file.read(16))
    file.readline()
    rmaxis = float(file.read(16))
    zmaxis = float(file.read(16))
    simag = float(file.read(16))
    sibry = float(file.read(16))
    bcentr = float(file.read(16))
    file.readline()
    current = float(file.read(16))
    simag = float(file.read(16))
    xdum = float(file.read(16))
    rmaxis = float(file.read(16))
    xdum = float(file.read(16))
    file.readline()

    zmaxis = float(file.read(16))
    xdum = float(file.read(16))
    sibry = float(file.read(16))
    xdum = float(file.read(16))
    xdum = float(file.read(16))
    file.readline()

    def _read_data(count, width=16):
        data = np.ndarray(shape=[count], dtype=float)

        for n in range(count):
            data[n] = float(file.read(width))
            if n >= count - 1 or ((n + 1) % 5 == 0):
                file.readline()
        return data

    #
    fpol = _read_data(nw)
    pres = _read_data(nw)
    ffprim = _read_data(nw)
    pprim = _read_data(nw)

    psirz = _read_data(nw * nh).reshape([nw, nh])

    qpsi = _read_data(nw)

    nbbs = int(file.read(5))
    limitr = int(file.read(5))
    file.readline()

    bbsrz = _read_data(nbbs * 2).reshape([nbbs, 2])
    limrz = _read_data(limitr * 2).reshape([limitr, 2])

    data = Dict({
        "description": description,
        # "idum": idum,
        "nw": nw,
        "nh": nh,
        "rdim": rdim,
        "zdim": zdim,
        "rcentr": rcentr,
        "rleft": rleft,
        "zmid": zmid,
        "rmaxis": rmaxis,
        "zmaxis": zmaxis,
        "simag": simag,
        "sibry": sibry,
        "bcentr": bcentr,
        "current": current,
        # "simag": simag,
        # "rmaxis": rmaxis,
        # "zmaxis": zmaxis,
        # "sibry": sibry,
        "fpol": fpol,
        "pres": pres,
        "ffprim": ffprim,
        "pprim": pprim,
        "psirz": psirz,
        "qpsi": qpsi,
        "bbsrz": bbsrz,
        "limrz": limrz,
    })
    return data


def sp_write_geqdsk(p, file):
    """
    :param profile: object

    :param file: file path / file
    :return:
    """

    nw = p["nw"]
    nh = p["nh"]

    file.write("%48s%4i%4i%4i\n" % (p.get("description", "UNTITLED"), 3, p["nw"], p["nh"]))
    file.write("%16.9e%16.9e%16.9e%16.9e%16.9e\n" %
               (p["rdim"], p["zdim"], p["rcentr"], p["rleft"], p["zmid"]))
    file.write("%16.9e%16.9e%16.9e%16.9e%16.9e\n" %
               (p["rmaxis"], p["zmaxis"], p["simag"], p["sibry"], p["bcentr"]))
    file.write("%16.9e%16.9e%16.9e%16.9e%16.9e\n" %
               (p["current"], p["simag"], 0, p["rmaxis"], 0))
    file.write("%16.9e%16.9e%16.9e%16.9e%16.9e\n" %
               (p["zmaxis"], 0, p["sibry"], 0, 0))

    def _write_data(d, count):
        count = count or len(d)
        if not isinstance(d, np.ndarray) and not d:
            d = np.zeros(count)
        else:
            d = d.reshape([count])
        for n in range(count):
            file.write("%16.9e" % d[n])
            if n >= count - 1 or ((n + 1) % 5 == 0):
                file.write('\n')

    _write_data(p["fpol"], nw)
    _write_data(p["pres"], nw)
    _write_data(p["ffprim"], nw)
    _write_data(p["pprim"], nw)
    _write_data(p["psirz"], nw * nh)
    _write_data(p["qpsi"], nw)
    file.write("%5i%5i\n" % (p["bbsrz"].shape[0], p["limrz"].shape[0]))
    _write_data(p["bbsrz"], p["bbsrz"].size)
    _write_data(p["limrz"], p["limrz"].size)

    return


def sp_imas_to_geqdsk(d):

    eq = d.equilibrium.time_slice
    wall = d.wall

    dim_r = eq.profiles_2d.grid.dim1
    dim_z = eq.profiles_2d.grid.dim2

    rleft = dim_r.min()
    rdim = dim_r.max() - dim_r.min()
    zdim = dim_z.max() - dim_z.min()

    # rdim = 0.0
    # zdim = 0.0
    rcentr = eq.boundary.geometric_axis.r
    # rleft = 0.0
    zmid = eq.boundary.geometric_axis.z
    rmaxis = eq.global_quantities.magnetic_axis.r
    zmaxis = eq.global_quantities.magnetic_axis.z
    simag = eq.global_quantities.psi_axis
    sibry = eq.global_quantities.psi_boundary
    bcentr = eq.global_quantities.magnetic_axis.b_field_tor
    current = eq.global_quantities.ip

    # boundary
    if not eq.boundary.lcfs:
        rbbs = eq.boundary.outline.r
        zbbs = eq.boundary.outline.z
    else:
        rbbs = eq.boundary.lcfs.r
        zbbs = eq.boundary.lcfs.z

    rcentr = float(rcentr or (rbbs.min()+rbbs.max())/2.0)
    zmid = float(rcentr or (zbbs.min()+zbbs.max())/2.0)

    bbsrz = np.append(rbbs.reshape([1, rbbs.size]), zbbs.reshape(
        [1, rbbs.size]), axis=0).transpose()
    # psi
    # grid_r, grid_z = np.mgrid[rleft:rleft + rdim: nw *
    #                           1j, zmid - zdim / 2: zmid + zdim / 2: nh * 1j]
    # coord_r = np.append(coord_r[:, :], coord_r[:, 0].reshape(
    #     coord_r.shape[0], 1), axis=1)
    # coord_z = np.append(coord_z[:, :], coord_z[:, 0].reshape(
    #     coord_z.shape[0], 1), axis=1)
    # points = np.append(coord_r.reshape(
    #     [coord_r.size, 1]), coord_z.reshape([coord_z.size, 1]), axis=1)
    # psi = eq.profiles_2d[1].psi
    # values = psi[:coord_r.shape[0], :coord_r.shape[1]].reshape(points.shape[0])
    # psirz = griddata(points, values, (grid_r, grid_z),
    #                  method='cubic').transpose()

    psirz = eq.profiles_2d.psi

    nw = psirz.shape[0]
    nz = psirz.shape[1]
    # profile

    fpol = eq.profiles_1d.f
    pres = eq.profiles_1d.pressure
    ffprim = eq.profiles_1d.f_df_dpsi
    pprim = eq.profiles_1d.dpressure_dpsi
    qpsi = eq.profiles_1d.q

    if not isinstance(pres, np.ndarray) and isinstance(pprim, np.ndarray):
        pres = scipy.integrate.cumtrapz(pprim[::-1], np.linspace(1.0, 0.0, nw), initial=0.0)[::-1]
        logger.warning(f"Pressure is obtained from 'pprime'!")
    if not wall:
        limrz = np.ndarray([0, 2])
    else:
        limr = wall.description_2d.limiter.unit.outline.r
        limz = wall.description_2d.limiter.unit.outline.z
        limrz = np.append(limr.reshape([1, limr.size]), limz.reshape([1, limz.size]), axis=0).transpose()
    return {
        "description": d.description,
        "nw": nw,
        "nh": nz,
        "rdim": rdim,
        "zdim": zdim,
        "rcentr": rcentr,
        "rleft": rleft,
        "zmid": zmid,
        "rmaxis": rmaxis,
        "zmaxis": zmaxis,
        "simag": simag,
        "sibry": sibry,
        "bcentr": bcentr,
        "current": current,
        "bbsrz": bbsrz,
        "psirz": psirz,
        "fpol": fpol,
        "pres": pres,
        "ffprim": ffprim,
        "pprim": pprim,
        "qpsi": qpsi,
        "limrz": limrz
    }


def sp_geqdsk_to_imas(geqdsk, doc=None):
    # rdim = 0.0
    # zdim = 0.0
    doc = doc or Dict()
    doc.equilibrium.ids_properties.homogeneous_time = 1
    eq = doc.equilibrium.time_slice
    eq.time = 0.0

    eq.boundary.geometric_axis.r = geqdsk["rcentr"]
    eq.boundary.geometric_axis.z = geqdsk["zmid"]
    # rleft = 0.0
    eq.global_quantities.magnetic_axis.r = geqdsk["rmaxis"]
    eq.global_quantities.magnetic_axis.z = geqdsk["zmaxis"]
    eq.global_quantities.psi_axis = geqdsk["simag"]
    eq.global_quantities.psi_boundary = geqdsk["sibry"]
    eq.global_quantities.magnetic_axis.b_field_tor = geqdsk["bcentr"]
    eq.global_quantities.ip = geqdsk["current"]

    # boundary

    eq.boundary.outline.r = geqdsk["bbsrz"][:, 0]
    eq.boundary.outline.z = geqdsk["bbsrz"][:, 1]

    eq.profiles_2d.grid_type.name = "rectangular"
    eq.profiles_2d.grid_type.index = 1
    eq.profiles_2d.psi = geqdsk["psirz"]

    # profile
    eq.profiles_1d.f = geqdsk["fpol"]
    eq.profiles_1d.pressure = geqdsk["pres"]
    eq.profiles_1d.f_df_dpsi = geqdsk["ffprim"]
    eq.profiles_1d.dpressure_dpsi = geqdsk["pprim"]
    eq.profiles_1d.q = geqdsk["qpsi"]

    # limiter
    doc.wall.ids_properties.homogeneous_time = 2
    doc.wall.description_2d.limiter.unit.outline.r = geqdsk["limrz"][:, 0]
    doc.wall.description_2d.limiter.unit.outline.z = geqdsk["limrz"][:, 1]

    return doc


class FileGEQdsk(File):
    schema = "geqdsk"

    def __init__(self,  *args,  **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def extension_name(self):
        return ".gfile"

    @property
    def root(self):
        if self._data is not None:
            return super().root

        with open(self._path, mode="r") as fp:
            d = sp_geqdsk_to_imas(sp_read_geqdsk(fp))

        self._data = d

        return super().root

    def update(self, d):
        if d is None:
            return
        elif isinstance(d, pathlib.PosixPath):
            self._path = d
            return
        # elif not isinstance(d, collections.abc.Mapping):
        #     raise TypeError(type(d))

        elif isinstance(d, Document):
            d = {
                "description": "Convert from SPDB",
                "equilibrium": d.entry.equilibrium.__value__(),
                "wall": d.entry.wall.__value__()
            }

        with open(self.path, mode="w") as fp:
            sp_write_geqdsk(sp_imas_to_geqdsk(d), fp)


__SP_EXPORT__ = FileGEQdsk
