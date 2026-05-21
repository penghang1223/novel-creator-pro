import { useParams } from "react-router-dom";
import { useNovel } from "../hooks/useApi";
import KanbanBoard from "../components/kanban/KanbanBoard";

export default function KanbanPage() {
  const { platform, novelName } = useParams<{ platform: string; novelName: string }>();
  const decodedPlatform = decodeURIComponent(platform || "");
  const decodedName = decodeURIComponent(novelName || "");
  const { novel, loading, error, refetch } = useNovel(decodedPlatform, decodedName);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        加载中...
      </div>
    );
  }

  if (error || !novel) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="text-red-400">加载失败: {error || "未找到小说"}</p>
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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-sm font-bold text-gray-100">{novel.novel_name}</h1>
          <p className="text-xs text-gray-500">
            {novel.platform} · {novel.chapters_written}/{novel.total_chapters_planned || "?"} 章
          </p>
        </div>
        <button
          onClick={refetch}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-xs text-gray-300"
        >
          刷新
        </button>
      </div>

      {/* Kanban */}
      <div className="flex-1 min-h-0">
        <KanbanBoard
          chapters={novel.chapters}
          platform={decodedPlatform}
          novelName={decodedName}
          onRefresh={refetch}
        />
      </div>
    </div>
  );
}
