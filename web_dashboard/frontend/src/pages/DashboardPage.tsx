import { useNavigate } from "react-router-dom";
import { useNovelList } from "../hooks/useApi";
import { STAGE_COLORS } from "../types";

export default function DashboardPage() {
  const { novels, loading, error, refetch } = useNovelList();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        加载中...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="text-red-400">连接失败: {error}</p>
        <button
          onClick={refetch}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm text-gray-200"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-100">小说总览</h1>
        <button
          onClick={refetch}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs text-gray-300"
        >
          刷新
        </button>
      </div>

      {novels.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-2">novel_output/ 下暂无小说</p>
          <p className="text-sm">创建小说后刷新页面</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {novels.map((novel) => (
            <div
              key={`${novel.platform}/${novel.novel_name}`}
              onClick={() =>
                navigate(
                  `/novel/${encodeURIComponent(novel.platform)}/${encodeURIComponent(novel.novel_name)}`
                )
              }
              className="p-4 bg-gray-900 border border-gray-800 rounded-lg cursor-pointer hover:bg-gray-800/60 transition"
            >
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-100 truncate">
                  {novel.novel_name}
                </h2>
                <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">
                  {novel.platform}
                </span>
              </div>

              <div className="flex items-center gap-3 text-xs text-gray-400">
                <span>{novel.chapters_written} 章</span>
                <span
                  className="px-1.5 py-0.5 rounded"
                  style={{
                    backgroundColor: STAGE_COLORS[novel.current_stage] + "22",
                    color: STAGE_COLORS[novel.current_stage],
                  }}
                >
                  {novel.current_stage}
                </span>
              </div>

              {novel.last_updated && (
                <p className="mt-2 text-xs text-gray-600">
                  更新于 {new Date(novel.last_updated).toLocaleDateString("zh-CN")}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
