#!/usr/bin/env python3
"""
lu_mpd_control.py

Single-file Python app (PyQt5) to control a remote MPD/MPD client via SSH
Commands supported: mpc load <playlist>, mpc play, mpc pause, mpc random, mpc prev/next, mpc volume <0-99>

Dependencies:
- paramiko
- PyQt5

How it works:
- Connects over SSH to a remote host using username/password or private key
- Sends mpc commands to control music player client
- Keeps GUI responsive via QThread

Note: this is a simple, single-file example intended for local-network usage.
Store credentials safely; for production prefer a secure secrets store or key-based auth.
"""

import sys
import threading
import resources_rc
import paramiko
import socket
from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QSplashScreen, QSystemTrayIcon, QMenu, QAction, QStyle
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer

# ---------- SSH helper ----------
class SSHClientWrapper:
    def __init__(self, host, port=22, username=None, password=None, key_filename=None, timeout=5):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.timeout = timeout
        self.client = None
        self.lock = threading.Lock()

    def connect(self):
        with self.lock:
            if self.client:
                try:
                    transport = self.client.get_transport()
                    if transport and transport.is_active():
                        return True
                except Exception:
                    self.client = None

            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.client.connect(self.host, port=self.port, username=self.username,
                                    password=self.password, key_filename=self.key_filename,
                                    timeout=self.timeout, look_for_keys=False, allow_agent=False)
                return True
            except Exception as e:
                self.client = None
                raise

    def exec_command(self, cmd, timeout=10):
        with self.lock:
            if not self.client:
                self.connect()
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode(errors='ignore')
            err = stderr.read().decode(errors='ignore')
            code = stdout.channel.recv_exit_status()
            return code, out, err

    def close(self):
        with self.lock:
            try:
                if self.client:
                    self.client.close()
            finally:
                self.client = None

# ---------- Worker thread for running SSH commands without blocking UI ----------
class SSHWorker(QtCore.QThread):
    result = QtCore.pyqtSignal(bool, str)

    def __init__(self, wrapper: SSHClientWrapper, command: str):
        super().__init__()
        self.wrapper = wrapper
        self.command = command

    def run(self):
        try:
            code, out, err = self.wrapper.exec_command(self.command)
            ok = (code == 0)
            text = out.strip() or err.strip() or f"Exit code: {code}"
            self.result.emit(ok, text)
        except Exception as e:
            self.result.emit(False, str(e))

