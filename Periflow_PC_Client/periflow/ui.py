from __future__ import annotations

import queue
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from .config import DESKTOP_APP_NAME, SettingsStore, resolve_local_ip
from .models import (
    AUDIO_QUALITY_PRESETS,
    AUDIO_TRANSPORT_PRESETS,
    FRAME_RATE_PRESETS,
    RESOLUTION_PRESETS,
    AppSettings,
)
from .resources import resource_path
from .server import PeriflowServer
from .system import ensure_firewall_rules, is_running_as_admin


class PeriflowUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(DESKTOP_APP_NAME)
        self.root.geometry("820x620")
        self.root.minsize(760, 560)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._apply_window_icon()

        self._settings_store = SettingsStore()
        self._settings = self._settings_store.load()
        self._server: PeriflowServer | None = None
        self._events: queue.Queue[tuple[str, dict]] = queue.Queue()
        self._log_lines = 0
        self._is_admin = is_running_as_admin()

        self._init_variables()
        self._build_ui()
        self._load_settings_into_form()
        self._bind_variable_updates()
        self._refresh_endpoint()
        self.root.after(200, self._drain_events)
        self._append_log("Periflow client is ready.")
        if self._is_admin:
            self._append_log("Administrator privileges detected. Firewall automation and elevated app control are available.")
        else:
            self._append_log("Running without Administrator privileges. Firewall automation and control over elevated apps may fail.")

    def _apply_window_icon(self) -> None:
        logo_path = resource_path("build_assets", "periflow_logo.png")
        if not logo_path.exists():
            return
        try:
            self._logo_image = tk.PhotoImage(file=str(logo_path))
            self.root.iconphoto(True, self._logo_image)
        except Exception:
            return

    def _init_variables(self) -> None:
        self.server_port_var = tk.StringVar(value=str(self._settings.server_port))
        self.audio_port_var = tk.StringVar(value=str(self._settings.audio_port))
        self.audio_transport_var = tk.StringVar(
            value=self._label_for_transport(self._settings.audio_transport)
        )
        self.video_enabled_var = tk.BooleanVar(value=self._settings.video_enabled)
        self.audio_enabled_var = tk.BooleanVar(value=self._settings.audio_enabled)
        self.control_enabled_var = tk.BooleanVar(value=self._settings.control_enabled)
        self.resolution_var = tk.StringVar(value=self._settings.resolution)
        self.fps_var = tk.StringVar(value=str(self._settings.fps))
        self.audio_quality_var = tk.StringVar(value=self._settings.audio_quality)
        self.status_var = tk.StringVar(value="Stopped")
        self.client_var = tk.StringVar(value="No client connected")
        self.endpoint_var = tk.StringVar(value="Resolving local IP...")
        self.admin_var = tk.StringVar(value="Administrator" if self._is_admin else "Standard user")
        self.firewall_var = tk.StringVar(value="Unknown")

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 16))

        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=DESKTOP_APP_NAME, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Windows desktop bridge for phone camera, microphone, and remote input over local Wi-Fi.",
            foreground="#4b5563",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        status_card = ttk.LabelFrame(container, text="Server Status", padding=12)
        status_card.grid(row=1, column=0, sticky="ew", pady=(16, 10))
        status_card.columnconfigure(1, weight=1)
        ttk.Label(status_card, text="Endpoint").grid(row=0, column=0, sticky="w")
        ttk.Label(status_card, textvariable=self.endpoint_var).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(status_card, text="Status").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(status_card, textvariable=self.status_var).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        ttk.Label(status_card, text="Client").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Label(status_card, textvariable=self.client_var).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        ttk.Label(status_card, text="Privileges").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Label(status_card, textvariable=self.admin_var).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        ttk.Label(status_card, text="Firewall").grid(row=4, column=0, sticky="w", pady=(6, 0))
        ttk.Label(status_card, textvariable=self.firewall_var).grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

        controls = ttk.Frame(status_card)
        controls.grid(row=0, column=2, rowspan=5, sticky="ne", padx=(16, 0))
        self.start_button = ttk.Button(controls, text="Start Server", command=self._start_server)
        self.start_button.grid(row=0, column=0, sticky="ew")
        self.stop_button = ttk.Button(controls, text="Stop Server", command=self._stop_server, state="disabled")
        self.stop_button.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.firewall_button = ttk.Button(controls, text="Apply Firewall Rule", command=self._apply_firewall_rules)
        self.firewall_button.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        config_grid = ttk.Frame(container)
        config_grid.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        config_grid.columnconfigure(0, weight=1)
        config_grid.columnconfigure(1, weight=1)

        network_card = ttk.LabelFrame(config_grid, text="Network", padding=12)
        network_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        network_card.columnconfigure(1, weight=1)
        ttk.Label(network_card, text="TCP Port").grid(row=0, column=0, sticky="w")
        self.server_port_entry = ttk.Entry(network_card, textvariable=self.server_port_var, width=14)
        self.server_port_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(network_card, text="UDP Audio Port").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.audio_port_entry = ttk.Entry(network_card, textvariable=self.audio_port_var, width=14)
        self.audio_port_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Label(network_card, text="Audio Transport").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.audio_transport_combo = ttk.Combobox(
            network_card,
            textvariable=self.audio_transport_var,
            values=list(AUDIO_TRANSPORT_PRESETS.keys()),
            state="readonly",
        )
        self.audio_transport_combo.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        media_card = ttk.LabelFrame(config_grid, text="Control", padding=12)
        media_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        media_card.columnconfigure(0, weight=1)
        ttk.Checkbutton(media_card, text="Remote Control", variable=self.control_enabled_var).grid(row=0, column=0, sticky="w")

        log_card = ttk.LabelFrame(container, text="Event Log", padding=12)
        log_card.grid(row=3, column=0, sticky="nsew")
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_card, height=18, wrap="word", bg="#101827", fg="#e5e7eb", insertbackground="#e5e7eb")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_card, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.configure(state="disabled")

    def _load_settings_into_form(self) -> None:
        self.server_port_var.set(str(self._settings.server_port))
        self.audio_port_var.set(str(self._settings.audio_port))
        self.audio_transport_var.set(self._label_for_transport(self._settings.audio_transport))
        self.video_enabled_var.set(self._settings.video_enabled)
        self.audio_enabled_var.set(self._settings.audio_enabled)
        self.control_enabled_var.set(self._settings.control_enabled)
        self.resolution_var.set(self._settings.resolution)
        self.fps_var.set(str(self._settings.fps))
        self.audio_quality_var.set(self._settings.audio_quality)

    def _bind_variable_updates(self) -> None:
        variables = [
            self.server_port_var,
            self.audio_port_var,
            self.audio_transport_var,
            self.video_enabled_var,
            self.audio_enabled_var,
            self.control_enabled_var,
            self.resolution_var,
            self.fps_var,
            self.audio_quality_var,
        ]
        for variable in variables:
            variable.trace_add("write", self._on_setting_changed)

    def _label_for_transport(self, value: str) -> str:
        for label, internal in AUDIO_TRANSPORT_PRESETS.items():
            if internal == value:
                return label
        return "UDP (Recommended)"

    def _transport_value_from_label(self, label: str) -> str:
        return AUDIO_TRANSPORT_PRESETS.get(label, "udp")

    def _on_setting_changed(self, *_args) -> None:
        settings = self._collect_settings()
        if settings is None:
            return
        self._settings = settings
        self._settings_store.save(settings)
        self._refresh_endpoint()
        if self._server is not None:
            self._server.update_settings(settings)

    def _collect_settings(self) -> AppSettings | None:
        try:
            server_port = int(self.server_port_var.get())
            audio_port = int(self.audio_port_var.get())
            fps = int(self.fps_var.get())
        except ValueError:
            return None

        if server_port <= 0 or audio_port <= 0 or fps <= 0:
            return None

        return AppSettings(
            server_port=server_port,
            audio_port=audio_port,
            audio_transport=self._transport_value_from_label(self.audio_transport_var.get()),
            video_enabled=self.video_enabled_var.get(),
            audio_enabled=self.audio_enabled_var.get(),
            control_enabled=self.control_enabled_var.get(),
            resolution=self.resolution_var.get(),
            fps=fps,
            audio_quality=self.audio_quality_var.get(),
            auto_firewall_rule=self._settings.auto_firewall_rule,
            client_timeout_seconds=self._settings.client_timeout_seconds,
        )

    def _refresh_endpoint(self) -> None:
        ip_address = resolve_local_ip()
        tcp_port = self.server_port_var.get()
        udp_port = self.audio_port_var.get()
        if self._transport_value_from_label(self.audio_transport_var.get()) == "udp":
            self.endpoint_var.set(f"{ip_address}:{tcp_port} | UDP audio {udp_port}")
        else:
            self.endpoint_var.set(f"{ip_address}:{tcp_port} | TCP audio only")

    def _sync_network_controls(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        combo_state = "disabled" if running else "readonly"
        self.server_port_entry.configure(state=state)
        self.audio_port_entry.configure(state=state)
        self.audio_transport_combo.configure(state=combo_state)

    def _start_server(self) -> None:
        settings = self._collect_settings()
        if settings is None:
            self._append_log("Ports must be valid integers.")
            return
        self._settings = settings
        if self._server is None:
            self._server = PeriflowServer(settings, self._handle_server_event)
        else:
            self._server.update_settings(settings)
        try:
            self._server.start()
        except OSError as exc:
            self._append_log(f"Server failed to start: {exc}")
            return
        self.status_var.set("Listening")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._sync_network_controls(True)

    def _stop_server(self) -> None:
        if self._server is None:
            return
        self._server.stop()
        self.status_var.set("Stopped")
        self.client_var.set("No client connected")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._sync_network_controls(False)

    def _apply_firewall_rules(self) -> None:
        settings = self._collect_settings()
        if settings is None:
            self._append_log("Cannot apply firewall rules because the ports are invalid.")
            return
        result = ensure_firewall_rules(settings.server_port, settings.audio_port)
        self.firewall_var.set("Ready" if result.success else "Needs admin")
        prefix = "Firewall configured." if result.success else "Firewall setup failed."
        self._append_log(f"{prefix} {result.message}")

    def _handle_server_event(self, event_type: str, payload: dict) -> None:
        self._events.put((event_type, payload))

    def _drain_events(self) -> None:
        while True:
            try:
                event_type, payload = self._events.get_nowait()
            except queue.Empty:
                break
            self._apply_event(event_type, payload)
        self.root.after(200, self._drain_events)

    def _apply_event(self, event_type: str, payload: dict) -> None:
        if event_type == "log":
            self._append_log(payload.get("message", ""))
        elif event_type == "server_started":
            self.status_var.set("Listening")
            display_host = payload.get("display_host")
            port = payload.get("port")
            audio_port = payload.get("audio_port")
            audio_transport = payload.get("audio_transport")
            if display_host and port:
                if audio_transport == "udp":
                    self.endpoint_var.set(f"{display_host}:{port} | UDP audio {audio_port}")
                else:
                    self.endpoint_var.set(f"{display_host}:{port} | TCP audio only")
        elif event_type == "server_stopped":
            self.status_var.set("Stopped")
            self.client_var.set("No client connected")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self._sync_network_controls(False)
        elif event_type == "client_connected":
            name = payload.get("name", "Client")
            address = payload.get("address", "unknown")
            port = payload.get("port", "?")
            self.client_var.set(f"{name} ({address}:{port})")
            self.status_var.set("Client connected")
        elif event_type == "client_disconnected":
            self.client_var.set("No client connected")
            self.status_var.set("Listening")
        elif event_type == "firewall_status":
            self.firewall_var.set("Ready" if payload.get("success") else "Needs attention")

    def _append_log(self, message: str) -> None:
        if not message:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self._log_lines += 1
        if self._log_lines > 300:
            self.log_text.delete("1.0", "3.0")
            self._log_lines -= 2
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _on_close(self) -> None:
        if self._server is not None:
            self._server.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run() -> None:
    PeriflowUI().run()
