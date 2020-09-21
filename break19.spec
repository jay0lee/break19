# -*- mode: python -*-

import sys

import importlib
from PyInstaller.utils.hooks import copy_metadata

sys.modules['FixTk'] = None

a = Analysis(['break19.py'],
             hiddenimports=[],
             hookspath=None,
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             runtime_hooks=None)

for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break


pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='break19',
          debug=False,
          strip=None,
          upx=False,
          console=True )
