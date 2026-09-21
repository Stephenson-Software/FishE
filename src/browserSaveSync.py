# @author Daniel McCoy Stephenson
"""Browser-storage sync now lives in tak (tak.saves.browser); this module
keeps FishE's import path working. Every code path that writes or deletes a
save must still call syncBrowserSaves() afterwards."""

from tak.saves.browser import getJsModule, syncBrowserSaves  # noqa: F401
