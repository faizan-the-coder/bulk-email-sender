from cx_Freeze import setup,Executable,sys
import os
includefiles=['icon.ico']
excludes=[]
packages=[]
base=None
if sys.platform=="win32":
    base="Win32GUI"

if os.path.exists("sounds"):
    includefiles.append(("sounds", "sounds"))

shortcut_table=[
    ("DesktopShortcut",
     "DesktopFolder",
     "Email App",
     "TARGETDIR",
     "[TARGETDIR]\main.exe",
     None,
     None,
     None,
     None,
     None,
     None,
     "TARGETDIR",
     )
]
msi_data={"Shortcut":shortcut_table}

bdist_msi_options={'data':msi_data}
setup(
    version="0.1",
    description="Email app created by Faizan Khan",
    author="Faizan Khan",
    name="Email App",
    options={'build_exe':{'include_files':includefiles},'bdist_msi':bdist_msi_options,},
    executables=[
        Executable(
            script="main.py",
            base=base,
            icon='icon.ico',
        )
    ]
)