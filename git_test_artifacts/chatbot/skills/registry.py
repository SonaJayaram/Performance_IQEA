"""Skill registry.

LOCATOR is fully wired to the real backend (Milestone 3): open browser →
extract → pick locators → save → optionally generate the Page Object.
TESTCASE remains a guided preview until Milestone 4.
"""
import streamlit as st

from chatbot.skills.base import GuidedSkill, step, action, embed
from chatbot.services import locator_service, testcase_service


# ---------------------------------------------------------------- help ----
def _help_text(slots):
    return (
        "I'm your QE assistant. Tell me what you want in plain language:\n\n"
        "• **Extract locators / build a Page Object** — live now: I'll open a URL, "
        "scrape the elements, let you pick xpaths, and generate the page file.\n"
        "• **Generate test cases** — guided preview (full generation lands next).\n\n"
        "Try: *\"extract xpaths for my app\"* or *\"generate test cases\"*."
    )


HELP = GuidedSkill(
    id="help",
    triggers=["help", "hi", "hello", "hey", "what can you do", "capabilities", "start"],
    description="Explain what the assistant can do.",
    steps=[],
    on_complete=_help_text,
)


# ----------------------------------------------------- locators / POM ----
def _open_browser(slots):
    locator_service.open_browser(slots["url"])
    return {}


def _extract(slots):
    xdict = locator_service.extract_xpaths(slots.get("app_type"), slots.get("tags") or [])
    return {"_xdict": xdict, "_xpaths": locator_service.flatten(xdict)}


def _xpath_options(slots):
    return [{"label": f"{it['element']} · {it['xpath']}"[:100], "value": it["xpath"]}
            for it in slots.get("_xpaths", [])]


def _save(slots):
    chosen = set(slots.get("sel") or [])
    items = [it for it in slots.get("_xpaths", []) if it["xpath"] in chosen]
    slots["selected_items"] = items
    if items:
        locator_service.save_selected(items, slots["page_name"])
    return {}


def _generate(slots):
    path = locator_service.generate_page_object(slots["page_name"], slots["language"])
    return {"_pom_path": path}


def _has_xpaths(s):
    return len(s.get("_xpaths") or []) > 0


def _has_selection(s):
    return len(s.get("sel") or []) > 0


def _wants_pom(s):
    return s.get("gen_pom") is True


def _locator_complete(slots):
    if not _has_xpaths(slots):
        return ("I couldn't find any elements on that page for those settings. "
                "Try different element types or another URL — just say *extract xpaths* again.")
    if not _has_selection(slots):
        return "No locators were selected, so nothing was saved. Say *extract xpaths* to try again."
    msg = f"✅ Saved **{len(slots.get('selected_items', []))}** locator(s) to page **{slots['page_name']}**."
    if _wants_pom(slots) and slots.get("_pom_path"):
        msg += f"\n\n📄 Generated the Page Object: `{slots['_pom_path']}`"
    return msg


def _locator_suggest(slots):
    if _has_selection(slots) and not _wants_pom(slots):
        return "Want the Page Object file from these locators later? Just say *generate page object*."
    return None


LOCATOR = GuidedSkill(
    id="locator",
    triggers=["xpath", "xpaths", "locator", "locators", "page object", "pom",
              "extract element", "extract elements"],
    description="Extract locators from a live page and build a Page Object.",
    steps=[
        step("url", "TEXT", "Sure — what's the URL of the page you want to work on?"),
        action("open_browser", _open_browser,
               status=lambda s: f"🌐 Opened the browser at {s['url']}."),
        step("app_type", "CHOICE", "Is this a Web app or a Power BI report?",
             options=[{"label": "🌐 Web", "value": "Web"},
                      {"label": "📊 Power BI", "value": "PowerBi"}]),
        step("tags", "MULTISELECT", "Which element types should I extract?",
             options=["input", "button", "a", "select", "textarea", "div", "span"],
             condition=lambda s: s.get("app_type") == "Web"),
        action("extract", _extract,
               status=lambda s: f"🔎 Found **{len(s.get('_xpaths', []))}** candidate locator(s)."),
        step("sel", "MULTISELECT", "Select the locators you want to keep:",
             options=_xpath_options, condition=_has_xpaths),
        step("page_name", "TEXT", "What page name should I save these under?",
             condition=_has_selection),
        action("save", _save,
               status=lambda s: f"💾 Saved to page **{s.get('page_name')}**.",
               condition=_has_selection),
        step("gen_pom", "CONFIRM", "Generate the Page Object file now?",
             condition=_has_selection),
        step("language", "CHOICE", "Which language / framework?",
             options=["Java-Selenium", "Java-Playwright", "Python-Selenium", "Python-Playwright"],
             condition=_wants_pom),
        action("generate", _generate,
               status="🛠️ Generating the Page Object file…", condition=_wants_pom),
    ],
    on_complete=_locator_complete,
    suggest=_locator_suggest,
)


# ------------------------------------------------- test case (preview) ---
def _collect_recorded(slots):
    """Chain the recording's outputs into the test-case flow — no re-selection."""
    rec = slots.get("recording") or {}
    return {"_action_file": rec.get("action_file"),
            "_rec_shots": rec.get("screenshots") or []}


