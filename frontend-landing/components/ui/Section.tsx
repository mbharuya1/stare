"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { HTMLAttributes, ReactNode } from "react";

interface Props extends Omit<HTMLAttributes<HTMLElement>, "children"> {
  children: ReactNode;
  /** Pad y-axis. Defaults to py-24 md:py-32. */
  pad?: string;
  /** Disable scroll-into-view animation (e.g. for hero on first paint). */
  noAnimate?: boolean;
}

/** Section wrapper with a fade-up animation when scrolled into view. */
export function Section({
  children,
  className,
  pad = "py-24 md:py-32",
  noAnimate = false,
  ...props
}: Props) {
  const inner = (
    <div className={cn(pad, className)}>{children}</div>
  );

  if (noAnimate) {
    return <section {...props}>{inner}</section>;
  }

  return (
    <section {...props}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className={cn(pad, className)}
      >
        {children}
      </motion.div>
    </section>
  );
}
