import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function Card({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-mist bg-cream-50 p-6 shadow-sm",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
