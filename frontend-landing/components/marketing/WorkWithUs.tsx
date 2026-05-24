"use client";

import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";
import { Button } from "@/components/ui/Button";

const CARDS = [
  {
    title: "Join the team",
    body:
      "We are hiring across engineering, legal research, and design. Send " +
      "us your story.",
    cta: "Apply",
    href: "mailto:mbharuya1@babson.edu?subject=Joining%20Stare",
  },
  {
    title: "Partner with us",
    body:
      "Law firms, legal-aid organizations, and university clinics " +
      "interested in piloting Stare can reach out.",
    cta: "Get in touch",
    href: "mailto:mbharuya1@babson.edu?subject=Partnership%20inquiry",
  },
  {
    title: "Press and investors",
    body:
      "Investors and journalists writing about AI in legal practice can " +
      "contact us directly.",
    cta: "Reach out",
    href: "mailto:mbharuya1@babson.edu?subject=Press%20inquiry",
  },
];

export function WorkWithUs() {
  return (
    <Section className="bg-cream-100">
      <Container>
        <div className="text-center">
          <h2 className="font-display text-5xl font-semibold tracking-tight text-navy-900">
            Work with us.
          </h2>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {CARDS.map((c) => (
            <div
              key={c.title}
              className="flex flex-col rounded-2xl border border-navy-900/10 bg-paper p-8 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <h3 className="font-display text-2xl font-semibold tracking-tight text-navy-900">
                {c.title}
              </h3>
              <p className="mt-4 grow font-sans text-[15px] leading-relaxed text-navy-800/80">
                {c.body}
              </p>
              <div className="mt-6">
                <Button href={c.href} variant="primary" size="lg">
                  {c.cta}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
