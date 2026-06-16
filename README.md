# rvi_capture

rvictl for Linux and Windows: capture packets sent/received by iOS devices

A utility to create packet capture dumps from iOS devices; useful for debugging network activity via Wireshark.

Tested on Arch Linux with iOS 14.8 and Windows with iOS 26.5.

## Prerequisites

### Linux

* `libimobiledevice` and `python3` must be installed.
* Ensure that the `usbmuxd` daemon is running.

### Windows

* iTunes must be installed.
* `python3` must be installed, such as through [pymanager](https://www.python.org/downloads/release/pymanager-262/) or `winget install 9NQ7512CXL7T`
* Ensure that the `AppleMobileDeviceService.exe` process is running.
* Note that `libimobiledevice` will be downloaded as needed.
* Install pywin32 from `requirements_windows.txt` for named pipe support, as shown below:

```powershell
# optional but suggested: set up and activate a venv
py -m venv .venv
.\.venv\Scripts\activate.ps1

# Install requirements
pip install -r requirements_windows.txt
```

## Usage

1. Plug the phone into the computer using the appropriate USB-C or Lighting cable
2. Enter your PIN on the phone, and trust the computer
3. Run `rvi_capture` as shown below:

```
./rvi_capture.py [--format {pcap,pcapng}] [--udid UDID] outfile
```

* `--format`: capture format
    * pcapng: The default. Newer and allows for distinguishing between interfaces.
      Wireshark 3.0+ supports streaming captures with this format.
    * pcap: Older format for compatibility.
* `--udid`: device UDID
  The specific device to target. If omitted, the first device found will be used.
* `outfile`: output file or FIFO, or `-` for standard output.
    * On Windows, you can alternatively use: `--pipe arbitrary_pipe_name`

## Using with Wireshark

* Wireshark must be installed.

### Linux

```sh
./rvi_capture.py - | wireshark -k -i -
```

### Windows

```powershell
# first powershell window/tab
py .\rvi_capture.py --pipe rvi_capture
# second powershell window/tab
# Note that rvi_capture will also print this command for you
& "$env:ProgramFiles\Wireshark\Wireshark.exe" -i"\\.\pipe\rvi_capture" -k
```

### Tips

- In Wireshark, you can filter for a particular network interface based on the `frame.interface_name` field. Here are some possible values (as tested on iOS 14.8):
  - `en0`: wifi interface
  - `pdp_ip0`: cellular interface
  - `ipsec1`: IPSec outer transport for VoLTE
  - `ipsec3`: IPSec inner transport for VoLTE
