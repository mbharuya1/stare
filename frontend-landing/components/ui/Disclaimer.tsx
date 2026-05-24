import { cn } from "@/lib/utils";

interface Props {
  className?: string;
  short?: boolean;
}

const SHORT = "Research and portfolio project. Not legal advice.";
const LONG =
  "Stare is a portfolio research project, not a commercial legal-research product. " +
  "It is not a substitute for advice from a licensed attorney. The corpus covers " +
  "Supreme Court opinions from 1946 through 2025 and excludes lower courts, statutes, " +
  "regulations, agency guidance, and unpublished opinions. Do not rely on Stare for " +
  "real client matters.";

export function Disclaimer({ className, short = false }: Props) {
  return (
    <p
      className={cn(
        "text-xs leading-relaxed text-navy-800/55",
        className,
      )}
    >
      {short ? SHORT : LONG}
    </p>
  );
}
