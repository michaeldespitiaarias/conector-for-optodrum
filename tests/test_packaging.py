"""
The standalone build only contains the modules PyInstaller can see; one
loaded only by name at run time has to be listed in build.spec.
"""
import os
import re

_SPEC = os.path.join(os.path.dirname(__file__), "..", "packaging",
                     "build.spec")


def test_the_spanish_interface_is_bundled():
    with open(_SPEC, encoding="utf-8") as fh:
        block = re.search(r"hiddenimports=\[(.*?)\]", fh.read(), re.S)
    assert "locale_es" in re.findall(r'"([^"]+)"', block.group(1))
