from pathlib import Path

import click

from functions.format_timestamp import format_timestamp
from functions.i18n import _


def clean_srt_lines(lines: list[str]) -> list[str]:
    """Return plain text lines from SRT lines (no numbering/timestamps/blank lines)."""
    cleaned: list[str] = []
    for line in lines:
        s = line.strip()
        if not s or s.isdigit() or "-->" in s:
            continue
        cleaned.append(s)
    return cleaned


def clean_srt_file_to_txt(
    srt_path: str, out_path: str | None = None
) -> str:
    if not srt_path:
        raise click.BadParameter(_("Error: No input file provided."))

    p = Path(srt_path)
    if not p.exists():
        raise click.ClickException(_("📄 File not found: ") + str(p))
    if p.suffix.lower() not in (".srt", ".txt"):
        raise click.BadParameter(
            _("Input file must end with: '.srt' or '.txt'")
        )

    out = (
        Path(out_path)
        if out_path
        else p.with_name(p.name[:-4] + ".txt")
    )
    if out.suffix.lower() != ".txt":
        raise click.BadParameter(_("Output file must end with: '.txt'"))

    lines = p.read_text(encoding="utf-8").splitlines()
    cleaned = clean_srt_lines(lines)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    return str(out.resolve())


def write_segments(
    segments: list[dict], output: str, clean: bool
) -> str:
    final_out = output
    if clean and final_out.lower().endswith(".srt"):
        final_out = final_out[:-4] + ".txt"

    Path(final_out).parent.mkdir(parents=True, exist_ok=True)

    if clean:
        with open(final_out, "w", encoding="utf-8") as f:
            for seg in segments:
                text = str(seg.get("text", "")).strip()
                if text:
                    f.write(text + "\n")
        return final_out

    # SRT mode
    with open(final_out, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, start=1):
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", 0.0))
            text = str(seg.get("text", "")).strip()
            f.write(f"{idx}\n")
            f.write(
                f"{format_timestamp(start)} --> {format_timestamp(end)}\n"
            )
            f.write(text + "\n\n")
    return final_out
