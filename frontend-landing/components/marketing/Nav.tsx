"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";
import { APP_URL, GITHUB_URL } from "@/lib/utils";

export function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-mist bg-cream-100/85 backdrop-blur-md">
      <Container className="flex h-14 items-center justify-between">
        <Link
          href="/"
          className="font-display text-2xl font-semibold tracking-tight text-navy-900"
        >
          Stare
        </Link>
        <nav className="flex items-center gap-2 md:gap-4">
          <Link
            href="/about"
            className="hidden text-sm text-navy-800/75 transition-colors hover:text-navy-900 md:inline-flex"
          >
            About
          </Link>
          <Link
            href="/about#how-it-works"
            className="hidden text-sm text-navy-800/75 transition-colors hover:text-navy-900 md:inline-flex"
          >
            Architecture
          </Link>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden items-center gap-1 text-sm text-navy-800/75 transition-colors hover:text-navy-900 md:inline-flex"
          >
            GitHub
            <ArrowUpRight size={14} strokeWidth={2} />
          </a>
          <Button href={APP_URL} variant="primary" size="md" external className="ml-2">
            Try Stare
          </Button>
        </nav>
      </Container>
    </header>
  );
}
