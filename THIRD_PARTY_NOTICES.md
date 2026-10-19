# Third-party notices

This project bundles the third-party modules listed below. Each file keeps its
original copyright and license header. All of them are distributed under the
MIT License, reproduced at the end of this file.

| Module | Files | Copyright | Upstream |
| --- | --- | --- | --- |
| `tinyweb` | `cplus2_admin/libs/network/tinyweb.py` | (C) 2017-2018 Konstantin Belyalov | https://github.com/belyalov/tinyweb |
| `mpu6886` | `cplus2_admin/libs/sensor/mpu6886.py` | (c) 2020 Mika Tuupola | https://github.com/tuupola/micropython-mpu6886 |
| `pcf8563` | `cplus2_admin/libs/rtc/pcf8563.py` | (c) 2020 Sebastian Wicki, (c) 2020 Mika Tuupola | https://github.com/tuupola/pcf8563 |
| `st7789` | `cplus2_admin/libs/display/st7789.py` | (c) 2024 Rafael Correia, (c) 2020 Sebastian Wicki, (c) 2019 Ivan Belokobylskiy | https://github.com/gandro/micropython-m5stickc-plus and https://github.com/devbis/st7789py_mpy |
| `colors` | `cplus2_admin/libs/display/colors.py` | (c) 2020 Sebastian Wicki, (c) 2019 Ivan Belokobylskiy | https://github.com/gandro/micropython-m5stickc-plus |
| `logging` | `cplus2_admin/libs/std/logging.py` | MicroPython project contributors | https://github.com/micropython/micropython-lib |
| `time` | `cplus2_admin/libs/std/time.py` | MicroPython project contributors | https://github.com/micropython/micropython-lib |

`buzzercontroller.py`, `buttoncontroller.py`, `ledcontroller.py`,
`bitmap.py`, `wlancontroller.py`, `webcontroller.py`,
`batterycontroller.py`, `systemcontroller.py`, `microphonecontroller.py`,
`notes.py`, `main.py` and `boot.py` are original to this project and use the
same MIT License.

The optional PDM RX patch in `firmware/pdm_rx/` is adapted from
[MicroPython PR #14176](https://github.com/micropython/micropython/pull/14176)
and follows MicroPython's MIT License. The prebuilt firmware in
`firmware/pdm_rx/build/` is a MicroPython build (MIT License) with that patch
applied; it bundles the libraries used by the ESP32 port.

## MIT License

Copyright (c) the respective authors listed above.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
