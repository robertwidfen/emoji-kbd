import sys
import socket
import threading
import qdarkstyle

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt

import logging as log

from guikbd import KeyboardWidget

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

    def show_window(self):
        """Show and activate the window"""
        self.window.emoji_input_field.clear()
        # Center on the current active screen
        screen = QApplication.primaryScreen()
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

    def start_server(self):
        thread = threading.Thread(target=self.run_server, daemon=True)
        thread.start()

    def run_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((SOCKET_HOST, 0))
                server_socket.listen(1)
                server_socket.settimeout(1.0)

                self.port = server_socket.getsockname()[1]
                with open(".local/emoji-kbd-daemon.port", "w") as f:
                    f.write(str(self.port))
                log.info(f"Socket server listening on {SOCKET_HOST}:{self.port}")

                while self.running:
                    try:
                        conn, addr = server_socket.accept()
                        with conn:
                            data = conn.recv(1024).decode("utf-8").strip()
                            log.info(f"Received command: {data}")
                            if data == "SHOW":
                                self.show_window_signal.emit()
                                conn.sendall(b"OK\n")
                            elif data == "GET":
                                # Clear previous result and show window
                                self.result_ready.clear()
                                self.result_text = ""
                                self.show_window_signal.emit()

                                # Block until window is closed
                                log.info("Waiting for window to close...")
                                self.result_ready.wait()

                                # Send the result
                                response = self.result_text.encode("utf-8") + b"\n"
                                log.info(f"Sending result: {self.result_text}")
                                conn.sendall(response)
                            elif data == "QUIT":
                                conn.sendall(b"OK\n")
                                log.info(
                                    f"Quit command received, shutting down server."
                                )
                                QTimer.singleShot(100, QApplication.instance().quit)  # type: ignore
                                break
                            else:
                                log.error(f"Unknown command '{data}'")
                    except socket.timeout:
                        continue
                    except Exception as e:
                        log.error(f"Socket error: {e}")
        except Exception as e:
            log.error(f"Failed to start socket server: {e}")


class DaemonKeyboardWidget(KeyboardWidget):
    def __init__(self, server=None):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.server = server

    def closeEvent(self, event):  # type: ignore
        """Hide instead of closing and notify server with result"""
        event.ignore()

        if self.server:
            self.server.result_text = self.emoji_input_field.text()
            self.server.result_ready.set()

        self.hide()


def start_daemon():
    log.info("Starting Emoji Keyboard Daemon...")

    app = QApplication(sys.argv)
    # Keep app running when window is hidden
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())

    # Create server first
    server = SocketServer()

    # Create window with server reference
    window = DaemonKeyboardWidget(server)
    server.window = window

    server.start_server()

    # Show window off-screen to initialize, then hide
    window.move(-10000, -10000)
    window.show()
    QTimer.singleShot(100, window.hide)

    log.info("Daemon ready, window hidden, waiting for commands...")

    sys.exit(app.exec())


def send_command(port: int, command: str):
    try:
        log.info(f"Sending command '{command}' to port {port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SOCKET_HOST, port))
            s.sendall(f"{command}\n".encode("utf-8"))
            response = s.recv(1024).decode("utf-8").strip()
            log.info(f"Received response: {response}")
            return response
    except ConnectionRefusedError:
        log.error("Error: Emoji keyboard daemon is not running")
        return ""
    except Exception as e:
        log.error(f"Error: {e}")
        return ""


if __name__ == "__main__":
    log.basicConfig(
        # filename='app.log',
        # filemode='a',
        level=log.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    if len(sys.argv) >= 2:
        with open(".local/emoji-kbd-daemon.port", "r") as f:
            port = int(f.read().strip())
        args = sys.argv[1:]
        for a in args:
            print(send_command(port, a), end="")
    else:
        start_daemon()