def _recorded(s):
    return s.get("source") == "recorded"


def _recorded_has_shots(s):
    return _recorded(s) and len(s.get("_rec_shots") or []) > 0


def _recorded_add_more(s):
    return _recorded(s) and s.get("add_more") is True


def _recorded_has_tc(s):
    return _recorded(s) and bool(s.get("_tc_response"))


def _recorded_use_tmt(s):
    return _recorded(s) and s.get("use_tmt") is True


def _gap_pending(s):
    # gap analysis produced, but cases not yet generated from it
    return _recorded(s) and bool(s.get("_gap")) and not s.get("_tc_response")


def _gap_answered(s):
    return _recorded(s) and bool(s.get("_gap")) and (s.get("approve_gap") is not None)


def _can_push(s):
    return (_recorded(s) and bool(s.get("_tc_response"))
            and (s.get("_tmt") or {}).get("tool") == "Azure Test Plans")


def _build_ctx(slots):
    kept = (slots.get("shots_reviewed") or {}).get("selected")
    if kept is None:
        kept = list(slots.get("_rec_shots") or [])
    extra = (slots.get("extra_shots") or {}).get("filenames") or []
    all_shots = list(kept) + list(extra)
    req = (slots.get("requirements") or "").strip()
    if req.lower() == "skip":
        req = ""
    return {
        "navigation": ", ".join(all_shots),
        "image_data": testcase_service.ocr_images(all_shots) if all_shots else "",
        "action_data": testcase_service.read_action_file(slots.get("_action_file")),
        "req": req,
    }


def _generate_recorded(slots):
    """Build context; if a TMT knowledge base was pulled, gap-analyse first —
    otherwise generate directly."""
    ctx = _build_ctx(slots)
    existing = (slots.get("_tmt") or {}).get("existing") or []
    if existing:
        return {"_gen_ctx": ctx, "_gap": testcase_service.gap_analysis(
            existing, ctx["action_data"], ctx["image_data"], ctx["req"])}
    resp = testcase_service.from_recorded(
        ctx["navigation"], ctx["image_data"], ctx["action_data"], ctx["req"])
    return {"_gen_ctx": ctx, "_tc_response": resp or ""}


def _resolve_gap(slots):
    """After the user sees the gap: approve → generate only the missing/replacement
    cases; decline → generate normally."""
    ctx = slots.get("_gen_ctx") or {}
    gap = slots.get("_gap") or {}
    if slots.get("approve_gap"):
        out = testcase_service.generate_targeted(
            gap.get("new", []), ctx.get("action_data"), ctx.get("image_data"), ctx.get("req"))
        for item in gap.get("update", []):
            repl = testcase_service.generate_replacement(
                item.get("title"), item.get("reason"),
                ctx.get("action_data"), ctx.get("image_data"), ctx.get("req"))
            if repl:
                out += "\n" + repl
        return {"_tc_response": (out or "").strip()}
    resp = testcase_service.from_recorded(
        ctx.get("navigation"), ctx.get("image_data"), ctx.get("action_data"), ctx.get("req"))
    return {"_tc_response": resp or ""}


_CAT_ICON = {"positive": "🟢", "negative": "🔴", "workflow": "🔵", "ui": "🟡",
             "edge case": "🟣", "backend": "🟢", "performance": "🟠",
             "accessibility": "🔴", "others": "⚪"}


def _category_summary(response):
    """Category-wise counts (like the panel) instead of dumping the raw table."""
    counts, total = testcase_service.category_counts(response)
    if total == 0:
        return None
    lines = "\n".join(
        f"- {_CAT_ICON.get(cat, '•')} **{cat.title()}** — {n}"
        for cat, n in sorted(counts.items(), key=lambda x: -x[1])
    )
    return f"🧪 **{total} test case(s) generated** across categories:\n\n{lines}"


def _show_gen(slots):
    """Status after generate: category counts, or the gap summary if TMT is in play."""
    if slots.get("_tc_response"):
        return _category_summary(slots["_tc_response"]) or \
            "⚠️ Generated a response but couldn't parse any test cases."
    gap = slots.get("_gap")
    if gap:
        lines = "\n".join(f"- {s}" for s in gap.get("new", [])[:15])
        return (f"📊 **Gap analysis** — {len(gap.get('new', []))} new, "
                f"{len(gap.get('update', []))} to replace, {len(gap.get('skip', []))} already covered.\n\n"
                f"**New scenarios I'd add:**\n{lines or '(none)'}")
    return "⚠️ I couldn't generate test cases from that input — try a clearer prompt and run again."


def _show_cases(slots):
    resp = slots.get("_tc_response")
    return _category_summary(resp) if resp else "⚠️ Nothing was generated from the gap analysis."


def _save_recorded(slots):
    return {"_tc_path": testcase_service.save_testcases(slots.get("_tc_response"))}


def _push_azure(slots):
    return {"_push_result": testcase_service.push_to_azure(slots.get("_tc_response"))}


