"""Shared, cross-process ownership for SpectrumSnek's RTL-SDR device.

Every SpectrumSnek component that opens the RTL-SDR must hold this lock.
The lock is advisory and cannot control unrelated applications that do not
use SpectrumSnek's manager; we therefore also refuse to launch readsb when an
external readsb process is already present instead of killing it.
"""
from __future__ import annotations

import fcntl
import os
import shutil
import subprocess
import time
from typing import Optional


class SDRBusyError(RuntimeError):
    """Raised when another SpectrumSnek component owns the SDR."""


class SDRUnavailableError(RuntimeError):
    """Raised when the RTL-SDR hardware is not available."""


class SDRManager:
    def __init__(self, lock_path: Optional[str] = None, json_dir: Optional[str] = None,
                 readsb_bin: Optional[str] = None):
        self.lock_path = lock_path or os.environ.get(
            "SPECTRUMSNEK_SDR_LOCK", "/tmp/spectrumsnek-sdr.lock"
        )
        self.json_dir = json_dir or os.environ.get(
            "SPECTRUMSNEK_READSB_DIR", "/tmp/spectrumsnek/readsb"
        )
        # Prefer SpectrumSnek's own RTL-SDR-enabled build. The distro package may
        # be compiled without RTL-SDR support, so do not silently select it when
        # setup.sh has installed the project-local binary.
        project_readsb = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".local", "bin", "readsb"
        )
        self.readsb_bin = (
            readsb_bin
            or os.environ.get("READSB_BIN")
            or (project_readsb if os.path.isfile(project_readsb) else "readsb")
        )
        self._lease_fd: Optional[int] = None
        self._process: Optional[subprocess.Popen] = None

    def acquire_device(self, owner: str, blocking: bool = False) -> int:
        """Acquire exclusive device ownership and return the lock file descriptor."""
        if self._lease_fd is not None:
            raise RuntimeError("This SDRManager instance already owns the SDR")
        os.makedirs(os.path.dirname(os.path.abspath(self.lock_path)), exist_ok=True)
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o660)
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(fd, flags)
        except BlockingIOError as exc:
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                owner_info = os.read(fd, 256).decode("utf-8", "replace").strip()
            finally:
                os.close(fd)
            detail = f" (owner: {owner_info})" if owner_info else ""
            raise SDRBusyError(f"RTL-SDR is already in use{detail}") from exc

        os.ftruncate(fd, 0)
        os.write(fd, f"{owner} pid={os.getpid()} since={int(time.time())}\\n".encode())
        os.fsync(fd)
        self._lease_fd = fd
        return fd

    def release_device(self) -> None:
        """Release the lock held by this manager, if any."""
        fd, self._lease_fd = self._lease_fd, None
        if fd is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def start_readsb(self, startup_timeout: float = 5.0) -> str:
        """Start readsb under the exclusive SDR lock and return aircraft.json path."""
        if self._process is not None and self._process.poll() is None:
            return os.path.join(self.json_dir, "aircraft.json")

        self.acquire_device("adsb_radar")
        try:
            # Never terminate a decoder we did not start. It may be managed by
            # systemd or another receiver application.
            existing = subprocess.run(
                ["pgrep", "-a", "-x", "readsb"],
                capture_output=True, text=True, check=False
            )
            if existing.returncode == 0 and existing.stdout.strip():
                raise SDRBusyError(
                    "A readsb process is already running outside SpectrumSnek. "
                    "Stop or reconfigure that receiver yourself, or point this plugin "
                    "at its existing JSON output."
                )

            binary = shutil.which(self.readsb_bin)
            if not binary:
                raise RuntimeError(
                    f"readsb executable not found ({self.readsb_bin!r}). "
                    "Install readsb or set READSB_BIN to its full path."
                )

            os.makedirs(self.json_dir, exist_ok=True)
            for name in ("aircraft.json", "receiver.json", "stats.json"):
                try:
                    os.unlink(os.path.join(self.json_dir, name))
                except FileNotFoundError:
                    pass

            command = [
                binary, "--net", "--write-json", self.json_dir, "--quiet",
                "--no-interactive", "--device-type", "rtlsdr", "--gain", "auto"
            ]
            self._process = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, text=True, start_new_session=True
            )

            deadline = time.monotonic() + startup_timeout
            while time.monotonic() < deadline:
                if self._process.poll() is not None:
                    code = self._process.returncode
                    _, stderr_text = self._process.communicate()
                    self._process = None
                    detail = (stderr_text or "").strip()
                    lower_detail = detail.lower()
                    if "no supported devices found" in lower_detail:
                        raise SDRUnavailableError(
                            "No RTL-SDR dongle detected. Check the Pi's USB data/OTG "
                            "port, adapter, and dongle connection."
                        )
                    if ("unknown device type:rtlsdr" in lower_detail
                            or "sdr type 'rtlsdr' not recognized" in lower_detail):
                        raise SDRUnavailableError(
                            "The selected readsb binary was built without RTL-SDR support. "
                            "Build readsb with RTLSDR=yes and set READSB_BIN to that binary's "
                            "full path, or install an RTL-SDR-enabled build."
                        )
                    message = f"readsb exited during startup (exit code {code})."
                    if detail:
                        message += f" readsb said: {detail}"
                    else:
                        message += " readsb produced no stderr; check device permissions and SDR availability."
                    raise RuntimeError(message)
                time.sleep(0.1)
            return os.path.join(self.json_dir, "aircraft.json")
        except Exception:
            self.stop_readsb()
            raise

    def stop_readsb(self) -> None:
        """Stop only the readsb child process owned by this manager."""
        process, self._process = self._process, None
        try:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
        finally:
            self.release_device()

    def __enter__(self):
        self.acquire_device("sdr_manager")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release_device()
