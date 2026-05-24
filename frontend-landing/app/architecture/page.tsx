import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Nav } from "@/components/marketing/Nav";
import { Footer } from "@/components/marketing/Footer";
import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

export const metadata: Metadata = {
  title: "Architecture. Stare.",
  description: "How Stare is built: corpus pipeline, retrieval, agent, and observability.",
};

export default function ArchitecturePage() {
  return (
    <>
      <Nav />
      <main>
        <Section className="bg-cream-100" pad="pt-16 pb-12">
          <Container className="max-w-3xl">
            <Link
              href="/about"
              className="inline-flex items-center gap-1 font-sans text-sm text-navy-800/65 transition-colors hover:text-navy-900"
            >
              <ArrowLeft size={14} strokeWidth={2} />
              Back to About
            </Link>
            <h1 className="mt-6 font-display text-5xl font-semibold tracking-tight text-navy-900">
              Architecture
            </h1>
          </Container>
        </Section>

        <Section className="bg-cream-100" pad="py-8">
          <Container className="max-w-3xl space-y-10 font-sans text-base leading-relaxed text-navy-800/85">
            <section>
              <h2 className="font-display text-2xl font-semibold text-navy-900">
                Pipeline at a glance
              </h2>
              <ol className="mt-4 list-decimal space-y-2 pl-5">
                <li><strong>Ingest.</strong> Download per-volume CAP archives, join with SCDB by U.S. citation, scrape Cornell LII for 2015+ gaps.</li>
                <li><strong>Embed.</strong> Sentence-aware chunking (~500 tokens, 50-token overlap), all-MiniLM-L6-v2 embeddings, persist to ChromaDB (collection <code className="rounded bg-paper px-1 font-mono text-sm">scotus_v2</code>).</li>
                <li><strong>Retrieve.</strong> Top-20 vector recall → cross-encoder rerank → top-5.</li>
                <li><strong>Route.</strong> LangGraph state machine: <code className="rounded bg-paper px-1 font-mono text-sm">classify → retrieve_and_rerank → generate | refuse</code>.</li>
                <li><strong>Generate.</strong> Claude Sonnet 4.6 with a citation-grounding system prompt.</li>
                <li><strong>Verify.</strong> Regex-parse every <code className="rounded bg-paper px-1 font-mono text-sm">[Case, Cite (Year)]</code>, drop unverifiable cites.</li>
              </ol>
            </section>

            <section>
              <h2 className="font-display text-2xl font-semibold text-navy-900">
                Observability
              </h2>
              <p className="mt-4">
                LangSmith tracing is wired up at startup; each query produces
                a trace covering classify → retrieve → rerank → generate.
                MLflow logs the A/B comparison: routing accuracy, P@5,
                citation grounding, refusal accuracy, latency, and token
                spend, with reranker on/off as the discriminator.
              </p>
            </section>

            <section>
              <h2 className="font-display text-2xl font-semibold text-navy-900">
                Deployment target
              </h2>
              <p className="mt-4">
                Landing page: AWS Amplify (static export). Streamlit app +
                FastAPI backend: AWS EC2. Corpus snapshots: AWS S3 versioned bucket.
              </p>
            </section>
          </Container>
        </Section>
      </main>
      <Footer />
    </>
  );
}
