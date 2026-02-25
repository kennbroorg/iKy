import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";

interface VizCardProps {
  title: string;
  children: ReactNode;
  className?: string;
}

export function VizCard({ title, children, className = "" }: VizCardProps) {
  return (
    <Card className={`overflow-hidden border-border/60 p-0 ${className}`}>
      <div className="border-b border-border/40 px-3 py-2">
        <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {title}
        </h4>
      </div>
      <div className="p-3">{children}</div>
    </Card>
  );
}
