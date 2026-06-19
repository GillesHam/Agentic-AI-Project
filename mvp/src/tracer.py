"""
trace.py, lightweight observability for the agent loop.

The course (Session 3 & 4) stresses that agentic systems are non-deterministic and
need END-TO-END TRACING: chain-of-thought, tools used, tool output, retries/adaptation,
and human-in-the-loop pauses. Real systems use LangSmith / Langfuse / Azure AI Foundry;
here we implement a tiny console tracer so the audience can SEE the agent think.

Every step is tagged with one of the agentic-loop phases:
    PERCEIVE -> REASON -> PLAN -> ACT -> OBSERVE -> ADAPT
"""

import sys
import time

# ANSI colors (degrade gracefully if the terminal doesn't support them)
_C = {
    "PERCEIVE": "\033[96m", # cyan
    "REASON":   "\033[95m", # magenta
    "PLAN":     "\033[94m", # blue
    "ACT":      "\033[93m", # yellow
    "OBSERVE":  "\033[92m", # green
    "ADAPT":    "\033[91m", # red
    "HITL":     "\033[1;33m", # bold yellow
    "AGENT":    "\033[1;36m", # bold cyan
    "DIM":      "\033[2m",
    "RESET":    "\033[0m",
}

ENABLE_COLOR = sys.stdout.isatty()
SLOW = False  # set True for a paced live demo


def _c(tag):
    return _C.get(tag, "") if ENABLE_COLOR else ""


def _reset():
    return _C["RESET"] if ENABLE_COLOR else ""


def banner(title):
    line = "=" * 78
    print(f"\n{_c('AGENT')}{line}\n  {title}\n{line}{_reset()}\n")


def agent_header(agent_name, role):
    print(f"{_c('AGENT')}┌─ AGENT: {agent_name}{_reset()}  {_c('DIM')}({role}){_reset()}")


def step(phase, message, detail=None):
    """Print one agentic-loop step."""
    tag = f"{_c(phase)}[{phase:<8}]{_reset()}"
    print(f"  {tag} {message}")
    if detail:
        for line in str(detail).splitlines():
            print(f"             {_c('DIM')}{line}{_reset()}")
    if SLOW:
        time.sleep(0.8)


def tool_call(tool_name, args, action_type, requires_approval):
    flag = ""
    if requires_approval:
        flag = f"  {_c('HITL')}⟨requires human approval⟩{_reset()}"
    print(
        f"  {_c('ACT')}[ACT     ]{_reset()} tool.call "
        f"{_c('AGENT')}{tool_name}{_reset()}({_fmt_args(args)})  "
        f"{_c('DIM')}[{action_type}]{_reset()}{flag}"
    )
    if SLOW:
        time.sleep(0.6)


def tool_result(tool_name, summary):
    print(f"  {_c('OBSERVE')}[OBSERVE ]{_reset()} {tool_name} -> {summary}")
    if SLOW:
        time.sleep(0.6)


def hitl(message):
    print(f"\n  {_c('HITL')}*** HUMAN-IN-THE-LOOP ***{_reset()} {message}\n")
    if SLOW:
        time.sleep(0.6)


def agent_footer():
    print(f"{_c('AGENT')}└─{_reset()}")


def _fmt_args(args):
    return ", ".join(f"{k}={v!r}" for k, v in args.items())
