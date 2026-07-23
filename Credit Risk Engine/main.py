import asyncio
import concurrent.futures
import os
import random
import re
import shutil
import subprocess
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from reactpy import component, html, use_effect, use_state
from reactpy.backend.fastapi import configure

app = FastAPI()

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

ide_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# ------------------------------------------------------------------
# SHARED NAVY BLUE THEME STYLES
# ------------------------------------------------------------------
# Color Palette:
# Main Background: #020617 (Deep Slate Navy)
# Panels / Cards: #0F172A (Navy Container)
# Borders: #1E293B (Navy Border Accent)
# Inputs / Sub-items: #1E293B / #0B132B
# Text Primary: #F8FAFC
# Text Muted: #94A3B8
# Accent Cyan / Blue: #38BDF8

LOGO_BTN_STYLE = {
    "background": "transparent",
    "border": "none",
    "cursor": "pointer",
    "padding": "0",
    "display": "block",
    "margin": "0 auto 16px auto",
    "outline": "none"
}

LOGO_IMG_STYLE = {
    "width": "42px",
    "height": "42px",
    "objectFit": "contain",
    "mixBlendMode": "screen",
    "transition": "transform 0.2s ease"
}

SIDEBAR_BTN_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "10px",
    "width": "100%",
    "padding": "10px 14px",
    "marginBottom": "8px",
    "backgroundColor": "#0F172A",
    "border": "1px solid #1E293B",
    "borderRadius": "8px",
    "color": "#94A3B8",
    "fontSize": "13px",
    "fontWeight": "500",
    "cursor": "pointer",
    "textAlign": "left",
    "boxSizing": "border-box",
    "whiteSpace": "nowrap"
}

SIDEBAR_BTN_ACTIVE = {
    **SIDEBAR_BTN_STYLE,
    "backgroundColor": "#1E293B",
    "borderColor": "#38BDF8",
    "color": "#38BDF8"
}

SUB_LINK_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "10px",
    "width": "100%",
    "padding": "8px 14px 8px 32px",
    "marginBottom": "6px",
    "backgroundColor": "#0B132B",
    "border": "1px solid #1E293B",
    "borderRadius": "6px",
    "color": "#94A3B8",
    "fontSize": "12px",
    "fontWeight": "500",
    "cursor": "pointer",
    "textDecoration": "none",
    "boxSizing": "border-box",
    "whiteSpace": "nowrap",
    "transition": "all 0.2s ease"
}

SUB_LINK_ACTIVE = {
    **SUB_LINK_STYLE,
    "backgroundColor": "#1E293B",
    "borderColor": "#38BDF8",
    "color": "#38BDF8"
}

CLOUD_ICON_STYLE = {
    "width": "18px",
    "height": "18px",
    "objectFit": "contain",
    "borderRadius": "2px"
}

SECTION_LABEL = {
    "fontSize": "11px",
    "fontWeight": "bold",
    "color": "#64748B",
    "letterSpacing": "1px",
    "marginTop": "20px",
    "marginBottom": "10px",
    "paddingLeft": "4px",
    "whiteSpace": "nowrap"
}


def _spawn_process(executable: str, filepath: str = None):
    try:
        args = [executable]
        if filepath:
            args.append(filepath)

        if os.name == "nt":
            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            creation_flags = DETACHED_PROCESS | CREATE_NO_WINDOW

            subprocess.Popen(
                args,
                shell=False,
                creationflags=creation_flags,
                close_fds=True
            )
        else:
            subprocess.Popen(
                args,
                start_new_session=True,
                close_fds=True
            )
    except Exception as err:
        print(f"[IDE Launcher Error]: {err}")


def launch_ide(ide_key: str, filepath: str = None):
    fast_paths = {
        "vscode": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            r"C:\Program Files\Microsoft VS Code\Code.exe"
        ],
        "pycharm": [
            r"C:\Program Files\JetBrains\PyCharm Community Edition\bin\pycharm64.exe",
            r"C:\Program Files\JetBrains\PyCharm Professional\bin\pycharm64.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\PyCharm Community\bin\pycharm64.exe")
        ],
        "spyder": [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\Scripts\spyder.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\anaconda3\Scripts\spyder.exe")
        ],
        "intellij": [
            r"C:\Program Files\JetBrains\IntelliJ IDEA Community Edition\bin\idea64.exe",
            r"C:\Program Files\JetBrains\IntelliJ IDEA\bin\idea64.exe"
        ]
    }

    candidates = fast_paths.get(ide_key, [])
    for candidate in candidates:
        if os.path.isfile(candidate):
            ide_executor.submit(_spawn_process, candidate, filepath)
            return

    fallback_names = {"vscode": "Code.exe", "pycharm": "pycharm64.exe", "spyder": "spyder.exe",
                      "intellij": "idea64.exe"}
    path_exe = shutil.which(fallback_names.get(ide_key, ""))
    if path_exe:
        ide_executor.submit(_spawn_process, path_exe, filepath)


