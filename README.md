Козорез Е.И Вариант 9 группа ИКБО-20-24
Этап 1. REPL
1 требование: Приложение должно быть реализовано в форме графического интерфейса(GUI).
Реализация:
Это требование было выполнено с помощью следующих библиотек:
import tkinter as tk
from tkinter import scrolledtext

В интерфейсе предусмотрены поле вывода и поле ввода:

self.OutputArea = scrolledtext.ScrolledText(RootWindow, state='disabled', height=20, width=80)
self.OutputArea.pack(padx=10, pady=10)

self.InputEntry = tk.Entry(RootWindow, width=80)
self.InputEntry.pack(padx=10, pady=(0, 10))

Пользователь вводит команды в это поле и нажимает Enter, после чего вызывается метод ProcessCommand: 

self.InputEntry.bind("<Return>", self.ProcessCommand)

2 требование: Заголовок окна должен содержать имя VFS.
Реализация:
Создаётся главное окно приложения, инициализируемое в классе VFSEmulator. В конструкторе задаётся заголовок окна, содержащий имя эмулятора:

self.VFSname = "VFS Emulator"
self.RootWindow.title(self.VFSname)

3 требование: Реализовать парсер, который корректно обрабатывает аргументы в кавычках.
Реализация:
Он разбирает строку с учётом кавычек и экранирования символов:

def ParseArguments(self, CommandString):
    Args = []
    CurrentArg = []
    InsideQuotes = False
    EscapeNext = False

    for char in CommandString:
        if EscapeNext:
            CurrentArg.append(char)
            EscapeNext = False
        elif char == '\\':
            EscapeNext = True
        elif char == '"':
            InsideQuotes = not InsideQuotes
        elif char == ' ' and not InsideQuotes:
            if CurrentArg:
                Args.append(''.join(CurrentArg))
                CurrentArg = []
        else:
            CurrentArg.append(char)

4 требование: Реализовать команды-заглушки, которые выводят свое имя и аргументы: ls, cd.
Реализация:
Основные команды программы зарегистрированы в словаре self.Commands:

self.Commands = {
    "ls": self.CMDls,
    "cd": self.CMDcd,
    "exit": self.CMDexit
}

Команды ls и cd являются заглушками, которые просто выводят своё имя и переданные аргументы:

def CMDls(self, Args):
    return f"Команда ls вызвана с аргументами: {Args}"

def CMDcd(self, Args):
    return f"Команда cd вызвана с аргументами: {Args}"

5 требование: Реализовать команду exit.
Реализация:
def CMDexit(self, Args):
    self.Print(f"Команда exit вызвана. Приложение закрывается...")
    self.RootWindow.destroy()

6 требование: Продемонстрировать работу прототипа в интерактивном режиме. Необходимо показать примеры работы всей реализованной функциональности, включая обработку ошибок.
Реализация:
Основная логика взаимодействия с пользователем реализована в методе ProcessCommand. Этот метод получает введённую строку, разбирает её на части с помощью парсера, затем выполняет соответствующую команду:

def ProcessCommand(self, event):
    CommandString = self.InputEntry.get()
    self.InputEntry.delete(0, tk.END)
    self.Print(f"${CommandString}\n")

    try:
        Parts = self.ParseArguments(CommandString)
    except ValueError as e:
        self.Print(f"Ошибка парсера: {e}\n\n")
        return

    if not Parts:
        self.Print("\n")
        return

    CMDname = Parts[0]
    CMDargs = Parts[1:]

    if CMDname in self.Commands:
        try:
            Result = self.Commands[CMDname](CMDargs)
            if Result:
                self.Print(Result + "\n")
        except Exception as e:
            self.Print(f"Произошла ошибка при выполнении команды '{CMDname}': {e}\n\n")
    else:
        self.Print(f"Команда не найдена: {CMDname}\n\n")
    
Демонстрация работы:
![alt text](image-1.png)

-------------------------------------------------------------------------

Этап 2:

Цель: сделать эмулятор настраиваемым, то есть поддержать ввод параметров
пользователя в приложение. Организовать для этого этапа отладочный вывод всех заданных параметров при запуске эмулятора.

1 требование: Параметры командной строки:
– Путь к физическому расположению VFS.
– Путь к стартовому скрипту.

Реализация:
self.VFSpath = VFSpath
self.StartupScript = StartupScript

2 требоване: Стартовый скрипт для выполнения команд эмулятора: выполняет команды последовательно, ошибочные строки пропускает. При выполнении скрипта на экране отображается как ввод, так и вывод, имитируя диалог с пользователем.

