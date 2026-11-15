import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "evaluate_ai.py"
CASES = TOOL.parents[1] / "evaluation" / "cases.json"


def test_evaluation_requires_explicit_live_opt_in(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, str(TOOL), "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env={},
    )
    assert result.returncode == 2
    assert "Pass --live explicitly" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("count", [0, 7])
def test_evaluation_rejects_unbounded_case_lists_before_credentials_or_network(
    tmp_path: Path, count: int
) -> None:
    original = json.loads(CASES.read_text())[0]
    cases = [{**original, "id": f"case-{index}"} for index in range(count)]
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(cases))
    output = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, str(TOOL), "--live", "--cases", str(path), "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env={},
    )
    assert result.returncode == 2
    assert "Choose between one and 6 cases" in result.stderr
    assert not output.exists()
