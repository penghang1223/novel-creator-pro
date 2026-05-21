// API client for backend

const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Novels
export const getNovels = () => request<any[]>("/novels");
export const getNovel = (platform: string, name: string) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}`);
export const getNovelState = (platform: string, name: string) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/state`);

// Chapters
export const getChapters = (platform: string, name: string) =>
  request<any[]>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/chapters`);
export const getChapter = (platform: string, name: string, num: number) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/chapters/${num}`);
export const saveChapter = (platform: string, name: string, num: number, content: string) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/chapters/${num}`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
export const getChapterSummary = (platform: string, name: string, num: number) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/chapters/${num}/summary`);

// Pipeline
export const runPipeline = (platform: string, name: string, action: string, chapter?: number) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/pipeline/${action}`, {
    method: "POST",
    body: JSON.stringify({ chapter }),
  });
export const getJobStatus = (platform: string, name: string, jobId: string) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/pipeline/jobs/${jobId}`);
export const getJobs = (platform: string, name: string) =>
  request<any[]>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/pipeline/jobs`);

// Memory
export const getMemoryStats = (platform: string, name: string) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/memory/stats`);
export const queryMemory = (platform: string, name: string, type: string) =>
  request<any[]>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/memory/query?type=${type}`);
export const getEntityGraph = (platform: string, name: string) =>
  request<any>(`/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/memory/entity-graph`);

// Health
export const healthCheck = () => request<any>("/health");
