import CtaButton from "./CtaButton";

function ClosingCta() {
  return (
    <section className="bg-[var(--surface-warm)] px-4 py-16 text-center sm:px-6">
      <h2 className="mx-auto max-w-xl text-2xl font-bold text-[var(--primary)] sm:text-3xl">
        Ready to watch without the risk of a spoiler?
      </h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-[var(--text-muted)]">
        Pick a show, set your episode, and let AniFerret handle the rest.
      </p>
      <div className="mt-6 flex justify-center">
        <CtaButton to="/app" variant="solid">
          Enter AniFerret
        </CtaButton>
      </div>
    </section>
  );
}

export default ClosingCta;
