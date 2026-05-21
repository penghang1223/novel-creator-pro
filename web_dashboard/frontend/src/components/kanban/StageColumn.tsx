import type { ChapterCard, PipelineStage } from "../../types";
import ChapterCardComponent from "./ChapterCard";

interface Props {
  stage: PipelineStage;
  chapters: ChapterCard[];
  color: string;
  selectedChapter: ChapterCard | null;
  onSelect: (ch: ChapterCard) => void;
}

export default function StageColumn({ stage, chapters, color, selectedChapter, onSelect }: Props) {
  return (
    <div className="flex-shrink-0 w-64 flex flex-col bg-gray-900/50 rounded-lg">
      {/* Column header */}
      <div className="p-3 border-b border-gray-800" style={{ borderTopColor: color, borderTopWidth: 3 }}>
        <div className="flex items-center justify-between">
          <span className="font-semibold text-sm text-gray-200">{stage}</span>
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ backgroundColor: color + "22", color }}
          >
            {chapters.length}
          </span>
        </div>
      </div>

      {/* Chapter cards */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {chapters.length === 0 ? (
          <div className="text-center py-8 text-gray-600 text-xs">暂无章节</div>
        ) : (
          chapters.map((ch) => (
            <ChapterCardComponent
              key={ch.chapter_number}
              chapter={ch}
              isSelected={selectedChapter?.chapter_number === ch.chapter_number}
              onClick={() => onSelect(ch)}
            />
          ))
        )}
      </div>
    </div>
  );
}
