"use client";

import { Container } from "@/components/ui/Container";
import { Section } from "@/components/ui/Section";

const TECH = [
  {
    name: "PyTorch + Hugging Face",
    why: "Cross-encoder reranker (ms-marco-MiniLM-L-6-v2) on Apple MPS.",
  },
  {
    name: "LangChain + LangGraph",
    why: "Agent orchestration: classify → route → retrieve → generate.",
  },
  {
    name: "ChromaDB",
    why: "Local vector store, 72K chunks indexed with all-MiniLM-L6-v2.",
  },
  {
    name: "Claude Sonnet 4.6",
    why: "Citation-grounded generation with explicit refusal logic.",
  },
  {
    name: "LangSmith",
    why: "Production tracing of every query through the LangGraph state machine.",
  },
  {
    name: "MLflow",
    why: "Experiment tracking. Reranker on/off A/B with logged metrics.",
  },
  {
    name: "FastAPI",
    why: "Async backend, pydantic-validated, OpenAPI-documented.",
  },
  {
    name: "AWS (Amplify + EC2 + S3)",
    why: "Static landing on Amplify, backend on EC2, corpus snapshots on S3.",
  },
];

function FlowDiagram() {
  // Lightweight inline SVG. Three stacked rounded-rect nodes with arrows.
  // Deliberately understated; not a Mermaid blob.
  return (
    <div className="mx-auto mt-12 max-w-3xl">
      <svg
        viewBox="0 0 720 220"
        className="h-auto w-full"
        role="img"
        aria-label="Pipeline: question → LangGraph router → retrieval, rerank, generation → cited answer"
      >
        <defs>
          <marker
            id="arr"
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M0 0 L10 5 L0 10 z" fill="currentColor" />
          </marker>
        </defs>

        {/* node 1. Question */}
        <g transform="translate(20 80)" className="text-navy-800">
          <rect width="140" height="60" rx="12" fill="#f5f3ee" stroke="currentColor" strokeWidth="1" />
          <text x="70" y="36" textAnchor="middle" fontFamily="var(--font-display)" fontSize="16" fill="currentColor">
            Question
          </text>
        </g>

        {/* arrow 1 */}
        <line
          x1="170" y1="110" x2="230" y2="110"
          stroke="currentColor" strokeWidth="1.2"
          className="text-navy-800/60"
          markerEnd="url(#arr)"
        />

        {/* node 2. Router */}
        <g transform="translate(240 60)" className="text-navy-800">
          <rect width="220" height="100" rx="12" fill="#1a2540" stroke="#1a2540" />
          <text x="110" y="38" textAnchor="middle" fontFamily="var(--font-display)" fontSize="16" fill="#fafaf7">
            LangGraph Router
          </text>
          <text x="110" y="62" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="11" fill="#fafaf7" opacity="0.7">
            classify → retrieve+rerank
          </text>
          <text x="110" y="78" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="11" fill="#fafaf7" opacity="0.7">
            → generate | refuse
          </text>
        </g>

        {/* arrow 2 */}
        <line
          x1="470" y1="110" x2="530" y2="110"
          stroke="currentColor" strokeWidth="1.2"
          className="text-navy-800/60"
          markerEnd="url(#arr)"
        />

        {/* node 3. Cited answer */}
        <g transform="translate(540 80)" className="text-navy-800">
          <rect width="160" height="60" rx="12" fill="#f5f3ee" stroke="currentColor" strokeWidth="1" />
          <text x="80" y="32" textAnchor="middle" fontFamily="var(--font-display)" fontSize="15" fill="currentColor">
            Cited answer
          </text>
          <text x="80" y="50" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="10" fill="currentColor" opacity="0.65">
            verified citations
          </text>
        </g>
      </svg>
    </div>
  );
}

export function TechStack() {
  return (
    <Section id="how-it-works" className="bg-cream-100">
      <Container>
        <div className="text-center">
          <p className="mb-4 font-mono text-xs uppercase tracking-wider text-navy-500">
            Inside Lawyer mode
          </p>
          <h2 className="font-display text-5xl font-semibold tracking-tight text-navy-900">
            How it works
          </h2>
          <p className="mx-auto mt-4 max-w-xl font-sans text-lg text-navy-800/70">
            Every query passes through a classify, retrieve, rerank, generate,
            and verify pipeline. One state machine, one honest answer.
          </p>
        </div>

        <FlowDiagram />

        <div className="mt-16 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {TECH.map((t) => (
            <div
              key={t.name}
              className="rounded-xl border border-mist bg-cream-50 p-5 transition-all hover:border-navy-200 hover:shadow-sm"
            >
              <h3 className="font-display text-lg font-semibold text-navy-900">
                {t.name}
              </h3>
              <p className="mt-2 font-sans text-sm leading-relaxed text-navy-800/70">
                {t.why}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
