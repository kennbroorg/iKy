import { useMemo } from "react";

import { cn } from "@/lib/utils";

interface WordCloudProps {
  words: { text: string; value: number }[];
  maxWords?: number;
}

/** Cyan/teal color palette for word cloud variation */
const WORD_COLORS = [
  "text-cyan-400",
  "text-cyan-500",
  "text-teal-400",
  "text-teal-500",
  "text-cyan-300",
  "text-teal-300",
  "text-cyan-600",
  "text-teal-600",
] as const;

/**
 * Map a value in [min, max] to a font size in [minSize, maxSize] rem.
 */
function scaleSize(
  value: number,
  min: number,
  max: number,
  minSize: number,
  maxSize: number,
): number {
  if (max === min) return (minSize + maxSize) / 2;
  const ratio = (value - min) / (max - min);
  return minSize + ratio * (maxSize - minSize);
}

/**
 * Flexbox-based word cloud component.
 * Each word is rendered as a span with size proportional to its value
 * and varying cyan/teal colors with opacity.
 */
export function WordCloud({ words, maxWords = 50 }: WordCloudProps) {
  const processedWords = useMemo(() => {
    if (!words || words.length === 0) return [];

    // Sort by value descending, take top N
    const sorted = [...words]
      .sort((a, b) => b.value - a.value)
      .slice(0, maxWords);

    const min = Math.min(...sorted.map((w) => w.value));
    const max = Math.max(...sorted.map((w) => w.value));

    // Map each word to its display props
    return sorted.map((word, i) => ({
      text: word.text,
      value: word.value,
      fontSize: scaleSize(word.value, min, max, 0.75, 2.5),
      colorClass: WORD_COLORS[i % WORD_COLORS.length],
      // Higher-value words get higher opacity
      opacity: scaleSize(word.value, min, max, 0.5, 1),
    }));
  }, [words, maxWords]);

  if (processedWords.length === 0) {
    return (
      <p className="text-sm italic text-muted-foreground">
        No word data available.
      </p>
    );
  }

  // Shuffle for visual variety (deterministic based on text)
  const shuffled = useMemo(() => {
    const arr = [...processedWords];
    // Simple shuffle using text chars as seed-like variation
    for (let i = arr.length - 1; i > 0; i--) {
      const j = arr[i].text.charCodeAt(0) % (i + 1);
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }, [processedWords]);

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 rounded-md border border-border bg-background/30 p-4">
      {shuffled.map((word) => (
        <span
          key={word.text}
          className={cn(
            "inline-block cursor-default font-medium transition-opacity duration-200 hover:opacity-100",
            word.colorClass,
          )}
          style={{
            fontSize: `${word.fontSize}rem`,
            opacity: word.opacity,
          }}
          title={`${word.text}: ${word.value}`}
        >
          {word.text}
        </span>
      ))}
    </div>
  );
}
