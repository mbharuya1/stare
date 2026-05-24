"use client";

import { motion } from "framer-motion";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";
import { APP_URL } from "@/lib/utils";

function scrollToId(id: string) {
  if (typeof document === "undefined") return;
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function Hero() {
  return (
    <section className="relative bg-hero-radial">
      <Container className="flex min-h-[80vh] flex-col items-center justify-center py-24 text-center md:py-32">
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="font-display text-[64px] font-semibold leading-none tracking-tightest text-navy-900 md:text-[120px]"
        >
          Stare
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.12, ease: "easeOut" }}
          className="mx-auto mt-10 max-w-[700px] text-pretty font-sans text-[22px] leading-snug text-navy-900/75"
        >
          AI Law Assistant. Built by lawyers and engineers, for anyone who
          needs the law explained, cited, and trusted.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.25, ease: "easeOut" }}
          className="mt-14 flex flex-col items-center gap-3 sm:flex-row sm:gap-4"
        >
          <Button href={APP_URL} variant="primary" size="lg">
            Try Stare
          </Button>
          <Button
            href="#how-it-works"
            variant="secondary"
            size="lg"
            onClick={(e) => {
              e.preventDefault();
              scrollToId("how-it-works");
            }}
          >
            How it works
          </Button>
        </motion.div>
      </Container>
    </section>
  );
}
