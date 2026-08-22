"""Test environment isolation.

osh.py and ask.py call check_and_activate_venv() at module level (not guarded
by `if __name__ == "__main__":`), so importing either module can trigger
os.execv() based on the developer's real ~/.config/osh/config.json and hijack
the process running the tests. Point XDG_CONFIG_HOME at an empty directory
before osh/ask are ever imported so collection can't see a real config with a
python_venv set.
"""
import os
import tempfile

os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="osh-test-config-")
