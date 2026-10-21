'''
Author: seven 865762826@qq.com
Date: 2023-04-21 11:21:33
LastEditors: notmmao@gmail.com
LastEditTime: 2024-12-09 18:51:32
'''
from ctypes import *


import os
import platform
import sys
import shutil

from ...dllpath import DRIVER_DLL_DIR

if DRIVER_DLL_DIR:
    _curr_path = DRIVER_DLL_DIR.joinpath('libTOSUN').as_posix()

_arch, _os = platform.architecture()
_os = platform.system()
_is_windows, _is_linux = False, False
if 'windows' in _os.lower():
    from ctypes import WinDLL,windll
    _is_windows = True
    _lib_dep = []
    if _arch == '32bit':
        if sys.version_info < (3,8):
            _lib_dep.append(os.path.join(_curr_path, 'x86/libTSH.dll'))
            _lib_dep.append(os.path.join(_curr_path, 'x86/libLog.dll'))
            _lib_dep.append(os.path.join(_curr_path, 'x86/binlog.dll'))
            # shutil.copy(os.path.join(_curr_path, 'windows/x86/libTSH.dll'),'./')
            # shutil.copy(os.path.join(_curr_path, 'windows/x86/libLog.dll'),'./')
            # shutil.copy(os.path.join(_curr_path, 'windows/x86/binlog.dll'),'./')
        _lib_path = os.path.join(_curr_path, 'x86/libTSCAN.dll')
    else:
        if sys.version_info < (3,8):
        #     shutil.copy(os.path.join(_curr_path, 'windows/x64/libTSH.dll'),'./')
            _lib_dep.append(os.path.join(_curr_path, 'x64/libTSH.dll'))
        _lib_path = os.path.join(_curr_path, 'x64/libTSCAN.dll')

    for _lib in _lib_dep:
        windll.LoadLibrary(_lib)
    dll = windll.LoadLibrary(_lib_path)
    ascdll = None
elif 'linux' in _os.lower():
    _is_linux = True
    if _arch == '64bit':
        oracle_libs = os.path.join(_curr_path, 'linux')
        if not os.path.isfile('./libTSH.so'):
            shutil.copy(os.path.join(_curr_path, 'linux/libTSCANApiOnLinux.so'),'./')
            shutil.copy(os.path.join(_curr_path, 'linux/libASCLog.so'),'./')
            shutil.copy(os.path.join(_curr_path, 'linux/libbinlog.so'),'./')
            shutil.copy(os.path.join(_curr_path, 'linux/libTSH.so'),'./')
        _lib_path = './libTSCANApiOnLinux.so'
        _libasc_path =  './libASCLog.so'
    else:
        _lib_path = None
    if _lib_path:
        dll = cdll.LoadLibrary(_lib_path)
        ascdll = cdll.LoadLibrary(_libasc_path)
else:
    _library = None
