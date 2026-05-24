"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const BADGES = ["Law, Assas", "CS, Sorbonne", "MSBA, Babson"];

export function Founder() {
  return (
    <Section className="bg-cream-100">
      <Container>
        <div className="text-center">
          <h2 className="font-display text-5xl font-semibold tracking-tight text-navy-900">
            Who is behind Stare.
          </h2>
        </div>

        <div className="mx-auto mt-16 max-w-2xl rounded-2xl border border-mist bg-paper p-12 text-center shadow-lg">
          <motion.div
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="mx-auto h-40 w-40 overflow-hidden rounded-full ring-2 ring-navy-900 ring-offset-4 ring-offset-paper"
          >
            <Image
              src="/team/mabrok.png"
              alt="Mabrok BHARUYA, founder of Stare"
              width={160}
              height={160}
              className="h-full w-full object-cover"
              priority
            />
          </motion.div>

          <h3 className="mt-8 font-display text-[32px] font-semibold tracking-tight text-navy-900">
            Mabrok BHARUYA
          </h3>
          <p className="mt-2 font-sans text-sm uppercase tracking-wider text-navy-600">
            Founder
          </p>

          <p className="mx-auto mt-6 max-w-[620px] text-pretty font-sans text-[17px] leading-relaxed text-navy-800">
            Mabrok holds a law degree from Université Paris-Panthéon-Assas,
            the top-ranked law school in France, and a computer science
            degree from Sorbonne Université, France&apos;s top-ranked
            research university for sciences. He is finishing an MSBA on the
            quantitative track at Babson College. Before founding Stare, he
            built production AI systems at Venture Space in London, where he
            led the development of a legal technology platform deployed to
            law firms, and at Assas Lab in Paris. He started Stare because
            he kept watching legal AI products fail in one of two ways:
            technically impressive but legally wrong, or legally cautious
            but technically broken. Stare is the answer to that gap.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
            {BADGES.map((b) => (
              <span
                key={b}
                className="inline-flex items-center rounded-full bg-navy-900/10 px-3 py-1 font-sans text-[13px] font-medium text-navy-800"
              >
                {b}
              </span>
            ))}
          </div>
        </div>

        <p className="mx-auto mt-12 max-w-[620px] text-center text-pretty font-sans text-[17px] leading-relaxed text-navy-700">
          We are building a small, intentional team. If you are an attorney, a
          machine learning engineer, or a designer who cares about the rule of
          law and the craft of software in equal measure, we want to hear from
          you.
        </p>
      </Container>
    </Section>
  );
}
