import glob
import os
import queue
import re
import shutil
import subprocess
import sys

import tempfile

import threading
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, ttk

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

def project_uses_user_cflags(project_dir, configuration_names):
    tree = ET.parse(os.path.join(project_dir, ".cproject"))
    matched = set()

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

        if name not in configuration_names:
            continue

        c_flags = False
        cpp_flags = False
        for tool in config.iter("tool"):
            identity = " ".join((
                tool.attrib.get("id", ""),
                tool.attrib.get("name", ""),
                tool.attrib.get("superClass", ""),
            )).lower()
            if "USER_CFLAGS" not in ET.tostring(tool, encoding="unicode"):
                continue
            if "g++ compiler" in identity or ".cpp.compiler" in identity:
                cpp_flags = True
            elif "gcc compiler" in identity or ".c.compiler" in identity:
                c_flags = True

        if c_flags and cpp_flags:
            matched.add(name)

    return all(name in matched for name in configuration_names)

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

def verify_bin_crc(bin_path):

    if not os.path.isfile(bin_path):
        raise ValueError("Binary file not found")

    with open(bin_path, "rb") as source:
        data = source.read()

    if len(data) < 2:
        return False, False, None, None

    stored_crc = int.from_bytes(data[-2:], byteorder="little")
    payload = data[:-2]

    if not os.path.isfile(DEFAULT_CRC):
        raise ValueError("CRC generator main.exe not found")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".bin",
        ) as temp:
            temp.write(payload)
            temp_path = temp.name

        calculated_crc = int(
            subprocess.check_output(
                [DEFAULT_CRC, temp_path],
                text=True,
                creationflags=hidden_flags(),
            ).strip()
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    valid = stored_crc == calculated_crc
    return valid, valid, stored_crc, calculated_crc

def extract_error_entries(text):

    primary = []
    fallback = []
    seen = set()

    for raw_line in text.splitlines():
        line = ANSI.sub("", raw_line).strip()
        if not line:
            continue

        lower = line.lower()
        if "warning:" in lower:
            continue

        match = re.search(r"\berror:\s*(.+)$", line, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            key = ("primary", line)
            if key not in seen:
                seen.add(key)
                primary.append((title, line))
            continue

        if "undefined reference to" in lower:
            title = line[line.lower().find("undefined reference to"):].strip()
            key = ("primary", line)
            if key not in seen:
                seen.add(key)
                primary.append((title, line))
            continue

        fallback_patterns = (
            "build failed",
            "hex merge failed",
            "crc verification failed",
            "failed configurations:",
        )
        if any(pattern in lower for pattern in fallback_patterns):
            key = ("fallback", line)
            if key not in seen:
                seen.add(key)
                fallback.append((line, line))

    return primary if primary else fallback

def read_build_error_entries(log_path):
    if not os.path.isfile(log_path):
        return []

    with open(
        log_path,
        "r",
        encoding="utf-8",
        errors="replace",
    ) as build_log:
        return extract_error_entries(build_log.read())

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
        self.create_hex = tk.BooleanVar(value=False)

        self.revision_value = tk.StringVar(value="")

        self.status = tk.StringVar(value="Ready")
        self.percent = tk.DoubleVar(value=0)

        self.configuration_vars = {}
        self.configuration_rows = {}

        self.configuration_selection_cache = {}

        self.workspace_refresh_job = None

        self.process = None
        self.events = queue.Queue()
        self.cancelled = False

        self.error_entries = []

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

        tk.Button(
            header,
            text="CRC TOOL",
            command=self.open_crc_tool,
            bg=self.BUTTON,
            fg=self.MUTED,
            activebackground="#303030",
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=10,
        ).pack(side="right", anchor="e")

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
        panel.grid_rowconfigure(3, weight=1)

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

        revision_frame = tk.Frame(mode, bg=self.PANEL)
        revision_frame.pack(fill="x", anchor="w", pady=(1, 1))

        tk.Label(
            revision_frame,
            text="MANUAL REVISION INPUT",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        tk.Entry(
            revision_frame,
            textvariable=self.revision_value,
            bg=self.BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 9),
        ).pack(
            fill="x",
            anchor="w",
            pady=(4, 0),
            ipady=7,
        )

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

        shell = tk.Frame(panel, bg=self.PANEL)
        shell.grid(
            row=3,
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

        def resize_pre_canvas(event):
            self.pre_canvas.itemconfigure(
                self.pre_window,
                width=event.width,
            )
            content_height = self.pre_frame.winfo_reqheight()
            self.pre_canvas.configure(
                scrollregion=(
                    0,
                    0,
                    event.width,
                    max(content_height, event.height),
                )
            )
            if content_height <= event.height:
                self.pre_canvas.yview_moveto(0)

        self.pre_canvas.bind(
            "<Configure>",
            resize_pre_canvas,
        )

        self.bind_all(
            "<MouseWheel>",
            self._on_preprocessor_mousewheel,
            add="+",
        )
        self.bind_all(
            "<Button-4>",
            self._on_preprocessor_mousewheel,
            add="+",
        )
        self.bind_all(
            "<Button-5>",
            self._on_preprocessor_mousewheel,
            add="+",
        )

        tk.Frame(
            panel,
            height=1,
            bg=self.BORDER,
        ).grid(
            row=4,
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
            row=5,
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

        self.log_button = tk.Button(
            footer,
            text="log+",
            command=self.open_error_log,
            bg=self.BG,
            fg=self.MUTED,
            activebackground=self.BG,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 8),
            padx=5,
            pady=1,
        )
        self.log_button.grid(
            row=3,
            column=0,
            sticky="e",
            pady=(4, 0),
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

        self.configuration_selection_cache.update({
            name: bool(variable.get())
            for name, variable in self.configuration_vars.items()
        })
        previous_configurations = dict(
            self.configuration_selection_cache
        )

        try:
            _, project_dir, project_name = (
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

        fc22_configurations = {
            name: symbols
            for name, symbols in configurations.items()
            if name in VARIATION_LIST
        }

        config_header = tk.Frame(self.pre_frame, bg=self.PANEL)
        config_header.pack(
            fill="x",
            anchor="w",
            pady=(0, 3),
        )

        tk.Label(
            config_header,
            text="Build configurations",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 9),
        ).pack(side="left")

        tk.Button(
            config_header,
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
            config_header,
            text="None",
            command=self.select_none,
            bg=self.PANEL,
            fg=self.MUTED,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
        ).pack(side="right", padx=(0, 8))

        for configuration, symbols in fc22_configurations.items():
            variable = tk.BooleanVar(
                value=previous_configurations.get(configuration, True)
            )
            self.configuration_vars[configuration] = variable

            configuration_text = (
                ", ".join(symbols)
                if symbols
                else "no defined symbols"
            )
            row = ttk.Checkbutton(
                self.pre_frame,
                text=f"{configuration}   ·   {configuration_text}",
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

    def _on_preprocessor_mousewheel(self, event):
        if not hasattr(self, "pre_canvas"):
            return

        x = self.winfo_pointerx()
        y = self.winfo_pointery()
        left = self.pre_canvas.winfo_rootx()
        top = self.pre_canvas.winfo_rooty()
        right = left + self.pre_canvas.winfo_width()
        bottom = top + self.pre_canvas.winfo_height()

        if not (left <= x <= right and top <= y <= bottom):
            return

        content_height = self.pre_frame.winfo_reqheight()
        if content_height <= self.pre_canvas.winfo_height():
            self.pre_canvas.yview_moveto(0)
            return "break"

        if getattr(event, "num", None) == 4:
            units = -1
        elif getattr(event, "num", None) == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return
            units = -1 if delta > 0 else 1

        self.pre_canvas.yview_scroll(units, "units")
        return "break"

    def select_all(self):
        for variable in self.configuration_vars.values():
            variable.set(True)

    def select_none(self):
        for variable in self.configuration_vars.values():
            variable.set(False)

    def selected_configurations(self):
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

        git = resolve_git_executable()

        if subprocess.run(
            [git, "rev-parse", "--is-inside-work-tree"],
            cwd=project_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=hidden_flags(),
        ).returncode != 0:
            raise ValueError("Git repository not found")

        relative_version = os.path.relpath(
            version_file,
            project_dir,
        ).replace("\\", "/")
        relative_version = "/" + relative_version

        selected = self.selected_configurations()
        missing = [name for name in selected if name not in configurations]
        if missing:
            raise ValueError(
                "Missing build configurations: " + ", ".join(missing)
            )

        revision_value = self.revision_value.get().strip()
        if not revision_value.isdigit():
            raise ValueError(
                "MANUAL REVISION INPUT must be a revision number"
            )
        if int(revision_value) < 50:
            raise ValueError(
                "MANUAL REVISION INPUT must be 50 or greater"
            )

        if not project_uses_user_cflags(project_dir, selected):
            raise ValueError(
                "USER_CFLAGS must be configured for both C and C++ "
                "in every selected CubeIDE configuration"
            )

        command = [
            self.python_exe(),
            "-u",
            BACKEND,
            "-d",
            project_dir.replace("\\", "/"),
            "-v",
            relative_version,
            "--workspace",
            workspace.replace("\\", "/"),
            "--project-name",
            project_name,
            "--ide",
            ide,
            "--git",
            git,
            "--revision-value",
            revision_value,
        ]

        for configuration in selected:
            command += ["--configuration", configuration]

        if self.create_hex.get():
            command.append("--create-programmer-hex")

        return command

    def start_build(self):
        if self.process and self.process.poll() is None:
            return

        try:

            command = self.build_command()
        except Exception as exc:
            messagebox.showwarning(
                "Fartak Control",
                str(exc),
            )
            return

        self.release_info = ""

        self.set_progress(0, "Starting")
        self.build_button.config(state="disabled")
        self.cancelled = False

        self.error_entries = []

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

                    self.release_info = (
                        f"Revision {event[1]} · {event[2]}"
                    )
                    self.status.set(self.release_info)

                elif kind == "confirm":

                    ok = messagebox.askyesno(
                        "Fartak Control - Confirm Build",
                        f"{self.release_info or self.status.get()}\n\nContinue build?"
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
                    self.error_entries = [(event[1], event[1])]
                    self.set_progress(0, f"Error: {event[1]}")

                elif kind == "done":
                    _, return_code, recent = event
                    self.build_button.config(state="normal")

                    if self.cancelled:
                        self.set_progress(0, "Cancelled")
                    elif return_code == 0:
                        self.set_progress(100, "Release completed")

                        messagebox.showinfo(
                            "Fartak Control",
                            "CRC presence and validity were verified.",
                        )

                    else:
                        log_path = os.path.join(
                            os.path.dirname(BACKEND),
                            "bulper_build.log",
                        )
                        self.error_entries = read_build_error_entries(
                            log_path
                        )

                        backend_errors = extract_error_entries(
                            "\n".join(recent)
                        )
                        known_lines = {
                            full_line
                            for _, full_line in self.error_entries
                        }
                        for entry in backend_errors:
                            if entry[1] not in known_lines:
                                self.error_entries.append(entry)
                                known_lines.add(entry[1])

                        if not self.error_entries:
                            self.error_entries = [
                                (

                                    "Build failed",
                                    "Build failed",
                                )
                            ]

                        error_title = self.error_entries[0][0]
                        self.set_progress(0, f"Error: {error_title}")

        except queue.Empty:
            pass

        self.after(60, self.poll_events)

    def open_error_log(self):
        window = tk.Toplevel(self)
        window.title("Fartak Control - Error Log")
        window.geometry("650x330")
        window.minsize(520, 260)
        window.configure(bg=self.BG)
        window.transient(self)

        panel = tk.Frame(
            window,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        panel.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18,
        )
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        tk.Label(
            panel,
            text="ERROR LOG",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 13),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=12,
            pady=(12, 2),
        )

        tk.Label(
            panel,

            text="Errors only",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=12,
            pady=(0, 8),
        )

        text_frame = tk.Frame(panel, bg=self.PANEL)
        text_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=12,
            pady=(0, 12),
        )
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        error_text = tk.Text(
            text_frame,
            bg=self.BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            wrap="word",
            font=("Consolas", 9),
            padx=9,
            pady=9,
        )
        error_text.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=error_text.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        error_text.configure(
            yscrollcommand=scrollbar.set
        )

        entries = self.error_entries
        if not entries:
            log_path = os.path.join(
                os.path.dirname(BACKEND),
                "bulper_build.log",
            )
            entries = read_build_error_entries(log_path)

        if entries:
            for index, (_, full_line) in enumerate(entries, start=1):
                error_text.insert(
                    "end",
                    f"{index}. {full_line}\n\n",
                )
        else:
            error_text.insert(
                "end",
                "No build errors recorded.",
            )

        error_text.config(state="disabled")

    def open_crc_tool(self):
        window = tk.Toplevel(self)
        window.title("Fartak Control - CRC Tool")
        window.geometry("520x265")
        window.minsize(470, 240)
        window.configure(bg=self.BG)
        window.transient(self)

        file_path = tk.StringVar()
        crc_status = tk.StringVar(value="Select a .bin file")
        present_status = tk.StringVar(value="CRC detected: —")
        valid_status = tk.StringVar(value="CRC valid: —")

        panel = tk.Frame(
            window,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        panel.grid_columnconfigure(0, weight=1)

        tk.Label(
            panel,
            text="CRC CHECK",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 13),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=12,
            pady=(12, 3),
        )

        tk.Label(
            panel,
            text="Verify the appended 16-bit CRC of an update .bin file",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            padx=12,
            pady=(0, 10),
        )

        entry = tk.Entry(
            panel,
            textvariable=file_path,
            bg=self.BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 9),
        )
        entry.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=(12, 8),
            pady=(0, 10),
            ipady=7,
        )

        def choose_file():
            selected = filedialog.askopenfilename(
                title="Select update.bin",
                filetypes=[
                    ("Binary files", "*.bin"),
                    ("All files", "*.*"),
                ],
            )
            if selected:
                file_path.set(selected.replace("\\", "/"))
                crc_status.set("Ready to verify")
                present_status.set("CRC detected: —")
                valid_status.set("CRC valid: —")

        def verify_file():
            path = file_path.get().strip()
            if not path:
                messagebox.showwarning(
                    "Fartak Control",
                    "Select a .bin file",
                    parent=window,
                )
                return

            try:
                present, valid, stored_crc, calculated_crc = (
                    verify_bin_crc(path)
                )
            except Exception as exc:
                present_status.set("CRC detected: ✕")
                valid_status.set("CRC valid: ✕")
                crc_status.set(str(exc))
                return

            present_status.set(
                "CRC detected: ✓" if present else "CRC detected: ✕"
            )
            valid_status.set(
                "CRC valid: ✓" if valid else "CRC valid: ✕"
            )

            if valid:
                crc_status.set(
                    f"CRC OK · stored {stored_crc} · calculated {calculated_crc}"
                )
            else:
                crc_status.set(
                    f"CRC mismatch · stored {stored_crc} · "
                    f"calculated {calculated_crc}"
                )

        tk.Button(
            panel,
            text="Browse",
            command=choose_file,
            bg=self.BUTTON,
            fg=self.TEXT,
            activebackground="#303030",
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=12,
        ).grid(
            row=2,
            column=1,
            padx=(0, 12),
            pady=(0, 10),
            ipady=4,
        )

        tk.Label(
            panel,
            textvariable=present_status,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 9),
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            padx=12,
            pady=(2, 1),
        )

        tk.Label(
            panel,
            textvariable=valid_status,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 9),
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            padx=12,
            pady=1,
        )

        tk.Label(
            panel,
            textvariable=crc_status,
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Consolas", 8),
            anchor="w",
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=12,
            pady=(5, 8),
        )

        tk.Button(
            panel,
            text="VERIFY CRC",
            command=verify_file,
            bg=self.ACCENT,
            fg=self.BG,
            activebackground="#cfcfcf",
            activeforeground=self.BG,
            relief="flat",
            bd=0,
            font=("Segoe UI Semibold", 9),
        ).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=12,
            pady=(0, 12),
            ipady=7,
        )

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
