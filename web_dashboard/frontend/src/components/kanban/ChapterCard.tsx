import type { ChapterCard } from "../../types";

interface Props {
  chapter: ChapterCard;
  isSelected: boolean;
  onClick: () => void;
}

export default function ChapterCardComponent({ chapter, isSelected, onClick }: Props) {
  const { chapter_number, title, rhythm_type, word_count, gate_passed, audit_passed, sub_stages } = chapter;

  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-lg cursor-pointer transition border ${
        isSelected
          ? "border-blue-500 bg-blue-500/10"
          : "border-gray-800 bg-gray-800/60 hover:bg-gray-800"
      }`}
    >
      {/* Chapter number + title */}
      <div className="flex items-baseline gap-1.5">
        <span className="text-xs text-gray-500 font-mono">#{chapter_number}</span>
        <span className="text-sm font-medium text-gray-100 truncate">{title}</span>
      </div>

      {/* Metadata row */}
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        {word_count != null && (
          <span className="text-xs text-gray-400">{word_count}字</span>
        )}
        {rhythm_type && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">
            {rhythm_type}
          </span>
        )}
      </div>

      {/* Sub-stage indicators for 正文 */}
      {chapter.stage === "正文" && Object.keys(sub_stages).length > 0 && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {[
            { key: "pre_write", label: "写前" },
            { key: "gate", label: "门禁" },
            { key: "audit", label: "审计" },
            { key: "style", label: "风格" },
            { key: "memory_sync", label: "记忆" },
          ].map(({ key, label }) => (
            <span
              key={key}
              className={`text-xs px-1.5 py-0.5 rounded ${
                sub_stages[key] ? "bg-green-500/20 text-green-400" : "bg-gray-700 text-gray-500"
              }`}
            >
              {label}
            </span>
          ))}
        </div>
      )}

      {/* Quality indicators */}
      {(gate_passed != null || audit_passed != null) && (
        <div className="flex gap-2 mt-1.5">
          {gate_passed != null && (
            <span className={`text-xs ${gate_passed ? "text-green-400" : "text-red-400"}`}>
              Gate {gate_passed ? "✓" : "✗"}
            </span>
          )}
          {audit_passed != null && (
            <span className={`text-xs ${audit_passed ? "text-green-400" : "text-red-400"}`}>
              Audit {audit_passed ? "✓" : "✗"}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
