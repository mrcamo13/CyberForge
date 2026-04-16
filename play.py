"""play.py — CyberForge Launcher

Single entry point for all CyberForge simulators.

Usage:
    python play.py          — show game selector
    python play.py --dev    — pass dev flag through to selected game
"""

import os
import runpy
import sys

# ---------------------------------------------------------------------------
# ANSI helpers (no shared utils at this level — keep it self-contained)
# ---------------------------------------------------------------------------
_RESET  = "\033[0m"
_CYAN   = "\033[96m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_GRAY   = "\033[90m"
_WHITE  = "\033[97m"


def _p(color: str, msg: str) -> None:
    print(f"{color}{msg}{_RESET}")


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------

_LOGO = r"""
   ____      _               _____
  / ___|   _| |__   ___ _ __|  ___|__  _ __ __ _  ___
 | |  | | | | '_ \ / _ \ '__| |_ / _ \| '__/ _` |/ _ \
 | |__| |_| | |_) |  __/ |  |  _| (_) | | | (_| |  __/
  \____\__, |_.__/ \___|_|  |_|  \___/|_|  \__, |\___|
       |___/                                |___/

  CYBERSECURITY TRAINING SIMULATOR  v1.0
"""

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    dev_flag = "--dev" in sys.argv

    _clear()
    _p(_CYAN, _LOGO)

    while True:
        _p(_CYAN,   "=" * 50)
        _p(_CYAN,   "  SELECT SIMULATOR")
        _p(_CYAN,   "=" * 50)
        _p(_WHITE,  "  [1] CIPHER  — Red Team   (PenTest+)")
        _p(_WHITE,  "  [2] AEGIS   — Blue Team  (CySA+)")
        _p(_GRAY,   "  [0] Quit")
        _p(_CYAN,   "=" * 50)

        choice = input("> ").strip()

        if choice == "0":
            _p(_GRAY, "Goodbye.")
            sys.exit(0)

        if choice in ("1", "2"):
            target_dir = "cipher" if choice == "1" else "aegis"
            target_main = os.path.join(HERE, target_dir, "main.py")

            if not os.path.exists(target_main):
                _p(_YELLOW, f"Could not find {target_dir}/main.py — check your install.")
                continue

            # Pass --dev through if set
            if dev_flag and "--dev" not in sys.argv[1:]:
                sys.argv.append("--dev")
            elif not dev_flag and "--dev" in sys.argv:
                sys.argv.remove("--dev")

            # Add the simulator's own directory to the path, then run it
            sys.path.insert(0, os.path.join(HERE, target_dir))
            runpy.run_path(target_main, run_name="__main__")
            return  # game exited cleanly; drop back to OS

        _p(_YELLOW, "Enter 1, 2, or 0.")


if __name__ == "__main__":
    main()
