import React, { useEffect, useState } from "react";

type AgentLog = {
  step: number;
  tool: string;
  input: any;
  output: any;
  timestamp: number;
};

const TOOL_COLORS: Record<string, string> = {
  search_pdf: "bg-blue-100 border-blue-400",
  web_search: "bg-blue-100 border-blue-400",
  summarize: "bg-yellow-100 border-yellow-400",
  ask_question: "bg-green-100 border-green-400",
  add_note: "bg-purple-100 border-purple-400",
  goto_upload_page: "bg-pink-100 border-pink-400",
  default: "bg-gray-100 border-gray-300",
};

function formatTime(ts: number) {
  const d = new Date(ts * 1000);
  return d.toLocaleString();
}

export const AgentTimeline: React.FC = () => {
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/logs");
      const data = await res.json();
      setLogs(Array.isArray(data) ? data : data.logs || []);
    } catch (e) {
      setLogs([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Agent 操作轨迹</h2>
        <button
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          onClick={fetchLogs}
          disabled={loading}
        >
          {loading ? "刷新中..." : "刷新"}
        </button>
      </div>
      <div className="space-y-4">
        {logs.length === 0 && (
          <div className="text-gray-400 text-center">暂无日志</div>
        )}
        {logs.map((log) => {
          const color =
            TOOL_COLORS[log.tool] || TOOL_COLORS.default;
          return (
            <div
              key={log.step}
              className={`border-l-4 p-4 shadow rounded ${color}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold">
                  Step {log.step} · <span className="capitalize">{log.tool}</span>
                </span>
                <span className="text-xs text-gray-500">
                  {formatTime(log.timestamp)}
                </span>
              </div>
              <div className="mb-1">
                <span className="font-medium text-gray-700">输入：</span>
                <pre className="inline text-sm text-gray-800 break-all">{JSON.stringify(log.input, null, 2)}</pre>
              </div>
              <div>
                <span className="font-medium text-gray-700">输出：</span>
                <pre className="inline text-sm text-gray-800 break-all">{typeof log.output === "string" ? log.output : JSON.stringify(log.output, null, 2)}</pre>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentTimeline; 