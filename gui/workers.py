from PyQt6.QtCore import QThread, pyqtSignal


class WorkerThread(QThread):
    result_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            if 'progress_callback' in self.kwargs:
                result = self.func(*self.args, progress_callback=self.progress_signal.emit, **self.kwargs)
            else:
                result = self.func(*self.args, **self.kwargs)
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
