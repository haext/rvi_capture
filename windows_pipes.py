import sys
import pywintypes
import win32pipe, win32file, win32event, winerror
from enum import Enum
from output import OutputClosedError

def add_windows_output_arguments(parser):
    output_option = parser.add_mutually_exclusive_group(required=True)
    output_option.add_argument('outfile', help='output file (- for stdout)', nargs="?")
    output_option.add_argument('--pipe', help='output to named pipe', nargs=1)


class PipeState(Enum):
    DISCONNECTED = 0
    LISTEN_PENDING = 1
    LISTENING = 2
    CONNECTED = 3

class OutputPipe:
    def __init__(self, pipe_name):
        self._state = PipeState.DISCONNECTED
        self._pipe_name = pipe_name
        self._pipe = win32pipe.CreateNamedPipe(
            self._pipe_path(),
            win32pipe.PIPE_ACCESS_OUTBOUND,
            win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_NOWAIT,
            1, 65536, 65536,
            0,
            None)

        self._connect_pipe()

    def _pipe_path(self):
        return f'\\\\.\\pipe\\{self._pipe_name}'

    def _can_write(self):
        if self._state != PipeState.CONNECTED:
            self._connect_pipe()
            return False
        else:
            return True

    def _connect_pipe(self):
        if self._state == PipeState.CONNECTED:
            return

        self._overlapped = pywintypes.OVERLAPPED()
        result = 0
        try:
            result = win32pipe.ConnectNamedPipe(self._pipe, self._overlapped)
            if result > 0:
                self._state = PipeState.CONNECTED
        except pywintypes.error as e:
            self._handle_connect_results(result, e.winerror)

    def _handle_connect_results(self, result, error):
        # If result is nonzero, need to disconnect and reconnect
        if result != 0:
            self.reconnect()
        else:
            # Three options: pending listening, listening, or connected
            if error == winerror.ERROR_PIPE_LISTENING:
                self._state = PipeState.LISTENING
            elif error == winerror.ERROR_IO_PENDING:
                # Wait until we're listening
                win32event.WaitForSingleObject(self._overlapped.hEvent, win32event.INFINITE)
                try:
                    result = win32pipe.GetOverlappedResult(self._pipe, self._overlapped, False)
                    if result != 0:
                        print('Unexpected nonzero result opening pipe', file=sys.stderr, flush=True)
                        exit(1)
                    self._state = PipeState.LISTENING
                except pywintypes.error as e:
                    self._handle_connect_results(result, e.winerror)
            elif error == winerror.ERROR_PIPE_CONNECTED:
                self._state = PipeState.CONNECTED
            else:
                print("UNKNOWN PIPE ERROR", error, flush=True, file=sys.stderr)

    def reconnect(self):
        win32pipe.DisconnectNamedPipe(self._pipe)
        self._state = PipeState.DISCONNECTED
        raise OutputClosedError()

    def _handle_write_error(self, e):
        if e.winerror == winerror.ERROR_BROKEN_PIPE:
            self.reconnect()
        elif e.winerror == winerror.ERROR_NO_DATA:
            # Need to reconnect a formerly-used pipe
            self.reconnect()
        else:
            raise e

    def write(self, data):
        if self._can_write():
            try:
                win32file.WriteFile(self._pipe, data)
            except pywintypes.error as e:
                self._handle_write_error(e)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def close(self):
        win32file.CloseHandle(self._pipe)

    def ready(self):
        return self._can_write()

    def capture_instructions(self):
        return (f"Waiting for connection {self._pipe_path()} ...\n"
            f"  Use Wireshark with:\n  & \"$env:ProgramFiles\\Wireshark\\Wireshark.exe\" -i\"{self._pipe_path()}\" -k"
        )
