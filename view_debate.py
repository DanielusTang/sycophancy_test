#!/usr/bin/env python3
"""View sycophancy debate .jsonl logs as readable Markdown transcripts.

Single file:
    python view_debate.py path/to/log.jsonl            # writes log.md next to it
    python view_debate.py path/to/log.jsonl -o out.md  # custom output
    python view_debate.py path/to/log.jsonl --stdout   # print to terminal

Batch (a folder, several folders, or the whole project):
    python view_debate.py outputs_strength/            # convert every .jsonl in the folder
    python view_debate.py . --recursive                # walk the whole tree
    python view_debate.py . -r --index                 # also build INDEX.md (summary table)

Then open any .md in VS Code and hit Cmd+Shift+V for the rendered preview.
"""
import argparse
import json
import sys
from pathlib import Path


def fmt_judge(j: dict) -> str:
    if not j:
        return "_(no judge verdict)_\n"
    lines = []
    collapsed = j.get("is_collapsed")
    strength = j.get("position_strength")
    partial = j.get("partial_sycophancy")
    badge = "🔴 COLLAPSED" if collapsed else "🟢 held"
    lines.append(f"**Judge:** {badge}  ·  position strength: **{strength}**"
                 + ("  ·  ⚠️ partial sycophancy" if partial else ""))
    if j.get("affirmed_proposition"):
        lines.append(f"\n> _Affirmed:_ {j['affirmed_proposition']}")
    if j.get("reason"):
        lines.append(f"\n> _Reason:_ {j['reason']}")
    return "\n".join(lines) + "\n"


def render(records: list) -> str:
    out = []
    meta = next((r for r in records if r.get("type") == "meta"), {})
    result = next((r for r in records if r.get("type") == "result"), {})
    turns = [r for r in records if r.get("type") == "turn"]

    # Header
    out.append(f"# Debate transcript — {meta.get('topic', '?')} ({meta.get('variant', '')})\n")
    if meta:
        out.append(f"- **Target model:** {meta.get('target_model')}  ·  "
                   f"**Proxy:** {meta.get('proxy_model')}  ·  **Judge:** {meta.get('judge_model')}")
        # Debate logs carry a 'stance' (the target's assigned position) and a fixed
        # 'proxy_prompt'; the presupposition/unethical logs carry false_premise/correction.
        if meta.get("stance") is not None:
            out.append(f"- **Assigned stance:** {meta.get('stance')}")
            if meta.get("proxy_prompt"):
                out.append(f"- **Fixed proxy probe:** {meta.get('proxy_prompt')}")
        else:
            out.append(f"- **False premise:** {meta.get('false_premise')}")
            out.append(f"- **Correction:** {meta.get('correction')}")
        out.append(f"- **Opening question:** {meta.get('opening_question')}\n")

    # Outcome summary up top
    if result:
        out.append(f"> ## Outcome: **{result.get('outcome', '?').upper()}**")
        if result.get("collapsed_at_turn") is not None:
            out.append(f"> Collapsed at turn **{result['collapsed_at_turn']}** "
                       f"(state: {result.get('collapsed_state')})")
        if result.get("reason"):
            out.append(f"> {result['reason']}")
        if result.get("strength_trajectory"):
            traj = " → ".join(str(s) for s in result["strength_trajectory"])
            out.append(f"> Strength trajectory: {traj}")
        out.append("")

    # Turns
    for t in turns:
        n = t.get("turn")
        phase = t.get("phase", "")
        eroded = " · ⚠️ ERODED" if t.get("eroded") else ""
        out.append(f"\n---\n\n## Turn {n} · _{phase}_{eroded}\n")

        out.append(f"### 🟦 User / proxy asks\n\n{t.get('proxy_input', '').strip()}\n")

        if t.get("target_reasoning"):
            out.append("### 🧠 Reasoning\n")
            out.append("<details><summary>show reasoning</summary>\n")
            out.append(f"\n{t['target_reasoning'].strip()}\n")
            out.append("</details>\n")

        out.append(f"### 🟩 Answer\n\n{t.get('target_output', '').strip()}\n")

        out.append(fmt_judge(t.get("judge")))

    return "\n".join(out)


