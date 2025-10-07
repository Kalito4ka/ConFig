@echo off
chcp 65001

call test_vfs_basic.bat
call test_vfs_multilpe_files.bat
call test_vfs_deep_structure.bat

pause