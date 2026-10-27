"""Lesson lab: explain SIL decode → HID after image evidence exists."""

from harness.ready import require_lessons
from software.fixture import run_fixture


def main() -> None:
    require_lessons()
    result = run_fixture({})
    print("SIL fixture ok:", result.get("ok"), "samples:", result.get("count"))
    print(
        "Next: capture On-Off, then the other AUX buttons, under "
        "reports/pico/<stamp>/captures/. Render keymap.yaml with --profile. "
        "Leave keymap.example.yaml synthetic."
    )


if __name__ == "__main__":
    main()
