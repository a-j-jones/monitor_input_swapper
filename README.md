# Input Swapper

This is a simple script that detects an input device being plugged in / unplugged
and sends a message to your monitor to switch to a specific input.

## Usage

1. Clone this repository
2. Create a virtual environment & Install requirements.txt
2. Configure the constants in main.py
3. Run main.py

I have set up `InputSwapper.bat` which activates the virtual environment and runs 
in pythonw so that the code runs in the background, then the code can be paused or 
exited from the system tray.

## References
I used the following resources to help me write this script:
  - [Find monitor/Send code](https://gist.github.com/mchubby/853bf4c31e2b924c5be004ab7e39fa3e)
  - [VCP Codes](https://github.com/dot-osk/monitor_ctrl/blob/master/vcp_code.py)