"use client";

import { ArrowUpRight } from "lucide-react";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const SOURCES = [
  {
    name: "Caselaw Access Project",
    org: "Harvard Law School Library",
    provides:
      "Full-text Supreme Court opinions, 1946 – 2014, harvested from U.S. Reports volumes 327 – 572.",
    href: "https://case.law",
  },
  {
    name: "Supreme Court Database",
    org: "Penn State (originally Washington U. in St. Louis)",
    provides:
      "Structured case-level metadata: issue area, decision direction, voting coalitions, majority writer.",
    href: "http://scdb.la.psu.edu",
  },
  {
    name: "Legal Information Institute",
    org: "Cornell Law School",
    provides:
      "Recent slip opinions, 2015 – present, supplementing the CAP corpus through the current Term.",
    href: "https://www.law.cornell.edu",
  },
];

export function DataSources() {
  return (
    <Section className="bg-ink text-cream-100">
      <Container>
        <div className="mx-auto max-w-3xl text-center">
          <p className="mb-4 font-mono text-xs uppercase tracking-wider text-cream-100/55">
            Inside Lawyer mode
          </p>
          <h2 className="font-display text-4xl font-semibold tracking-tight text-cream-100">
            Our SCOTUS research capability is built on the most trusted open
            legal datasets in the world.
          </h2>
          <p className="mx-auto mt-8 max-w-2xl text-pretty font-sans text-lg leading-relaxed text-cream-100/80">
            Built on case law from the Caselaw Access Project (Harvard Law
            School Library), enriched with structured metadata from the
            Supreme Court Database (Penn State, originally Washington
            University in St. Louis), and supplemented with recent opinions
            from the Legal Information Institute (Cornell Law School).
          </p>
        </div>

        <div className="mt-16 grid gap-4 md:grid-cols-3">
          {SOURCES.map((s) => (
            <a
              key={s.name}
              href={s.href}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative rounded-2xl border border-cream-100/15 bg-cream-100/[0.04] p-6 backdrop-blur-md transition-all hover:border-cream-100/30 hover:bg-cream-100/[0.07]"
            >
              <div className="absolute right-5 top-5 text-cream-100/40 transition-colors group-hover:text-cream-100/80">
                <ArrowUpRight size={16} strokeWidth={2} />
              </div>
              <h3 className="font-display text-xl font-semibold text-cream-100">
                {s.name}
              </h3>
              <p className="mt-1 font-mono text-xs uppercase tracking-wider text-cream-100/55">
                {s.org}
              </p>
              <p className="mt-4 font-sans text-sm leading-relaxed text-cream-100/75">
                {s.provides}
              </p>
            </a>
          ))}
        </div>

        <div className="mt-16 text-center">
          <p className="font-mono text-sm text-cream-100/60">
            9,068 cases · 1946–2025 · 72,496 indexed chunks
          </p>
        </div>
      </Container>
    </Section>
  );
}
