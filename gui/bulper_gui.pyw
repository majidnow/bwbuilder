import glob
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, ttk

# ============================================================
# GUI - FARTAK CONTROL / HELP BUILDER
# Separate from bulper_poimu_final.py
# ============================================================

# GUI added by poimu
BACKEND = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "bulper_poimu_final.py",
)

VARIATION_LIST = [
    "FC22-01",
    "FC22-02",
    "FC22-02-LL",
    "FC22-03",
    "FC22R-01",
    "FC22R-02",
]

DEFAULT_WORKSPACE = "D:/Projects/STM32CubeIDE/workspace_1.15.0"
DEFAULT_IDE = "C:/ST/STM32CubeIDE_1.15.0/STM32CubeIDE/headless-build.bat"
DEFAULT_RELEASE = "D:/Storage/beachwolf/Archive/Release"
DEFAULT_WOLFLOADER_V2 = "D:/Storage/wolfloader/Archive/ver 2"
DEFAULT_WOLFLOADER_V1 = "D:/Storage/wolfloader/Archive/ver 1"
DEFAULT_CRC = r"D:\Storage\tools\crcc\main.exe"

ANSI = re.compile(r"\x1b\[[0-9;]*m")
PROGRESS = re.compile(r"\[\s*(\d+)%\]\s*(.*)")
VERSION = re.compile(
    r"Build Version:\s*(\d+),\s*Commit Hash:\s*(\S+)"
)

APP_ICON_PNG = """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"""


def hidden_flags():
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def read_project_name(project_dir):
    project_file = os.path.join(project_dir, ".project")
    if os.path.isfile(project_file):
        try:
            name = ET.parse(project_file).getroot().findtext("name")
            if name:
                return name.strip()
        except ET.ParseError:
            pass
    return os.path.basename(os.path.normpath(project_dir))


def resolve_workspace_project(selected_path):
    selected_path = os.path.abspath(
        os.path.expanduser(selected_path.strip())
    )

    if not os.path.isdir(selected_path):
        raise ValueError("Workspace not found")

    if os.path.isfile(os.path.join(selected_path, ".cproject")):
        return (
            os.path.dirname(selected_path),
            selected_path,
            read_project_name(selected_path),
        )

    beachwolf = os.path.join(selected_path, "BeachWolf")
    if os.path.isfile(os.path.join(beachwolf, ".cproject")):
        return (
            selected_path,
            beachwolf,
            read_project_name(beachwolf),
        )

    projects = [
        os.path.join(selected_path, name)
        for name in os.listdir(selected_path)
        if os.path.isfile(
            os.path.join(selected_path, name, ".cproject")
        )
    ]

    if len(projects) == 1:
        project = projects[0]
        return (
            selected_path,
            project,
            read_project_name(project),
        )

    if not projects:
        raise ValueError(".cproject not found")
    raise ValueError("Multiple STM32 projects found")


def read_cproject(project_dir):
    tree = ET.parse(os.path.join(project_dir, ".cproject"))
    result = {}

    for config in tree.getroot().iter("cconfiguration"):
        name = None

        for item in config.iter():
            if (
                item.tag.endswith("storageModule")
                and item.attrib.get("moduleId")
                    == "org.eclipse.cdt.core.settings"
                and item.attrib.get("name")
            ):
                name = item.attrib["name"]
                break

        if not name:
            for item in config.iter():
                if (
                    item.tag.endswith("configuration")
                    and item.attrib.get("name")
                ):
                    name = item.attrib["name"]
                    break

        if not name:
            continue

        symbols = []
        for option in config.iter("option"):
            option_id = option.attrib.get("id", "")
            super_class = option.attrib.get("superClass", "")
            value_type = option.attrib.get("valueType", "")

            if (
                value_type != "definedSymbols"
                and "preprocessor.def.symbols" not in option_id
                and "preprocessor.def.symbols" not in super_class
            ):
                continue

            for value in option.findall("listOptionValue"):
                symbol = value.attrib.get("value")
                if symbol and symbol not in symbols:
                    symbols.append(symbol)

        result[name] = symbols

    return result


def resolve_version_file(project_dir):
    for folder in ("include", "Inc", "Include"):
        path = os.path.join(project_dir, folder, "versions.h")
        if os.path.isfile(path):
            return path

    for root, dirs, files in os.walk(project_dir):
        relative = os.path.relpath(root, project_dir)
        if relative.count(os.sep) > 2:
            dirs[:] = []
            continue
        if "versions.h" in files:
            return os.path.join(root, "versions.h")

    raise ValueError("versions.h not found")