# ------------------------------------------------------------------
# COMPONENT 1: Top Navigation Bar
# ------------------------------------------------------------------
@component
def TopHeader(settlement_vol, utc_time, is_nav_open, toggle_nav):
    return html.header(
        {
            "style": {
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "backgroundColor": "#090D16",
                "borderBottom": "1px solid #1E293B",
                "height": "56px",
                "padding": "0 16px",
                "boxSizing": "border-box",
                "width": "100%",
                "position": "relative",
                "zIndex": "10"
            }
        },
        html.div(
            {"style": {"display": "flex", "alignItems": "center", "gap": "12px", "whiteSpace": "nowrap",
                       "minWidth": "280px"}},
            html.span(
                {"style": {"color": "#38BDF8", "fontWeight": "bold", "fontSize": "16px", "letterSpacing": "0.5px"}},
                "Barclays Credit Engine"),
            html.span({"style": {"backgroundColor": "#064E3B", "color": "#34D399", "padding": "3px 8px",
                                 "borderRadius": "12px", "fontSize": "11px", "fontWeight": "600"}}, "● Engine Active"),
            html.span({"style": {"backgroundColor": "#064E3B", "color": "#34D399", "padding": "3px 8px",
                                 "borderRadius": "12px", "fontSize": "11px", "fontWeight": "600"}},
                      "● Python + Java Mesh Live")
        ),
        html.div(
            {
                "class_name": f"horizontal-navbar {'navbar-expanded' if is_nav_open else 'navbar-collapsed'}"
            },
            html.div(
                {"style": {"display": "flex", "alignItems": "center", "gap": "12px"}},
                html.input({
                    "type": "text",
                    "placeholder": "Search Credit TX Hash / Account...",
                    "style": {
                        "backgroundColor": "#0F172A",
                        "border": "1px solid #1E293B",
                        "borderRadius": "6px",
                        "padding": "6px 12px",
                        "color": "#F8FAFC",
                        "width": "220px",
                        "fontSize": "12px"
                    }
                }),
                html.select(
                    {"style": {"backgroundColor": "#0F172A", "border": "1px solid #1E293B", "color": "#F8FAFC",
                               "padding": "6px 10px", "borderRadius": "6px", "fontSize": "12px", "outline": "none"}},
                    html.option("Region: UK Main Engine"),
                    html.option("Region: US Core Engine"),
                    html.option("Region: APAC Sync")
                )
            ),
            html.div(
                {"style": {"display": "flex", "alignItems": "center", "gap": "16px", "fontSize": "12px",
                           "whiteSpace": "nowrap"}},
                html.div(
                    html.span({"style": {"color": "#94A3B8"}}, "Settlement Vol: "),
                    html.span(
                        {"style": {"color": "#4ADE80", "fontWeight": "bold", "fontSize": "13px"}},
                        f"£{settlement_vol:,.2f}M"
                    )
                ),
                html.span({"style": {"color": "#94A3B8"}}, f"{utc_time} UTC")
            )
        )
    )


