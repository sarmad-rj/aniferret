function FeatureCard({ number, tag, title, description, icon: Icon }) {
  return (
    <article className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-2xl font-bold text-[var(--border)]">
          {number}
        </span>
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--surface-warm)]">
          <Icon className="h-4 w-4 text-[var(--ferret)]" />
        </span>
      </div>
      <span className="mb-1.5 inline-block rounded-full bg-[var(--sky)]/25 px-2.5 py-1 text-xs font-medium text-[var(--primary)]">
        {tag}
      </span>
      <h3 className="mb-1.5 text-sm font-semibold text-[var(--text)]">
        {title}
      </h3>
      <p className="text-xs text-[var(--text-muted)]">{description}</p>
    </article>
  );
}

export default FeatureCard;
