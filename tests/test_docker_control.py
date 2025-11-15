from pathlib import Path

from ha_template.docker_control import DockerController


class FakeProcess:
    def __init__(self, stdout=""):
        self.stdout = stdout


def test_docker_controller_status(monkeypatch, tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}")
    calls = []

    def run(cmd, cwd, check, capture_output=False, text=False):
        calls.append((tuple(cmd), Path(cwd), capture_output))
        return FakeProcess(stdout="running")

    monkeypatch.setattr("subprocess.run", run)
    controller = DockerController(compose_file)

    result = controller.status()
    assert result == "running"
    assert any("ps" in call[0] for call in calls)


def test_is_running(monkeypatch, tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}")

    def run(cmd, cwd, check, capture_output=False, text=False):
        stdout = "id" if "-q" in cmd else ""
        return FakeProcess(stdout=stdout)

    monkeypatch.setattr("subprocess.run", run)
    controller = DockerController(compose_file)
    assert controller.is_running() is True
