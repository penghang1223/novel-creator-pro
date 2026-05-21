import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ChapterCard } from "../../types";

interface Props {
  chapter: ChapterCard;
  platform: string;
  novelName: string;
  onClose: () => void;
  onRefresh: () => void;
}

const PIPELINE_ACTIONS = [
  { action: "pre-write-check", label: "写前9问", color: "#8b5cf6" },
  { action: "gate-check", label: "门禁检查", color: "#3b82f6" },
  { action: "post-audit", label: "AI词审计", color: "#f59e0b" },
  { action: "style-check", label: "风格校准", color: "#06b6d4" },
  { action: "character-check", label: "人物一致性", color: "#10b981" },
  { action: "memory-sync", label: "记忆同步", color: "#ef4444" },
  { action: "memory-pack", label: "记忆包", color: "#ec4899" },
];

export default function ChapterDetail({ chapter, platform, novelName, onClose, onRefresh }: Props) {
  const navigate = useNavigate();
  const [runningAction, setRunningAction] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<any>(null);

  const runAction = async (action: string) => {
    setRunningAction(action);
    setJobResult(null);
    try {
      const res = await fetch(
        `/api/novels/${encodeURIComponent(platform)}/${encodeURIComponent(novelName)}/pipeline/${action}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chapter: chapter.chapter_number }),
        }
      );
      const data = await res.json();
      setJobResult(data);

      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const statusRes = await fetch(
            `/api/novels/${encodeURIComponent(platform)}/${encodeURIComponent(novelName)}/pipeline/jobs/${data.job_id}`
          );
          if (statusRes.ok) {
            const status = await statusRes.json();
            if (["completed", "failed", "error"].includes(status.status)) {
              setJobResult(status);
              clearInterval(poll);
              setRunningAction(null);
            }
          }
        } catch {}
      }, 1000);
    } catch (e: any) {
      setJobResult({ error: e.message });
      setRunningAction(null);
    }
  };

  return (
    <div className="w-80 bg-gray-900 border-l border-gray-800 flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-gray-100">第{chapter.chapter_number}章</h3>
          <p className="text-xs text-gray-400">{chapter.title}</p>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-lg leading-none">
          ×
        </button>
      </div>

      {/* Info */}
      <div className="p-4 space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">阶段</span>
          <span className="text-gray-200">{chapter.stage}</span>
        </div>
        {chapter.word_count != null && (
          <div className="flex justify-between">
            <span className="text-gray-500">字数</span>
            <span className="text-gray-200">{chapter.word_count}</span>
          </div>
        )}
        {chapter.rhythm_type && (
          <div className="flex justify-between">
            <span className="text-gray-500">节奏</span>
            <span className="text-amber-400">{chapter.rhythm_type}</span>
          </div>
        )}
      </div>

      {/* Pipeline actions */}
      <div className="p-4 border-t border-gray-800">
        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">流水线操作</h4>
        <div className="space-y-1.5">
          {PIPELINE_ACTIONS.map(({ action, label, color }) => (
            <button
              key={action}
              onClick={() => runAction(action)}
              disabled={runningAction !== null}
              className="w-full text-left px-3 py-2 rounded text-sm bg-gray-800 hover:bg-gray-700 disabled:opacity-50 transition flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-gray-200">{label}</span>
              {runningAction === action && (
                <span className="ml-auto text-xs text-blue-400 animate-pulse">运行中...</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Edit button */}
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={() =>
            navigate(
              `/novel/${encodeURIComponent(platform)}/${encodeURIComponent(novelName)}/chapter/${chapter.chapter_number}`
            )
          }
          className="w-full px-3 py-2 rounded text-sm bg-blue-600 hover:bg-blue-500 text-white transition"
        >
          编辑正文
        </button>
      </div>

      {/* Job result */}
      {jobResult && (
        <div className="p-4 border-t border-gray-800">
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">执行结果</h4>
          {jobResult.error ? (
            <p className="text-xs text-red-400">{jobResult.error}</p>
          ) : (
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">Job ID</span>
                <span className="text-gray-300 font-mono">{jobResult.id || jobResult.job_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">状态</span>
                <span
                  className={
                    jobResult.status === "completed"
                      ? "text-green-400"
                      : jobResult.status === "failed"
                      ? "text-red-400"
                      : "text-yellow-400"
                  }
                >
                  {jobResult.status}
                </span>
              </div>
              {jobResult.logs && jobResult.logs.length > 0 && (
                <div className="mt-2 max-h-40 overflow-y-auto bg-gray-950 rounded p-2 font-mono">
                  {jobResult.logs.slice(-10).map((log: any, i: number) => (
                    <div
                      key={i}
                      className={log.level === "error" ? "text-red-400" : "text-gray-400"}
                    >
                      {log.message}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Foreshadowing */}
      {(chapter.foreshadowing_planted.length > 0 || chapter.foreshadowing_resolved.length > 0) && (
        <div className="p-4 border-t border-gray-800">
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">伏笔</h4>
          {chapter.foreshadowing_planted.map((f, i) => (
            <div key={`p${i}`} className="text-xs text-amber-400 mb-1">
              + {typeof f === "string" ? f : JSON.stringify(f)}
            </div>
          ))}
          {chapter.foreshadowing_resolved.map((f, i) => (
            <div key={`r${i}`} className="text-xs text-green-400 mb-1">
              ✓ {typeof f === "string" ? f : JSON.stringify(f)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
