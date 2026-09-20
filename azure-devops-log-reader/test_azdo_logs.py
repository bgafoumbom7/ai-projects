"""Offline tests against the bundled sample data. Run with: python -m pytest  (or python test_azdo_logs.py)"""

from azdo_logs import DemoClient, build_tree, failed_tasks, find_error_lines, strip_timestamps


def test_tree_structure():
    roots = build_tree(DemoClient().get_timeline(4821))
    assert [r.name for r in roots] == ["Build", "Deploy to Production"]
    deploy = roots[1]
    assert deploy.result == "failed"
    assert deploy.children[1].name == "Deploy webapp"  # checkpoint is child 0
    assert deploy.duration == "4m15s"


def test_failed_tasks_found():
    roots = build_tree(DemoClient().get_timeline(4821))
    failed = failed_tasks(roots)
    assert [t.name for t in failed] == ["Azure Web App Deploy: webshop-prod"]
    assert failed[0].log_id == 12
    assert len(failed[0].issues) == 2


def test_error_extraction():
    log = DemoClient().get_log(4821, 12)
    lines = find_error_lines(log, context=0)
    assert any("ERESOLVE" in l for l in lines)
    assert any("##[error]" in l for l in lines)
    assert not any(l.startswith("2026-") for l in lines), "timestamps should be stripped"


def test_strip_timestamps():
    assert strip_timestamps("2026-09-18T09:46:04.1001000Z hello") == "hello"


def test_failed_filter():
    assert [b["id"] for b in DemoClient().list_builds(failed_only=True)] == [4821]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
