import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { GITHUB_URL } from "@/lib/utils";

export function Footer() {
  return (
    <footer className="border-t border-mist bg-cream-100">
      <Container className="py-12">
        <div className="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
          <div>
            <Link
              href="/"
              className="font-display text-2xl font-semibold tracking-tight text-navy-900"
            >
              Stare
            </Link>
            <p className="mt-2 font-sans text-sm text-navy-800/65">
              © 2026 Stare. All rights reserved.
            </p>
          </div>

          <nav className="flex items-center gap-6 text-sm text-navy-800/75">
            <Link href="/about" className="transition-colors hover:text-navy-900">
              About
            </Link>
            <Link
              href="/about#how-it-works"
              className="transition-colors hover:text-navy-900"
            >
              Architecture
            </Link>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 transition-colors hover:text-navy-900"
            >
              GitHub
              <ArrowUpRight size={14} strokeWidth={2} />
            </a>
            <Link href="#" className="transition-colors hover:text-navy-900">
              Privacy
            </Link>
          </nav>
        </div>

        <div className="mt-10 border-t border-mist pt-8">
          <p className="font-sans text-[13px] leading-relaxed text-navy-800/55">
            Stare is a research and engineering project. Information provided
            by Stare is not legal advice. For specific legal matters, consult
            a licensed attorney.
          </p>
        </div>
      </Container>
    </footer>
  );
}
