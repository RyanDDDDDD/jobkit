import subprocess
import sys

import pytest

from jobkit.docs import DOC_NAMES, read_doc


@pytest.mark.parametrize("name", DOC_NAMES)
def test_read_doc_nonempty(name):
    assert read_doc(name).strip()


def test_read_doc_unknown_raises():
    with pytest.raises(KeyError):
        read_doc("does-not-exist")


def test_cli_doc_unknown_exits_2():
    r = subprocess.run([sys.executable, "-m", "jobkit", "doc", "nope"],
                       capture_output=True, text=True)
    assert r.returncode == 2
    assert "workflow-rules" in r.stderr