# ------------------------------------------------------------------
# COMPONENT 2: Left Navigation Sidebar
# ------------------------------------------------------------------
@component
def LeftSidebar(active_item, set_active_item, is_open, toggle_open, toggle_nav):
    is_cloud_open, set_cloud_open = use_state(True)
    is_health_open, set_health_open = use_state(True)

    def toggle_cloud(e): set_cloud_open(not is_cloud_open)

    def toggle_health(e): set_health_open(not is_health_open)

    def handle_logo_click(e):
        toggle_open(e)
        toggle_nav(e)

    return html.aside(
        {"style": {
            "width": "230px" if is_open else "60px",
            "backgroundColor": "#090D16",
            "borderRight": "1px solid #1E293B",
            "padding": "16px 12px",
            "boxSizing": "border-box",
            "transition": "width 0.3s ease",
            "overflowY": "auto",
            "overflowX": "hidden"
        }},
        html.button(
            {
                "style": LOGO_BTN_STYLE,
                "onClick": handle_logo_click,
                "title": "Click to toggle Top Navbar and Left Menu"
            },
            html.img({
                "src": "/static/Barclays.png",
                "style": LOGO_IMG_STYLE,
                "alt": "Toggle Left Sidebar & Navbar"
            })
        ),

        html.div({"style": SECTION_LABEL if is_open else {"display": "none"}}, "CLOUD SERVICES"),
        html.button(
            {
                "style": SIDEBAR_BTN_ACTIVE if active_item.startswith("cloud_") else SIDEBAR_BTN_STYLE,
                "onClick": toggle_cloud
            },
            html.span({"style": {"minWidth": "16px"}}, "☁️"),
            html.span({"style": {"display": "inline" if is_open else "none", "flex": "1"}}, "Cloud Providers"),
            html.span({"style": {"display": "inline" if is_open else "none", "fontSize": "10px"}},
                      "▲" if is_cloud_open else "▼")
        ),

        html.div(
            {"style": {"display": "block" if (is_cloud_open and is_open) else "none"}},
            html.a(
                {"href": "https://cloud.ibm.com/login", "target": "_blank", "rel": "noopener noreferrer",
                 "style": SUB_LINK_STYLE, "onClick": lambda e: set_active_item("cloud_ibm")},
                html.img({"src": "/static/IBM.jpg", "style": CLOUD_ICON_STYLE, "alt": "IBM"}),
                html.span("IBM Cloud Login ↗")
            ),
            html.a(
                {"href": "https://cloud.oracle.com", "target": "_blank", "rel": "noopener noreferrer",
                 "style": SUB_LINK_STYLE, "onClick": lambda e: set_active_item("cloud_oracle")},
                html.img({"src": "/static/Oracle.jpg", "style": CLOUD_ICON_STYLE, "alt": "Oracle"}),
                html.span("Oracle Cloud Login ↗")
            ),
            html.a(
                {"href": "https://aws.amazon.com/console/", "target": "_blank", "rel": "noopener noreferrer",
                 "style": SUB_LINK_STYLE, "onClick": lambda e: set_active_item("cloud_aws")},
                html.img({"src": "/static/aws.jpg", "style": CLOUD_ICON_STYLE, "alt": "AWS"}),
                html.span("AWS Console Login ↗")
            )
        ),

        html.div({"style": SECTION_LABEL if is_open else {"display": "none"}}, "DEVELOPMENT IDES"),
        html.button(
            {
                "style": SIDEBAR_BTN_STYLE,
                "onClick": toggle_health
            },
            html.span({"style": {"minWidth": "16px"}}, "💻"),
            html.span({"style": {"display": "inline" if is_open else "none", "flex": "1"}}, "IDE Launchers"),
            html.span({"style": {"display": "inline" if is_open else "none", "fontSize": "10px"}},
                      "▲" if is_health_open else "▼")
        ),

        html.div(
            {"style": {"display": "block" if (is_health_open and is_open) else "none"}},
            html.button({"style": SUB_LINK_STYLE, "onClick": lambda e: launch_ide("pycharm")}, html.span("🐍"),
                        html.span("PyCharm (Python)")),
            html.button({"style": SUB_LINK_STYLE, "onClick": lambda e: launch_ide("intellij")}, html.span("☕"),
                        html.span("IntelliJ (Java)")),
            html.button({"style": SUB_LINK_STYLE, "onClick": lambda e: launch_ide("vscode")}, html.span("💙"),
                        html.span("VS Code (Polyglot)")),
            html.button({"style": SUB_LINK_STYLE, "onClick": lambda e: launch_ide("spyder")}, html.span("🕷️"),
                        html.span("Spyder (Data)"))
        )
    )