def _push_status(slots):
    r = slots.get("_push_result") or {}
    msg = f"📤 Pushed **{len(r.get('created', []))}** test case(s) to Azure DevOps."
    if r.get("errors"):
        msg += f"\n\n⚠️ {len(r['errors'])} failed: " + "; ".join(str(e) for e in r["errors"][:5])
    return msg


def _testcase_complete(slots):
    src = slots.get("source", "?")
    if src == "recorded":
        if not slots.get("_tc_response"):
            return ("I couldn't generate test cases from that recording — add a clearer prompt "
                    "and say *generate test cases* again.")
        parts = ["✅ Test cases generated"]
        saved = slots.get("_tc_path")
        if slots.get("save_tc") and saved:
            parts.append(f" and saved to `{saved}`")
        pushed = slots.get("_push_result")
        if pushed:
            parts.append(f"; pushed {len(pushed.get('created', []))} to Azure DevOps")
        return "".join(parts) + ".\n\nNext: generate an automation script from these (coming soon)."
    if src == "document":
        return (
            f"📝 **(preview)** Document source captured (input: {slots.get('doc_kind', '—')}). "
            "Upload → extract → generate goes live next."
        )
    return "📋 **(preview)** TMT user-stories source captured. Full generation lands next."


TESTCASE = GuidedSkill(
    id="testcase",
    triggers=["test case", "test cases", "testcase", "testcases", "generate tests",
              "scenario", "scenarios"],
    description="Generate functional test cases from documents, recordings, or TMT stories.",
    steps=[
        step("source", "CHOICE",
             "Happy to help generate test cases. What should I work from?",
             options=[{"label": "📄 A document / wireframe", "value": "document"},
                      {"label": "🎬 A recorded user flow", "value": "recorded"},
                      {"label": "📋 User stories from a test-management tool", "value": "tmt"}]),
        # Recorded → surface the REAL recorder inline; flow advances once it's saved.
        embed("recording", "recorder",
              prompt="Great — let's record your flow. Open your app, record your journey, then save it:",
              condition=_recorded),
        # Auto-chain the recording's outputs (action file + this recording's screenshots).
        action("collect_recorded", _collect_recorded,
               status=lambda s: (f"📎 Using recording **{(s.get('recording') or {}).get('page', '?')}** — "
                                 f"action file + **{len(s.get('_rec_shots') or [])}** screenshot(s)."),
               condition=_recorded),
        # Quick thumbnail review of the auto-collected screenshots (deselect any).
        embed("shots_reviewed", "screenshot_review",
              prompt="Here are the screenshots from your recording — untick any you don't want:",
              condition=_recorded_has_shots),
        # Optional extra screenshots / wireframes.
        step("add_more", "CONFIRM", "Any additional screenshots or wireframes to add?",
             condition=_recorded),
        embed("extra_shots", "image_upload", prompt="Upload the extra images:",
              condition=_recorded_add_more),
        # Optional TMT knowledge base → gap analysis.
        step("use_tmt", "CONFIRM",
             "Import existing test cases from a TMT as a knowledge base (for gap analysis)?",
             condition=_recorded),
        embed("_tmt", "tmt_fetch",
              prompt="Connect a Test Management Tool and fetch existing test cases:",
              condition=_recorded_use_tmt),
        # Optional steering prompt (we already have rich context).
        step("requirements", "TEXT",
             "Any requirements or a prompt to steer generation? (type 'skip' if none)",
             condition=_recorded),
        # Generate — real backend. With a TMT base this returns a gap analysis first.
        action("generate_recorded", _generate_recorded, status=_show_gen, condition=_recorded),
        # Gap path: approve → generate only the missing/replacement cases.
        step("approve_gap", "CONFIRM",
             "Generate the new + replacement test cases from this gap analysis? "
             "(No = generate the full set instead)",
             condition=_gap_pending),
        action("resolve_gap", _resolve_gap, status=_show_cases, condition=_gap_answered),
        # Save.
        step("save_tc", "CONFIRM", "Save these test cases to Excel?", condition=_recorded_has_tc),
        action("save_recorded", _save_recorded,
               status=lambda s: f"💾 Saved to `{s.get('_tc_path')}`.",
               condition=lambda s: s.get("save_tc") is True),
        # Optional push back to Azure DevOps (only when Azure was the knowledge base).
        step("push_tmt", "CONFIRM", "Push these test cases to Azure DevOps as work items?",
             condition=_can_push),
        action("push_azure", _push_azure, status=_push_status,
               condition=lambda s: s.get("push_tmt") is True),
        # Document → (preview until next milestone)
        step("doc_kind", "CHOICE", "Where does the document live?",
             options=[{"label": "Upload a file", "value": "upload"},
                      {"label": "Azure Board work item", "value": "azure"},
                      {"label": "Jira issue", "value": "jira"}],
             condition=lambda s: s.get("source") == "document"),
    ],
    on_complete=_testcase_complete,
)


# ---------------------------------------------------------------- table ---
REGISTRY = {s.id: s for s in (HELP, LOCATOR, TESTCASE)}
DEFAULT_SKILL = "help"


def get(skill_id):
    return REGISTRY.get(skill_id, REGISTRY[DEFAULT_SKILL])
