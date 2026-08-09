import tkinter as tk
from tkinter import ttk


# GUI added by poimu
# Standalone GUI preview only.
# No backend, Git, CubeIDE, workspace, or external files are required.

VARIATION_LIST = [
    ("FC22-01", "FC22_01"),
    ("FC22-02", "FC22_02"),
    ("FC22-02-LL", "FC22_02_LL"),
    ("FC22-03", "FC22_03"),
    ("FC22R-01", "FC22R_01"),
    ("FC22R-02", "FC22R_02"),
]


class HelpBuilderGUITest(tk.Tk):
    BG = "#090909"
    PANEL = "#111111"
    BORDER = "#2a2a2a"
    TEXT = "#eeeeee"
    MUTED = "#888888"
    BUTTON = "#202020"
    ACCENT = "#e6e6e6"

    def __init__(self):
        super().__init__()

        self.title("Fartak Control - Help Builder")
        self.geometry("610x650")
        self.minsize(520, 560)
        self.configure(bg=self.BG)

        self.workspace = tk.StringVar(value="D:/Projects/STM32CubeIDE/workspace_1.15.0")
        self.select_configurations = tk.BooleanVar(value=False)
        self.create_hex = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="BeachWolf · 6 configurations")
        self.percent = tk.DoubleVar(value=0)

        self.configuration_vars = {}
        self.configuration_rows = {}

        self._configure_style()
        self._build_gui()
        self.load_demo_configurations()

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
            text="Help Builder · GUI Preview",
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

        tk.Entry(
            panel,
            textvariable=self.workspace,
            bg=self.BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 9),
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(12, 8),
            pady=(0, 11),
            ipady=7,
        )

        tk.Button(
            panel,
            text="Browse",
            command=self.demo_browse,
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
            text="Auto · original FC22 if available, otherwise all",
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
        self.pre_canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            shell,
            orient="vertical",
            command=self.pre_canvas.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.pre_canvas.configure(yscrollcommand=scrollbar.set)

        self.pre_frame = tk.Frame(self.pre_canvas, bg=self.PANEL)
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
        self.progress_canvas.grid(row=0, column=0, sticky="ew")
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
            command=self.start_demo_build,
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

    def load_demo_configurations(self):
        for configuration, symbol in VARIATION_LIST:
            variable = tk.BooleanVar(value=True)
            self.configuration_vars[configuration] = variable

            row = ttk.Checkbutton(
                self.pre_frame,
                text=f"{configuration}   ·   {symbol}",
                variable=variable,
                style="Dark.TCheckbutton",
            )
            row.pack(fill="x", anchor="w", pady=1)
            self.configuration_rows[configuration] = row

        self.update_configuration_state()

    def update_configuration_state(self):
        enabled = self.select_configurations.get()
        for row in self.configuration_rows.values():
            row.state(["!disabled"] if enabled else ["disabled"])

    def select_all(self):
        for variable in self.configuration_vars.values():
            variable.set(True)

    def select_none(self):
        for variable in self.configuration_vars.values():
            variable.set(False)

    def demo_browse(self):
        self.status.set("Preview mode · no workspace required")

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

    def start_demo_build(self):
        self.build_button.config(state="disabled")
        self.demo_steps = iter([
            (0, "Starting"),
            (10, "Reading Git commit"),
            (20, "Waiting for confirmation"),
            (30, "Building STM32 configurations"),
            (60, "Build completed"),
            (65, "Packaging WolfLoader"),
            (75, "Packaged FC22-01"),
            (82, "Packaged FC22-02"),
            (88, "Packaged FC22-02-LL"),
            (93, "Packaged FC22-03"),
            (97, "Packaged FC22R-01"),
            (98, "Packaged FC22R-02"),
            (100, "Release completed"),
        ])
        self.run_demo_step()

    def run_demo_step(self):
        try:
            value, text = next(self.demo_steps)
        except StopIteration:
            self.build_button.config(state="normal")
            return

        self.set_progress(value, text)
        self.after(250, self.run_demo_step)


if __name__ == "__main__":
    HelpBuilderGUITest().mainloop()
