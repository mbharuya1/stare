import { Nav } from "@/components/marketing/Nav";
import { Hero } from "@/components/marketing/Hero";
import { WhatStareDoes } from "@/components/marketing/WhatStareDoes";
import { ModeSelector } from "@/components/marketing/ModeSelector";
import { WhyStare } from "@/components/marketing/WhyStare";
import { DataSources } from "@/components/marketing/DataSources";
import { TechStack } from "@/components/marketing/TechStack";
import { EvalResults } from "@/components/marketing/EvalResults";
import { Founder } from "@/components/marketing/Founder";
import { WorkWithUs } from "@/components/marketing/WorkWithUs";
import { Footer } from "@/components/marketing/Footer";

export default function HomePage() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <WhatStareDoes />
        <ModeSelector />
        <WhyStare />
        <DataSources />
        <TechStack />
        <EvalResults />
        <Founder />
        <WorkWithUs />
      </main>
      <Footer />
    </>
  );
}
