# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.Qt import Qt
from PyQt5.QtGui import QGuiApplication

import threading, time

from ui_monitor import MonitorWidget, Ui_Form

class MonitorWindow(MonitorWidget, Ui_Form):
    sigTaskUpdating = pyqtSignal(dict)

    app = None
    _stat = None
    _thread = None
    _thread_should_stop = False

    TICKS_PER_TASK = 4
    TICK_INTERVAL = 0.5 # second(s)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet("background-color: rgba(135, 206, 235, 0.8)")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.app = QGuiApplication.instance()

        self.app.settings.applySettings.connect(self._setMonitorFullSpeed)
        self._setMonitorFullSpeed()

        self._thread = threading.Thread(target = self.updateTaskThread,
                                        name = "monitor task updating",
                                        daemon = True)
        self._thread.start()

    def updateTaskThread(self):
        while True:
            runningTaskIds = self.app.etmpy.runningTasksStat.getTIDs()
            if runningTaskIds:
                for tid in runningTaskIds:
                    for i in range(self.TICKS_PER_TASK):
                        task = self.app.etmpy.runningTasksStat.getTask(tid)

                        if self._thread_should_stop:
                            return # end the thread

                        logging.debug("updateSpeedsThread, deadlock incoming, maybe")
                        try:
                            self.sigTaskUpdating.emit(task)
                        except TypeError:
                            # monitor closed
                            return # end the thread
                        time.sleep(self.TICK_INTERVAL)
            else:
                time.sleep(self.TICK_INTERVAL)

    @pyqtSlot()
    def _setMonitorFullSpeed(self):
        fullSpeed = self.app.settings.getint("frontend", "monitorfullspeed")
        logging.info("monitor full speed -> {}".format(fullSpeed))
        self.graphicsView.FULLSPEED = 1024 * fullSpeed

    def closeEvent(self, qCloseEvent):
        self._thread_should_stop = True
        super().closeEvent(qCloseEvent)