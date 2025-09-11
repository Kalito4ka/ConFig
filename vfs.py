import tkinter as tk
from tkinter import scrolledtext

class VFSEmulator:
    def __init__(self, RootWindow):
        self.RootWindow = RootWindow
        self.RootWindow.title("VFS EMULATOR")
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

    def CMDls(self, Args):
        return f"Команда ls вызвана с аргументами: {Args}"

    def CMDcd(self, Args):
        return f"Команда cd вызвана с аргументами: {Args}"

    def CMDexit(self, Args):
        self.Print(f"Команда exit вызвана. Приложение закрывается...")
        self.RootWindow.destroy()

if __name__ == "__main__":
    RootWindow = tk.Tk()
    App = VFSEmulator(RootWindow)
    RootWindow.mainloop()
