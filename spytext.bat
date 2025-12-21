@echo off
REM SpyText Batch Wrapper
REM Allows running: spytext --scan document.pdf
REM Without building an executable

python "%~dp0spytext_exe.py" %*
