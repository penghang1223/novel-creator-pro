import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function EditorPage() {
  const { platform, novelName, chapterNum } = useParams<{
    platform: string;
    novelName: string;
    chapterNum: string;
  }>();
  const navigate = useNavigate();
  const decodedPlatform = decodeURIComponent(platform || "");
  const decodedName = decodeURIComponent(novelName || "");
  const chapterNumber = parseInt(chapterNum || "1", 10);

  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [wordCount, setWordCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const loadChapter = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(
        `/api/novels/${encodeURIComponent(decodedPlatform)}/${encodeURIComponent(decodedName)}/chapters/${chapterNumber}`
      );
      if (res.ok) {
        const data = await res.json();
        setContent(data.content || "");
        setTitle(data.title || "");
        setWordCount(data.word_count || 0);
      }
    } catch (e: any) {
      setSaveMsg("加载失败: " + e.message);
    } finally {
      setLoading(false);
    }
  }, [decodedPlatform, decodedName, chapterNumber]);

  useEffect(() => { loadChapter(); }, [loadChapter]);

  const handleSave = async () => {
    try {
      setSaving(true);
      setSaveMsg(null);
      const res = await fetch(
        `/api/novels/${encodeURIComponent(decodedPlatform)}/${encodeURIComponent(decodedName)}/chapters/${chapterNumber}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        }
      );
      if (res.ok) {
        const data = await res.json();
        setWordCount(data.word_count || 0);
        setSaveMsg("已保存");
        setTimeout(() => setSaveMsg(null), 2000);
      } else {
        setSaveMsg("保存失败");
      }
    } catch (e: any) {
      setSaveMsg("保存失败: " + e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        加载中...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="px-4 py-2 border-b border-gray-800 flex items-center gap-3 flex-shrink-0">
        <button
          onClick={() => navigate(-1)}
          className="text-xs text-gray-400 hover:text-gray-200"
        >
          ← 返回
        </button>
        <span className="text-sm font-medium text-gray-200">
          第{chapterNumber}章 {title}
        </span>
        <span className="text-xs text-gray-500">{wordCount} 字</span>
        <div className="ml-auto flex items-center gap-2">
          {saveMsg && (
            <span className={`text-xs ${saveMsg.includes("失败") ? "text-red-400" : "text-green-400"}`}>
              {saveMsg}
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded text-xs text-white"
          >
            {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 min-h-0">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full h-full bg-gray-950 text-gray-200 p-4 text-sm leading-relaxed resize-none focus:outline-none font-mono"
          placeholder="开始写作..."
          spellCheck={false}
        />
      </div>
    </div>
  );
}