# ------------------------------------------------------------------
# COMPONENT 3: Right Sidebar
# ------------------------------------------------------------------
@component
def RightSidebar(active_db, set_active_db, is_open, toggle_open, toggle_nav):
    is_db_open, set_db_open = use_state(True)

    data_sources = [
        ("postgres", "🐘", "PostgreSQL Ledger (Java)"),
        ("mysql", "🐬", "MySQL Replica"),
        ("redis", "⚡", "Redis Cache (Python/Java)"),
        ("kafka", "📡", "Apache Kafka Event Bus")
    ]

    def toggle_db(e): set_db_open(not is_db_open)

    def handle_logo_click(e):
        toggle_open(e)
        toggle_nav(e)

    return html.aside(
        {"style": {
            "width": "240px" if is_open else "60px",
            "backgroundColor": "#090D16",
            "borderLeft": "1px solid #1E293B",
            "padding": "16px 12px",
            "boxSizing": "border-box",
            "transition": "width 0.3s ease",
            "overflowY": "auto",
            "overflowX": "hidden"
        }},
        html.button(
            {
                "style": LOGO_BTN_STYLE,
                "onClick": handle_logo_click,
                "title": "Click to toggle Top Navbar and Right Menu"
            },
            html.img({
                "src": "/static/Barclays.png",
                "style": LOGO_IMG_STYLE,
                "alt": "Toggle Right Sidebar & Navbar"
            })
        ),

        html.div({"style": SECTION_LABEL if is_open else {"display": "none"}}, "DATA & MESSAGING"),
        html.button(
            {
                "style": SIDEBAR_BTN_ACTIVE if active_db else SIDEBAR_BTN_STYLE,
                "onClick": toggle_db
            },
            html.span({"style": {"minWidth": "16px"}}, "🗄️"),
            html.span({"style": {"display": "inline" if is_open else "none", "flex": "1"}}, "Data Connections"),
            html.span({"style": {"display": "inline" if is_open else "none", "fontSize": "10px"}},
                      "▲" if is_db_open else "▼")
        ),
        html.div(
            {"style": {"display": "block" if (is_db_open and is_open) else "none"}},
            *[
                html.button(
                    {
                        "style": SUB_LINK_ACTIVE if active_db == db_id else SUB_LINK_STYLE,
                        "onClick": lambda e, id=db_id: set_active_db(id)
                    },
                    html.span(icon),
                    html.span(label)
                ) for db_id, icon, label in data_sources
            ]
        )
    )


