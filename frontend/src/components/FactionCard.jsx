import { Users } from "lucide-react";

function FactionCard({ faction, members }) {
  return (
    <article className="rounded-lg border border-[var(--border)] bg-[var(--surface-warm)] p-4">
      <div className="mb-1 flex items-center gap-2">
        <Users className="h-4 w-4 text-[var(--ferret)]" />
        <h3 className="text-sm font-semibold text-[var(--text)]">
          {faction.name}
        </h3>
      </div>

      {faction.description && (
        <p className="mb-2 text-xs text-[var(--text-muted)]">
          {faction.description}
        </p>
      )}

      <ul className="flex flex-wrap gap-1.5">
        {members.length === 0 ? (
          <li className="text-xs text-[var(--text-muted)]">
            No known members yet
          </li>
        ) : (
          members.map((member) => (
            <li
              key={member.id}
              className="rounded-full bg-[var(--surface)] px-2.5 py-1 text-xs text-[var(--text)]"
            >
              {member.name}
            </li>
          ))
        )}
      </ul>
    </article>
  );
}

export default FactionCard;
