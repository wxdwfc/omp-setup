#!/usr/bin/env python3
"""omp-style minimalist single-line HUD statusline for Google Antigravity CLI (agy).

Reads agy's statusLine JSON state from stdin and renders a right-aligned,
Catppuccin/omp-styled single-line status bar with a dynamic double-line rail.

Environment overrides (all optional):
  AGY_OMP_RAIL="double"|"thin"|"none"   Left rail style (default: "double" -> ═)
  AGY_OMP_QUOTA="remaining"|"used"      Quota percentage mode (default: "remaining")
  AGY_OMP_ASCII="1"                     Use pure ASCII/Unicode fallbacks (no Nerd Font)
  AGY_OMP_SYNC_INTERVAL="300"           Cache/sync interval in seconds (default: 300 = 5 min)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from typing import Any

# ── Exact RGB palette sampled from omp HUD (Catppuccin Mocha friendly) ──────
RESET = "\x1b[0m"


def fg(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\x1b[38;2;{r};{g};{b}m"


C_RAIL = fg("#4e8fec")      # ════ double horizontal rail
C_CLOCK = fg("#aeb3ec")     #  icon
C_MODEL = fg("#ffca38")     # model / tier name (warm gold)
C_SEP = fg("#6c738a")       # · middle dot separator
C_LABEL = fg("#dfe7ff")     # 5h / 7d window label
C_MUTED = fg("#7e858f")     # calm quota pct & countdown
C_GREEN = fg("#91e087")     # git branch / secondary accent
C_CTX = fg("#c7cee9")       # context window readout
C_WAND = fg("#8d8cb6")      # 󰁨 effort icon
C_EFFORT = fg("#ae7ed1")    # effort level text
C_CYAN = fg("#89dceb")      # plan mode badge
C_WARN = fg("#ffca38")      # amber warning
C_CRIT = fg("#f38ba8")      # coral red critical

ASCII_MODE = os.environ.get("AGY_OMP_ASCII", "0") == "1"
RAIL_MODE = os.environ.get("AGY_OMP_RAIL", "double").lower()
QUOTA_MODE = os.environ.get("AGY_OMP_QUOTA", "remaining").lower()
try:
    SYNC_INTERVAL = max(0.0, float(os.environ.get("AGY_OMP_SYNC_INTERVAL", "300")))
except ValueError:
    SYNC_INTERVAL = 300.0
CACHE_FILE = os.path.join(tempfile.gettempdir(), f"agy-omp-statusline-{os.getuid()}.json")

ICON_MODEL = "*" if ASCII_MODE else "\uf43a"      #  nf-oct-clock
ICON_STAR = "*" if ASCII_MODE else "\u2726"       # ✦ four-pointed star
ICON_GIT = "@" if ASCII_MODE else "\ue0a0"        #  powerline git branch
ICON_CTX = "#" if ASCII_MODE else "\U000f05b3"    # 󰖳 nf-md-microsoft_windows / pane
ICON_WAND = "~" if ASCII_MODE else "\U000f0068"   # 󰁨 nf-md-auto_fix

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_width(text: str) -> int:
    clean = ANSI_RE.sub("", text)
    width = 0
    for ch in clean:
        cat = unicodedata.category(ch)
        if cat in ("Mn", "Me", "Cf"):
            continue
        # PUA Nerd Font icons render 1 cell wide in monospace Nerd Fonts
        cp = ord(ch)
        if (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0xFFFFD) or (0x100000 <= cp <= 0x10FFFD):
            width += 1
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def shorten_model(model_obj: Any) -> tuple[str, str]:
    """Return (compact_model_name, effort_str) in omp's terse lowercase style."""
    if not isinstance(model_obj, dict):
        return ("auto", "-")

    raw_name = str(model_obj.get("display_name") or model_obj.get("id") or model_obj.get("current") or "auto").strip()
    effort = str(model_obj.get("effort") or "").strip().lower()

    # Extract trailing "(High)" / "(Medium)" etc. from display_name
    m = re.search(r"\((low|medium|med|high|xhigh|max|minimal|min)\)\s*$", raw_name, flags=re.I)
    if m:
        if not effort:
            effort = m.group(1).lower()
        raw_name = raw_name[: m.start()].strip()

    # Handle Orchestrator (Planner)
    orch = re.match(r"^Orchestrator\s*(?:\(([^)]+)\))?", raw_name, flags=re.I)
    if orch:
        sub = (orch.group(1) or "").strip().lower()
        name = f"orch:{sub}" if sub else "orch"
    else:
        # Strip common vendor/version boilerplate: "Gemini 4 Carbon" -> "carbon"
        cleaned = re.sub(r"^(Google\s+)?Gemini\s+(\d+(?:\.\d+)?\s+)?", "", raw_name, flags=re.I).strip()
        cleaned = re.sub(r"^(Anthropic\s+)?Claude\s+(\d+(?:\.\d+)?\s+)?", "claude-", cleaned, flags=re.I).strip()
        cleaned = re.sub(r"^OpenAI\s+", "", cleaned, flags=re.I).strip()
        name = cleaned.lower().replace(" ", "") or raw_name.lower()

    effort_map = {
        "minimal": "min",
        "min": "min",
        "low": "low",
        "medium": "med",
        "med": "med",
        "high": "high",
        "xhigh": "xhigh",
        "max": "max",
    }
    effort_disp = effort_map.get(effort, effort if effort else "-")
    return (name, effort_disp)


