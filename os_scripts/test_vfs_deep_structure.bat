@echo off
chcp 65001
REM Тест с глубокой структурой
python ..\vfs.py --vfs "C:\Users\cozor\OneDrive\Рабочий стол\Практические работы\КОНФИГ\ConFig\CSV_files\deep_structure_vfs.csv" --script "C:\Users\cozor\OneDrive\Рабочий стол\Практические работы\КОНФИГ\ConFig\script_files\deep_structure_test.txt"
pause