Реализация: 
Парсинг аргументов командной строки выполнен вручную в функции ManualParseArgs, которая извлекает --vfs и --script из sys.argv и передаёт их в конструктор VFSEmulator: 
def ManualParseArgs():
    VFSpath = None
    StartupScript = None
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--vfs" and i+1 < len(argv):
            VFSpath = argv[i+1]
            i += 2
        elif argv[i] == "--script" and i+1 < len(argv):
            StartupScript = argv[i+1]
            i += 2
        else:
            i += 1
    return VFSpath, StartupScript

if __name__ == "__main__":
    VFSpath, StartupScript = ManualParseArgs()
    RootWindow = tk.Tk()
    App = VFSEmulator(RootWindow, VFSpath=VFSpath, StartupScript=StartupScript)
    RootWindow.mainloop()

Метод RunStartupScript читает файл скрипта, формирует очередь строк StartupQueue, отключает ввод, если DisableInput=True, и последовательно вызывает ExecuteCommandString для каждой непустой и некомментированной строки.

def RunStartupScript(self, ScriptPath, DelayMs=50, UseComments=True, DisableInput=True):
    if not os.path.exists(ScriptPath):
        self.Print(f"Стартовый скрипт не найден: {ScriptPath}\n\n")
        self._startup_had_errors = True
        return
    with open(ScriptPath, 'r', encoding='utf-8') as f:
        RawLines = list(enumerate(f, start=1))

    self.StartupQueue = []
    for linenumber, rawline in RawLines:
        line = rawline.rstrip('\n').rstrip('\r')
        self.StartupQueue.append((linenumber, line))

    if DisableInput:
        try:
            self.InputEntry.configure(state='disabled')
        except Exception:
            pass

    self._running_startup = True
    self._startup_had_errors = False

    def ProcessNext():
        if not self.StartupQueue:
            if self._startup_had_errors:
                self.Print("Стартовый скрипт завершён с ошибками.\n\n")
            else:
                self.Print("Стартовый скрипт завершён.\n\n")
            self._running_startup = False
            if DisableInput:
                try:
                    self.InputEntry.configure(state='normal')
                except Exception:
                    pass
            return

        linenumber, line = self.StartupQueue.pop(0)
        stripped = line.strip()

        if not stripped:
            self.RootWindow.after(DelayMs, ProcessNext)
            return

        if UseComments and stripped.startswith('#'):
            self.RootWindow.after(DelayMs, ProcessNext)
            return

        try:
            self.ExecuteCommandString(stripped, EchoInput=True)
        except Exception as e:
            self.Print(f"Необработанная ошибка на строке {linenumber}: {e}\n")
            if getattr(self, "_running_startup", False):
                self._startup_had_errors = True

        self.RootWindow.after(DelayMs, ProcessNext)

    self.RootWindow.after(0, ProcessNext)

3 требование: Сообщить об ошибке во время исполнения стартового скрипта.
Реализация:
Во время выполнения стартового скрипта используется флаг self._running_startup. Если произошла ошибка парсера или была введена неизвестная команда, устанавливается self._startup_had_errors = True. В конце выводится: "Стартовый скрипт завершён." или "Стартовый скрипт завершён с ошибками."
В ExecuteCommandString при ошибках:

except ValueError as e:
    self.Print(f"Ошибка парсера: {e}\n\n")
    if getattr(self, "_running_startup", False):
        self._startup_had_errors = True
    return

При неизвестной команде:
else:
    self.Print(f"Команда не найдена: {cmd}\n\n")
    if getattr(self, "_running_startup", False):
        self._startup_had_errors = True

По окончании RunStartupScript:
if self._startup_had_errors:
    self.Print("Стартовый скрипт завершён с ошибками.\n\n")
else:
    self.Print("Стартовый скрипт завершён.\n\n")

В CMDexit:
def CMDexit(self, Args):
    if getattr(self, "_startup_had_errors", False):
        self.Print("Внимание: при выполнении стартового скрипта были ошибки.\n")
    self.Print("Команда exit вызвана. Приложение закрывается...\n")
    self.RootWindow.destroy()

4 Требование: Создать несколько скриптов реальной ОС, в которой выполняется эмулятор. Включить в каждый скрипт вызовы эмулятора для тестирования всех поддерживаемых параметров командной строки.

Реализация:
Файл script_1.txt:
![alt text](image-2.png)

Файл script_2.txt:
![alt text](image-3.png)

Файл VFS.csv пока что можно оставить пустым, так как он не задействован в программе.

Файл test1.bat:
![alt text](image-4.png)
Результат выполнения:
![alt text](image-8.png)

Файл test2.bat:
![alt text](image-5.png)
Результат выполнения:
![alt text](image-9.png)

Файл test3.bat:
![alt text](image-6.png)
Результат выполнения:
![alt text](image-10.png)

Файл test4.bat:
![alt text](image-7.png)
Результат выполнения:
![alt text](image-11.png)
![alt text](image-12.png)

------------------------------------------------------------------------

Этап 3. VFS