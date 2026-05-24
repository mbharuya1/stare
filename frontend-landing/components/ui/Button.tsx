"use client";

import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost";
type Size = "md" | "lg";

interface Props extends Omit<HTMLMotionProps<"a">, "href"> {
  href: string;
  variant?: Variant;
  size?: Size;
  external?: boolean;
}

const base =
  "inline-flex items-center justify-center gap-2 font-sans font-medium " +
  "transition-all focus-visible:outline-none focus-visible:ring-2 " +
  "focus-visible:ring-navy-500 focus-visible:ring-offset-2 " +
  "focus-visible:ring-offset-cream-100 whitespace-nowrap";

const variants: Record<Variant, string> = {
  primary:
    "bg-navy-800 text-cream-100 border border-navy-900 shadow-md " +
    "hover:bg-navy-700 hover:shadow-lg",
  secondary:
    "bg-cream-100 text-navy-800 border border-mist shadow-sm " +
    "hover:bg-paper hover:border-navy-200",
  ghost:
    "text-navy-800 hover:text-navy-900 hover:bg-paper/60 border border-transparent",
};

const sizes: Record<Size, string> = {
  md: "h-10 px-4 text-sm rounded-lg",
  lg: "h-12 px-6 text-base rounded-lg",
};

export function Button({
  href,
  variant = "primary",
  size = "md",
  external,
  className,
  children,
  ...props
}: Props) {
  return (
    <motion.a
      href={href}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer" : undefined}
      whileHover={{ y: variant === "primary" ? -1 : 0 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.15, ease: "easeOut" }}
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </motion.a>
  );
}
