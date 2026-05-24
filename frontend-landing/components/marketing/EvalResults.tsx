"use client";

import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const STATS = [
  { value: "87.5%", label: "Retrieval precision@5 (with reranker)" },
  { value: "+25pp", label: "Improvement over plain-vector baseline" },
  { value: "100%",  label: "Citation grounding rate" },
  { value: "100%",  label: "Refusal accuracy on out-of-scope" },
];

export function EvalResults() {
  return (
    <Section className="bg-paper">
      <Container>
        <div className="text-center">
          <p className="mb-4 font-mono text-xs uppercase tracking-wider text-navy-500">
            Inside Lawyer mode
          </p>
          <h2 className="font-display text-4xl font-semibold tracking-tight text-navy-900">
            What works, measured
          </h2>
          <p className="mx-auto mt-4 max-w-xl font-sans text-base text-navy-800/65">
            Not a vibe. Numbers from a 15-question evaluation suite, repeated
            with and without the reranker.
          </p>
        </div>

        <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((s) => (
            <div
              key={s.label}
              className="rounded-2xl border border-mist bg-cream-50 p-8 text-center shadow-sm transition-all hover:shadow-md"
            >
              <div className="font-display text-6xl font-semibold tracking-tightest text-navy-900">
                {s.value}
              </div>
              <div className="mt-4 font-sans text-sm leading-snug text-navy-800/70">
                {s.label}
              </div>
            </div>
          ))}
        </div>

        <p className="mt-10 text-center font-mono text-xs text-navy-800/55">
          Measured on a 15-question evaluation suite. See{" "}
          <span className="text-navy-900">eval/results.md</span> in the repo.
        </p>
      </Container>
    </Section>
  );
}
