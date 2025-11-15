from pathlib import Path

import pytest

from ha_template.git_setup import GitSetup


class CallRecorder:
    def __init__(self):
        self.calls = []

    def __call__(self, args, cwd, check):
        self.calls.append((tuple(args), Path(cwd)))


def test_git_setup_configures_identity(monkeypatch, tmp_path):
    recorder = CallRecorder()
    monkeypatch.setattr("subprocess.run", recorder)

    repo = tmp_path
    hooks_dir = repo / ".githooks"
    hooks_dir.mkdir()

    setup = GitSetup(repo)
    setup.configure_identity("name", "email@example.com")
    setup.configure_hooks(hooks_dir)

    assert ("git", "config", "user.name", "name") in [call[0] for call in recorder.calls]
    assert ("git", "config", "core.hooksPath", ".githooks") in [call[0] for call in recorder.calls]
