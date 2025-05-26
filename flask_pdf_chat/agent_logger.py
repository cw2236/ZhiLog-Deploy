import time
from flask import session, Blueprint, jsonify
from typing import List, Any

class AgentOperationLogger:
    SESSION_KEY = 'agent_operation_logs'

    @classmethod
    def log(cls, tool: str, input_args: List, output: Any):
        logs = session.get(cls.SESSION_KEY, [])
        step = len(logs) + 1
        log_entry = {
            'step': step,
            'tool': tool,
            'input': input_args,
            'output': output,
            'timestamp': int(time.time())
        }
        logs.append(log_entry)
        session[cls.SESSION_KEY] = logs
        session.modified = True

    @classmethod
    def get_logs(cls):
        return session.get(cls.SESSION_KEY, [])

    @classmethod
    def clear(cls):
        session[cls.SESSION_KEY] = []
        session.modified = True

# --- Flask API 路由 ---
try:
    api_logger_bp = Blueprint('api_logger', __name__)

    @api_logger_bp.route('/api/logs')
    def api_logs():
        return jsonify(AgentOperationLogger.get_logs())
except ImportError:
    pass 