import { useState } from "react";
import { ChevronRight, Flag, Users } from "lucide-react";
import CharacterChip from "./CharacterChip";

function FactionTreeNode({
  node,
  depth,
  defaultOpen,
  onSelectCharacter,
  onSelectFactionGroup,
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const hasChildren = node.children.length > 0;
  const hasMembers = node.members.length > 0;
  const isExpandable = hasChildren || hasMembers;
  const allMembers = [
    ...node.members,
    ...node.children.flatMap((child) => child.members),
  ];

  const handleToggle = () => {
    if (isExpandable) {
      setIsOpen((previous) => !previous);
    }
  };

  const handleViewAll = () => {
    onSelectFactionGroup({ faction: node, members: allMembers });
  };

  return (
    <div
      className={depth > 0 ? "ml-3 border-l border-[var(--border)] pl-3" : ""}
    >
      <div className="flex items-center gap-2 py-2.5">
        <button
          type="button"
          onClick={handleToggle}
          disabled={!isExpandable}
          className="flex flex-1 items-center gap-2 text-left disabled:cursor-default"
        >
          {isExpandable ? (
            <ChevronRight
              className={`h-3.5 w-3.5 shrink-0 text-[var(--text-muted)] transition-transform duration-150 ${
                isOpen ? "rotate-90" : ""
              }`}
            />
          ) : (
            <span className="h-3.5 w-3.5 shrink-0" />
          )}

          {depth === 0 ? (
            <Users className="h-4 w-4 shrink-0 text-[var(--ferret)]" />
          ) : (
            <Flag className="h-3.5 w-3.5 shrink-0 text-[var(--text-muted)]" />
          )}

          <span
            className={
              depth === 0
                ? "text-sm font-semibold text-[var(--text)]"
                : "text-sm font-medium text-[var(--text)]"
            }
          >
            {node.name}
          </span>

          {depth === 0 && node.description && (
            <span className="hidden truncate text-xs text-[var(--text-muted)] sm:inline">
              {node.description}
            </span>
          )}
        </button>

        {allMembers.length > 0 && (
          <button
            type="button"
            onClick={handleViewAll}
            className="shrink-0 rounded-full bg-[var(--sky)]/25 px-2 py-0.5 text-xs font-medium text-[var(--primary)]"
            aria-label={`View all ${allMembers.length} members of ${node.name}`}
          >
            {allMembers.length}
          </button>
        )}
      </div>

      {isOpen && (
        <div className="pb-1 pl-8">
          {!isExpandable && (
            <p className="pb-2 text-xs text-[var(--text-muted)]">
              No known members introduced yet
            </p>
          )}

          {hasMembers && (
            <ul className="mb-2 flex flex-wrap gap-1.5">
              {node.members.map((member) => (
                <CharacterChip
                  key={member.id}
                  character={member}
                  onSelect={onSelectCharacter}
                />
              ))}
            </ul>
          )}
        </div>
      )}

      {isOpen &&
        node.children.map((child) => (
          <FactionTreeNode
            key={child.id}
            node={child}
            depth={depth + 1}
            defaultOpen={false}
            onSelectCharacter={onSelectCharacter}
            onSelectFactionGroup={onSelectFactionGroup}
          />
        ))}
    </div>
  );
}

export default FactionTreeNode;