def fmt_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return ""
    sec = int(seconds)
    if sec <= 0:
        return ""
    if sec >= 86400:
        d = sec // 86400
        h = (sec % 86400) // 3600
        return f"{d}d {h}h" if h > 0 else f"{d}d"
    if sec >= 3600:
        h = sec // 3600
        m = (sec % 3600) // 60
        return f"{h}h {m}m" if m > 0 else f"{h}h"
    m = max(1, sec // 60)
    return f"{m}m"


def extract_reset_seconds(bucket: dict[str, Any]) -> int | None:
    if bucket.get("reset_in_seconds") is not None:
        try:
            val = int(float(bucket["reset_in_seconds"]))
            return val if val > 0 else None
        except (ValueError, TypeError):
            pass
    if bucket.get("resets_at") is not None:
        try:
            val = int(float(bucket["resets_at"]) - time.time())
            return val if val > 0 else None
        except (ValueError, TypeError):
            pass
    rt = bucket.get("reset_time")
    if isinstance(rt, str) and rt:
        try:
            iso = rt.replace("Z", "+00:00")
            target = dt.datetime.fromisoformat(iso)
            now = dt.datetime.now(dt.timezone.utc)
            val = int((target - now).total_seconds())
            return val if val > 0 else None
        except ValueError:
            pass
    return None


def extract_rem_pct(bucket: dict[str, Any]) -> float | None:
    if bucket.get("remaining_fraction") is not None:
        try:
            return max(0.0, min(100.0, float(bucket["remaining_fraction"]) * 100.0))
        except (ValueError, TypeError):
            pass
    if bucket.get("remaining_percentage") is not None:
        try:
            return max(0.0, min(100.0, float(bucket["remaining_percentage"])))
        except (ValueError, TypeError):
            pass
    if bucket.get("used_percentage") is not None:
        try:
            return max(0.0, min(100.0, 100.0 - float(bucket["used_percentage"])))
        except (ValueError, TypeError):
            pass
    return None


def quota_color(rem_pct: float) -> str:
    if rem_pct <= 10.0:
        return C_CRIT
    if rem_pct <= 25.0:
        return C_WARN
    return C_MUTED


def fmt_pct_int(pct: float) -> str:
    if pct >= 99.95:
        return "100%"
    if pct <= 0.05:
        return "0%"
    return f"{max(1, min(99, round(pct)))}%"


def format_quota_segment(
    label: str,
    rem_pct: float,
    reset_sec: int | None,
    include_timer: bool = True,
    accent_star: bool = False,
) -> str:
    disp_pct = (100.0 - rem_pct) if QUOTA_MODE == "used" else rem_pct
    pct_str = fmt_pct_int(disp_pct)
    timer_str = fmt_duration(reset_sec) if include_timer else ""

    if accent_star:
        # Matches omp's green `✦ argon 84% 5d 2h` style
        col = C_CRIT if rem_pct <= 10.0 else (C_WARN if rem_pct <= 25.0 else C_GREEN)
        tail = f" {timer_str}" if timer_str else ""
        return f"{col}{ICON_STAR} {label} {pct_str}{tail}{RESET}"

    val_col = quota_color(rem_pct)
    tail = f" ({timer_str})" if timer_str else ""
    return f"{C_LABEL}{label}{RESET} {val_col}{pct_str}{tail}{RESET}"


def collect_quotas(data: dict[str, Any], model_slug: str) -> list[dict[str, Any]]:
    """Normalize quota / rate_limits into ordered display buckets."""
    raw_quota = data.get("quota")
    entries: list[tuple[str, dict[str, Any]]] = []

    if isinstance(raw_quota, dict):
        for k, v in raw_quota.items():
            if isinstance(v, dict) and not v.get("disabled", False):
                entries.append((k.lower(), v))

    # Fallback to rate_limits schema if quota map is absent
    if not entries and isinstance(data.get("rate_limits"), dict):
        rl = data["rate_limits"]
        if isinstance(rl.get("five_hour"), dict):
            entries.append(("gemini-5h", rl["five_hour"]))
        if isinstance(rl.get("seven_day"), dict):
            entries.append(("gemini-weekly", rl["seven_day"]))
        if isinstance(rl.get("primary_window"), dict):
            entries.append(("5h", rl["primary_window"]))
        if isinstance(rl.get("secondary_window"), dict):
            entries.append(("7d", rl["secondary_window"]))

    is_3p = any(t in model_slug for t in ("claude", "sonnet", "opus", "haiku", "gpt", "o1", "o3", "o4"))
    is_argon = "argon" in model_slug

    primary_5h: tuple[str, float, int | None] | None = None
    primary_7d: tuple[str, float, int | None] | None = None
    extras: list[tuple[str, float, int | None]] = []

    for key, bucket in entries:
        rem = extract_rem_pct(bucket)
        if rem is None:
            continue
        rsec = extract_reset_seconds(bucket)

        bucket_is_3p = any(t in key for t in ("third", "3p", "claude", "gpt"))
        bucket_is_argon = "argon" in key
        bucket_is_5h = ("5h" in key) or ("five" in key) or (rsec is not None and rsec <= 6 * 3600 and "week" not in key and "7d" not in key)
        bucket_is_7d = ("week" in key) or ("7d" in key) or ("seven" in key) or (rsec is not None and rsec > 6 * 3600)

        if bucket_is_argon:
            if is_argon or rem < 99.95:
                extras.append(("argon", rem, rsec))
            continue

        if bucket_is_3p != is_3p:
            # Non-active family bucket: show only if partially consumed
            if rem < 99.95:
                tag = "3p" if bucket_is_3p else "gem"
                win = "5h" if bucket_is_5h else "7d"
                extras.append((f"{tag}:{win}", rem, rsec))
            continue

        if bucket_is_5h and primary_5h is None:
            primary_5h = ("5h", rem, rsec)
        elif bucket_is_7d and primary_7d is None:
            primary_7d = ("7d", rem, rsec)
        else:
            # Unclassified bucket: surface only if active/consumed or has timer
            if rem < 99.95 or rsec:
                short_k = re.sub(r"^gemini[-_]?", "", key)[:8] or "q"
                extras.append((short_k, rem, rsec))

    result: list[dict[str, Any]] = []
    if primary_5h:
        result.append({"label": primary_5h[0], "rem": primary_5h[1], "rsec": primary_5h[2], "star": False})
    if primary_7d:
        result.append({"label": primary_7d[0], "rem": primary_7d[1], "rsec": primary_7d[2], "star": False})
    for label, rem, rsec in extras:
        result.append({"label": label, "rem": rem, "rsec": rsec, "star": True})
    return result


def get_vcs_info(data: dict[str, Any]) -> tuple[str, bool]:
    vcs = data.get("vcs")
    if isinstance(vcs, dict) and vcs.get("branch"):
        return (str(vcs["branch"]), bool(vcs.get("dirty", False)))

    ws = data.get("workspace")
    if isinstance(ws, dict) and ws.get("git_worktree"):
        return (str(ws["git_worktree"]), False)

    cwd = data.get("cwd") or (ws.get("current_dir") if isinstance(ws, dict) else None)
    if isinstance(cwd, str) and os.path.isdir(cwd):
        try:
            proc = subprocess.run(
                ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=0.12,
                check=False,
            )
            if proc.returncode == 0:
                br = proc.stdout.strip()
                if br and br != "HEAD":
                    return (br, False)
        except Exception:
            pass
    return ("", False)


def fmt_token_limit(limit: int | float | None) -> str:
    if not limit or limit <= 0:
        return "1.0M"
    n = int(limit)
    if n >= 1_000_000:
        # 1,048,576 -> 1.0M; 1,000,000 -> 1.0M; 2,097,152 -> 2.0M
        denom = 1_048_576 if abs(n - round(n / 1_048_576) * 1_048_576) < 50_000 else 1_000_000
        return f"{n / denom:.1f}M"
    if n >= 1_000:
        # 944,128 -> 922K; 200,000 -> 200K
        if n % 1024 == 0:
            return f"{n // 1024}K"
        return f"{round(n / 1000)}K"
    return str(n)


def format_context(data: dict[str, Any], include_limit: bool = True) -> str:
    cw = data.get("context_window")
    used_pct = 0.0
    limit_str = "1.0M"
    if isinstance(cw, dict):
        try:
            used_pct = float(cw.get("used_percentage") or 0.0)
        except (ValueError, TypeError):
            used_pct = 0.0
        size = cw.get("context_window_size") or cw.get("total_limit")
        limit_str = fmt_token_limit(size)

    col = C_CRIT if used_pct >= 85.0 else (C_WARN if used_pct >= 70.0 else C_CTX)
    if include_limit:
        return f"{col}{ICON_CTX} {used_pct:.1f}%/{limit_str}{RESET}"
    return f"{col}{ICON_CTX} {used_pct:.1f}%{RESET}"


def build_line(data: dict[str, Any]) -> str:
    cols = 0
    try:
        cols = int(data.get("terminal_width") or 0)
    except (ValueError, TypeError):
        cols = 0
    if cols <= 0:
        cols = shutil.get_terminal_size((120, 24)).columns

    # Leave 2 columns breathing room so TUI borders/margins never trigger line-wrap
    target_width = max(40, cols - 2)

    model_slug, effort = shorten_model(data.get("model"))
    cycle_mode = str(data.get("cycle_mode") or "").strip().lower()
    quotas = collect_quotas(data, model_slug)
    branch, dirty = get_vcs_info(data)

    sep = f" {C_SEP}\u00b7{RESET} "

    def assemble(include_timers: bool, include_branch: bool, include_ctx_limit: bool, include_extras: bool) -> str:
        segs: list[str] = []

        # 1. Model (+ optional [plan] badge)
        mode_badge = f" {C_CYAN}[plan]{RESET}" if cycle_mode == "plan" else ""
        segs.append(f"{C_CLOCK}{ICON_MODEL}{RESET} {C_MODEL}{model_slug}{RESET}{mode_badge}")

        # 2. Quotas
        for q in quotas:
            if q["star"] and not include_extras:
                continue
            segs.append(
                format_quota_segment(
                    q["label"],
                    q["rem"],
                    q["rsec"],
                    include_timer=include_timers,
                    accent_star=q["star"],
                )
            )

        # 3. Git branch (in omp's soft mint green)
        if include_branch and branch:
            br_disp = branch if len(branch) <= 20 else (branch[:19] + "\u2026")
            dirty_mark = f"{C_WARN}*{RESET}" if dirty else ""
            segs.append(f"{C_GREEN}{ICON_GIT} {br_disp}{RESET}{dirty_mark}")

        # 4. Context window + thinking effort (omp signature tail: `󰖳 1.0%/922K 󰁨 -`)
        ctx_part = format_context(data, include_limit=include_ctx_limit)
        effort_part = f"{C_WAND}{ICON_WAND}{RESET} {C_EFFORT}{effort}{RESET}"
        segs.append(f"{ctx_part} {effort_part}")

        return sep.join(segs)

    # Progressive responsive compaction so it ALWAYS stays on 1 clean line
    candidates = [
        assemble(True, True, True, True),
        assemble(True, True, True, False),
        assemble(False, True, True, False),
        assemble(False, False, True, False),
        assemble(False, False, False, False),
    ]

    right = candidates[-1]
    for cand in candidates:
        if visible_width(cand) + 4 <= target_width:
            right = cand
            break

    right_w = visible_width(right)
    rail_len = max(0, target_width - right_w - 1)

    if rail_len <= 0:
        return right

    if RAIL_MODE == "none":
        return (" " * (rail_len + 1)) + right
    rail_char = "\u2500" if RAIL_MODE == "thin" else ("\u2550" if not ASCII_MODE else "=")
    return f"{C_RAIL}{rail_char * rail_len}{RESET} {right}"


def _cache_key(data: dict[str, Any]) -> list[Any]:
    ws = data.get("workspace")
    cwd = data.get("cwd") or (ws.get("current_dir") if isinstance(ws, dict) else "")
    model = data.get("model") if isinstance(data.get("model"), dict) else {}
    return [
        data.get("terminal_width") or 0,
        cwd,
        model.get("id") or model.get("display_name") or model.get("current") or "",
        model.get("effort") or "",
        data.get("cycle_mode") or "",
        ASCII_MODE,
        RAIL_MODE,
        QUOTA_MODE,
    ]


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    now = time.time()
    key = _cache_key(data)

    if SYNC_INTERVAL > 0:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if (
                isinstance(cached, dict)
                and isinstance(cached.get("line"), str)
                and cached.get("key") == key
                and (now - float(cached.get("ts", 0.0))) < SYNC_INTERVAL
            ):
                sys.stdout.write(cached["line"] + "\n")
                return
        except Exception:
            pass

    line = build_line(data)

    if SYNC_INTERVAL > 0:
        try:
            tmp_path = f"{CACHE_FILE}.{os.getpid()}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump({"ts": now, "key": key, "line": line}, f)
            os.replace(tmp_path, CACHE_FILE)
        except Exception:
            pass

    sys.stdout.write(line + "\n")


if __name__ == "__main__":
    main()
