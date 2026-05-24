"use client";

import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const PILLARS = [
  {
    title: "Built by practitioners",
    body:
      "Our team writes briefs. We know what good legal reasoning looks " +
      "like, and what it does not.",
  },
  {
    title: "Built by engineers",
    body:
      "Our team ships production systems. We know what AI can do, and " +
      "where it fails. We do not pretend either side is solved.",
  },
];

export function WhyStare() {
  return (
    <Section className="bg-ink text-cream-100">
      <Container>
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="font-display text-[56px] font-semibold leading-tight tracking-tightest text-cream-100">
            We speak both languages.
          </h2>
          <p className="mx-auto mt-8 max-w-[760px] text-pretty font-sans text-[19px] leading-relaxed text-cream-100/85">
            Most legal AI is built by engineers who do not understand the law,
            or by lawyers who do not understand the model. Stare is different.
            Our team holds degrees in both law and computer science. Every
            answer the system produces is grounded in real precedent. Every
            architectural decision is reviewed by someone who has practiced
            and someone who has shipped. If you have ever worried that AI
            legal tools are technically impressive but legally sloppy, or
            legally correct but technically fragile, that is the problem we
            are solving.
          </p>
        </div>

        <div className="mx-auto mt-16 grid max-w-4xl gap-4 md:grid-cols-2">
          {PILLARS.map((p) => (
            <div
              key={p.title}
              className="rounded-2xl border border-cream-100/15 bg-cream-100/[0.04] p-8 backdrop-blur-md transition-all duration-200 hover:-translate-y-0.5 hover:border-cream-100/30 hover:bg-cream-100/[0.07]"
            >
              <h3 className="font-display text-2xl font-semibold text-cream-100">
                {p.title}
              </h3>
              <p className="mt-4 font-sans text-[15px] leading-relaxed text-cream-100/80">
                {p.body}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