def resolve_cubeide_builder():
    if os.path.isfile(DEFAULT_IDE):
        return DEFAULT_IDE

    candidates = glob.glob(
        r"C:\ST\STM32CubeIDE_*\STM32CubeIDE\headless-build.bat"
    )
    if not candidates:
        raise ValueError("STM32CubeIDE builder not found")

    def version_key(path):
        folder = os.path.basename(
            os.path.dirname(os.path.dirname(path))
        )
        version = folder.replace("STM32CubeIDE_", "")
        return tuple(
            int(x) if x.isdigit() else 0
            for x in version.split(".")
        )

    return max(candidates, key=version_key)


# added by poimu
def resolve_git_executable():
    git = shutil.which("git")
    if git:
        return git

    app_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(app_dir, "tools", "git", "cmd", "git.exe"),
        os.path.join(app_dir, "git", "cmd", "git.exe"),
        os.path.join(app_dir, "tools", "git", "bin", "git.exe"),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    raise ValueError("Git not found")


class HelpBuilderGUI(tk.Tk):
    BG = "#090909"
    PANEL = "#111111"
    BORDER = "#2a2a2a"
    TEXT = "#eeeeee"
    MUTED = "#888888"
    BUTTON = "#202020"
    ACCENT = "#e6e6e6"

    def __init__(self):
        super().__init__()

        self.app_icon = tk.PhotoImage(data=APP_ICON_PNG)
        self.iconphoto(True, self.app_icon)

        self.title("Fartak Control - Help Builder")
        self.geometry("610x650")
        self.minsize(520, 560)
        self.configure(bg=self.BG)

        self.workspace = tk.StringVar(value=DEFAULT_WORKSPACE)
        self.select_configurations = tk.BooleanVar(value=False)
        self.create_hex = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Ready")
        self.percent = tk.DoubleVar(value=0)

        self.configuration_vars = {}
        self.configuration_rows = {}
        self.workspace_refresh_job = None

        self.process = None
        self.events = queue.Queue()
        self.cancelled = False

        # GUI added by poimu
        self.release_info = ""

        self._configure_style()
        self._build_gui()

        self.workspace.trace_add(
            "write",
            self.workspace_changed,
        )
        self.after(120, self.refresh_workspace)
        self.after(60, self.poll_events)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Dark.TCheckbutton",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 9),
        )
        style.map(
            "Dark.TCheckbutton",
            background=[("active", self.PANEL)],
            foreground=[("active", self.TEXT)],
        )

        style.configure(
            "Dark.TRadiobutton",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 9),
        )
        style.map(
            "Dark.TRadiobutton",
            background=[("active", self.PANEL)],
            foreground=[("active", self.TEXT)],
        )

    def _panel(self):
        return tk.Frame(
            self,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )

    def _build_gui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = tk.Frame(self, bg=self.BG)
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=22,
            pady=(18, 8),
        )

        tk.Label(
            header,
            text="FARTAK CONTROL",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 16),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Help Builder",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(1, 0))

        self.build_workspace_panel()
        self.build_options_panel()
        self.build_footer()

    def build_workspace_panel(self):
        panel = self._panel()
        panel.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=22,
            pady=7,
        )
        panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            panel,
            text="Workspace",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=12,
            pady=(10, 4),
        )

        entry = tk.Entry(
            panel,
            textvariable=self.workspace,
            bg=self.BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 9),
        )
        entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(12, 8),
            pady=(0, 11),
            ipady=7,
        )
        entry.bind(
            "<Return>",
            lambda _: self.refresh_workspace(),
        )
        entry.bind(
            "<FocusOut>",
            lambda _: self.refresh_workspace(),
        )

        tk.Button(
            panel,
            text="Browse",
            command=self.choose_workspace,
            bg=self.BUTTON,
            fg=self.TEXT,
            activebackground="#303030",
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=12,
        ).grid(
            row=1,
            column=1,
            padx=(0, 12),
            pady=(0, 11),
            ipady=4,
        )

    def build_options_panel(self):
        panel = self._panel()
        panel.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=22,
            pady=7,
        )
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(4, weight=1)

        tk.Label(
            panel,
            text="Build mode",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 9),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=12,
            pady=(11, 4),
        )

        mode = tk.Frame(panel, bg=self.PANEL)
        mode.grid(row=1, column=0, sticky="ew", padx=10)

        ttk.Radiobutton(
            mode,
            text="Auto · original six FC22 configurations",
            variable=self.select_configurations,
            value=False,
            command=self.update_configuration_state,
            style="Dark.TRadiobutton",
        ).pack(anchor="w", pady=1)

        ttk.Radiobutton(
            mode,
            text="Select build configurations",
            variable=self.select_configurations,
            value=True,
            command=self.update_configuration_state,
            style="Dark.TRadiobutton",
        ).pack(anchor="w", pady=1)

        tk.Frame(
            panel,
            height=1,
            bg=self.BORDER,
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            padx=12,
            pady=9,
        )

        header = tk.Frame(panel, bg=self.PANEL)
        header.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=12,
        )

        tk.Label(
            header,
            text="Build configurations",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 9),
        ).pack(side="left")

        tk.Button(
            header,
            text="All",
            command=self.select_all,
            bg=self.PANEL,
            fg=self.MUTED,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
        ).pack(side="right")

        tk.Button(
            header,
            text="None",
            command=self.select_none,
            bg=self.PANEL,
            fg=self.MUTED,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
        ).pack(side="right", padx=(0, 8))

        shell = tk.Frame(panel, bg=self.PANEL)
        shell.grid(
            row=4,
            column=0,
            sticky="nsew",
            padx=12,
            pady=(5, 8),
        )
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(0, weight=1)

        self.pre_canvas = tk.Canvas(
            shell,
            bg=self.PANEL,
            highlightthickness=0,
            bd=0,
            height=150,
        )
        self.pre_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            shell,
            orient="vertical",
            command=self.pre_canvas.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        self.pre_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.pre_frame = tk.Frame(
            self.pre_canvas,
            bg=self.PANEL,
        )
        self.pre_window = self.pre_canvas.create_window(
            (0, 0),
            window=self.pre_frame,
            anchor="nw",
        )

        self.pre_frame.bind(
            "<Configure>",
            lambda _: self.pre_canvas.configure(
                scrollregion=self.pre_canvas.bbox("all")
            ),
        )
        self.pre_canvas.bind(
            "<Configure>",
            lambda event: self.pre_canvas.itemconfigure(
                self.pre_window,
                width=event.width,
            ),
        )

        tk.Frame(
            panel,
            height=1,
            bg=self.BORDER,
        ).grid(
            row=5,
            column=0,
            sticky="ew",
            padx=12,
            pady=(2, 8),
        )

        ttk.Checkbutton(
            panel,
            text="Create programmer Firmware.hex",
            variable=self.create_hex,
            style="Dark.TCheckbutton",
        ).grid(
            row=6,
            column=0,
            sticky="w",
            padx=12,
            pady=(0, 11),
        )

    def build_footer(self):
        footer = tk.Frame(self, bg=self.BG)
        footer.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=22,
            pady=(7, 18),
        )
        footer.grid_columnconfigure(0, weight=1)

        self.progress_canvas = tk.Canvas(
            footer,
            height=8,
            bg="#202020",
            highlightthickness=0,
            bd=0,
        )
        self.progress_canvas.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        self.progress_canvas.bind(
            "<Configure>",
            lambda _: self.draw_progress(),
        )

        status_row = tk.Frame(footer, bg=self.BG)
        status_row.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(7, 9),
        )
        status_row.grid_columnconfigure(0, weight=1)

        tk.Label(
            status_row,
            textvariable=self.status,
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=0, column=0, sticky="w")

        self.percent_label = tk.Label(
            status_row,
            text="0%",
            bg=self.BG,
            fg=self.TEXT,
            font=("Consolas", 9),
        )
        self.percent_label.grid(row=0, column=1, sticky="e")

        self.build_button = tk.Button(
            footer,
            text="BUILD",
            command=self.start_build,
            bg=self.ACCENT,
            fg=self.BG,
            activebackground="#cfcfcf",
            activeforeground=self.BG,
            relief="flat",
            bd=0,
            font=("Segoe UI Semibold", 10),
        )
        self.build_button.grid(
            row=2,
            column=0,
            sticky="ew",
            ipady=9,
        )

    def choose_workspace(self):
        selected = filedialog.askdirectory(
            title="Select STM32CubeIDE workspace",
            initialdir=self.workspace.get() or None,
        )
        if selected:
            self.workspace.set(selected.replace("\\", "/"))

    def workspace_changed(self, *_):
        if self.workspace_refresh_job is not None:
            self.after_cancel(self.workspace_refresh_job)
        self.workspace_refresh_job = self.after(
            300,
            self.refresh_workspace,
        )

    def refresh_workspace(self):
        self.workspace_refresh_job = None

        try:
            workspace, project_dir, project_name = (
                resolve_workspace_project(self.workspace.get())
            )
            configurations = read_cproject(project_dir)
            resolve_version_file(project_dir)

            try:
                git = resolve_git_executable()
                git_ok = subprocess.run(
                    [git, "rev-parse", "--is-inside-work-tree"],
                    cwd=project_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=hidden_flags(),
                ).returncode == 0
            except Exception:
                git_ok = False

            if git_ok:
                self.status.set(
                    f"{project_name} · {len(configurations)} configurations"
                )
            else:
                self.status.set("Git repository not found")

        except Exception:
            configurations = {}
            self.status.set("Workspace incomplete")

        for widget in self.pre_frame.winfo_children():
            widget.destroy()

        self.configuration_vars.clear()
        self.configuration_rows.clear()

        # removed by poimu
        # Non-FC22 configurations were previously display-only.

        # removed by poimu
        # Every real .cproject Build Configuration was previously selectable.

        # added by poimu
        # The locked backend supports the production FC22 configurations only.
        # Preprocessor symbols are displayed as information only.
        fc22_configurations = {
            name: symbols
            for name, symbols in configurations.items()
            if name in VARIATION_LIST
        }

        for configuration, symbols in fc22_configurations.items():
            variable = tk.BooleanVar(value=True)
            self.configuration_vars[configuration] = variable

            text = ", ".join(symbols) if symbols else "no defined symbols"
            row = ttk.Checkbutton(
                self.pre_frame,
                text=f"{configuration}   ·   {text}",
                variable=variable,
                style="Dark.TCheckbutton",
            )
            row.pack(fill="x", anchor="w", pady=1)
            self.configuration_rows[configuration] = row

        if not fc22_configurations:
            tk.Label(
                self.pre_frame,
                text="No FC22 build configurations found",
                bg=self.PANEL,
                fg=self.MUTED,
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=3)

        self.update_configuration_state()

    def update_configuration_state(self):
        enabled = self.select_configurations.get()
        for row in self.configuration_rows.values():
            row.state(
                ["!disabled"] if enabled else ["disabled"]
            )

    def select_all(self):
        for variable in self.configuration_vars.values():
            variable.set(True)

    def select_none(self):
        for variable in self.configuration_vars.values():
            variable.set(False)

    def selected_configurations(self):
        if not self.select_configurations.get():
            return []

        selected = [
            name
            for name, variable in self.configuration_vars.items()
            if variable.get()
        ]
        if not selected:
            raise ValueError("Select a build configuration")
        return selected

    def set_progress(self, value, text):
        value = max(0, min(100, float(value)))
        self.percent.set(value)
        self.status.set(text)
        self.percent_label.config(text=f"{round(value)}%")
        self.draw_progress()

    def draw_progress(self):
        canvas = self.progress_canvas
        canvas.delete("all")

        width = max(1, canvas.winfo_width())
        height = canvas.winfo_height()
        filled = width * self.percent.get() / 100

        canvas.create_rectangle(
            0, 0, width, height,
            fill="#202020", outline=""
        )
        canvas.create_rectangle(
            0, 0, filled, height,
            fill=self.ACCENT, outline=""
        )

    def python_exe(self):
        exe = sys.executable
        if (
            os.name == "nt"
            and exe.lower().endswith("pythonw.exe")
        ):
            python = exe[:-11] + "python.exe"
            if os.path.isfile(python):
                return python
        return exe

    def build_command(self):
        workspace, project_dir, project_name = (
            resolve_workspace_project(self.workspace.get())
        )
        version_file = resolve_version_file(project_dir)
        ide = resolve_cubeide_builder()
        configurations = read_cproject(project_dir)

        # added by poimu
        # Only availability/repository presence is checked here.
        # Workspace cleanliness remains exclusively the strict stash -u check
        # inside bulper_poimu_final.py.
        git = resolve_git_executable()

        if subprocess.run(
            [git, "rev-parse", "--is-inside-work-tree"],
            cwd=project_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=hidden_flags(),
        ).returncode != 0:
            raise ValueError("Git repository not found")

        # removed by poimu
        # Base mode no longer blocks the GUI only because FC22 configuration
        # names are absent. Generic workspaces can use their real configurations.

        relative_version = os.path.relpath(
            version_file,
            project_dir,
        ).replace("\\", "/")
        relative_version = "/" + relative_version

        command = [
            self.python_exe(),
            "-u",
            BACKEND,
            "-d",
            project_dir.replace("\\", "/"),
            "-v",
            relative_version,

            # added by poimu
            # versions.h has one release REVISION; select that exact first token.
            "-b",
            "1",

            "--workspace",
            workspace.replace("\\", "/"),
            "--project-name",
            project_name,
            "--ide",
            ide,

            # added by poimu
            "--git",
            git,

            # GUI added by poimu
            # Enables the backend's GUI-only interface without changing
            # standalone backend behavior.
            "--gui-application",
        ]

        selected = self.selected_configurations()

        # removed by poimu
        # Base mode previously fell back to arbitrary non-FC22 configurations.

        # added by poimu
        # Auto mode preserves the locked backend's exact six FC22 variations.
        production_base = all(
            name in configurations
            for name in VARIATION_LIST
        )

        if not self.select_configurations.get() and not production_base:
            missing = [
                name for name in VARIATION_LIST
                if name not in configurations
            ]
            raise ValueError(
                "Missing FC22 build configurations: " + ", ".join(missing)
            )

        for configuration in selected:
            command += ["--configuration", configuration]

        if self.create_hex.get():
            command.append("--create-programmer-hex")

        return command

    def start_build(self):
        if self.process and self.process.poll() is None:
            return

        try:
            self.refresh_workspace()
            command = self.build_command()
        except Exception as exc:
            messagebox.showwarning(
                "Fartak Control",
                str(exc),
            )
            return

        self.set_progress(0, "Starting")
        self.build_button.config(state="disabled")
        self.cancelled = False
        # GUI added by poimu
        self.release_info = ""

        threading.Thread(
            target=self.run_backend,
            args=(command,),
            daemon=True,
        ).start()

    def run_backend(self, command):
        try:
            self.process = subprocess.Popen(
                command,
                cwd=os.path.dirname(BACKEND),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,
                creationflags=hidden_flags(),
            )
        except Exception as exc:
            self.events.put(("error", str(exc)))
            return

        buffer = ""
        recent = []

        while True:
            char = self.process.stdout.read(1)
            if not char:
                break

            buffer += char

            if char == "\n":
                line = ANSI.sub("", buffer).strip()
                buffer = ""

                if line:
                    recent.append(line)
                    recent = recent[-8:]

                match = PROGRESS.search(line)
                if match:
                    self.events.put(
                        (
                            "progress",
                            int(match.group(1)),
                            match.group(2),
                        )
                    )

                match = VERSION.search(line)
                if match:
                    self.events.put(
                        (
                            "version",
                            match.group(1),
                            match.group(2),
                        )
                    )

                if line in ("Build failed", "HEX merge failed"):
                    self.events.put(("failure", line))
                    try:
                        self.process.stdin.write("\n")
                        self.process.stdin.flush()
                    except Exception:
                        pass

            if "Continue? (y/n):" in ANSI.sub("", buffer):
                buffer = ""
                self.events.put(("confirm",))

        self.events.put(
            ("done", self.process.wait(), recent)
        )

    def poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]

                if kind == "progress":
                    self.set_progress(event[1], event[2])

                elif kind == "version":
                    # GUI added by poimu
                    self.release_info = (
                        f"Revision {event[1]} · {event[2]}"
                    )
                    self.status.set(self.release_info)

                elif kind == "confirm":
                    ok = messagebox.askyesno(
                        "Fartak Control",
                        f"{self.release_info or self.status.get()}\n\nContinue?"
                    )
                    self.cancelled = not ok
                    try:
                        self.process.stdin.write(
                            "y\n" if ok else "n\n"
                        )
                        self.process.stdin.flush()
                    except Exception:
                        pass

                elif kind == "failure":
                    self.status.set(event[1])

                elif kind == "error":
                    self.build_button.config(state="normal")
                    self.set_progress(0, "Failed")
                    messagebox.showerror(
                        "Fartak Control",
                        event[1],
                    )

                elif kind == "done":
                    _, return_code, recent = event
                    self.build_button.config(state="normal")

                    if self.cancelled:
                        self.set_progress(0, "Cancelled")
                    elif return_code == 0:
                        self.set_progress(100, "Release completed")
                    else:
                        self.set_progress(0, "Failed")
                        messagebox.showerror(
                            "Fartak Control",
                            "\n".join(recent[-4:])
                            or f"Exit code: {return_code}",
                        )

        except queue.Empty:
            pass

        self.after(60, self.poll_events)

    def close_app(self):
        if (
            self.process
            and self.process.poll() is None
            and not messagebox.askyesno(
                "Fartak Control",
                "Build is running. Stop it?",
            )
        ):
            return

        if self.process and self.process.poll() is None:
            self.process.terminate()

        self.destroy()


if __name__ == "__main__":
    HelpBuilderGUI().mainloop()
