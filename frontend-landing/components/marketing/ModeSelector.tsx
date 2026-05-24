"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { cn, APP_URL } from "@/lib/utils";
import {
  DoricColumnGlyph,
  BookQuillGlyph,
  PersonQuestionGlyph,
} from "./Glyphs";

type CapGroup = {
  label: string;
  tone: "live" | "soon";
  items: string[];
};

type Mode = {
  id: string;
  title: string;
  description: string;
  status: { label: string; tone: "active" | "soon" };
  glyph: React.ReactNode;
  href?: string;
  groups: CapGroup[];
};

const MODES: Mode[] = [
  {
    id: "lawyer",
    title: "Lawyer",
    description:
      "Production legal research, grounded citations, and honest refusal " +
      "when the evidence is thin.",
    status: { label: "Available now", tone: "active" },
    glyph: <DoricColumnGlyph size={56} />,
    href: APP_URL,
    groups: [
      {
        label: "Live",
        tone: "live",
        items: [
          "SCOTUS research (9,000+ Supreme Court opinions, 1946 to 2025)",
          "Citation-grounded answers with source verification",
          "Honest refusal when evidence is insufficient",
        ],
      },
      {
        label: "Coming soon",
        tone: "soon",
        items: [
          "Lower federal court opinions",
          "Federal and state statutes",
          "Federal regulations",
          "Federal agency guidance",
        ],
      },
    ],
  },
  {
    id: "law-student",
    title: "Law Student",
    description:
      "An AI tutor that drills, briefs, and quizzes alongside you.",
    status: { label: "Q3 2026", tone: "soon" },
    glyph: <BookQuillGlyph size={56} />,
    groups: [
      {
        label: "Coming soon",
        tone: "soon",
        items: [
          "Case brief generator",
          "IRAC drill mode",
          "Cold-call simulator",
          "Bar-exam practice questions",
        ],
      },
    ],
  },
  {
    id: "general",
    title: "General User",
    description:
      "Plain-English answers for everyday legal questions.",
    status: { label: "Q4 2026", tone: "soon" },
    glyph: <PersonQuestionGlyph size={56} />,
    groups: [
      {
        label: "Coming soon",
        tone: "soon",
        items: [
          "Plain-English legal guidance",
          "Tenant rights",
          "Employment basics",
          "Consumer protection",
        ],
      },
    ],
  },
];


function CapabilityList({ group }: { group: CapGroup }) {
  const isLive = group.tone === "live";
  return (
    <div className="mt-5">
      <div
        className={cn(
          "font-mono text-xs uppercase tracking-wider",
          isLive ? "text-green-700" : "text-navy-500",
        )}
      >
        {group.label}
      </div>
      <ul className="mt-3 space-y-2">
        {group.items.map((item) => (
          <li
            key={item}
            className="flex items-start gap-2.5 font-sans text-sm leading-snug text-navy-800/85"
          >
            <span
              aria-hidden="true"
              className={cn(
                "mt-[7px] inline-block h-1.5 w-1.5 shrink-0 rounded-full",
                isLive ? "bg-green-600" : "bg-neutral-400",
              )}
            />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}


export function ModeSelector() {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <Section id="modes" className="bg-cream-100">
      <Container>
        <div className="text-center">
          <h2 className="font-display text-5xl font-semibold tracking-tight text-navy-900">
            Choose your experience
          </h2>
          <p className="mx-auto mt-4 max-w-xl font-sans text-lg text-navy-800/70">
            Stare adapts to who is asking.
          </p>
        </div>

        <div
          className="mt-16 grid gap-6 md:grid-cols-3"
          onMouseLeave={() => setHovered(null)}
        >
          {MODES.map((m) => {
            const isActive = m.status.tone === "active";
            const dim = hovered !== null && hovered !== m.id;
            const Wrapper = isActive ? motion.a : motion.div;
            const wrapperProps = isActive
              ? {
                  href: m.href,
                  onMouseEnter: () => setHovered(m.id),
                  whileHover: { y: -3 },
                  transition: { duration: 0.2, ease: "easeOut" },
                }
              : { onMouseEnter: () => setHovered(m.id) };

            return (
              <Wrapper
                key={m.id}
                {...(wrapperProps as object)}
                className={cn(
                  "group block rounded-2xl border bg-cream-50 p-8 text-left shadow-sm transition-all",
                  isActive
                    ? "cursor-pointer border-mist focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-500 focus-visible:ring-offset-2 hover:border-navy-200 hover:shadow-glow"
                    : "cursor-default border-mist/70",
                  !isActive && "opacity-65",
                  dim && "opacity-50",
                )}
              >
                <div className="mb-6 flex items-start justify-between">
                  <div
                    className={cn(
                      "flex h-14 w-14 items-center justify-center text-navy-800",
                      !isActive && "text-navy-800/60",
                    )}
                  >
                    {m.glyph}
                  </div>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                      m.status.tone === "active"
                        ? "bg-burgundy-100/60 text-burgundy-700"
                        : "bg-neutral-100 text-neutral-600",
                    )}
                  >
                    {m.status.label}
                  </span>
                </div>

                <h3 className="font-display text-2xl font-semibold tracking-tight text-navy-900">
                  {m.title}
                </h3>
                <p className="mt-3 font-sans text-sm leading-relaxed text-navy-800/70">
                  {m.description}
                </p>

                {m.groups.map((g) => (
                  <CapabilityList key={g.label} group={g} />
                ))}
              </Wrapper>
            );
          })}
        </div>

        <div className="mt-12 text-center">
          <Disclaimer short className="mx-auto" />
        </div>
      </Container>
    </Section>
  );
}
