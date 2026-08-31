"""
IQEA Mobile Automation — mobile_iqea.py
========================================
Complete Mobile Test Automation Platform (Streamlit UI)

Tab 1  →  Device & Connection    — Appium server, app config, device discovery, session
Tab 2  →  Record Actions         — Start/Stop recording, save .txt + screenshots, download
Tab 2B →  Test Case Generation   — Select recording → screenshots → requirements → LLM → Excel
Tab 3  →  Test Script Generation — Select test cases + recording → language → LLM → save script
"""

import json
import os
import time
from datetime import datetime

import streamlit as st

from utility_mobile import (
    ADBManager,
    AVDManager,
    ActionRecorder,
    AppiumManager,
    BrowserStackManager,
    MobileLogger,
    ScrcpyManager,
    ScriptExecutor,
    ScriptGenerator,
    device_label,
    generate_session_id,
)
from mobile_automation_helpers import (
    SCRIPTS_DIR,
    ActionFileManager,
    LLMClientWrapper,
    ScriptBuilder,
    TestCaseBuilder,
    save_recording_workflow,
    save_test_cases_to_excel,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="IQEA – Mobile Automation", page_icon="📱", layout="wide")


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

def _init():
    # Singleton backend objects
    if "logger"   not in st.session_state: st.session_state.logger   = MobileLogger()
    lg = st.session_state.logger
    if "adb"      not in st.session_state: st.session_state.adb      = ADBManager(lg)
    if "avd_mgr"  not in st.session_state: st.session_state.avd_mgr  = AVDManager(logger=lg)
    if "bs"       not in st.session_state: st.session_state.bs       = BrowserStackManager(logger=lg)
    if "appium"   not in st.session_state: st.session_state.appium   = AppiumManager(logger=lg)
    if "scrcpy"   not in st.session_state: st.session_state.scrcpy   = ScrcpyManager(lg)
    if "recorder" not in st.session_state: st.session_state.recorder = ActionRecorder(logger=lg)
    if "gen"      not in st.session_state: st.session_state.gen      = ScriptGenerator(lg)
    if "executor" not in st.session_state: st.session_state.executor = None
    if "llm"      not in st.session_state: st.session_state.llm      = LLMClientWrapper()

    defaults = {
        # ── Tab 1 ──────────────────────────────────────────────────
        "usb_devices":    [],
        "bs_devices":     [],
        "avd_booting":    False,   # True while waiting for emulator boot
        "selected_device": None,
        "session_id":     None,
        "app_path_input": "",
        "app_type":       "Native App",
        "bs_user":        "",
        "bs_key":         "",
        "bs_plan":        {},
        "bs_project":     "IQEA Mobile",
        "bs_build":       "Build 1",

        # ── Tab 2: Recording state machine ────────────────────────
        # rec_phase: "idle" | "recording" | "stopped" | "saved"
        "rec_phase":      "idle",
        "rec_filename":   "",
        "rec_save_result": {},   # {txt_file, json_file, screenshots_dir, error}

        # ── Tab 2B: Test Case Generation ──────────────────────────
        "tc_rec_file":       None,   # selected *_recordings.json filename
        "tc_rec_data":       None,   # loaded dict from recording JSON
        "tc_screenshots":    [],     # selected screenshot indices
        "tc_requirements":   "",     # user text area input
        "tc_generated":      [],     # list of parsed TC dicts from LLM
        "tc_base_filename":  "",     # base name used when saving
        "tc_saved_paths":    [],     # paths written to disk

        # ── Tab 3: Script Generation ──────────────────────────────
        "tsg_tc_file":       None,
        "tsg_rec_file":      None,
        "tsg_language":      "Python",
        "tsg_requirements":  "",
        "tsg_script":        "",
        "tsg_save_filename": "",

        # ── Tab 4: Execution ──────────────────────────────────────
        "exec_script_file":   "",    # path of script selected / auto-loaded
        "exec_output":        "",    # captured stdout+stderr from pytest run
        "exec_running":       False, # subprocess active flag
        "exec_returncode":    None,  # last pytest exit code
        "allure_proc":        None,  # subprocess handle for allure serve
        "allure_port":        56789, # port allure serve listens on
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init()

# Convenience aliases
lg       = st.session_state.logger
adb      = st.session_state.adb
bs       = st.session_state.bs
appium   = st.session_state.appium
scrcpy   = st.session_state.scrcpy
recorder = st.session_state.recorder
gen      = st.session_state.gen
llm      = st.session_state.llm

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📱 IQEA – Mobile Automation")

# Status bar
session_active = appium.session_id is not None
dev_name = (st.session_state.selected_device or {}).get("model", "—")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Appium Server", "🟢 Running"  if appium.is_server_running() else "🔴 Stopped")
c2.metric("Session",       "🟢 Active"   if session_active             else "⚪ None")
c3.metric("Device",        dev_name)
c4.metric("Actions",       len(recorder.actions))
st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab2b, tab3, tab4 = st.tabs([
    "1 · Device & Connection",
    "2 · Record Actions",
    "2B · Test Case Generation",
    "3 · Test Script Generation",
    "4 · Execute & Report",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Device & Connection
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    left1, right1 = st.columns(2)

    with left1:
        # ── Appium Server ──────────────────────────────────────────────────────
        st.subheader("Appium Server")
        a1, a2, a3 = st.columns([3, 1, 1])
        with a1:
            appium_url = st.text_input("URL", value=appium.base_url,
                                       placeholder="http://localhost:4723")
            if appium_url != appium.base_url:
                appium.base_url = appium_url.rstrip("/")
        with a2:
            if st.button("▶ Start"):
                with st.spinner("Starting…"):
                    appium.start_server()
                st.rerun()
        with a3:
            if appium.is_server_running(): st.success("✅ Up")
            else:                          st.error("❌ Down")

        if not appium.is_server_running():
            st.caption("`appium` — run this in a separate terminal to start the server")

        st.divider()

        # ── App Configuration ──────────────────────────────────────────────────
        st.subheader("App Configuration")
        app_type = st.radio(
            "Type", ["Native App", "Mobile Browser"], horizontal=True,
            index=0 if st.session_state.app_type == "Native App" else 1,
        )
        st.session_state.app_type = app_type

        if app_type == "Native App":
            st.session_state.app_path_input = st.text_input(
                "App Path / Package / BrowserStack URL",
                value=st.session_state.app_path_input,
                placeholder="com.example.app  |  /path/app.apk  |  bs://abc123",
            )
        else:
            b1, b2 = st.columns(2)
            with b1: st.selectbox("Browser", ["Chrome", "Safari", "Firefox"])
            with b2: st.text_input("Start URL", placeholder="https://example.com")

        st.divider()

        # ── BrowserStack ───────────────────────────────────────────────────────
        st.subheader("BrowserStack (Cloud Testing)")
        st.caption("Run tests on real cloud devices — no local device needed.")

        bs_u = st.text_input("BS Username", value=st.session_state.bs_user, key="bs_user_input")
        bs_k = st.text_input("BS Access Key", value=st.session_state.bs_key,
                             type="password", key="bs_key_input")

        bv1, bv2, bv3 = st.columns(3)
        with bv1:
            if st.button("✅ Validate", use_container_width=True):
                bs.set_credentials(bs_u, bs_k)
                st.session_state.bs_user = bs_u
                st.session_state.bs_key  = bs_k
                result = bs.validate_credentials()
                if result["valid"]:
                    plan = result.get("plan", {})
                    st.session_state.bs_plan = plan
                    st.success("Valid ✓")
                else:
                    st.error(f"Invalid: {result.get('error','')}")
        with bv2:
            if st.button("📱 Fetch Devices", use_container_width=True):
                bs.set_credentials(bs_u, bs_k)
                st.session_state.bs_user = bs_u
                st.session_state.bs_key  = bs_k
                with st.spinner("Fetching…"):
                    st.session_state.bs_devices = bs.get_devices()
                st.rerun()
        with bv3:
            st.link_button("🔗 BS Dashboard",
                           "https://app-automate.browserstack.com/dashboard",
                           use_container_width=True)

        # Plan info
        if st.session_state.get("bs_plan"):
            plan = st.session_state.bs_plan
            p1, p2, p3 = st.columns(3)
            p1.metric("Plan", plan.get("plan_name", "Trial"))
            p2.metric("Parallel Sessions",
                      f"{plan.get('parallel_sessions_running', 0)} / "
                      f"{plan.get('parallel_sessions_max_allowed', 1)}")
            p3.metric("Sessions Used", plan.get("automate_sessions_used", "—"))

        st.divider()

        # ── App Upload to BrowserStack ─────────────────────────────────────────
        st.markdown("#### Upload App to BrowserStack")
        st.caption("Upload your APK/IPA once — use the `bs://` URL in App Path above.")

        uploaded_file = st.file_uploader(
            "Choose APK / IPA",
            type=["apk", "ipa"],
            key="bs_app_upload",
        )
        custom_id_input = st.text_input(
            "Custom ID (optional — reuse same bs:// URL on re-upload)",
            placeholder="e.g. MyApp_Android",
            key="bs_custom_id",
        )

        if uploaded_file:
            up1, up2 = st.columns([2, 1])
            with up1:
                st.caption(f"Ready to upload: **{uploaded_file.name}** "
                           f"({uploaded_file.size // 1024} KB)")
            with up2:
                if st.button("⬆ Upload to BS", type="primary", use_container_width=True):
                    if not bs_u or not bs_k:
                        st.error("Enter BS credentials first.")
                    else:
                        bs.set_credentials(bs_u, bs_k)
                        # Save temp file then upload
                        import tempfile
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
                        ) as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name
                        with st.spinner(f"Uploading {uploaded_file.name}…"):
                            res = bs.upload_app(tmp_path, custom_id=custom_id_input.strip())
                        os.unlink(tmp_path)
                        if res["ok"]:
                            st.session_state.app_path_input = res["app_url"]
                            st.success(f"✅ Uploaded! `{res['app_url']}`")
                            st.info("App Path above has been updated automatically.")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {res['error']}")

        # Show existing bs:// URL if already set
        if st.session_state.app_path_input.startswith("bs://"):
            st.success(f"Current app: `{st.session_state.app_path_input}`")

    with right1:
        # ── Device Discovery ───────────────────────────────────────────────────
        st.subheader("Device Discovery")
        d1, d2, d3 = st.columns(3)
        with d1:
            if st.button("🔌 Scan USB"):
                with st.spinner("Scanning…"):
                    st.session_state.usb_devices = adb.scan_all()
                st.rerun()
        with d2:
            if st.button("➕ Add Emulator"):
                st.session_state.usb_devices.append(ADBManager.make_emulator_entry())
                st.rerun()
        with d3:
            if st.button("🔄 Restart ADB"):
                with st.spinner("Restarting…"):
                    adb.restart_adb_server()
                st.rerun()

        all_devices = st.session_state.usb_devices + st.session_state.bs_devices
        if all_devices:
            labels = [device_label(d) for d in all_devices]
            chosen = st.selectbox("Select Device", labels)
            st.session_state.selected_device = all_devices[labels.index(chosen)]
            dev = st.session_state.selected_device
            st.info(f"**{dev['model']}** · {dev['os']} · {dev['source'].upper()}")
        else:
            st.info("No devices found. Click Scan USB or launch an AVD below.")

        st.divider()

        # ── Android Emulator (AVD) ─────────────────────────────────────────────
        avd_mgr = st.session_state.avd_mgr
        st.subheader("Android Emulator (AVD)")
        st.caption("Launch Android Studio virtual devices directly from here.")

        if not avd_mgr.is_available():
            st.warning(
                "⚠️ `emulator` binary not found.\n\n"
                "Install **Android Studio** (free) and create an AVD via its AVD Manager, "
                "or install the [Android SDK command-line tools](https://developer.android.com/studio#command-tools) "
                "and ensure `ANDROID_HOME/emulator` is on PATH.\n\n"
                f"Detected SDK path: `{avd_mgr.sdk_path or 'not found'}`"
            )
        else:
            sdk_display = avd_mgr.sdk_path or "on PATH"
            st.caption(f"SDK: `{sdk_display}`")

            avd_list = avd_mgr.list_avds()
            running_serials = avd_mgr.get_running_serials()

            if not avd_list:
                st.info(
                    "No AVDs found. Open **Android Studio → Device Manager** "
                    "and create a virtual device first."
                )
            else:
                sel_avd = st.selectbox("Select AVD", avd_list, key="sel_avd")
                is_running = len(running_serials) > 0

                av1, av2, av3 = st.columns(3)
                with av1:
                    if st.button("▶ Launch AVD", use_container_width=True,
                                 disabled=is_running):
                        if avd_mgr.launch_avd(sel_avd):
                            st.session_state.avd_booting = True
                            st.success(f"✅ Launching **{sel_avd}**…")
                        else:
                            st.error("Failed to launch. Check system log.")
                        st.rerun()

                with av2:
                    if st.button("⟳ Check Boot", use_container_width=True):
                        serials = avd_mgr.get_running_serials()
                        if serials and avd_mgr.is_booted(serials[0]):
                            st.session_state.avd_booting = False
                            st.success("✅ Boot complete!")
                        elif serials:
                            st.info("Emulator detected but still booting…")
                        else:
                            st.warning("Emulator not detected yet. Wait 30s and retry.")
                        st.rerun()

                with av3:
                    if st.button("⏹ Stop", use_container_width=True,
                                 disabled=not is_running):
                        for s in running_serials:
                            avd_mgr.stop(s)
                        st.session_state.avd_booting = False
                        st.rerun()

                if is_running:
                    for serial in running_serials:
                        booted = avd_mgr.is_booted(serial)
                        label  = "✅ Ready" if booted else "⏳ Booting…"
                        st.success(f"{label} — `{serial}`")

                    if st.button("➕ Add Emulator to Device List", use_container_width=True):
                        existing = {d["serial"] for d in st.session_state.usb_devices}
                        added = 0
                        for serial in running_serials:
                            if serial not in existing:
                                info = avd_mgr.get_device_info(serial)
                                st.session_state.usb_devices.append(info)
                                added += 1
                        if added:
                            st.success(f"✅ Added {added} emulator(s) to the device list.")
                        else:
                            st.info("Already in device list.")
                        st.rerun()

                elif st.session_state.avd_booting:
                    st.info("⏳ Emulator starting — takes 30–60 s. Click **Check Boot** to check.")

        st.divider()

        # ── Session ────────────────────────────────────────────────────────────
        st.subheader("Session")

        # BrowserStack project/build fields when BS device is selected
        sel_dev = st.session_state.selected_device or {}
        if sel_dev.get("source") == "browserstack":
            s1, s2 = st.columns(2)
            with s1:
                st.session_state.bs_project = st.text_input(
                    "Project Name", value=st.session_state.bs_project, key="bs_proj"
                )
            with s2:
                st.session_state.bs_build = st.text_input(
                    "Build Name", value=st.session_state.bs_build, key="bs_bld"
                )
            st.caption("⚡ BrowserStack session — no local Appium server required")

        if not appium.session_id:
            if st.button("⚡ Connect & Start Session", type="primary",
                         use_container_width=True):
                dev = st.session_state.selected_device
                if not dev:
                    st.warning("Select a device first.")
                else:
                    with st.spinner("Creating session… (may take 30-60s)"):
                        result = appium.create_session(
                            device          = dev,
                            app_path        = st.session_state.app_path_input,
                            app_type        = "native" if app_type == "Native App" else "browser",
                            bs_user         = st.session_state.bs_user,
                            bs_key          = st.session_state.bs_key,
                            bs_project      = st.session_state.bs_project,
                            bs_build        = st.session_state.bs_build,
                            bs_session_name = f"IQEA-{dev.get('model','')}",
                        )
                    if result["ok"]:
                        recorder.appium = appium
                        st.session_state.session_id = generate_session_id()
                        st.session_state.executor   = ScriptExecutor(appium, lg)
                        st.success(f"✅ Session started: `{appium.session_id}`")
                        if dev.get("source") == "browserstack":
                            st.info("📊 View session live at https://app-automate.browserstack.com/dashboard")
                        st.rerun()
                    else:
                        st.error(result.get("error", "Unknown error"))
        else:
            dev = st.session_state.selected_device or {}
            st.success(
                f"✅ **{dev.get('model','?')}** connected\n\n"
                f"Appium: `{appium.session_id}`\n\n"
                f"IQEA: `{st.session_state.session_id}`"
            )
            if st.button("🔌 Disconnect", use_container_width=True):
                appium.delete_session()
                recorder.recording = False
                st.rerun()

    # System Log
    if lg.entries:
        st.divider()
        with st.expander("System Log", expanded=False):
            st.code(
                "\n".join(
                    f"[{e['ts']}]  {e['level'].upper():<4}  {e['msg']}"
                    for e in lg.tail(40)
                ),
                language="text",
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Record Actions
# State machine: rec_phase = "idle" | "recording" | "stopped" | "saved"
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not appium.session_id:
        st.warning("⚠️ Connect a device in **Tab 1** first.")
    else:
        phase = st.session_state.rec_phase

        # ── IDLE ──────────────────────────────────────────────────────────────
        if phase == "idle":
            st.subheader("Recording")
            st.caption(
                "Click **Start Recording**, then interact naturally with your phone. "
                "Every tap, type, and scroll is auto-detected with a screenshot."
            )
            if st.button("⏺ Start Recording", type="primary"):
                recorder.start()
                st.session_state.rec_phase = "recording"
                st.rerun()

        # ── RECORDING ─────────────────────────────────────────────────────────
        elif phase == "recording":
            st.success(
                f"🔴 **Recording…** — {len(recorder.actions)} action(s) captured so far "
                "— interact with your phone"
            )

            rc1, rc2 = st.columns([1, 5])
            with rc1:
                if st.button("⏹ Stop Recording", use_container_width=True):
                    recorder.stop()
                    st.session_state.rec_phase = "stopped"
                    st.rerun()
            with rc2:
                if st.button("🗑 Clear Actions", use_container_width=True):
                    recorder.clear()
                    st.rerun()

            # Live action feed
            if recorder.actions:
                st.divider()
                st.subheader(f"Captured Actions ({len(recorder.actions)})")
                for a in recorder.actions[-10:]:   # Show last 10 to keep UI fast
                    badge = {
                        "tap": "🟢 TAP", "input": "🔵 INPUT",
                        "swipe": "🟡 SWIPE", "scroll": "🟤 SCROLL",
                    }.get(a["type"], "⚪")
                    c1, c2, c3 = st.columns([1, 3, 2])
                    with c1:
                        st.write(f"**#{a['seq']:02d}** {badge}")
                        st.caption(a["ts"])
                    with c2:
                        st.write(f"**{a['label']}**")
                        if a.get("xpath"):
                            st.code(a["xpath"], language="text")
                        if a.get("value"):
                            st.caption(f"Value: `{a['value']}`")
                    with c3:
                        if a.get("screenshot_b64"):
                            st.image(
                                f"data:image/png;base64,{a['screenshot_b64']}",
                                width=160,
                            )
                    st.divider()

            # Auto-refresh every 2 s while recording
            time.sleep(2)
            st.rerun()

        # ── STOPPED — ask for filename, then save ─────────────────────────────
        elif phase == "stopped":
            actions = list(recorder.actions)
            st.info(f"✅ Recording stopped — **{len(actions)} action(s)** captured")

            # Compact action summary
            if actions:
                st.subheader("Captured Actions")
                rows = [
                    {
                        "#": a["seq"],
                        "Time": a["ts"],
                        "Type": a["type"].upper(),
                        "Label": a["label"],
                        "XPath": a.get("xpath", ""),
                        "Value": a.get("value", ""),
                    }
                    for a in actions
                ]
                st.dataframe(rows, use_container_width=True)

            st.divider()
            st.subheader("💾 Save Recording")
            st.caption(
                "Enter a filename and click **Save**. "
                "The recording will be saved as a **.txt** file + screenshots "
                "in the `output/mobile_recordings/` folder."
            )

            dev = st.session_state.selected_device or {}
            default_fname = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            fname = st.text_input(
                "File Name (no extension)",
                value=st.session_state.rec_filename or default_fname,
                placeholder="my_login_flow",
            )
            st.session_state.rec_filename = fname

            sc1, sc2 = st.columns([1, 3])
            with sc1:
                if st.button("💾 Save Recording", type="primary",
                             use_container_width=True, disabled=not fname.strip()):
                    if not fname.strip():
                        st.error("Please enter a filename.")
                    else:
                        with st.spinner("Saving…"):
                            result = save_recording_workflow(
                                actions    = actions,
                                device     = dev,
                                session_id = st.session_state.session_id or "",
                                filename   = fname.strip(),
                            )
                        if result["error"]:
                            st.error(f"❌ Save failed: {result['error']}")
                        else:
                            st.session_state.rec_save_result = result
                            st.session_state.rec_phase = "saved"
                            st.rerun()
            with sc2:
                if st.button("🔄 Record Again (discard)", use_container_width=True):
                    recorder.clear()
                    st.session_state.rec_phase = "idle"
                    st.session_state.rec_filename = ""
                    st.rerun()

        # ── SAVED — show download + summary ───────────────────────────────────
        elif phase == "saved":
            result = st.session_state.rec_save_result or {}
            fname  = st.session_state.rec_filename

            st.success(f"✅ Recording **{fname}** saved successfully!")

            # Show saved file paths
            st.info(
                f"📁 **Files saved:**\n"
                f"- {result.get('txt_file', '—')}\n"
                f"- {result.get('json_file', '—')}\n"
                f"- Screenshots → `{result.get('screenshots_dir', '—')}`"
            )

            # Download .txt button (reads saved file)
            txt_path = result.get("txt_file")
            if txt_path and os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    txt_content = f.read()
                st.download_button(
                    label           = f"⬇ Download {fname}.txt",
                    data            = txt_content,
                    file_name       = f"{fname}.txt",
                    mime            = "text/plain",
                    use_container_width = True,
                )

            st.divider()

            # Summary table
            actions_recorded = list(recorder.actions)
            if actions_recorded:
                st.subheader("Recorded Actions Summary")
                st.dataframe(
                    [
                        {
                            "#": a["seq"], "Type": a["type"].upper(),
                            "Label": a["label"], "XPath": a.get("xpath", ""),
                            "Value": a.get("value", ""),
                        }
                        for a in actions_recorded
                    ],
                    use_container_width=True,
                )

            st.caption(
                "💡 Go to **Tab 2B** to generate test cases from this recording, "
                "or **Tab 3** to generate executable scripts."
            )

            if st.button("🔄 Record Again (clear current)", use_container_width=True):
                recorder.clear()
                st.session_state.rec_phase = "idle"
                st.session_state.rec_filename = ""
                st.session_state.rec_save_result = {}
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2B — Test Case Generation (LLM-driven)
# Flow: select recording → select screenshots → describe requirements
#       → LLM generate → show by category → save Excel (single or separate)
# ══════════════════════════════════════════════════════════════════════════════
with tab2b:
    st.subheader("📋 AI Test Case Generation")
    st.caption(
        "Select a saved recording, choose relevant screenshots, describe your requirements, "
        "then let AI generate comprehensive test cases for you."
    )

    recording_files = ActionFileManager.list_recording_files()

    if not recording_files:
        st.info(
            "No saved recordings found.\n\n"
            "Go to **Tab 2**, record your actions, then save the recording."
        )
    else:
        # ── Step 1: Select Recording File ─────────────────────────────────────
        st.markdown("### Step 1 · Select Recording")
        selected_rec = st.selectbox(
            "Choose a saved recording",
            recording_files,
            key="tab2b_rec_select",
        )

        if selected_rec != st.session_state.tc_rec_file:
            # Reset state when a different file is selected
            st.session_state.tc_rec_file    = selected_rec
            st.session_state.tc_rec_data    = None
            st.session_state.tc_screenshots = []
            st.session_state.tc_generated   = []

        if st.session_state.tc_rec_file:
            # Load recording data
            if st.session_state.tc_rec_data is None:
                st.session_state.tc_rec_data = ActionFileManager.load_recording(
                    st.session_state.tc_rec_file
                )

            rec_data = st.session_state.tc_rec_data
            if not rec_data:
                st.error(f"❌ Could not load recording: {st.session_state.tc_rec_file}")
            else:
                actions     = rec_data.get("actions", [])
                device_info = rec_data.get("device", {})
                app_name    = device_info.get("model", "Mobile App")

                st.success(
                    f"✅ Loaded **{len(actions)} actions** from `{st.session_state.tc_rec_file}`  "
                    f"| Device: **{app_name}**"
                )

                # ── Step 2: Screenshot Mode Radio ──────────────────────────────
                st.markdown("### Step 2 · Screenshot Mode")
                screenshot_mode = st.radio(
                    "How should AI generate test cases?",
                    options=["Use Screenshots (Tesseract OCR)", "Actions Only (no screenshots)"],
                    index=0,
                    horizontal=True,
                    key="tab2b_ss_mode",
                )
                use_screenshots = screenshot_mode == "Use Screenshots (Tesseract OCR)"

                screenshot_paths = ActionFileManager.get_screenshot_paths(
                    st.session_state.tc_rec_file
                )

                # ── Step 3: Screenshot selection (only shown when mode = screenshots) ─
                checkbox_states = {}
                if use_screenshots:
                    if not screenshot_paths and not any(a.get("screenshot_b64") for a in actions):
                        st.warning("⚠️ No screenshots found for this recording. Switch to **Actions Only** mode.")
                    else:
                        st.markdown("### Step 3 · Select Screenshots")
                        st.caption(
                            "Check the screenshots to include. "
                            "Tesseract will extract UI text from selected images only when you click **Generate**."
                        )

                        # Show thumbnails + checkboxes (3 per row)
                        cols_per_row = 3
                        total_items  = max(len(screenshot_paths), len(actions))

                        for row_start in range(0, total_items, cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                idx = row_start + j
                                if idx >= total_items:
                                    break
                                action = actions[idx] if idx < len(actions) else {}
                                with col:
                                    if idx < len(screenshot_paths):
                                        fname = os.path.basename(screenshot_paths[idx])
                                        # Thumbnail — small size so rendering is fast
                                        try:
                                            st.image(screenshot_paths[idx], width=160)
                                        except Exception:
                                            st.caption("_(no preview)_")
                                    elif action.get("screenshot_b64"):
                                        fname = f"action_{idx+1:03d}.png"
                                        try:
                                            st.image(
                                                f"data:image/png;base64,{action['screenshot_b64']}",
                                                width=160,
                                            )
                                        except Exception:
                                            st.caption("_(no preview)_")
                                    else:
                                        fname = f"action_{idx+1:03d}.png"
                                        st.caption("_(no screenshot)_")

                                    checkbox_states[idx] = st.checkbox(
                                        f"Step {idx+1}: [{action.get('type','?').upper()}] "
                                        f"{action.get('label','N/A')[:25]}",
                                        key=f"tab2b_ss_{idx}",
                                    )
                else:
                    st.info("ℹ️ Test cases will be generated from recorded actions only — no screenshot processing.")

                # ── Step 4: Describe Requirements ──────────────────────────────
                step_num = "4" if use_screenshots else "3"
                st.markdown(f"### Step {step_num} · Describe Test Requirements")
                user_req = st.text_area(
                    "What should the AI focus on?",
                    value=st.session_state.tc_requirements,
                    placeholder=(
                        "• Test positive scenarios with valid credentials\n"
                        "• Test negative scenarios: wrong password, empty fields\n"
                        "• Test edge cases: very long inputs, special characters\n"
                        "• Verify all error messages are displayed correctly"
                    ),
                    height=130,
                    key="tab2b_requirements",
                )
                st.session_state.tc_requirements = user_req

                # ── Step 5: Generate ────────────────────────────────────────────
                step_num2 = "5" if use_screenshots else "4"
                st.markdown(f"### Step {step_num2} · Generate Test Cases")

                if st.button("🚀 Generate Test Cases with AI", type="primary",
                             use_container_width=True, key="tab2b_generate_btn"):

                    selected_indices = [idx for idx, checked in checkbox_states.items() if checked]
                    st.session_state.tc_screenshots = selected_indices

                    if not user_req.strip():
                        st.error("⚠️ Please describe your test requirements.")
                    elif use_screenshots and not selected_indices:
                        st.error("⚠️ Please select at least one screenshot, or switch to **Actions Only** mode.")
                    else:
                        image_extracted_text = ""

                        if use_screenshots and selected_indices:
                            with st.spinner(f"🔍 Extracting text from {len(selected_indices)} screenshot(s) using Tesseract…"):
                                image_extracted_text = TestCaseBuilder.extract_text_from_screenshots(
                                    screenshot_paths = screenshot_paths,
                                    selected_indices = selected_indices,
                                    actions          = actions,
                                )

                            if image_extracted_text.strip():
                                with st.expander(f"📄 OCR Extracted Text ({len(selected_indices)} screenshot(s))", expanded=False):
                                    st.code(image_extracted_text, language="text")
                            else:
                                st.warning("⚠️ Tesseract could not extract text from selected screenshots. Continuing with actions only.")

                        with st.spinner("🤖 Sending to AI — generating test cases…"):
                            prompt = TestCaseBuilder.build_prompt(
                                actions                     = actions,
                                selected_screenshot_indices = selected_indices,
                                user_description            = user_req,
                                app_name                    = app_name,
                                image_extracted_text        = image_extracted_text,
                            )
                            response = llm.query(prompt)

                        if response:
                            parsed = TestCaseBuilder.parse_json_response(response)
                            if parsed:
                                st.session_state.tc_generated = parsed
                                st.rerun()
                            else:
                                st.error(
                                    "❌ AI responded but test cases could not be parsed. "
                                    "Raw response shown below:"
                                )
                                st.code(response, language="text")
                        else:
                            st.error(
                                "❌ LLM call failed. "
                                "Check AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT env vars."
                            )

                # ── Step 5: Display + Save Generated Test Cases ────────────────
                if st.session_state.tc_generated:
                    test_cases = st.session_state.tc_generated

                    st.divider()
                    st.subheader(f"Generated Test Cases — {len(test_cases)} total")

                    # Category summary metrics
                    cat_counts: dict = {}
                    for tc in test_cases:
                        cat = tc.get("category", "Other")
                        cat_counts[cat] = cat_counts.get(cat, 0) + 1

                    metric_cols = st.columns(len(cat_counts) + 1)
                    for col, (cat, cnt) in zip(metric_cols, cat_counts.items()):
                        col.metric(cat, cnt)
                    metric_cols[-1].metric("Total", len(test_cases))

                    # Detailed table
                    with st.expander("📄 View All Test Cases", expanded=True):
                        for tc in test_cases:
                            with st.container():
                                h1, h2, h3, h4 = st.columns([2, 2, 2, 1])
                                h1.markdown(
                                    f"**{tc.get('tc_id','')}** — {tc.get('tc_name','')}"
                                )
                                h2.caption(f"Category: **{tc.get('category','')}**")
                                h3.caption(f"Type: **{tc.get('type','')}**")
                                h4.caption(f"Priority: **{tc.get('priority','')}**")

                                st.caption(
                                    f"_Precondition:_ {tc.get('precondition','—')}"
                                )

                                steps = tc.get("steps", [])
                                if steps:
                                    step_data = [
                                        {
                                            "Step": s.get("step_no", i + 1),
                                            "Action": s.get("step_desc", ""),
                                            "Expected": s.get("expected", ""),
                                        }
                                        for i, s in enumerate(steps)
                                    ]
                                    st.dataframe(step_data, use_container_width=True)

                                st.divider()

                    # ── Save Section ───────────────────────────────────────────
                    st.subheader("💾 Save Test Cases")

                    save_col1, save_col2 = st.columns(2)
                    with save_col1:
                        tc_filename = st.text_input(
                            "Save filename (no extension)",
                            value=(
                                st.session_state.tc_base_filename
                                or f"testcases_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            ),
                            key="tab2b_tc_filename",
                        )
                        st.session_state.tc_base_filename = tc_filename

                    with save_col2:
                        save_mode = st.radio(
                            "Save mode",
                            ["Single Excel (all in one sheet)", "Separate Excel (one per test case)"],
                            horizontal=False,
                        )

                    sv1, sv2, sv3 = st.columns(3)

                    with sv1:
                        if st.button("💾 Save to Excel", type="primary",
                                     use_container_width=True, disabled=not tc_filename.strip()):
                            mode = "single" if "Single" in save_mode else "separate"
                            with st.spinner("Saving Excel…"):
                                saved = save_test_cases_to_excel(
                                    test_cases = test_cases,
                                    filename   = tc_filename.strip(),
                                    mode       = mode,
                                )
                            if saved:
                                st.session_state.tc_saved_paths = saved
                                st.success(
                                    f"✅ Saved {len(saved)} file(s) to `output/mobile_test_cases/`"
                                )
                                for p in saved:
                                    st.caption(f"  → {os.path.basename(p)}")
                            else:
                                st.error("❌ Save failed — check openpyxl is installed.")

                    with sv2:
                        # Download all TCs as JSON
                        st.download_button(
                            "⬇ Download JSON",
                            data      = json.dumps(test_cases, indent=2, ensure_ascii=False),
                            file_name = f"{tc_filename or 'testcases'}.json",
                            mime      = "application/json",
                            use_container_width=True,
                        )

                    with sv3:
                        if st.button("🔄 Generate Testcases Again", use_container_width=True):
                            st.session_state.tc_generated = []
                            st.rerun()

                    # Inline download for each saved Excel file
                    if st.session_state.tc_saved_paths:
                        st.markdown("**Download saved files:**")
                        for path in st.session_state.tc_saved_paths:
                            if os.path.exists(path):
                                with open(path, "rb") as f:
                                    st.download_button(
                                        label           = f"⬇ {os.path.basename(path)}",
                                        data            = f.read(),
                                        file_name       = os.path.basename(path),
                                        mime            = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key             = f"dl_{os.path.basename(path)}",
                                        use_container_width=True,
                                    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Test Script Generation (LLM-driven)
# Flow: select test case file → select recording → language
#       → LLM generate → enter filename → save to SCRIPTS_DIR
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("⚙️ AI Test Script Generation")
    st.caption(
        "Select saved test cases and a recording, choose your language, "
        "then let AI generate a complete executable automation script."
    )

    tc_files  = ActionFileManager.list_test_case_files()
    rec_files = ActionFileManager.list_recording_files()

    if not tc_files:
        st.info(
            "No saved test case files found.\n\n"
            "Go to **Tab 2B**, generate test cases, then save them."
        )
    elif not rec_files:
        st.info(
            "No saved recording files found.\n\n"
            "Go to **Tab 2**, record actions, then save."
        )
    else:
        t3_left, t3_right = st.columns(2)

        # ── Step 1: Select Test Case File ─────────────────────────────────────
        with t3_left:
            st.markdown("### Step 1 · Select Test Cases")
            sel_tc_file = st.selectbox(
                "Choose saved test case file",
                tc_files,
                key="tab3_tc_select",
            )
            if sel_tc_file != st.session_state.tsg_tc_file:
                st.session_state.tsg_tc_file  = sel_tc_file
                st.session_state.tsg_script   = ""

            if st.session_state.tsg_tc_file:
                loaded_tcs = ActionFileManager.load_test_cases(st.session_state.tsg_tc_file)
                st.success(f"✅ {len(loaded_tcs)} test cases loaded")
                cat_counts: dict = {}
                for tc in loaded_tcs:
                    cat = tc.get("category", "Other")
                    cat_counts[cat] = cat_counts.get(cat, 0) + 1
                for cat, cnt in cat_counts.items():
                    st.caption(f"  • **{cat}**: {cnt}")

        # ── Step 2: Select Recording File ─────────────────────────────────────
        with t3_right:
            st.markdown("### Step 2 · Select Recording (for XPath locators)")
            sel_rec_file = st.selectbox(
                "Choose a saved recording",
                rec_files,
                key="tab3_rec_select",
            )
            if sel_rec_file != st.session_state.tsg_rec_file:
                st.session_state.tsg_rec_file = sel_rec_file
                st.session_state.tsg_script   = ""

            if st.session_state.tsg_rec_file:
                rec_data_t3 = ActionFileManager.load_recording(st.session_state.tsg_rec_file)
                if rec_data_t3:
                    actions_t3 = rec_data_t3.get("actions", [])
                    st.success(f"✅ {len(actions_t3)} actions loaded")
                else:
                    st.error("Could not load recording.")
                    actions_t3 = []

        st.divider()

        # ── Step 3: Language + Options ─────────────────────────────────────────
        st.markdown("### Step 3 · Language & Options")
        lang_col, req_col = st.columns([1, 2])

        with lang_col:
            language = st.selectbox(
                "Target Language",
                list(ScriptBuilder.LANGUAGE_MAP.keys()),
                index=list(ScriptBuilder.LANGUAGE_MAP.keys()).index(
                    st.session_state.tsg_language
                ),
                key="tab3_language",
            )
            st.session_state.tsg_language = language
            ext = ScriptBuilder.get_extension(language)
            st.caption(f"Output extension: **`.{ext}`**")

        with req_col:
            extra_req = st.text_area(
                "Additional requirements (optional)",
                value=st.session_state.tsg_requirements,
                placeholder=(
                    "• Use Page Object Model pattern\n"
                    "• Add Allure reporting annotations\n"
                    "• Use explicit waits of 10 seconds"
                ),
                height=100,
                key="tab3_requirements",
            )
            st.session_state.tsg_requirements = extra_req

        # ── Step 4: Generate ───────────────────────────────────────────────────
        st.markdown("### Step 4 · Generate Script")

        if st.button("🚀 Generate Script with AI", type="primary",
                     use_container_width=True):
            tcs   = ActionFileManager.load_test_cases(st.session_state.tsg_tc_file or "")
            r_dat = ActionFileManager.load_recording(st.session_state.tsg_rec_file or "")
            acts  = (r_dat or {}).get("actions", [])

            if not tcs:
                st.error("⚠️ No test cases loaded. Check Step 1.")
            elif not acts:
                st.error("⚠️ No actions loaded. Check Step 2.")
            else:
                with st.spinner(f"🤖 Generating {language} script…"):
                    prompt = ScriptBuilder.build_prompt(
                        test_cases          = tcs,
                        actions             = acts,
                        language            = language,
                        custom_requirements = extra_req,
                    )
                    generated = llm.query(prompt)

                if generated:
                    st.session_state.tsg_script = generated
                    st.rerun()
                else:
                    st.error(
                        "❌ LLM call failed. "
                        "Check AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT."
                    )

        # ── Step 5: Show Generated Script + Save ──────────────────────────────
        if st.session_state.tsg_script:
            st.divider()
            st.subheader(f"Generated {language} Script")

            lang_syntax = {
                "Python": "python", "Java": "java",
                "JavaScript": "javascript", "C#": "csharp",
                "C++": "cpp", "Ruby": "ruby", "Robot Framework": "text",
            }
            st.code(
                st.session_state.tsg_script,
                language=lang_syntax.get(language, "text"),
            )

            st.markdown("### Step 5 · Save Script")
            sav1, sav2 = st.columns(2)

            with sav1:
                save_fname = st.text_input(
                    "Script filename (no extension)",
                    value=(
                        st.session_state.tsg_save_filename
                        or f"test_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ),
                    key="tab3_save_fname",
                )
                st.session_state.tsg_save_filename = save_fname

                if st.button("💾 Save Script", type="primary",
                             use_container_width=True, disabled=not save_fname.strip()):
                    if save_fname.strip():
                        out_path = os.path.join(
                            SCRIPTS_DIR,
                            f"{save_fname.strip()}.{ext}",
                        )
                        try:
                            with open(out_path, "w", encoding="utf-8") as f:
                                f.write(st.session_state.tsg_script)
                            st.success(f"✅ Saved: `{out_path}`")
                        except Exception as e:
                            st.error(f"❌ Save failed: {e}")

            with sav2:
                st.download_button(
                    label           = f"⬇ Download .{ext}",
                    data            = st.session_state.tsg_script,
                    file_name       = f"{save_fname or 'script'}.{ext}",
                    mime            = "text/plain",
                    use_container_width=True,
                )

            if st.button("🔄 Generate Testascript Again", use_container_width=True):
                st.session_state.tsg_script       = ""
                st.session_state.tsg_save_filename = ""
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Execute & Report
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    import subprocess
    import sys
    import glob as _glob
    import re as _re

    st.subheader("▶ Execute & Report")

    ALLURE_RESULTS_DIR = os.path.join(os.path.dirname(SCRIPTS_DIR), "allure-results")
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)

    # ── Script selector ────────────────────────────────────────────────────
    script_files = sorted(
        _glob.glob(os.path.join(SCRIPTS_DIR, "*.py")),
        key=os.path.getmtime, reverse=True,
    )

    if not script_files:
        st.info("No scripts found. Go to **Tab 3**, generate and save a script first.")
    else:
        if not st.session_state.exec_script_file or \
                st.session_state.exec_script_file not in script_files:
            st.session_state.exec_script_file = script_files[0]

        sel_script = st.selectbox(
            "Select script to run",
            script_files,
            index=script_files.index(st.session_state.exec_script_file),
            format_func=os.path.basename,
            key="exec_script_select",
        )
        st.session_state.exec_script_file = sel_script

        with st.expander(f"📄 Script Preview — {os.path.basename(sel_script)}", expanded=False):
            try:
                with open(sel_script, encoding="utf-8") as f:
                    st.code(f.read(), language="python")
            except Exception as e:
                st.error(f"Could not read script: {e}")

        st.divider()

        # ══════════════════════════════════════════════════════════════════
        # EXECUTION TARGET: Local USB  or  BrowserStack
        # ══════════════════════════════════════════════════════════════════
        exec_target = st.radio(
            "Run on",
            ["💻 Local Device (USB/Emulator)", "☁ BrowserStack"],
            horizontal=True,
            key="exec_target",
        )
        run_on_bs = exec_target == "☁ BrowserStack"

        # ── BrowserStack config panel ──────────────────────────────────────
        if run_on_bs:
            st.markdown("#### BrowserStack Configuration")

            bs_creds_ok = bool(st.session_state.bs_user and st.session_state.bs_key)
            if not bs_creds_ok:
                st.warning("⚠️ BrowserStack credentials not set. Go to **Tab 1** and validate first.")

            bc1, bc2 = st.columns(2)
            with bc1:
                # Device selection from fetched BS devices
                bs_devs = st.session_state.bs_devices
                if bs_devs:
                    bs_dev_labels = [f"{d['model']} ({d['os']})" for d in bs_devs]
                    bs_sel_idx = st.selectbox(
                        "Target Device", range(len(bs_dev_labels)),
                        format_func=lambda i: bs_dev_labels[i],
                        key="exec_bs_device_idx",
                    )
                    bs_target_dev = bs_devs[bs_sel_idx]
                else:
                    st.caption("No BS devices loaded — go to Tab 1 → Fetch Devices")
                    bs_target_dev = {}

                bs_app_url = st.text_input(
                    "App URL (bs://...)",
                    value=st.session_state.app_path_input
                          if st.session_state.app_path_input.startswith("bs://") else "",
                    placeholder="bs://abc1234def...",
                    key="exec_bs_app_url",
                )

            with bc2:
                bs_proj = st.text_input("Project", value=st.session_state.bs_project, key="exec_bs_proj")
                bs_bld  = st.text_input("Build",   value=st.session_state.bs_build,   key="exec_bs_bld")
                bs_sess = st.text_input(
                    "Session Name",
                    value=f"IQEA-{datetime.now().strftime('%Y%m%d-%H%M')}",
                    key="exec_bs_sess",
                )

            st.caption(
                "Script caps will be **patched automatically** before running — "
                "original file is unchanged."
            )
            st.link_button(
                "📊 Open BS Dashboard",
                "https://app-automate.browserstack.com/dashboard",
                use_container_width=False,
            )
            st.divider()

        # ── Run / Stop / Report buttons ────────────────────────────────────
        run_col, stop_col, report_col = st.columns([2, 1, 2])

        with run_col:
            run_clicked = st.button(
                "▶ Run on BrowserStack" if run_on_bs else "▶ Run on Local Device",
                type="primary", use_container_width=True,
                disabled=st.session_state.exec_running,
            )
        with stop_col:
            stop_clicked = st.button(
                "⏹ Stop Session", use_container_width=True,
                disabled=not st.session_state.exec_running,
            )
        with report_col:
            report_clicked = st.button("📊 View Allure Report", use_container_width=True)

        # ── Stop ───────────────────────────────────────────────────────────
        if stop_clicked:
            st.session_state.exec_running = False
            st.warning("⏹ Stop requested.")

        # ── Allure report ──────────────────────────────────────────────────
        if report_clicked:
            prev = st.session_state.get("allure_proc")
            if prev and prev.poll() is None:
                prev.terminate()
            allure_abs = os.path.abspath(ALLURE_RESULTS_DIR)
            if not os.listdir(allure_abs):
                st.warning("⚠️ No Allure results yet. Run the script first.")
            else:
                try:
                    port = st.session_state.allure_port
                    proc = subprocess.Popen(
                        ["allure", "serve", allure_abs, "-p", str(port)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True,
                    )
                    st.session_state.allure_proc = proc
                    st.success(
                        f"✅ Allure report at **http://localhost:{port}**  \n"
                        f"[Click here to open](http://localhost:{port})"
                    )
                except FileNotFoundError:
                    st.error("❌ `allure` not found. Run: `npm install -g allure-commandline`")
                except Exception as e:
                    st.error(f"❌ Allure error: {e}")

        # ── Helper: patch script caps for BrowserStack ─────────────────────
        def _patch_script_for_bs(script_path: str, device: dict,
                                  app_url: str, bs_user: str, bs_key: str,
                                  project: str, build: str, session_name: str) -> str:
            """
            Read the script, replace driver fixture caps with BrowserStack caps,
            write to a temp file, return temp file path.
            """
            import tempfile
            with open(script_path, encoding="utf-8") as f:
                src = f.read()

            platform   = device.get("platform", "Android")
            model      = device.get("model", "Samsung Galaxy S23")
            os_version = device.get("bs_os_version", "13")
            automation = "UIAutomator2" if platform == "Android" else "XCUITest"

            bs_fixture = f'''@pytest.fixture(scope="module")
def driver():
    """BrowserStack fixture — auto-patched by IQEA Tab 4."""
    from appium.options import UiAutomator2Options
    options = UiAutomator2Options()
    options.platform_name       = "{platform}"
    options.platform_version    = "{os_version}"
    options.device_name         = "{model}"
    options.automation_name     = "{automation}"
    options.app                 = "{app_url}"
    options.no_reset            = True
    options.new_command_timeout = 300

    # BrowserStack options
    options.load_capabilities({{
        "bstack:options": {{
            "userName":    "{bs_user}",
            "accessKey":   "{bs_key}",
            "projectName": "{project}",
            "buildName":   "{build}",
            "sessionName": "{session_name}",
            "debug":       "true",
            "networkLogs": "true",
            "deviceLogs":  "true",
        }}
    }})

    logger.info("Connecting to BrowserStack hub…")
    drv = webdriver.Remote("https://hub.browserstack.com/wd/hub", options=options)
    yield drv
    try:
        drv.quit()
    except Exception:
        pass
'''

            # Replace existing fixture (from @pytest.fixture ... def driver(): ... yield driver)
            patched = _re.sub(
                r'@pytest\.fixture\(scope=["\']module["\']\)\s*\ndef driver\(\):.*?(?=\n\n|\Z)',
                bs_fixture,
                src,
                flags=_re.DOTALL,
            )

            # Write to temp file next to original
            tmp_dir  = os.path.dirname(script_path)
            tmp_name = f"_bs_{os.path.basename(script_path)}"
            tmp_path = os.path.join(tmp_dir, tmp_name)
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(patched)
            return tmp_path

        # ── Run handler ────────────────────────────────────────────────────
        if run_clicked:
            run_script = sel_script
            tmp_bs_script = None

            # Patch for BrowserStack if needed
            if run_on_bs:
                missing = []
                if not st.session_state.bs_user: missing.append("BS Username")
                if not st.session_state.bs_key:  missing.append("BS Access Key")
                if not bs_app_url:               missing.append("App URL (bs://...)")
                if not bs_target_dev:            missing.append("Target Device")

                if missing:
                    st.error(f"⚠️ Please fill in: {', '.join(missing)}")
                    st.stop()

                with st.spinner("Patching script with BrowserStack capabilities…"):
                    tmp_bs_script = _patch_script_for_bs(
                        script_path  = sel_script,
                        device       = bs_target_dev,
                        app_url      = bs_app_url,
                        bs_user      = st.session_state.bs_user,
                        bs_key       = st.session_state.bs_key,
                        project      = bs_proj,
                        build        = bs_bld,
                        session_name = bs_sess,
                    )
                run_script = tmp_bs_script
                st.info(f"✅ Patched script ready — running on BrowserStack device: **{bs_target_dev.get('model','')}**")

            st.session_state.exec_running    = True
            st.session_state.exec_output     = ""
            st.session_state.exec_returncode = None

            output_placeholder = st.empty()
            status_placeholder = st.empty()

            cmd = [
                sys.executable, "-m", "pytest",
                run_script, "-v", "--tb=short",
                f"--alluredir={os.path.abspath(ALLURE_RESULTS_DIR)}",
                "--no-header",
            ]

            target_label = "BrowserStack" if run_on_bs else "Local Device"
            status_placeholder.info(f"🔄 Running on **{target_label}** — `{os.path.basename(run_script)}`")

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=os.path.dirname(run_script),
                )

                collected_output = []
                for line in proc.stdout:
                    if not st.session_state.exec_running:
                        proc.terminate()
                        break
                    collected_output.append(line)
                    st.session_state.exec_output = "".join(collected_output)
                    output_placeholder.code(
                        st.session_state.exec_output[-6000:],
                        language="text",
                    )

                proc.wait()
                st.session_state.exec_returncode = proc.returncode
                st.session_state.exec_running    = False

                if proc.returncode == 0:
                    status_placeholder.success(f"✅ All tests passed on {target_label}!")
                elif proc.returncode == 1:
                    status_placeholder.warning("⚠️ Some tests failed — see output above.")
                elif proc.returncode == 5:
                    status_placeholder.warning("⚠️ No tests collected. Check script.")
                else:
                    status_placeholder.error(f"❌ pytest exit code {proc.returncode}")

                if run_on_bs:
                    status_placeholder.info(
                        "📊 Full session video, logs & screenshots → "
                        "[BrowserStack Dashboard](https://app-automate.browserstack.com/dashboard)"
                    )

            except Exception as e:
                st.session_state.exec_running = False
                st.error(f"❌ Execution error: {e}")
            finally:
                # Clean up temp patched script
                if tmp_bs_script and os.path.exists(tmp_bs_script):
                    try:
                        os.unlink(tmp_bs_script)
                    except Exception:
                        pass

        # ── Persisted output ───────────────────────────────────────────────
        if st.session_state.exec_output and not run_clicked:
            rc = st.session_state.exec_returncode
            if rc == 0:
                st.success("✅ Last run passed")
            elif rc is not None:
                st.warning(f"⚠️ Last run: exit code {rc}")

            st.subheader("Console Output")
            st.code(st.session_state.exec_output, language="text")

            lines = st.session_state.exec_output.splitlines()
            summary = next(
                (l for l in reversed(lines) if "passed" in l or "failed" in l or "error" in l),
                None,
            )
            if summary:
                st.info(f"📊 **{summary.strip()}**")

            st.download_button(
                "⬇ Download Console Log",
                data=st.session_state.exec_output,
                file_name=f"run_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("IQEA Platform · Mobile Automation Module · Powered by Azure OpenAI + Appium")
