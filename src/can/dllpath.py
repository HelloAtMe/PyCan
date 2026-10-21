# -*- coding: utf-8 -*-
'''
@ File         : dllpath.py
@ Author       : x
@ Contact      : 
@ Date         : 2026-10-21 23:32:15
@ Description  : 
                 
'''
from typing import Optional, Union
import pathlib

DRIVER_DLL_DIR: Optional[pathlib.Path] = None


def set_driver_dll_dir(dll_dir: Union[pathlib.Path, str]):
    global DRIVER_DLL_DIR
    if isinstance(dll_dir, str):
        dll_dir = pathlib.Path(dll_dir)

    if dll_dir.exists():
        DRIVER_DLL_DIR = dll_dir
    else:
        raise ReferenceError(f'Dir \"{dll_dir.as_posix()}\" is not found.')
