@echo off

rem -------------------------------------------
rem NOT guaranteed to work on Windows

set APPDIR=loapi
set REPOS=https://huggingface.co/spaces/aka7774/%APPDIR%
set VENV=venv

rem -------------------------------------------

set INSTALL_DIR=%~dp0
cd /d %INSTALL_DIR%

:git_clone
set DL_URL=%REPOS%
set DL_DST=%APPDIR%
git clone %DL_URL% %APPDIR%
if exist %DL_DST% goto install_python

set DL_URL=https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/PortableGit-2.41.0.3-64-bit.7z.exe
set DL_DST=PortableGit-2.41.0.3-64-bit.7z.exe
curl -L -o %DL_DST% %DL_URL%
if not exist %DL_DST% bitsadmin /transfer dl %DL_URL% %DL_DST%
%DL_DST% -y
del %DL_DST%

set GIT=%INSTALL_DIR%PortableGit\bin\git
%GIT% clone %REPOS%

:install_python
set DL_URL=https://github.com/indygreg/python-build-standalone/releases/download/20240415/cpython-3.10.14+20240415-x86_64-pc-windows-msvc-shared-install_only.tar.gz
set DL_DST="%INSTALL_DIR%python.tar.gz"
curl -L -o %DL_DST% %DL_URL%
if not exist %DL_DST% bitsadmin /transfer dl %DL_URL% %DL_DST%
tar -xzf %DL_DST%

set PYTHON=%INSTALL_DIR%python\python.exe
set PATH=%PATH%;%INSTALL_DIR%python310\Scripts

:install_venv
cd %APPDIR%
%PYTHON% -m venv %VENV%
set PYTHON=%VENV%\Scripts\python.exe

:install_pip
set DL_URL=https://bootstrap.pypa.io/get-pip.py
set DL_DST=%INSTALL_DIR%get-pip.py
curl -o %DL_DST% %DL_URL%
if not exist %DL_DST% bitsadmin /transfer dl %DL_URL% %DL_DST%
%PYTHON% %DL_DST%

%PYTHON% -m pip install gradio
%PYTHON% -m pip install -r requirements.txt

pause
