#Козорез Е.И. 9 вариант
import tkinter as tk
from tkinter import scrolledtext
import os
import sys

class VFSEmulator:
    def __init__(self, RootWindow, VFSpath=None, StartupScript=None):
        self.RootWindow = RootWindow
        self.VFSname = "VFS Emulator"
        self.RootWindow.title(self.VFSname)
        #область вывода
        self.OutputArea = scrolledtext.ScrolledText(RootWindow, state='disabled', height=20, width=80)
        self.OutputArea.pack(padx=10, pady=10)
        #область ввода
        self.InputEntry = tk.Entry(RootWindow, width=80)
        self.InputEntry.pack(padx=10, pady=(0, 10))

        self.Commands = {
            "ls": self.CMDls,
            "cd": self.CMDcd,
            "exit": self.CMDexit
        }

        self.InputEntry.bind("<Return>", self.ProcessCommand)

        #сохранить параметры
        self.VFSpath = VFSpath
        self.StartupScript = StartupScript

        self.Print(f"Параметры запуска:\n  VFS path: {self.VFSpath}\n  Startup script: {self.StartupScript}\n\n")

        if self.StartupScript:
            self.RootWindow.after(100, lambda: self.RunStartupScript(self.StartupScript))

        #приветственное сообщение
        self.Print("VFS Emulator приступил к работе! Напишите 'exit', чтобы выйти.\n")

    def Print(self, text):
        self.OutputArea.configure(state='normal')
        self.OutputArea.insert(tk.END, text)
        self.OutputArea.configure(state='disabled')
        self.OutputArea.see(tk.END)

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

        if CurrentArg:
            Args.append(''.join(CurrentArg))

        #проверяем ошибки
        if InsideQuotes:
            raise ValueError("Вы не закрыли кавычки!!!")
        if EscapeNext:
            raise ValueError("После '\' ничего нет!!!")

        return Args

    #универсальное выполнение 1 строки команды
    def ExecuteCommandString(self, CommandString, EchoInput=True):
        if EchoInput:
            self.Print(f"${CommandString}\n")
        try:
            Parts = self.ParseArguments(CommandString)
        except ValueError as e:
            self.Print(f"Ошибка парсера: {e}\n\n")
            return

        if not Parts:
            self.Print("\n")
            return

        cmd = Parts[0]
        args = Parts[1:]

        if cmd in self.Commands:
            try:
                result = self.Commands[cmd](args)
                if result:
                    self.Print(result+"\n")
            except Exception as e:
                self.Print(f"Ошибка при выполнении команды '{cmd}':{e}\n")
        else:
            self.Print(f"Команда не найдена: {cmd}\n\n")

    def ProcessCommand(self, event):
        CommandString = self.InputEntry.get()
        self.InputEntry.delete(0, tk.END)
        self.ExecuteCommandString(CommandString, EchoInput=True)

    def CMDls(self, Args):
        return f"Команда ls вызвана с аргументами: {Args}"

    def CMDcd(self, Args):
        return f"Команда cd вызвана с аргументами: {Args}"

    def CMDexit(self, Args):
        self.Print(f"Команда exit вызвана. Приложение закрывается...")
        self.RootWindow.destroy()



    def RunStartupScript(self, ScriptPath, DelayMs=50, UseComments=True, DisableInput=True):
        if not os.path.exists(ScriptPath):
            self.Print(f"Стартовый скрипт не найден: {ScriptPath}\n\n")
            return
        try:
            with open(ScriptPath, 'r', encoding='utf-8') as f:
                RawLines = list(enumerate(f, start=1))
        except Exception as e:
            self.Print(f"Не удалось открыть стартовый скрипт: {e}\n\n")
            return

        self.StartupQueue = []
        for linenumber, rawline in RawLines:
            line = rawline.rstrip('\n').rstrip('\r')
            self.StartupQueue.append((linenumber, line))

        if DisableInput:
            try:
                self.InputEntry.configure(state='disabled')
            except Exception:
                pass

        #пошаговое выполнение
        def ProcessNext():
            if not self.StartupQueue:
                self.Print("Стартовый скрипт завершён. \n\n")
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
            self.RootWindow.after(DelayMs, ProcessNext)

        self.RootWindow.after(0, ProcessNext)

def ManualParseArgs():
    VFSpath = None
    StartupScript = None
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--vfs" and i+1 < len(argv):
            VFSpath = argv[i+1]
            i+=2
        elif argv[i] == "--script" and i+1 < len(argv):
            StartupScript = argv[i+1]
            i+=2
        else:
            i+=1
    return VFSpath, StartupScript

if __name__ == "__main__":

    VFSpath, StartupScript = ManualParseArgs()

    RootWindow = tk.Tk()
    App = VFSEmulator(RootWindow, VFSpath=VFSpath, StartupScript=StartupScript)
    RootWindow.mainloop()
