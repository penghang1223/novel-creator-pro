// TypeScript types matching backend Pydantic models

export type PipelineStage = "创意" | "设定" | "大纲" | "细纲" | "正文" | "记忆更新" | "完结复盘";

export const STAGE_ORDER: PipelineStage[] = ["创意", "设定", "大纲", "细纲", "正文", "记忆更新", "完结复盘"];

export const STAGE_COLORS: Record<PipelineStage, string> = {
  "创意": "#8b5cf6",
  "设定": "#06b6d4",
  "大纲": "#3b82f6",
  "细纲": "#6366f1",
  "正文": "#f59e0b",
  "记忆更新": "#10b981",
  "完结复盘": "#ef4444",
};

export interface ChapterCard {
  chapter_number: number;
  title: string;
  stage: PipelineStage;
  rhythm_type: string | null;
  word_count: number | null;
  audit_passed: boolean | null;
  gate_passed: boolean | null;
  last_updated: string | null;
  sub_stages: Record<string, boolean>;
  foreshadowing_planted: string[];
  foreshadowing_resolved: string[];
}

export interface NovelListItem {
  novel_name: string;
  platform: string;
  chapters_written: number;
  current_stage: PipelineStage;
  last_updated: string | null;
}

export interface NovelOverview {
  novel_name: string;
  platform: string;
  total_chapters_planned: number;
  chapters_written: number;
  current_stage: PipelineStage;
  chapters: ChapterCard[];
  protagonist: Record<string, any>;
  last_updated: string | null;
}

export interface ChapterContent {
  chapter_number: number;
  title: string;
  content: string;
  word_count: number;
}

export interface ChapterMetrics {
  narrative_tension: number;
  emotional_change: number;
  foreshadowing_density: string;
  information_release: string;
  relationship_shift: string;
  knowledge_reference_count: number;
}

export interface LogEntry {
  timestamp: string;
  level: "info" | "warn" | "error" | "debug";
  message: string;
}

export interface JobStatus {
  id: string;
  action: string;
  status: "pending" | "running" | "completed" | "failed" | "error";
  exit_code: number | null;
  logs: LogEntry[];
}

export interface MemoryStats {
  style_dna: number;
  character: number;
  plot: number;
  context: number;
  history: number;
  entity_graph?: {
    entities: number;
    edges: number;
  };
}
