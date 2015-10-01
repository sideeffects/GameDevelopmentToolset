@echo off
rem
rem Usage: patch_make.bat old_file new_file patch_file ...
rem

rem enable extensions so we can use shift /n
setlocal ENABLEEXTENSIONS

rem find first three arguments
set old="%~1"
set new="%~2"
set patch="%~3"
shift /1
shift /1
shift /1
rem note: %* does not respect shift, we just use %1 ... %9
"%~dp0\xdelta3.0z.x86-32.exe" %1 %2 %3 %4 %5 %6 %7 %8 %9 -9 -e -s %old% %new% %patch%
