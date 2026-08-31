import { useOutletContext } from "react-router-dom";
import LoreAssistant from "../LoreAssistant";

function LoreAssistantPage() {
  const { selectedSlug, activeCheckpoint } = useOutletContext();

  return (
    <main className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
      {selectedSlug && activeCheckpoint ? (
        <LoreAssistant animeSlug={selectedSlug} checkpoint={activeCheckpoint} />
      ) : (
        <p className="text-sm text-[var(--text-muted)]">
          Select an anime to start asking the Lore Assistant questions.
        </p>
      )}
    </main>
  );
}

export default LoreAssistantPage;
