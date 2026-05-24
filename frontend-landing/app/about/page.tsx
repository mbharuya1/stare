import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Nav } from "@/components/marketing/Nav";
import { Footer } from "@/components/marketing/Footer";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";
import { Disclaimer } from "@/components/ui/Disclaimer";
import { GITHUB_URL } from "@/lib/utils";

export const metadata: Metadata = {
  title: "About. Stare.",
  description:
    "About Stare. What we are, what we are not, the team, and the data sources behind our Lawyer mode.",
};

export default function AboutPage() {
  return (
    <>
      <Nav />
      <main>
        <Section className="bg-cream-100" pad="pt-16 md:pt-24 pb-12">
          <Container className="max-w-3xl">
            <h1 className="font-display text-6xl font-semibold tracking-tightest text-navy-900">
              About Stare.
            </h1>
            <p className="mt-6 font-sans text-xl leading-relaxed text-navy-800/75">
              Stare is an AI Law Assistant. We are building it because most
              legal AI today is either technically impressive but legally
              wrong, or legally cautious but technically broken. We refuse
              to ship either.
            </p>
          </Container>
        </Section>

        {/* The project */}
        <Section className="bg-cream-100" pad="py-12">
          <Container className="max-w-3xl space-y-6 font-sans text-base leading-relaxed text-navy-800/85">
            <p>
              Stare (rhymes with <em>starry</em>) is short for <em>stare
              decisis</em>, the legal doctrine of precedent. The platform is
              organized around three modes: Lawyer (live today), Law Student
              (planned for Q3 2026), and General User (planned for Q4 2026).
              Lawyer mode is where our production capabilities live.
            </p>
            <p>
              Inside Lawyer mode, our first capability is SCOTUS research.
              Ask a question about U.S. Supreme Court doctrine, and we route
              it through a classify, retrieve, rerank, generate, and verify
              pipeline. Every answer is grounded in real precedent from a
              corpus of 9,068 Supreme Court opinions covering 1946 through
              2025. Every citation in the final answer is checked against
              the retrieved excerpts before the answer ships.
            </p>
            <p>
              The classify-first design is deliberate. A question about
              cooking pasta or the capital of France never reaches the
              expensive generation step. A small classifier routes it
              straight to a polite refusal. A question on a niche topic the
              corpus does not cover well, where the reranker top score falls
              below a confidence threshold, also refuses, instead of
              fabricating something plausible. We would rather decline than
              guess.
            </p>
            <p>
              The generation prompt instructs Claude to cite only cases
              appearing in the retrieved excerpts, in a strict
              <code className="mx-1 rounded bg-paper px-1.5 py-0.5 font-mono text-sm text-navy-900">[Case Name, US Cite (Year)]</code>
              format. A verification pass parses every citation out of the
              answer and drops any that do not match a retrieved case.
            </p>
            <p>
              On a 15-question evaluation suite, the SCOTUS research
              capability hits 87.5% precision@5 with the cross-encoder
              reranker (versus 62.5% without), 100% citation grounding, and
              100% refusal accuracy on out-of-scope and low-confidence
              questions.
            </p>
          </Container>
        </Section>

        {/* Data sources */}
        <Section className="bg-paper" pad="py-16">
          <Container className="max-w-3xl">
            <p className="mb-4 font-mono text-xs uppercase tracking-wider text-navy-500">
              Inside Lawyer mode
            </p>
            <h2
              id="data-sources"
              className="font-display text-3xl font-semibold tracking-tight text-navy-900"
            >
              Data sources
            </h2>
            <p className="mt-6 font-sans text-base leading-relaxed text-navy-800/80">
              Built on case law from the Caselaw Access Project (Harvard
              Law School Library), enriched with structured metadata from
              the Supreme Court Database (Penn State, originally Washington
              University in St. Louis), and supplemented with recent
              opinions from the Legal Information Institute (Cornell Law
              School).
            </p>
            <ul className="mt-6 space-y-2 font-sans text-sm text-navy-800/75">
              <li>· Caselaw Access Project. U.S. Reports vols 327 through 572 (1946 through 2014).</li>
              <li>· Supreme Court Database release 2025_01 (modern, case-centered, citation file).</li>
              <li>· Cornell LII slip opinions for 2015 through 2025 (about 700 cases supplementing the CAP gap).</li>
            </ul>
          </Container>
        </Section>

        {/* Architecture */}
        <Section className="bg-cream-100" pad="py-16">
          <Container className="max-w-3xl">
            <p className="mb-4 font-mono text-xs uppercase tracking-wider text-navy-500">
              Inside Lawyer mode
            </p>
            <h2
              id="how-it-works"
              className="font-display text-3xl font-semibold tracking-tight text-navy-900"
            >
              How it works
            </h2>
            <p className="mt-6 font-sans text-base leading-relaxed text-navy-800/80">
              Vector recall via ChromaDB pulls the top-20 chunks for a query
              (cosine similarity over MiniLM embeddings). A cross-encoder
              reranker (ms-marco-MiniLM-L-6-v2 on Apple MPS) jointly scores
              each (query, chunk) pair and resorts to top-5. A LangGraph
              state machine routes the request: classify, retrieve and
              rerank, generate, with branch nodes for the two refusal paths.
              Generation uses Claude Sonnet 4.6 with a citation-grounding
              prompt. The response goes through a regex-based verifier
              before reaching the user.
            </p>
            <p className="mt-4 font-sans text-base leading-relaxed text-navy-800/80">
              The full architecture write-up lives in{" "}
              <Link
                href="/architecture"
                className="font-medium text-navy-900 underline decoration-navy-300 underline-offset-4 hover:decoration-navy-800"
              >
                docs/architecture
              </Link>
              .
            </p>
          </Container>
        </Section>

        {/* What this isn't */}
        <Section className="bg-paper" pad="py-16">
          <Container className="max-w-3xl">
            <h2 className="font-display text-3xl font-semibold tracking-tight text-burgundy-700">
              What this is not.
            </h2>
            <p className="mt-6 font-sans text-base leading-relaxed text-navy-800/85">
              This is a research and engineering project. It is not legal
              advice. Lawyers should not use it for real client work today.
              The current corpus is limited to SCOTUS opinions from 1946
              through 2025 and excludes lower courts, statutes, regulations,
              agency guidance, and unpublished opinions. The system can
              still return imperfect retrieval ranking or surface a chunk
              from an overruled holding without explicitly flagging it.
              Read the citations, not just the prose.
            </p>
          </Container>
        </Section>

        <Section className="bg-cream-100" pad="py-12">
          <Container className="max-w-3xl">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-sans text-sm text-navy-800/75 transition-colors hover:text-navy-900"
            >
              See the code on GitHub
              <ArrowUpRight size={14} strokeWidth={2} />
            </a>
            <div className="mt-6">
              <Disclaimer />
            </div>
          </Container>
        </Section>
      </main>
      <Footer />
    </>
  );
}
