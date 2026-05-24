import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Combine class names with proper Tailwind override semantics. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:8501";
export const GITHUB_URL =
  process.env.NEXT_PUBLIC_GITHUB_URL ||
  "https://github.com/mabrokbharuya/legal-rag-scotus";
