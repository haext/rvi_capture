import sys
import io

class OutputClosedError(Exception):
    pass

class OutputFile:
    def __init__(self, filename):
        self._filename = filename
        self._file = open(filename, 'wb', 0)

    def write(self, data):
        self._file.write(data)

    def writelines(self, data):
        self._file.writelines(data)

    def close(self):
        self._file.close()

    def ready(self):
        return True

    def capture_instructions(self):
        return f"Capturing to {self._filename} ..."

class OutputStdout:
    def __init__(self):
        self._stdout = sys.stdout.buffer
        while isinstance(self._stdout, io.BufferedWriter):
            self._stdout = self._stdout.detach()

    def write(self, data):
        self._stdout.write(data)

    def writelines(self, data):
        self._stdout.writelines(data)

    def close(self):
        self._stdout.close()

    def ready(self):
        return True

    def capture_instructions(self):
        return f"Capturing to stdout ..."
