import { useMemo } from "react";

interface ContributionDay {
  date: string; // YYYY-MM-DD
  level: number; // 0-4
}

interface ContributionCalendarProps {
  htmlData?: string;
  structuredData?: ContributionDay[];
}

/**
 * Level-to-color mapping for contribution heatmap.
 * Follows a zinc (empty) -> emerald -> cyan gradient.
 */
const LEVEL_COLORS = [
  "rgba(63, 63, 70, 0.5)", // 0: zinc-800/50
  "rgba(6, 78, 59, 0.6)", // 1: emerald-900/60
  "rgba(4, 120, 87, 0.7)", // 2: emerald-700/70
  "rgba(16, 185, 129, 0.8)", // 3: emerald-500/80
  "#22d3ee", // 4: cyan-400
] as const;

/**
 * Parse GitHub-scraped contribution calendar HTML.
 * Extracts `data-date` and `data-level` attributes from table cells via regex.
 */
export function parseCalendarHtml(html: string): ContributionDay[] {
  if (!html) return [];

  const days: ContributionDay[] = [];
  // Match elements with data-date and data-level attributes
  const pattern = /data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"/g;
  // Also match the reverse order (data-level before data-date)
  const patternReverse =
    /data-level="(\d)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"/g;

  let match: RegExpExecArray | null;

  match = pattern.exec(html);
  while (match) {
    days.push({ date: match[1], level: Number(match[2]) });
    match = pattern.exec(html);
  }

  match = patternReverse.exec(html);
  while (match) {
    // Reverse order: level is group 1, date is group 2
    const date = match[2];
    // Skip if already captured in the forward pass
    if (!days.some((d) => d.date === date)) {
      days.push({ date, level: Number(match[1]) });
    }
    match = patternReverse.exec(html);
  }

  // Sort by date
  days.sort((a, b) => a.date.localeCompare(b.date));

  return days;
}

/**
 * Contribution calendar heatmap, similar to GitHub's contribution graph.
 * Renders a CSS grid with columns = weeks, rows = 7 days (Sun-Sat).
 * Accepts either raw HTML from a scraper or pre-parsed structured data.
 */
export function ContributionCalendar({
  htmlData,
  structuredData,
}: ContributionCalendarProps) {
  const days = useMemo(() => {
    if (structuredData && structuredData.length > 0) return structuredData;
    if (htmlData) return parseCalendarHtml(htmlData);
    return [];
  }, [htmlData, structuredData]);

  const grid = useMemo(() => {
    if (days.length === 0) return [];

    // Determine the day-of-week of the first date (0 = Sunday)
    const firstDate = new Date(days[0].date + "T00:00:00");
    const startDow = firstDate.getDay();

    // Pad the beginning so the first entry falls on the correct row
    const cells: (ContributionDay | null)[] = [];
    for (let i = 0; i < startDow; i++) {
      cells.push(null);
    }
    for (const day of days) {
      cells.push(day);
    }

    return cells;
  }, [days]);

  if (days.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">
        No contribution data available.
      </p>
    );
  }

  // Number of columns = ceil(total cells / 7)
  const totalWeeks = Math.ceil(grid.length / 7);

  return (
    <div className="overflow-x-auto">
      <div
        className="inline-grid"
        style={{
          gridTemplateRows: "repeat(7, 11px)",
          gridTemplateColumns: `repeat(${totalWeeks}, 11px)`,
          gap: "3px",
          gridAutoFlow: "column",
        }}
      >
        {grid.map((cell, i) => {
          if (!cell) {
            return (
              <div
                key={`empty-${i}`}
                style={{
                  width: 11,
                  height: 11,
                  borderRadius: 2,
                }}
              />
            );
          }

          const color = LEVEL_COLORS[cell.level] ?? LEVEL_COLORS[0];

          return (
            <div
              key={cell.date}
              title={`${cell.date}: level ${cell.level}`}
              style={{
                width: 11,
                height: 11,
                borderRadius: 2,
                backgroundColor: color,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

export type { ContributionDay };
