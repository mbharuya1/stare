"use client";

import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const CAPABILITIES = [
  {
    title: "Research with citations",
    body:
      "Ask a legal question. Get an answer grounded in real case law, with " +
      "every claim linked to the specific case and opinion it comes from. " +
      "Every citation is verified against our corpus before it ships to you.",
  },
  {
    title: "Built for trust",
    body:
      "Stare refuses when the evidence is thin. If the case law in our " +
      "corpus does not support an answer, we say so, instead of inventing " +
      "one. Lawyers do not invent precedent. Neither do we.",
  },
  {
    title: "Three modes, one platform",
    body:
      "Whether you are a practitioner researching precedent, a student " +
      "preparing for the bar, or someone trying to understand your rights, " +
      "Stare adapts to who is asking.",
  },
];

export function WhatStareDoes() {
  return (
    <Section className="bg-cream-100">
      <Container>
        <div className="grid gap-6 md:grid-cols-3">
          {CAPABILITIES.map((c) => (
            <div
              key={c.title}
              className="rounded-2xl border border-mist bg-cream-50 p-8 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <h3 className="font-display text-2xl font-semibold tracking-tight text-navy-900">
                {c.title}
              </h3>
              <p className="mt-4 text-pretty font-sans text-[15px] leading-relaxed text-navy-800/80">
                {c.body}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
