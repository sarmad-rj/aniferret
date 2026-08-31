import { useEffect } from "react";
import useAnimeCatalog from "../../hooks/useAnimeCatalog";
import LandingHeader from "./LandingHeader";
import LandingHero from "./LandingHero";
import TemporalMoatSection from "./TemporalMoatSection";
import FeatureGrid from "./FeatureGrid";
import AnimeShowcaseStrip from "./AnimeShowcaseStrip";
import HowItWorksSection from "./HowItWorksSection";
import ClosingCta from "./ClosingCta";
import LandingFooter from "./LandingFooter";

function LandingPage() {
  const { animeList, isLoading, error } = useAnimeCatalog();

  useEffect(() => {
    if (!window.location.hash) {
      return;
    }
    const target = document.querySelector(window.location.hash);
    target?.scrollIntoView({ block: "start" });
  }, []);

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <LandingHeader />
      <LandingHero animeList={animeList} />
      <TemporalMoatSection />
      <FeatureGrid />
      <AnimeShowcaseStrip
        animeList={animeList}
        isLoading={isLoading}
        error={error}
      />
      <HowItWorksSection />
      <ClosingCta />
      <LandingFooter />
    </div>
  );
}

export default LandingPage;