# ---------- Main Window ----------
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Luciano\'s Tech MPD remote control (SSH)')
        self.setWindowIcon(QtGui.QIcon(":/icono.ico"))
        self.ssh_wrapper = None
        self.workers = []
        self._build_ui()
        self.pass_edit.setText("abcd1234") #Change this to your password
        QTimer.singleShot(1000, self.on_connect_clicked)
        self.tray_icon = QSystemTrayIcon(QtGui.QIcon(":/icono.ico"), parent=self)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.setToolTip("Lu MPD Controller active")
        tray_menu = QMenu()
        # Acciones rápidas con íconos
        play_action = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Play", self)
        play_action.triggered.connect(lambda: self.on_command_clicked('mpc play'))

        pause_action = QAction(self.style().standardIcon(QStyle.SP_MediaPause), "Pause", self)
        pause_action.triggered.connect(lambda: self.on_command_clicked('mpc pause'))

        prev_action = QAction(self.style().standardIcon(QStyle.SP_MediaSkipBackward), "Prev", self)
        prev_action.triggered.connect(lambda: self.on_command_clicked('mpc prev'))

        next_action = QAction(self.style().standardIcon(QStyle.SP_MediaSkipForward), "Next", self)
        next_action.triggered.connect(lambda: self.on_command_clicked('mpc next'))

        mute_action = QAction(self.style().standardIcon(QStyle.SP_MediaVolumeMuted), "Mute", self)
        mute_action.triggered.connect(lambda: self.on_volume_changed(0))  # mute = volumen 0
        
        max_volume_action = QAction(self.style().standardIcon(QStyle.SP_MediaVolume), "Max", self)
        max_volume_action.triggered.connect(lambda: self.on_volume_changed(99))  # mute = volumen 99

        # Agregar acciones al menú
        tray_menu.addAction(play_action)
        tray_menu.addAction(pause_action)
        tray_menu.addAction(prev_action)
        tray_menu.addAction(next_action)
        tray_menu.addAction(mute_action)
        tray_menu.addAction(max_volume_action)
        tray_menu.addSeparator()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QtWidgets.QApplication.quit)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Lu MPD Controller (Left Click Play/Pause)")
        self.tray_icon.show()
    
    # -------------------- Click en tray --------------------
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Click izquierdo
            self.toggle_play_pause()
        elif reason == QSystemTrayIcon.DoubleClick:  # Doble click
            self.show()
            self.raise_()
            self.activateWindow()

    def toggle_play_pause(self):
        if not self.ssh_wrapper:
            self.log("Not Connected. Press connect first.")
            return
        worker = SSHWorker(self.ssh_wrapper, "mpc toggle")  
        worker.result.connect(self._on_worker_result)
        worker.finished.connect(lambda: self.workers.remove(worker))
        self.workers.append(worker)
        worker.start()
        self.log("Play/Pause activado desde icono de bandeja")
    
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self.host_edit = QtWidgets.QLineEdit('raspberrypi') # Change if you use another device
        self.port_edit = QtWidgets.QSpinBox(); self.port_edit.setRange(1, 65535); self.port_edit.setValue(22)
        self.user_edit = QtWidgets.QLineEdit('lu') # Change for your user
        self.pass_edit = QtWidgets.QLineEdit(); self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.key_edit = QtWidgets.QLineEdit('')

        form.addRow('Host (IP)', self.host_edit)
        form.addRow('Port', self.port_edit)
        form.addRow('User', self.user_edit)
        form.addRow('Password', self.pass_edit)
        form.addRow('Private key (optional)', self.key_edit)

        layout.addLayout(form)

        btn_layout = QtWidgets.QHBoxLayout()
        self.connect_btn = QtWidgets.QPushButton('Conectar')
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.disconnect_btn = QtWidgets.QPushButton('Desconectar')
        self.disconnect_btn.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        layout.addLayout(btn_layout)

        # Playlist controls
        controls = QtWidgets.QHBoxLayout()
        self.load_edit = QtWidgets.QLineEdit()
        self.load_edit.setPlaceholderText('Playlist o Archivo a cargar (ej: myplaylist)')
        self.load_btn = QtWidgets.QPushButton('mpc load')
        self.load_btn.clicked.connect(partial(self.on_command_clicked, 'mpc load'))
        self.prev_btn = QtWidgets.QPushButton('mpc prev')
        self.prev_btn.clicked.connect(partial(self.on_command_clicked, 'mpc prev'))
        self.play_btn = QtWidgets.QPushButton('mpc play')
        self.play_btn.clicked.connect(partial(self.on_command_clicked, 'mpc play'))
        self.next_btn = QtWidgets.QPushButton('mpc next')
        self.next_btn.clicked.connect(partial(self.on_command_clicked, 'mpc next'))
        self.random_btn = QtWidgets.QPushButton('mpc random')
        self.random_btn.clicked.connect(partial(self.on_command_clicked, 'mpc random'))
        self.pause_btn = QtWidgets.QPushButton('mpc pause')
        self.pause_btn.clicked.connect(partial(self.on_command_clicked, 'mpc pause'))
        
        controls.addWidget(self.load_edit)
        controls.addWidget(self.load_btn)
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.next_btn)
        controls.addWidget(self.random_btn)
        controls.addWidget(self.pause_btn)
        
        layout.addLayout(controls)
        
        output_vol_layout = QtWidgets.QHBoxLayout()
        
        # output
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        output_vol_layout.addWidget(self.output,1)

        # Volume Control Slider
        vol_layout = QtWidgets.QHBoxLayout()
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.volume_slider.setRange(0, 99)
        self.volume_slider.setValue(50)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.setTickPosition(QtWidgets.QSlider.TicksRight)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        vol_layout.addWidget(QtWidgets.QLabel("Volumen"))
        vol_layout.addWidget(self.volume_slider)
        output_vol_layout.addLayout(vol_layout)
        
        layout.addLayout(output_vol_layout)
        
        self.setLayout(layout)

    def log(self, *parts):
        text = ' '.join(str(p) for p in parts)
        self.output.appendPlainText(text)
    
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Lu MPD Controller",
            "La app sigue corriendo en la bandeja",
            QSystemTrayIcon.Information,
            2000
        )
        
    def on_connect_clicked(self):
        host = self.host_edit.text().strip()
        port = int(self.port_edit.value())
        user = self.user_edit.text().strip() or None
        passwd = self.pass_edit.text() or None
        key = self.key_edit.text().strip() or None

        self.log('Conectando a', host)
        self.ssh_wrapper = SSHClientWrapper(host, port, username=user, password=passwd, key_filename=key or None)

        def do_connect():
            try:
                self.ssh_wrapper.connect()
                QtCore.QMetaObject.invokeMethod(self, 'on_connect_success', QtCore.Qt.QueuedConnection)
            except Exception as e:
                QtCore.QMetaObject.invokeMethod(self, 'on_connect_fail', QtCore.Qt.QueuedConnection, 
                                                QtCore.Q_ARG(str, str(e)))

        threading.Thread(target=do_connect, daemon=True).start()
        self.connect_btn.setEnabled(False)

    @QtCore.pyqtSlot()
    def on_connect_success(self):
        self.log('Conectado correctamente')
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)

    @QtCore.pyqtSlot(str)
    def on_connect_fail(self, err):
        self.log('Error al conectar:', err)
        self.connect_btn.setEnabled(True)

    def on_disconnect_clicked(self):
        if self.ssh_wrapper:
            self.ssh_wrapper.close()
            self.ssh_wrapper = None
        self.log('Desconectado')
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)

    def on_command_clicked(self, base_cmd):
        if not self.ssh_wrapper:
            self.log('No conectado. Presione Conectar primero.')
            return

        # Form full command
        if base_cmd == 'mpc load':
            arg = self.load_edit.text().strip()
            if not arg:
                self.log('Especifique un playlist/archivo en el campo de la izquierda.')
                return
            cmd = f"mpc load {arg}"
        else:
            cmd = base_cmd

        # Use worker thread to run the command
        worker = SSHWorker(self.ssh_wrapper, cmd)
        worker.result.connect(self._on_worker_result)
        worker.finished.connect(lambda: self.workers.remove(worker))
        self.workers.append(worker)
        worker.start()
        self.log('Enviando:', cmd)
    
    def on_volume_changed(self, value):
        if not self.ssh_wrapper:
            return
        cmd = f"mpc volume {value}"
        worker = SSHWorker(self.ssh_wrapper, cmd)
        worker.result.connect(self._on_worker_result)
        worker.finished.connect(lambda: self.workers.remove(worker))
        self.workers.append(worker)
        worker.start()
        self.log(f"Volumen -> {value}")
    
    @QtCore.pyqtSlot(bool, str)
    def _on_worker_result(self, ok, text):
        if ok:
            self.log('OK:', text)
        else:
            self.log('ERROR:', text)

# ---------- Entry point ----------

def main():
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    screen_rect = screen.availableGeometry()
    pixmap = QPixmap(":/logo.webp")
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    x = screen_rect.center().x() - pixmap.width() // 2
    y = screen_rect.center().y() - pixmap.height() // 2
    splash.move(x, y)
    splash.show()
    app.processEvents()
    win = MainWindow()
    win.resize(900, 500)
    QTimer.singleShot(2000, lambda: (win.show(), splash.finish(win)))
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
