import { useState, useEffect, useCallback } from "react";
import type { NovelOverview, ChapterCard, JobStatus, LogEntry } from "../types";

export function useNovelList() {
  const [novels, setNovels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNovels = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/novels");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setNovels(await res.json());
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchNovels(); }, [fetchNovels]);
  return { novels, loading, error, refetch: fetchNovels };
}

export function useNovel(platform: string, name: string) {
  const [novel, setNovel] = useState<NovelOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNovel = useCallback(async () => {
    if (!platform || !name) return;
    try {
      setLoading(true);
      const res = await fetch(
        `/api/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setNovel(await res.json());
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [platform, name]);

  useEffect(() => { fetchNovel(); }, [fetchNovel]);
  return { novel, loading, error, refetch: fetchNovel };
}

export function useJobLogs(platform: string, name: string, jobId: string | null) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState<string>("pending");

  useEffect(() => {
    if (!jobId) return;

    const wsUrl = window.location.protocol === "https:"
      ? `wss://${window.location.host}/ws/logs`
      : `ws://${window.location.host}/ws/logs`;
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => {
      ws.send(JSON.stringify({ job_id: jobId }));
    };
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "log") {
        setLogs((prev) => [...prev, { timestamp: msg.timestamp, level: msg.level, message: msg.message }]);
      } else if (msg.type === "done") {
        setStatus(msg.status);
      }
    };
    ws.onerror = () => {
      // Fallback to polling
      const poll = setInterval(async () => {
        try {
          const res = await fetch(
            `/api/novels/${encodeURIComponent(platform)}/${encodeURIComponent(name)}/pipeline/jobs/${jobId}`
          );
          if (res.ok) {
            const data = await res.json();
            setLogs(data.logs || []);
            if (["completed", "failed", "error"].includes(data.status)) {
              setStatus(data.status);
              clearInterval(poll);
            }
          }
        } catch {}
      }, 1000);
    };
    return () => ws.close();
  }, [jobId, platform, name]);

  return { logs, status };
}