# ------------------------------------------------------------------
# COMPONENT 4: Center Main Content Dashboard
# ------------------------------------------------------------------
@component
def MainDashboard(active_left, active_db, set_active_db):
    # System Telemetry States
    latency_p95, set_latency_p95 = use_state(12)
    decisions_min, set_decisions_min = use_state(14200)
    kafka_lag, set_kafka_lag = use_state(0)
    active_workflows_cnt, set_active_workflows_cnt = use_state(142)
    grpc_tps, set_grpc_tps = use_state(8420)

    # Drools / Rule Evaluation Counters
    rules_eval_sec, set_rules_eval_sec = use_state(3210)
    rule_pass_rate, set_rule_pass_rate = use_state(98.4)

    # Structlog Stream Data
    logs, set_logs = use_state([
        {"time": "02:15:01 AM", "app_id": "APP-98201", "stage": "python.risk_inference", "status": "2ms (gRPC)"},
        {"time": "02:15:03 AM", "app_id": "APP-98201", "stage": "java.drools_rules", "status": "PASSED"},
        {"time": "02:15:04 AM", "app_id": "APP-98202", "stage": "python.fraud_jax", "status": "11ms (REST)"},
        {"time": "02:15:06 AM", "app_id": "APP-98201", "stage": "java.core_ledger_tx", "status": "ACID_COMMIT"},
        {"time": "02:15:08 AM", "app_id": "APP-98203", "stage": "kafka.credit_applied", "status": "PARTITION_2"},
        {"time": "02:15:10 AM", "app_id": "APP-98204", "stage": "python.document_ai", "status": "EMBEDDED"},
        {"time": "02:15:12 AM", "app_id": "APP-98202", "stage": "java.drools_rules", "status": "PASSED"},
        {"time": "02:15:15 AM", "app_id": "APP-98202", "stage": "java.core_ledger_tx", "status": "ACID_COMMIT"}
    ])

    workflows, set_workflows = use_state([
        {"app_id": "APP-98201", "stage": "Ledger Commit (Java)", "status": "completed"},
        {"app_id": "APP-98202", "stage": "Risk Model Inference (Python)", "status": "running"},
        {"app_id": "APP-98203", "stage": "Document OCR Parsing (Python)", "status": "running"},
        {"app_id": "APP-98204", "stage": "Drools Rules Verification (Java)", "status": "running"},
        {"app_id": "APP-98205", "stage": "Camunda Orchestration (Java)", "status": "running"},
        {"app_id": "APP-98206", "stage": "Ledger Commit (Java)", "status": "completed"}
    ])

    # Dynamic Simulation Loop
    @use_effect
    def update_metrics_loop():
        stages = [
            ("python.risk_inference", "2ms (gRPC)"),
            ("java.drools_rules", "PASSED"),
            ("python.fraud_jax", "8ms (REST)"),
            ("java.core_ledger_tx", "ACID_COMMIT"),
            ("kafka.credit_applied", "ACK_SYNC")
        ]

        async def loop():
            while True:
                await asyncio.sleep(2.0)
                set_latency_p95(random.randint(9, 15))
                set_decisions_min(random.randint(13800, 14900))
                set_kafka_lag(random.randint(0, 3))
                set_active_workflows_cnt(random.randint(130, 150))
                set_grpc_tps(random.randint(8100, 8900))
                set_rules_eval_sec(random.randint(3100, 3400))
                set_rule_pass_rate(round(98.0 + random.uniform(0, 1.5), 1))

                now_str = datetime.now(timezone.utc).strftime("%I:%M:%S %p")
                rand_app = f"APP-{random.randint(98200, 98210)}"
                rand_stage, rand_status = random.choice(stages)

                new_log = {"time": now_str, "app_id": rand_app, "stage": rand_stage, "status": rand_status}
                set_logs(lambda old_logs: old_logs[1:] + [new_log])

        task = asyncio.create_task(loop())
        return lambda: task.cancel()

    # Data Overlay
    if active_db:
        db_details = {
            "postgres": {
                "title": "PostgreSQL Transaction Core (Java Spring Boot)",
                "tech": "Hibernate JPA / HikariCP Connection Pool",
                "status": "ACID Compliance: ACTIVE",
                "metrics": "Pool Active: 24/50 | Read Replica Lag: 0.1ms | TPS: 3,210"
            },
            "mysql": {
                "title": "MySQL Analytics Replica Engine",
                "tech": "Read-Optimized Analytics Store",
                "status": "Replication Sync: OK",
                "metrics": "Slave IO Thread: Running | Query Cache Hit: 94.2%"
            },
            "redis": {
                "title": "Redis Real-Time Feature Cache & Session Store",
                "tech": "Distributed In-Memory Cluster",
                "status": "Cluster Health: GREEN",
                "metrics": "Keys: 1.4M | Memory Used: 4.2GB | Hit Rate: 99.1%"
            },
            "kafka": {
                "title": "Apache Kafka / Redpanda Polyglot Event Bus",
                "tech": "High-Throughput Distributed Streaming Log",
                "status": "Brokers: 5 Active | Lag: Minimal",
                "metrics": "Topics: 18 | Ingress: 14,200 msg/sec | DLQ: 0"
            }
        }
        info = db_details.get(active_db, {})
        return html.main(
            {"style": {"padding": "24px", "backgroundColor": "#020617", "overflowY": "auto", "flex": "1",
                       "color": "#F8FAFC"}},
            html.div(
                {"style": {"marginBottom": "24px", "borderBottom": "1px solid #1E293B", "paddingBottom": "16px",
                           "display": "flex", "justifyContent": "space-between", "alignItems": "center"}},
                html.h1({"style": {"margin": 0, "fontSize": "22px"}}, info.get("title", "Data Connection")),
                html.button(
                    {"style": {"backgroundColor": "#0F172A", "border": "1px solid #1E293B", "color": "#94A3B8",
                               "padding": "6px 12px", "borderRadius": "6px", "cursor": "pointer"},
                     "onClick": lambda e: set_active_db(None)},
                    "✕ Close Panel"
                )
            ),
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "20px",
                           "marginBottom": "16px", "border": "1px solid #1E293B"}},
                html.div({"style": {"color": "#38BDF8", "fontWeight": "bold", "marginBottom": "8px"}},
                         info.get("tech")),
                html.div({"style": {"color": "#4ADE80", "marginBottom": "12px"}}, info.get("status")),
                html.div({"style": {"color": "#94A3B8", "fontSize": "13px"}}, info.get("metrics"))
            )
        )

    return html.main(
        {"style": {
            "padding": "24px",
            "backgroundColor": "#020617",
            "overflowY": "auto",
            "flex": "1",
            "color": "#F8FAFC",
            "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        }},

        # 1. Polyglot Architecture Status Bar
        html.div(
            {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px 20px",
                       "marginBottom": "20px", "border": "1px solid #1E293B"}},
            html.div({"style": {"fontSize": "13px", "fontWeight": "bold", "color": "#38BDF8", "marginBottom": "12px",
                                "letterSpacing": "0.5px"}}, "POLYGLOT SYSTEM HEALTH & PROTOCOL BALANCER"),
            html.div(
                {"style": {"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "16px"}},
                html.div(
                    {"style": {"backgroundColor": "#0B132B", "padding": "12px", "borderRadius": "6px",
                               "border": "1px solid #1E293B"}},
                    html.div({"style": {"color": "#94A3B8", "fontSize": "11px", "fontWeight": "bold"}},
                             "🐍 PYTHON ML LAYER (FastAPI)"),
                    html.div(
                        {"style": {"fontSize": "14px", "fontWeight": "600", "color": "#F8FAFC", "marginTop": "4px"}},
                        "Risk Scoring & JAX Fraud"),
                    html.div({"style": {"fontSize": "11px", "color": "#34D399", "marginTop": "2px"}},
                             "Status: Healthy (12 Nodes)")
                ),
                html.div(
                    {"style": {"backgroundColor": "#0B132B", "padding": "12px", "borderRadius": "6px",
                               "border": "1px solid #1E293B"}},
                    html.div({"style": {"color": "#94A3B8", "fontSize": "11px", "fontWeight": "bold"}},
                             "☕ JAVA CORE LAYER (Spring Boot)"),
                    html.div(
                        {"style": {"fontSize": "14px", "fontWeight": "600", "color": "#F8FAFC", "marginTop": "4px"}},
                        "Ledger & Drools Rules"),
                    html.div({"style": {"fontSize": "11px", "color": "#34D399", "marginTop": "2px"}},
                             "Status: Healthy (ACID Locked)")
                ),
                html.div(
                    {"style": {"backgroundColor": "#0B132B", "padding": "12px", "borderRadius": "6px",
                               "border": "1px solid #1E293B"}},
                    html.div({"style": {"color": "#94A3B8", "fontSize": "11px", "fontWeight": "bold"}},
                             "⚡ PROTOCOL THROUGHPUT"),
                    html.div(
                        {"style": {"fontSize": "14px", "fontWeight": "600", "color": "#38BDF8", "marginTop": "4px"}},
                        f"gRPC: {grpc_tps:,} ops/s"),
                    html.div({"style": {"fontSize": "11px", "color": "#94A3B8", "marginTop": "2px"}},
                             "REST Ingress: 5,780 req/s")
                )
            )
        ),

        # 2. Top KPI Metric Cards
        html.div(
            {"style": {"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "16px",
                       "marginBottom": "20px"}},
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px 20px",
                           "border": "1px solid #1E293B"}},
                html.div({"style": {"color": "#94A3B8", "fontSize": "13px", "fontWeight": "500"}},
                         "Decision Latency (p95)"),
                html.div({"style": {"fontSize": "28px", "fontWeight": "600", "marginTop": "6px", "color": "#34D399"}},
                         f"{latency_p95} ms")
            ),
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px 20px",
                           "border": "1px solid #1E293B"}},
                html.div({"style": {"color": "#94A3B8", "fontSize": "13px", "fontWeight": "500"}}, "Decisions / min"),
                html.div({"style": {"fontSize": "28px", "fontWeight": "600", "marginTop": "6px"}}, f"{decisions_min:,}")
            ),
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px 20px",
                           "border": "1px solid #1E293B"}},
                html.div({"style": {"color": "#94A3B8", "fontSize": "13px", "fontWeight": "500"}},
                         "Kafka Consumer Lag"),
                html.div({"style": {"fontSize": "28px", "fontWeight": "600", "marginTop": "6px", "color": "#38BDF8"}},
                         f"{kafka_lag} msgs")
            ),
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px 20px",
                           "border": "1px solid #1E293B"}},
                html.div({"style": {"color": "#94A3B8", "fontSize": "13px", "fontWeight": "500"}}, "Active Workflows"),
                html.div({"style": {"fontSize": "28px", "fontWeight": "600", "marginTop": "6px"}},
                         f"{active_workflows_cnt}")
            )
        ),

        # 3. Intermediate Dashboard Section: Protocol Inspector & Business Rules Engine
        html.div(
            {"style": {"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px", "marginBottom": "20px"}},

            # gRPC vs REST Traffic Inspector
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px",
                           "border": "1px solid #1E293B"}},
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "8px", "color": "#F8FAFC",
                               "fontWeight": "600", "fontSize": "14px", "marginBottom": "12px"}},
                    html.span("⚡"), html.span("gRPC vs. REST Protocol Inspector")
                ),
                html.div(
                    {"style": {"display": "flex", "flexDirection": "column", "gap": "10px", "fontSize": "12px"}},
                    html.div(
                        {"style": {"display": "flex", "justifyContent": "space-between", "padding": "8px",
                                   "backgroundColor": "#0B132B", "borderRadius": "4px", "border": "1px solid #1E293B"}},
                        html.span({"style": {"color": "#94A3B8"}}, "Binary Protobuf Compression Savings:"),
                        html.span({"style": {"color": "#4ADE80", "fontWeight": "bold"}}, "68.4% smaller payloads")
                    ),
                    html.div(
                        {"style": {"display": "flex", "justifyContent": "space-between", "padding": "8px",
                                   "backgroundColor": "#0B132B", "borderRadius": "4px", "border": "1px solid #1E293B"}},
                        html.span({"style": {"color": "#94A3B8"}}, "HTTP/2 Multiplexed Streams:"),
                        html.span({"style": {"color": "#38BDF8", "fontWeight": "bold"}}, "128 Active Channels")
                    ),
                    html.div(
                        {"style": {"display": "flex", "justifyContent": "space-between", "padding": "8px",
                                   "backgroundColor": "#0B132B", "borderRadius": "4px", "border": "1px solid #1E293B"}},
                        html.span({"style": {"color": "#94A3B8"}}, "Serialization Time Overhead:"),
                        html.span({"style": {"color": "#F8FAFC", "fontWeight": "bold"}}, "< 0.4 ms")
                    )
                )
            ),

            # Java Drools Business Rules Inspector
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px",
                           "border": "1px solid #1E293B"}},
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "8px", "color": "#F8FAFC",
                               "fontWeight": "600", "fontSize": "14px", "marginBottom": "12px"}},
                    html.span("🌲"), html.span("Java Drools Business Rules Engine")
                ),
                html.div(
                    {"style": {"display": "flex", "flexDirection": "column", "gap": "10px", "fontSize": "12px"}},
                    html.div(
                        {"style": {"display": "flex", "justifyContent": "space-between", "padding": "8px",
                                   "backgroundColor": "#0B132B", "borderRadius": "4px", "border": "1px solid #1E293B"}},
                        html.span({"style": {"color": "#94A3B8"}}, "Rule Evaluations / sec:"),
                        html.span({"style": {"color": "#F8FAFC", "fontWeight": "bold"}}, f"{rules_eval_sec:,} eval/s")
                    ),
                    html.div(
                        {"style": {"display": "flex", "justifyContent": "space-between", "padding": "8px",
                                   "backgroundColor": "#0B132B", "borderRadius": "4px", "border": "1px solid #1E293B"}},
                        html.span({"style": {"color": "#94A3B8"}}, "Regulatory Compliance Pass Rate:"),
                        html.span({"style": {"color": "#4ADE80", "fontWeight": "bold"}}, f"{rule_pass_rate}%")
                    ),
                    html.div(
                        {"style": {"display": "flex", "justifyContent": "space-between", "padding": "8px",
                                   "backgroundColor": "#0B132B", "borderRadius": "4px", "border": "1px solid #1E293B"}},
                        html.span({"style": {"color": "#94A3B8"}}, "Active Policy Memory (KieSession):"),
                        html.span({"style": {"color": "#38BDF8", "fontWeight": "bold"}}, "142 Rules Loaded")
                    )
                )
            )
        ),

        # 4. Bottom Grid (structlog stream & Temporal/Camunda workflows)
        html.div(
            {"style": {"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"}},

            # Polyglot Event Stream Terminal
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px",
                           "border": "1px solid #1E293B", "position": "relative"}},
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "8px", "color": "#F8FAFC",
                               "fontWeight": "600", "fontSize": "14px", "marginBottom": "16px"}},
                    html.span("📄"), html.span("Polyglot Event & Telemetry Stream")
                ),
                html.div(
                    {"style": {"fontFamily": "Consolas, Monaco, 'Courier New', monospace", "fontSize": "12px",
                               "color": "#94A3B8", "lineHeight": "2"}},
                    *[
                        html.div(
                            {"key": idx},
                            html.span({"style": {"color": "#64748B", "marginRight": "12px"}}, log["time"]),
                            html.span({"style": {"color": "#F8FAFC"}}, f"{log['app_id']} "),
                            html.span({"style": {"color": "#38BDF8" if "python" in log["stage"] else "#F59E0B"}},
                                      f"[{log['stage']}] "),
                            html.span({"style": {"color": "#34D399"}}, log["status"])
                        ) for idx, log in enumerate(logs)
                    ]
                )
            ),

            # Workflows List
            html.div(
                {"style": {"backgroundColor": "#0F172A", "borderRadius": "8px", "padding": "16px",
                           "border": "1px solid #1E293B"}},
                html.div(
                    {"style": {"display": "flex", "alignItems": "center", "gap": "8px", "color": "#F8FAFC",
                               "fontWeight": "600", "fontSize": "14px", "marginBottom": "16px"}},
                    html.span("🕸️"), html.span("Camunda / Temporal Workflow Pipelines")
                ),
                html.div(
                    {"style": {"display": "flex", "flexDirection": "column", "gap": "8px"}},
                    *[
                        html.div(
                            {
                                "key": wf["app_id"],
                                "style": {
                                    "display": "flex", "alignItems": "center", "justifyContent": "space-between",
                                    "backgroundColor": "#0B132B", "border": "1px solid #1E293B",
                                    "borderRadius": "6px", "padding": "8px 14px", "fontSize": "12px"
                                }
                            },
                            html.span({"style": {"color": "#FFFFFF", "fontWeight": "600"}}, wf["app_id"]),
                            html.span({"style": {"color": "#94A3B8"}}, wf["stage"]),
                            html.span(
                                {
                                    "style": {
                                        "color": "#34D399" if wf["status"] == "completed" else "#38BDF8",
                                        "fontWeight": "500"
                                    }
                                },
                                wf["status"]
                            )
                        ) for wf in workflows
                    ]
                )
            )
        )
    )


