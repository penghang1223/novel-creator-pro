import { useState } from "react";
import { STAGE_ORDER, STAGE_COLORS } from "../../types";
import type { ChapterCard, PipelineStage } from "../../types";
import StageColumn from "./StageColumn";
import ChapterDetail from "./ChapterDetail";

interface Props {
  chapters: ChapterCard[];
  platform: string;
  novelName: string;
  onRefresh: () => void;
}

export default function KanbanBoard({ chapters, platform, novelName, onRefresh }: Props) {
  const [selectedChapter, setSelectedChapter] = useState<ChapterCard | null>(null);

  // Group chapters by stage
  const grouped: Record<string, ChapterCard[]> = {};
  for (const stage of STAGE_ORDER) {
    grouped[stage] = [];
  }
  for (const ch of chapters) {
    if (grouped[ch.stage]) {
      grouped[ch.stage].push(ch);
    }
  }

  return (
    <div className="flex h-full">
      {/* Kanban columns */}
      <div className="flex-1 flex gap-2 p-4 overflow-x-auto">
        {STAGE_ORDER.map((stage) => (
          <StageColumn
            key={stage}
            stage={stage}
            chapters={grouped[stage] || []}
            color={STAGE_COLORS[stage]}
            selectedChapter={selectedChapter}
            onSelect={setSelectedChapter}
          />
        ))}
      </div>

      {/* Detail side panel */}
      {selectedChapter && (
        <ChapterDetail
          chapter={selectedChapter}
          platform={platform}
          novelName={novelName}
          onClose={() => setSelectedChapter(null)}
          onRefresh={onRefresh}
        />
      )}
    </div>
  );
}
