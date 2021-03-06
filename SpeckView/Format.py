# coding=utf-8
"""
@author: Sebastian Badur
"""

# noinspection PyUnresolvedReferences
import gwy
from ctypes import c_double, c_byte
import cPickle
from cPickle import HIGHEST_PROTOCOL
from cStringIO import StringIO
from os import SEEK_END


SPECKVIEW = '/speckview/'
BYTE = '/byte'
PERM = '/perm'


def volume_data(c, inhalt, einheit_xy, einheit_z,
                dim, pixel, dim_y=0, pixel_y=0,
                titel=None):
    """
    :type c: gwy.Container
    :type inhalt: list
    :type einheit_xy: gwy.SIUnit
    :type einheit_z: gwy.SIUnit
    :type dim: float
    :type pixel: int
    :param dim_y: Wenn die Dimension von x und y verschieden sind
    :type dim_y: int
    :param pixel_y: Für nicht quadratische Datenfelder
    :type pixel_y: int
    :type titel: str
    """
    if pixel_y == 0:
        pixel_y = pixel
    if dim_y == 0:
        dim_y = dim

    # Neues, nicht initialisiertes Datenfeld erstellen:
    vd = gwy.DataField(pixel, pixel_y, dim, dim_y, False)
    vd.set_si_unit_xy(einheit_xy)
    vd.set_si_unit_z(einheit_z)

    # Belegen:
    c_feld = c_double * (pixel * pixel_y)
    zgr = c_feld.from_address(vd.get_data_pointer())
    zgr[:] = inhalt

    if not hasattr(c, 'n_sd'):
        c.n_sd = 0
    name = '/' + str(c.n_sd) + '/data'
    c.set_object_by_name(name, vd)
    if titel is not None:
        c.set_string_by_name(name + '/title', titel)
    c.n_sd += 1


def si_unit(einheit):
    """
    :type einheit: str
    :rtype: gwy.SIUnit
    """
    si = gwy.SIUnit()
    si.set_from_string(einheit)
    return si


def set_custom(c, name, objekt, permanent=True):
    """
    :type c: gwy.Container
    :type name: str
    :type objekt: object
    :var permanent: Wenn wahr, dann bleibt das Objekt im Gwyddion-Container enthalten. Das kann sehr speicherintensiv
    sein. Deshalb kann es sinnvoll sein, diesen Parameter auf falsch zu setzen, wodurch das Objekt durch den ersten
    Aufruf von get_custom(c, name) aus dem Container gelöscht wird.
    :type permanent: bool
    """
    ser = StringIO()
    cPickle.dump(objekt, ser, HIGHEST_PROTOCOL)
    ser.seek(0, SEEK_END)
    byte = ser.tell()
    go = gwy.DataField((byte+1)/4, 1, 1, 1, False)

    c_feld = c_byte * byte
    zgr = c_feld.from_address(go.get_data_pointer())
    zgr[:] = [ord(n) for n in ser.getvalue()]

    c.set_object_by_name(SPECKVIEW + name, go)
    c.set_int32_by_name(SPECKVIEW + name + BYTE, byte)
    c.set_boolean_by_name(SPECKVIEW + name + '/visible', False)
    c.set_boolean_by_name(SPECKVIEW + name + PERM, permanent)


def get_custom(c, name):
    """
    Gibt das SpeckView-Objekt mit dem gegebenen Namen. Dieses musste zuvor mit set_custom(c, name, objekt, permanent)
    überwiesen werden. War permanent = falsch, dann wird das Objekt zusätzlich aus dem Container gelöscht.
    :type c: gwy.Container
    :type name: str
    :rtype: object
    """
    go = c.get_object_by_name(SPECKVIEW + name)
    byte = c.get_int32_by_name(SPECKVIEW + name + BYTE)

    c_feld = c_byte * byte
    zgr = c_feld.from_address(go.get_data_pointer())
    ser = StringIO(zgr)

    if not c.get_boolean_by_name(SPECKVIEW + name + PERM):  # Also löschen:
        c.remove_by_name(SPECKVIEW + name)

    return cPickle.load(ser)


# wnd = gwy_app_find_window_for_channel(gwy_app_data_browser_get_containers()[0],-1).get_window()
