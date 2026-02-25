import type { TimelineEvent } from "@/types/api";
import type { TaskEntry } from "@/stores/gather-store";

export interface AggregatedTimelineEvent extends TimelineEvent {
  source: string;
}

export function aggregateTimeline(
  tasks: Record<string, TaskEntry>,
): AggregatedTimelineEvent[] {
  const events: AggregatedTimelineEvent[] = [];

  for (const [moduleName, task] of Object.entries(tasks)) {
    if (task.status !== "success" || !task.result?.timeline) continue;
    for (const event of task.result.timeline) {
      events.push({ ...event, source: moduleName });
    }
  }

  events.sort((a, b) => {
    const dateA = new Date(a.date.replace(/\//g, "-"));
    const dateB = new Date(b.date.replace(/\//g, "-"));
    return dateB.getTime() - dateA.getTime();
  });

  return events;
}
