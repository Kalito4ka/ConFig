#Козорез Е.И. 9 вариант
import tkinter as tk
from tkinter import scrolledtext
import os
import sys
import base64
import csv

class VFSNode:
    def __init__(self, Name, NodeType="directory", Content=None, Parent=None):
        self.Name = Name
        self.Type = NodeType
        self.Content = Content if Content else b""
        self.Children = {}
        self.Parent = Parent

    def AddChildren(self, Child):
        if self.Type != "directory":
            raise ValueError("Нельзя добавлять потомка в файл")
        self.Children[Child.Name] = Child
        Child.Parent = self

    def GetChild(self, Name):
        return self.Children.get(Name)

    def ListChildren(self):
        return list(self.Children.values())

    def Path(self):
        parts = []
        node = self
        while node is not None and node.Parent is not None:
            parts.append(node.Name)
            node = node.Parent
        return "/" + "/".join(reversed(parts))

class VFSEmulator:
    def __init__(self, RootWindow, VFSpath=None, StartupScript=None):
        self.RootWindow = RootWindow
        self.VFSname = "VFS Emulator"
        self.RootWindow.title(self.VFSname)

        self.OutputArea = scrolledtext.ScrolledText(RootWindow, state='disabled', height=20, width=80)
        self.OutputArea.pack(padx=10, pady=10)

        self.InputEntry = tk.Entry(RootWindow, width=80)
        self.InputEntry.pack(padx=10, pady=(0, 10))
        self.InputEntry.bind("<Return>", self.ProcessCommand)

        self.Commands = {"ls": self.CMDls,
                         "cd": self.CMDcd,
                         "who": self.CMDwho,
                         "cat": self.CMDcat,
                         "tac": self.CMDtac,
                         "exit": self.CMDexit,
                         }

        self.VFSpath = VFSpath
        self.StartupScript = StartupScript

        self.VFSRoot = None
        self.CurrentDir = None

        if self.VFSpath:
            self.LoadVFSManual(self.VFSpath)

        self._running_startup = False
        self._startup_had_errors = False

        self.Print(f"Параметры запуска:\n  VFS path: {self.VFSpath}\n  Startup script: {self.StartupScript}\n\n")
        self.Print("VFS Emulator приступил к работе! Напишите 'exit', чтобы выйти.\n")

        if self.StartupScript:
            if self.VFSRoot:
                self.RootWindow.after(100, lambda: self.RunStartupScript(self.StartupScript))
            else:
                self.Print("Стартовый скрипт не будет выполнен, VFS не загружена.\n")

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

        if InsideQuotes:
            raise ValueError("Вы не закрыли кавычки!!!")
        if EscapeNext:
            raise ValueError("После '\\' ничего нет!!!")

        return Args

    def ExecuteCommandString(self, CommandString, EchoInput=True):
        if EchoInput:
            self.Print(f"${CommandString}\n")
        try:
            Parts = self.ParseArguments(CommandString)
        except ValueError as e:
            self.Print(f"Ошибка парсера: {e}\n\n")
            if getattr(self, "_running_startup", False):
                self._startup_had_errors = True
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
                    self.Print(result + "\n")
            except Exception as e:
                self.Print(f"Ошибка при выполнении команды '{cmd}': {e}\n")
                if getattr(self, "_running_startup", False):
                    self._startup_had_errors = True
        else:
            self.Print(f"Команда не найдена: {cmd}\n\n")
            if getattr(self, "_running_startup", False):
                self._startup_had_errors = True

    def ProcessCommand(self, event):
        CommandString = self.InputEntry.get()
        self.InputEntry.delete(0, tk.END)
        self.ExecuteCommandString(CommandString, EchoInput=True)

    def ResolvePath(self, startNode, PathStr):
        if not PathStr:
            return startNode
        p = PathStr.strip()
        if p.startswith("/"):
            node = self.VFSRoot
            parts = [part for part in p.strip("/").split("/") if part != ""]
        else:
            node = startNode
            parts = [part for part in p.split("/") if part != ""]
        for part in parts:
            if part == ".":
                continue
            if part == "..":
                if node.Parent:
                    node = node.Parent
                else:
                    return None
                continue
            child = node.GetChild(part)
            if not child:
                return None
            node = child
        return node

    def CMDls(self, Args):
        if not self.CurrentDir:
            return "VFS не загружена. Невозможно выполнить ls."
        DirToList = self.CurrentDir
        if Args:
            target = Args[0].strip()
            node = self.ResolvePath(self.CurrentDir, target)
            if not node:
                return f"Нет такой директории: {target}"
            if node.Type != "directory":
                return f"{target} не является директорией"
            DirToList = node
        ChildNames = []
        for ChildNode in DirToList.ListChildren():
            ChildNames.append(ChildNode.Name)
        return "  ".join(ChildNames) if ChildNames else "(пусто)"

    def CMDcd(self, Args):
        if not self.CurrentDir:
            return "VFS не загружена. Невозможно выполнить cd."
        if not Args:
            self.CurrentDir = self.VFSRoot
            return
        Path = Args[0].strip()
        if Path == "..":
            if self.CurrentDir.Parent:
                self.CurrentDir = self.CurrentDir.Parent
            return
        Node = self.ResolvePath(self.CurrentDir, Path)
        if not Node:
            return f"Нет такой директории: {Path}"
        if Node.Type != "directory":
            return f"{Path} не является директорией"
        self.CurrentDir = Node

    def CMDwho(self, Args):
        try:
            user = os.getlogin()
        except Exception:
            user = os.environ.get("USER") or os.environ.get("USERNAME") or "user"
        return user

    def CMDcat(self, Args):
        if not Args:
            return "Использование: cat <путь>"
        path = Args[0]
        node = self.ResolvePath(self.CurrentDir, path)
        if not node:
            return f"Нет такого файла: {path}"
        if node.Type != "file":
            return f"{path} не является файлом"
        try:
            text = node.Content.decode('utf-8')
        except Exception:
            text = node.Content.decode('utf-8', errors='replace')
        return text

    def CMDtac(self, Args):
        if not Args:
            return "Использование: tac <путь>"
        path = Args[0]
        node = self.ResolvePath(self.CurrentDir, path)
        if not node:
            return f"Нет такого файла: {path}"
        if node.Type != "file":
            return f"{path} не является файлом"
        text = node.Content.decode('utf-8', errors='replace')
        lines = text.splitlines()
        return "\n".join(reversed(lines))

    def CMDexit(self, Args):
        if getattr(self, "_startup_had_errors", False):
            self.Print("Внимание: при выполнении стартового скрипта были ошибки.\n")
        self.Print("Команда exit вызвана. Приложение закрывается...\n")
        self.RootWindow.destroy()

    def RunStartupScript(self, ScriptPath, DelayMs=50, UseComments=True, DisableInput=True):
        if not os.path.exists(ScriptPath):
            self.Print(f"Стартовый скрипт не найден: {ScriptPath}\n\n")
            self._startup_had_errors = True
            return
        try:
            with open(ScriptPath, 'r', encoding='utf-8') as f:
                RawLines = list(enumerate(f, start=1))
        except Exception as e:
            self.Print(f"Не удалось открыть стартовый скрипт: {e}\n\n")
            self._startup_had_errors = True
            return

        self.StartupQueue = []
        for Num, Line in RawLines:
            CleanLine = Line.rstrip("\r\n")
            self.StartupQueue.append((Num, CleanLine))

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
            if not stripped or (UseComments and stripped.startswith('#')):
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

    def LoadVFSManual(self, CSVPath):
        if not os.path.exists(CSVPath):
            self.Print(f"Файл VFS не найден: {CSVPath}\n")
            self.VFSRoot = None
            self.CurrentDir = None
            self._startup_had_errors = True
            return

        root = VFSNode("/", "directory")
        nodes = {"/": root}

        errors = []
        processed_paths = set()

        try:
            with open(CSVPath, "r", encoding="utf-8-sig", newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                if reader.fieldnames is None:
                    self.Print(f"Ошибка формата VFS: CSV не содержит заголовков.\n")
                    self.VFSRoot = None
                    self.CurrentDir = None
                    self._startup_had_errors = True
                    return

                fnames = [fn.strip() for fn in reader.fieldnames]
                if "Path" not in fnames or "Type" not in fnames:
                    self.Print(
                        f"Ошибка формата VFS: в CSV обязателен столбец 'Path' и 'Type'. Найдены: {', '.join(fnames)}\n")
                    self.VFSRoot = None
                    self.CurrentDir = None
                    self._startup_had_errors = True
                    return

                raw_rows = list(enumerate(reader, start=2))  # start=2 — потому что header на 1 строке
                for lineno, row in raw_rows:
                    raw_path = row.get("Path")
                    raw_type = row.get("Type")
                    raw_content = row.get("Content", "")

                    if raw_path is None or raw_type is None:
                        errors.append((lineno, "Отсутствует обязательное поле 'Path' или 'Type'"))
                        continue

                    path = raw_path.replace("\\", "/").strip()
                    type_ = raw_type.strip()
                    content = raw_content.strip() if raw_content else ""

                    if not path:
                        errors.append((lineno, "Пустое значение Path"))
                        continue

                    if path == "/":
                        continue

                    stripped_path = path.strip("/")
                    path_parts = [p.strip() for p in stripped_path.split("/") if p.strip() != ""]
                    if not path_parts:
                        errors.append((lineno, f"Некорректный Path: '{raw_path}'"))
                        continue

                    node_name = path_parts[-1]
                    parent_path = "/" + "/".join(path_parts[:-1]) if len(path_parts) > 1 else "/"

                    parent = nodes.get(parent_path)
                    if not parent:
                        errors.append((lineno, f"Родительский путь не найден: '{parent_path}' для '{path}'"))
                        continue

                    if type_ == "file":
                        try:
                            content_bytes = base64.b64decode(content) if content else b""
                        except Exception:
                            content_bytes = b""
                            errors.append(
                                (lineno, f"Невалидный base64 в Content для файла '{path}' — содержимое будет пустым"))
                        node = VFSNode(node_name, "file", content_bytes, Parent=parent)
                    elif type_ == "directory":
                        node = VFSNode(node_name, "directory", None, Parent=parent)
                    else:
                        errors.append((lineno, f"Неизвестный Type '{type_}' в строке"))
                        continue

                    if node_name in parent.Children:
                        errors.append(
                            (lineno, f"Дубликат узла '{node_name}' в '{parent_path}' — строка проигнорирована"))
                        continue

                    parent.AddChildren(node)
                    processed_paths.add(path)

                    if type_ == "directory":
                        full_path = parent_path + "/" + node_name if parent_path != "/" else "/" + node_name
                        nodes[full_path] = node

            if errors:
                self.Print(f"В процессе загрузки VFS обнаружены ошибки в файле {CSVPath}:\n")
                for lineno, msg in errors:
                    self.Print(f"  строка {lineno}: {msg}\n")
                self.Print("\nVFS не загружена из-за ошибок формата.\n")
                self.VFSRoot = None
                self.CurrentDir = None
                self._startup_had_errors = True
                return

            self.VFSRoot = root
            self.CurrentDir = root
            self.Print(f"VFS загружена успешно: {CSVPath}\n")

        except Exception as e:
            self.Print(f"Ошибка при загрузке VFS: {e}\n")
            self.VFSRoot = None
            self.CurrentDir = None
            self._startup_had_errors = True

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