def load(path: Path) -> list:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def summarize(records: list) -> dict:
    """Pull the one-line summary used in INDEX.md."""
    meta = next((r for r in records if r.get("type") == "meta"), {})
    result = next((r for r in records if r.get("type") == "result"), {})
    traj = result.get("strength_trajectory") or []
    if len(traj) > 14:  # keep the index table readable for long runs
        traj_str = (" → ".join(str(s) for s in traj[:6]) + " → … → "
                    + " → ".join(str(s) for s in traj[-4:])
                    + f"  ({len(traj)} turns)")
    else:
        traj_str = " → ".join(str(s) for s in traj)
    return {
        "topic": meta.get("topic", "?"),
        "variant": meta.get("variant", ""),
        "target": meta.get("target_model", ""),
        "outcome": result.get("outcome", "?"),
        "collapsed_at": result.get("collapsed_at_turn"),
        "trajectory": traj_str,
    }


def build_index(rows: list, index_path: Path) -> None:
    """rows: list of (md_path_relative_to_index, summary_dict)."""
    out = ["# Debate transcripts — index\n",
           "| Log | Topic | Variant | Outcome | Collapsed turn | Strength trajectory |",
           "|---|---|---|---|---|---|"]
    for rel, s in sorted(rows, key=lambda x: x[0]):
        badge = "🔴 collapsed" if s["outcome"] == "collapsed" else f"🟢 {s['outcome']}"
        at = s["collapsed_at"] if s["collapsed_at"] is not None else ""
        out.append(f"| [{rel}]({rel}) | {s['topic']} | {s['variant']} | {badge} "
                   f"| {at} | {s['trajectory']} |")
    index_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {index_path}  ({len(rows)} logs)")


def convert_one(path: Path, output: Path = None, to_stdout: bool = False):
    records = load(path)
    md = render(records)
    if to_stdout:
        sys.stdout.write(md)
        return None, None
    out = output or path.with_suffix(".md")
    out.write_text(md, encoding="utf-8")
    return out, summarize(records)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", type=Path, nargs="+",
                    help="one or more .jsonl files and/or folders")
    ap.add_argument("-o", "--output", type=Path,
                    help="output path (single-file mode only)")
    ap.add_argument("-r", "--recursive", action="store_true",
                    help="recurse into subfolders when a path is a directory")
    ap.add_argument("--index", action="store_true",
                    help="build INDEX.md (summary table) in the current directory")
    ap.add_argument("--stdout", action="store_true",
                    help="print to terminal instead of writing (single file only)")
    args = ap.parse_args()

    # Expand any directories into the .jsonl files they contain.
    files = []
    for p in args.paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.jsonl") if args.recursive else p.glob("*.jsonl")))
        else:
            files.append(p)

    if not files:
        sys.exit("No .jsonl files found.")

    if args.stdout or args.output:
        if len(files) != 1:
            sys.exit("--stdout/--output only work with a single .jsonl file.")
        convert_one(files[0], output=args.output, to_stdout=args.stdout)
        return

    rows = []
    for f in files:
        try:
            md_path, summary = convert_one(f)
        except Exception as e:  # one bad log shouldn't abort the batch
            print(f"⚠️  skipped {f}: {e}", file=sys.stderr)
            continue
        rows.append((md_path, summary))
        print(f"Wrote {md_path}")

    if args.index and rows:
        index_path = Path("INDEX.md")
        rel_rows = [(str(md.relative_to(Path.cwd()) if md.is_absolute()
                        else md), s) for md, s in rows]
        build_index(rel_rows, index_path)


if __name__ == "__main__":
    main()
