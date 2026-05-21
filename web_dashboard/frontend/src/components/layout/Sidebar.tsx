import { Link, useLocation } from "react-router-dom";
import { useNovelList } from "../../hooks/useApi";
import type { PipelineStage } from "../../types";
import { STAGE_COLORS } from "../../types";

export default function Sidebar() {
  const { novels, loading } = useNovelList();
  const location = useLocation();

  // Extract current novel from URL
  const match = location.pathname.match(/\/novel\/([^/]+)\/(.+)/);
  const currentPlatform = match ? decodeURIComponent(match[1]) : "";
  const currentName = match ? decodeURIComponent(match[2]) : "";

  return (
    <aside className="w-64 bg-gray-900 text-gray-100 flex flex-col h-screen">
      <div className="p-4 border-b border-gray-700">
        <Link to="/" className="text-lg font-bold text-white hover:text-blue-400 transition">
          小说创作 Pro Max
        </Link>
        <p className="text-xs text-gray-500 mt-1">可视化工作流面板</p>
      </div>

      {/* Novel list */}
      <div className="flex-1 overflow-y-auto p-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">小说列表</h3>
        {loading ? (
          <p className="text-sm text-gray-500">加载中...</p>
        ) : novels.length === 0 ? (
          <p className="text-sm text-gray-500">未找到小说</p>
        ) : (
          <div className="space-y-1">
            {novels.map((novel) => {
              const isActive = novel.platform === currentPlatform && novel.novel_name === currentName;
              return (
                <Link
                  key={`${novel.platform}/${novel.novel_name}`}
                  to={`/novel/${encodeURIComponent(novel.platform)}/${encodeURIComponent(novel.novel_name)}`}
                  className={`block px-3 py-2 rounded text-sm transition ${
                    isActive ? "bg-blue-600 text-white" : "text-gray-300 hover:bg-gray-800"
                  }`}
                >
                  <div className="font-medium truncate">{novel.novel_name}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className="inline-block w-2 h-2 rounded-full"
                      style={{ backgroundColor: STAGE_COLORS[novel.current_stage as PipelineStage] || "#666" }}
                    />
                    <span className="text-xs text-gray-400">
                      {novel.platform} · {novel.chapters_written}章 · {novel.current_stage}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Navigation */}
      {currentPlatform && currentName && (
        <nav className="border-t border-gray-700 p-3">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">导航</h3>
          <div className="space-y-1">
            {[
              { path: "", label: "看板", icon: "⊞" },
              { path: "/audit", label: "审计", icon: "◉" },
              { path: "/memory", label: "记忆", icon: "◈" },
              { path: "/config", label: "配置", icon: "⚙" },
            ].map(({ path, label, icon }) => (
              <Link
                key={path}
                to={`/novel/${encodeURIComponent(currentPlatform)}/${encodeURIComponent(currentName)}${path}`}
                className="block px-3 py-1.5 rounded text-sm text-gray-300 hover:bg-gray-800 transition"
              >
                {icon} {label}
              </Link>
            ))}
          </div>
        </nav>
      )}
    </aside>
  );
}
