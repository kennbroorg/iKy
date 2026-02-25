import { useMemo } from "react";
import { Clock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { getModuleIcon } from "@/lib/icon-map";
import { getModule } from "@/lib/module-registry";
import {
  aggregateTimeline,
  type AggregatedTimelineEvent,
} from "@/lib/timeline-aggregator";
import { useGatherStore } from "@/stores/gather-store";

function EmptyState() {
  return (
    <p className="py-8 text-center text-sm italic text-muted-foreground">
      Run a search from the Gatherer page to see timeline events.
    </p>
  );
}

function TimelineEvent({ event }: { event: AggregatedTimelineEvent }) {
  const mod = getModule(event.source);
  const Icon = getModuleIcon(mod?.icon ?? "globe");
  const label = mod?.label ?? event.source;

  // Format the date for display
  const displayDate = event.date.replace(/\//g, "-");

  return (
    <div className="relative pl-8">
      {/* Dot on the timeline */}
      <div className="absolute left-[-5px] top-1.5 size-2.5 rounded-full border-2 border-primary bg-background" />

      <div className="space-y-1 pb-6">
        {/* Date + module badge row */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground">
            <Clock className="mr-1 inline size-3" />
            {displayDate}
          </span>
          <Badge variant="outline" className="gap-1 text-[10px]">
            <Icon className="size-3" />
            {label}
          </Badge>
        </div>

        {/* Action text */}
        <p className="text-sm font-medium text-foreground">{event.action}</p>

        {/* Optional description */}
        {event.desc && (
          <p className="text-xs text-muted-foreground">{event.desc}</p>
        )}
      </div>
    </div>
  );
}

export default function TimelinePage() {
  const tasks = useGatherStore((s) => s.tasks);
  const events = useMemo(() => aggregateTimeline(tasks), [tasks]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-primary">Timeline</h1>
      <p className="text-sm text-muted-foreground">
        Chronological events from all modules, newest first.
      </p>

      {events.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="ml-2 border-l-2 border-muted">
          {events.map((event, i) => (
            <TimelineEvent
              key={`${event.source}-${event.date}-${i}`}
              event={event}
            />
          ))}
        </div>
      )}
    </div>
  );
}
