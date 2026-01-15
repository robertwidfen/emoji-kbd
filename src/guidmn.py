import logging as log
import os
import socket
import subprocess
import sys
import threading
import time

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QGuiApplication
from PyQt6.QtWidgets import QApplication

from config import load_config
from guikbd import KeyboardWidget, setup_app
from tools import get_state_file

SOCKET_HOST = "127.0.0.1"


class SocketServer(QObject):
    show_window_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.window: DaemonKeyboardWidget = None  # type: ignore
        self.show_window_signal.connect(self.show_window)
        self.running = True
        self.port = 0
        self.result_ready = threading.Event()
        self.result_text = ""
        self.daemon_ready = False

    def show_window(self):
        """Show and activate the window"""
        log.info("show_window() called")
        self.window.emoji_input_field.clear()
        # Center on the current active screen
        screen = QGuiApplication.screenAt(QCursor.pos())
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.window.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.window.move(window_geometry.topLeft())
        self.window.setWindowState(
            self.window.windowState() & ~Qt.WindowState.WindowMinimized
            | Qt.WindowState.WindowActive
        )
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()
        self.window.setFocus()
        self.window.emoji_input_field.setFocus()
        log.info("show_window() completed")

    def start_server(self):
        thread = threading.Thread(target=self.run_server, daemon=True)
        thread.start()

    def run_server(self):
        log.info("Starting socket server...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((SOCKET_HOST, 0))
                server_socket.listen(1)
                server_socket.settimeout(1.0)

                self.port = server_socket.getsockname()[1]
                log.info(f"Socket server listening on {SOCKET_HOST}:{self.port}")
                port_file = get_state_file("emoji-kbd-daemon.port")
                log.info(f"Writing port to '{port_file}'.")
                with open(port_file, "w") as f:
                    f.write(str(self.port))

                while self.running:
                    try:
                        conn, addr = server_socket.accept()
                        with conn:
                            data = conn.recv(1024).decode("utf-8").strip()
                            log.info(f"Received command: {data}")

                            # Mark daemon as ready on first real command
                            if not self.daemon_ready and data not in ("HELLO",):
                                self.daemon_ready = True
                                log.info("Daemon marked as ready")

                            if data == "HELLO":
                                conn.sendall(b"OK\n")
                            elif data == "SHOW":
                                log.info("Emitting show_window_signal for SHOW")
                                self.show_window_signal.emit()
                                log.info("Signal emitted, sending OK")
                                conn.sendall(b"OK\n")
                            elif data == "GET":
                                # Clear previous result and show window
                                log.info("Processing GET command")
                                self.result_ready.clear()
                                self.result_text = ""
                                log.info("Emitting show_window_signal for GET")
                                self.show_window_signal.emit()
                                log.info("Signal emitted for GET")

                                # Block until window is closed
                                log.info("Waiting for window to close...")
                                self.result_ready.wait()

                                # Send the result
                                response = self.result_text.encode("utf-8") + b"\n"
                                log.info(f"Sending result: '{self.result_text}'")
                                conn.sendall(response)
                            elif data == "QUIT":
                                conn.sendall(b"OK\n")
                                log.info("Quit command received, shutting down.")
                                QTimer.singleShot(100, QApplication.instance().quit)  # type: ignore
                                break
                            else:
                                log.error(f"Unknown command '{data}'")
                    except TimeoutError:
                        continue
                    except Exception as e:
                        log.error(f"Socket error: {e}")
        except Exception as e:
            log.error(f"Failed to start socket server: {e}")


class DaemonKeyboardWidget(KeyboardWidget):
    def __init__(self, server, config):
        super().__init__(config)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.server = server

    def quit(self):
        log.info("Hiding Emoji Kbd...")
        self.close()

    def closeEvent(self, event):  # type: ignore
        """Hide instead of closing and notify server with result"""
        log.info("closeEvent called")
        event.ignore()

        if self.server:
            result = self.emoji_input_field.text()
            log.info(f"Setting result: '{result}'")
            self.server.result_text = result
            self.server.result_ready.set()
            log.info("result_ready event set")

        self.hide()
        log.info("Window hidden")


def start_daemon(config):
    log.info("Starting Emoji Kbd Daemon...")

    log.info("Creating QApplication")
    app = setup_app(config)
    # Keep app running when window is closed
    app.setQuitOnLastWindowClosed(False)

    # Create server first
    log.info("Creating SocketServer")
    server = SocketServer()

    # Create window with server reference
    log.info("Creating DaemonKeyboardWidget")
    window = DaemonKeyboardWidget(server, config)
    server.window = window

    # Show window off-screen to initialize, then hide
    log.info("Initializing window off-screen")
    window.move(-10000, -10000)
    window.show()

    def hide_after_init():
        if not server.daemon_ready:
            log.info("Hiding window after initialization")
            window.hide()
            server.daemon_ready = True
        else:
            log.info("Skipping initialization hide - daemon already active")

    QTimer.singleShot(100, hide_after_init)

    log.info("Window ready and hidden.")

    log.info("Starting socket server thread")
    server.start_server()

    log.info("Starting Qt event loop")

    sys.exit(app.exec())


def send_command(command: str, start_daemon_enabled=True) -> str | None:
    try:
        with open(get_state_file("emoji-kbd-daemon.port")) as f:
            port = int(f.read().strip())
        command = command.strip().upper()
        log.info(f"Sending command '{command}' to port {port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SOCKET_HOST, port))
            s.sendall(f"{command}\n".encode())
            response = s.recv(1024).decode("utf-8").strip()
            log.info(f"Received response: '{response}'")
            return response
    except (ConnectionRefusedError, FileNotFoundError, ValueError) as e:
        log.error(f"Exception: {e}")
        if command != "QUIT" and start_daemon_enabled:
            log.error("Emoji Kbd daemon not running - trying to start it.")
            return start_daemon_process(command)
        return None
    except Exception as e:
        log.error(f"Exception: {e}")
        return None


def start_daemon_process(command: str):
    # Start daemon
    log.info("Starting daemon...")
    env = os.environ.copy()
    env.pop("TERM", None)
    subprocess.Popen(
        [sys.executable, sys.argv[0], "--daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    # Wait for daemon to start and write port file
    for i in range(50):  # Wait up to 5 seconds
        time.sleep(0.1)
        result = send_command(command, False)
        if result != None:
            log.info("Daemon started.")
            return result
    raise RuntimeError("Failed to start daemon")


if __name__ == "__main__":
    config = load_config()
    if len(sys.argv) >= 2 and sys.argv[1] == "--daemon":
        log.basicConfig(
            force=True,
            filename=get_state_file("guidmn.log"),
            filemode=config.logging.log_mode,
            level=config.logging.log_level,
            format="%(asctime)s - D %(levelname)s - %(message)s",
        )
        start_daemon(config)
    elif len(sys.argv) >= 2:
        log.basicConfig(
            force=True,
            filename=get_state_file("guidmn.log"),
            filemode=config.logging.log_mode,
            level=config.logging.log_level,
            format="%(asctime)s - C %(levelname)s - %(message)s",
        )
        # Client mode with commands
        for a in sys.argv[1:]:
            result = send_command(a)
            if result == None:
                print("No result")
                sys.exit(-1)
            else:
                print(result)
    else:
        print(f"Usage: {sys.argv[0]} [--daemon] [SHOW|GET|QUIT]", file=sys.stderr)
        sys.exit(1)