# ------------------------------------------------------------------
# ROOT COMPONENT
# ------------------------------------------------------------------
@component
def DeveloperDashboard():
    active_left, set_active_left = use_state("overview")
    active_db, set_active_db = use_state(None)

    is_left_open, set_left_open = use_state(True)
    is_right_open, set_right_open = use_state(True)
    is_nav_open, set_nav_open = use_state(True)

    settlement_vol, set_settlement_vol = use_state(144.79)
    utc_time, set_utc_time = use_state(datetime.now(timezone.utc).strftime("%H:%M:%S"))

    def toggle_left(e=None): set_left_open(not is_left_open)

    def toggle_right(e=None): set_right_open(not is_right_open)

    def toggle_nav(e=None): set_nav_open(not is_nav_open)

    @use_effect
    def start_realtime_simulation():
        async def update_loop():
            while True:
                await asyncio.sleep(2.0)
                set_settlement_vol(round(140.0 + random.uniform(0, 10), 2))
                set_utc_time(datetime.now(timezone.utc).strftime("%H:%M:%S"))

        task = asyncio.create_task(update_loop())
        return lambda: task.cancel()

    return html.div(
        html.style(
            """
            html, body {
                margin: 0;
                padding: 0;
                background-color: #020617;
                color: #F8FAFC;
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                height: 100vh;
                overflow: hidden;
            }
            * { box-sizing: border-box; }

            .horizontal-navbar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex: 1;
                margin-left: 20px;
                overflow: hidden;
                white-space: nowrap;
                transition: max-width 0.4s ease-in-out, opacity 0.3s ease-in-out;
            }

            .navbar-expanded {
                max-width: 1200px;
                opacity: 1;
            }

            .navbar-collapsed {
                max-width: 0px;
                opacity: 0;
                pointer-events: none;
            }
            """
        ),
        html.div(
            {"style": {"display": "flex", "flexDirection": "column", "height": "100vh"}},
            TopHeader(settlement_vol, utc_time, is_nav_open, toggle_nav),
            html.div(
                {"style": {"display": "flex", "flex": "1", "overflow": "hidden"}},
                LeftSidebar(active_left, set_active_left, is_left_open, toggle_left, toggle_nav),
                MainDashboard(active_left, active_db, set_active_db),
                RightSidebar(active_db, set_active_db, is_right_open, toggle_right, toggle_nav)
            )
        )
    )


configure(app, DeveloperDashboard)