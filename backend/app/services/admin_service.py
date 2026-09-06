from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.anime import Anime
from app.models.character import Character
from app.models.faction import Faction
from app.models.temporal_fact import TemporalFact
from app.models.user import User
from app.schemas.admin import (
    AdminAnimeDetail,
    AdminAnimeSummary,
    AdminCharacterDetail,
    AdminFactionDetail,
    AdminUserSummary,
    CharacterWithoutFaction,
    DataIntegrityReport,
    EpisodeCountMismatch,
    OutOfRangeCheckpoint,
)
from app.services.reveal_engine import InvalidCheckpointError, parse_checkpoint


class AnimeNotFoundError(ValueError):
    """Raised when deleting an anime id that has no matching row."""


class UserNotFoundError(ValueError):
    """Raised when an admin user-management action targets a user id that has no
    matching row."""


class CannotModifySelfError(ValueError):
    """Raised when an admin targets their own account through the admin
    user-management surface — self-service, password-confirmed flows on the Profile
    page exist for that instead, and this surface has no re-authentication step."""


class CharacterNotFoundError(ValueError):
    """Raised when a data-integrity fix targets a character id that has no matching
    row."""


class FactNotFoundError(ValueError):
    """Raised when a data-integrity fix targets a temporal_fact id that has no
    matching row."""


class FactionNotFoundError(ValueError):
    """Raised when a faction-assignment fix targets a faction id that has no
    matching row."""


class InvalidFixError(ValueError):
    """Raised when a submitted data-integrity fix would not actually resolve the
    flagged issue (e.g. a 'corrected' checkpoint that is still out of range, or
    season_episode_counts that still don't sum to total_episodes) — fixes are
    re-validated with the exact same logic the report itself uses, rather than
    trusting admin input blindly. Also raised when a faction assignment crosses
    anime boundaries (a character can only belong to a faction from its own anime).
    """


class InvalidFactionHierarchyError(ValueError):
    """Raised when a faction's chosen parent doesn't belong to the same anime, is
    itself already nested under a parent (Faction.parent_id is a strict two-tier
    hierarchy, see the model's own docstring), or would make a faction its own
    parent."""


async def list_anime_summaries(db: AsyncSession) -> list[AdminAnimeSummary]:
    """Per-anime counts for the admin inventory table. Loaded eagerly and counted in
    Python rather than a SQL aggregate — the anime table is small (a handful of
    tracked series), so this stays simple rather than adding query complexity for a
    dataset size where it wouldn't move the needle.
    """
    stmt = (
        select(Anime)
        .options(selectinload(Anime.characters), selectinload(Anime.facts))
        .order_by(Anime.title)
    )
    result = await db.execute(stmt)
    animes = result.scalars().all()
    return [
        AdminAnimeSummary(
            id=anime.id,
            slug=anime.slug,
            title=anime.title,
            total_episodes=anime.total_episodes,
            character_count=len(anime.characters),
            fact_count=len(anime.facts),
        )
        for anime in animes
    ]


async def delete_anime(db: AsyncSession, anime_id: int) -> None:
    """Deletes the anime row; its characters/factions/facts/external metadata cascade
    via Anime's own ORM relationships, and any user watch-progress against it cascades
    via watch_progress.anime_id's ondelete=CASCADE at the DB level.
    """
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")
    await db.delete(anime)
    await db.commit()


async def bulk_delete_anime(
    db: AsyncSession, anime_ids: list[int]
) -> tuple[list[int], list[dict[str, str]]]:
    """Best-effort bulk delete: each id is attempted independently so one bad id in
    a multi-select doesn't block the rest. Returns (deleted_ids, failed), where each
    failed entry is {'id': str(id), 'reason': str}."""
    deleted: list[int] = []
    failed: list[dict[str, str]] = []
    for anime_id in anime_ids:
        try:
            await delete_anime(db, anime_id)
            deleted.append(anime_id)
        except AnimeNotFoundError as exc:
            failed.append({"id": str(anime_id), "reason": str(exc)})
    return deleted, failed


async def list_user_summaries(db: AsyncSession) -> list[AdminUserSummary]:
    stmt = (
        select(User)
        .options(selectinload(User.watch_progress))
        .order_by(User.created_at.desc())
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [
        AdminUserSummary(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_verified=user.is_verified,
            is_admin=user.is_admin,
            created_at=user.created_at,
            tracked_series_count=len(user.watch_progress),
        )
        for user in users
    ]


async def mark_user_verified(db: AsyncSession, user_id: int) -> None:
    """Manually verifies an account — a support fallback for when the verification
    email never arrives (SMTP misconfiguration, spam filtering, a typo'd address),
    without requiring the user to still hold the original token."""
    user = await db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"No user with id {user_id}")
    user.is_verified = True
    await db.commit()


async def delete_user(db: AsyncSession, admin: User, user_id: int) -> None:
    """Cascade-deletes a user the same way self-service account deletion does (see
    profile_service.delete_account) — via User.watch_progress's ORM cascade plus
    watch_progress.user_id's DB-level ondelete=CASCADE — minus the password
    re-verification step, since the admin's own session is the authentication here.
    Blocks an admin from deleting their own account through this path: there is no
    re-auth step here to confirm intent, unlike the Profile page's delete flow.
    """
    if user_id == admin.id:
        raise CannotModifySelfError(
            "Use your account settings to delete your own account."
        )
    user = await db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"No user with id {user_id}")
    await db.delete(user)
    await db.commit()


async def bulk_delete_users(
    db: AsyncSession, admin: User, user_ids: list[int]
) -> tuple[list[int], list[dict[str, str]]]:
    """Best-effort bulk delete, same semantics as bulk_delete_anime: one bad id
    (unknown, or the admin's own account slipping into a selection) fails on its
    own and doesn't block the rest."""
    deleted: list[int] = []
    failed: list[dict[str, str]] = []
    for user_id in user_ids:
        try:
            await delete_user(db, admin, user_id)
            deleted.append(user_id)
        except (CannotModifySelfError, UserNotFoundError) as exc:
            failed.append({"id": str(user_id), "reason": str(exc)})
    return deleted, failed


def _checkpoint_out_of_range_reason(checkpoint: str, season_counts: list[int]) -> str | None:
    """Mirrors tests/test_seed_data.py's static guard against the exact bug class
    found while adding One Piece (a checkpoint whose season/episode falls outside the
    anime's declared season_episode_counts can be satisfied by the wrong later
    checkpoint) — but live, against every anime actually in the database, not just
    the static seed corpus."""
    try:
        season, episode = parse_checkpoint(checkpoint)
    except InvalidCheckpointError:
        return f"'{checkpoint}' is not a valid checkpoint format"
    if season < 1 or season > len(season_counts):
        return f"season {season} exceeds the {len(season_counts)} declared season(s)"
    if episode > season_counts[season - 1]:
        return (
            f"episode {episode} exceeds season {season}'s declared length of "
            f"{season_counts[season - 1]}"
        )
    return None


async def get_data_integrity_report(db: AsyncSession) -> DataIntegrityReport:
    stmt = (
        select(Anime)
        .options(selectinload(Anime.characters), selectinload(Anime.facts))
        .order_by(Anime.title)
    )
    result = await db.execute(stmt)
    animes = result.scalars().all()

    episode_count_mismatches: list[EpisodeCountMismatch] = []
    out_of_range_checkpoints: list[OutOfRangeCheckpoint] = []
    characters_without_faction: list[CharacterWithoutFaction] = []

    for anime in animes:
        season_counts = anime.season_episode_counts
        season_counts_sum = sum(season_counts)
        if season_counts_sum != anime.total_episodes:
            episode_count_mismatches.append(
                EpisodeCountMismatch(
                    anime_id=anime.id,
                    anime_slug=anime.slug,
                    anime_title=anime.title,
                    declared_total_episodes=anime.total_episodes,
                    season_episode_counts=season_counts,
                    season_counts_sum=season_counts_sum,
                )
            )

        for character in anime.characters:
            if character.faction_id is None:
                characters_without_faction.append(
                    CharacterWithoutFaction(
                        anime_id=anime.id,
                        anime_slug=anime.slug,
                        anime_title=anime.title,
                        character_id=character.id,
                        character_name=character.name,
                    )
                )
            reason = _checkpoint_out_of_range_reason(character.first_revealed_at, season_counts)
            if reason:
                out_of_range_checkpoints.append(
                    OutOfRangeCheckpoint(
                        anime_slug=anime.slug,
                        anime_title=anime.title,
                        entity_type="character",
                        entity_id=character.id,
                        entity_label=character.name,
                        field="first_revealed_at",
                        checkpoint=character.first_revealed_at,
                        reason=reason,
                    )
                )

        for fact in anime.facts:
            for field_name in ("first_revealed_at", "first_hinted_at"):
                checkpoint = getattr(fact, field_name)
                if checkpoint is None:
                    continue
                reason = _checkpoint_out_of_range_reason(checkpoint, season_counts)
                if reason:
                    out_of_range_checkpoints.append(
                        OutOfRangeCheckpoint(
                            anime_slug=anime.slug,
                            anime_title=anime.title,
                            entity_type="temporal_fact",
                            entity_id=fact.fact_id,
                            entity_label=f"{fact.subject} / {fact.predicate}",
                            field=field_name,
                            checkpoint=checkpoint,
                            reason=reason,
                        )
                    )

    return DataIntegrityReport(
        episode_count_mismatches=episode_count_mismatches,
        out_of_range_checkpoints=out_of_range_checkpoints,
        characters_without_faction=characters_without_faction,
    )


async def fix_anime_episode_counts(
    db: AsyncSession, anime_id: int, total_episodes: int, season_episode_counts: list[int]
) -> AdminAnimeSummary:
    stmt = (
        select(Anime)
        .where(Anime.id == anime_id)
        .options(selectinload(Anime.characters), selectinload(Anime.facts))
    )
    result = await db.execute(stmt)
    anime = result.scalar_one_or_none()
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")

    season_counts_sum = sum(season_episode_counts)
    if season_counts_sum != total_episodes:
        raise InvalidFixError(
            f"season_episode_counts sums to {season_counts_sum}, which still doesn't "
            f"match total_episodes={total_episodes}"
        )

    anime.total_episodes = total_episodes
    anime.season_episode_counts = season_episode_counts
    await db.commit()

    return AdminAnimeSummary(
        id=anime.id,
        slug=anime.slug,
        title=anime.title,
        total_episodes=anime.total_episodes,
        character_count=len(anime.characters),
        fact_count=len(anime.facts),
    )


async def fix_character_checkpoint(db: AsyncSession, character_id: int, first_revealed_at: str) -> None:
    stmt = (
        select(Character)
        .where(Character.id == character_id)
        .options(selectinload(Character.anime))
    )
    result = await db.execute(stmt)
    character = result.scalar_one_or_none()
    if character is None:
        raise CharacterNotFoundError(f"No character with id {character_id}")

    reason = _checkpoint_out_of_range_reason(
        first_revealed_at, character.anime.season_episode_counts
    )
    if reason:
        raise InvalidFixError(f"'{first_revealed_at}' is still invalid: {reason}")

    character.first_revealed_at = first_revealed_at
    await db.commit()


async def fix_fact_checkpoint(db: AsyncSession, fact_id: int, field_name: str, checkpoint: str) -> None:
    stmt = (
        select(TemporalFact)
        .where(TemporalFact.fact_id == fact_id)
        .options(selectinload(TemporalFact.anime))
    )
    result = await db.execute(stmt)
    fact = result.scalar_one_or_none()
    if fact is None:
        raise FactNotFoundError(f"No fact with id {fact_id}")

    reason = _checkpoint_out_of_range_reason(checkpoint, fact.anime.season_episode_counts)
    if reason:
        raise InvalidFixError(f"'{checkpoint}' is still invalid: {reason}")

    setattr(fact, field_name, checkpoint)
    await db.commit()


def _faction_to_detail(faction: Faction) -> AdminFactionDetail:
    return AdminFactionDetail(
        id=faction.id,
        anime_id=faction.anime_id,
        name=faction.name,
        description=faction.description,
        parent_id=faction.parent_id,
        first_revealed_at=faction.first_revealed_at,
    )


async def list_anime_factions(db: AsyncSession, anime_id: int) -> list[AdminFactionDetail]:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")

    stmt = select(Faction).where(Faction.anime_id == anime_id).order_by(Faction.name)
    result = await db.execute(stmt)
    return [_faction_to_detail(faction) for faction in result.scalars().all()]


async def fix_character_faction(db: AsyncSession, character_id: int, faction_id: int) -> None:
    character = await db.get(Character, character_id)
    if character is None:
        raise CharacterNotFoundError(f"No character with id {character_id}")

    faction = await db.get(Faction, faction_id)
    if faction is None:
        raise FactionNotFoundError(f"No faction with id {faction_id}")
    if faction.anime_id != character.anime_id:
        raise InvalidFixError("That faction belongs to a different anime than this character.")

    character.faction_id = faction_id
    await db.commit()


async def get_anime_detail(db: AsyncSession, anime_id: int) -> AdminAnimeDetail:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")
    return AdminAnimeDetail(
        id=anime.id,
        slug=anime.slug,
        title=anime.title,
        total_episodes=anime.total_episodes,
        cover_image_url=anime.cover_image_url,
        genres=anime.genres,
        synopsis=anime.synopsis,
        score=anime.score,
    )


async def update_anime_metadata(
    db: AsyncSession,
    anime_id: int,
    title: str,
    cover_image_url: str | None,
    genres: list[str],
    synopsis: str | None,
    score: float | None,
) -> AdminAnimeDetail:
    """Covers the descriptive fields only -- total_episodes/season_episode_counts
    stay behind fix_anime_episode_counts, which cross-validates the two against
    each other rather than accepting either in isolation."""
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")

    anime.title = title
    anime.cover_image_url = cover_image_url
    anime.genres = genres
    anime.synopsis = synopsis
    anime.score = score
    await db.commit()

    return AdminAnimeDetail(
        id=anime.id,
        slug=anime.slug,
        title=anime.title,
        total_episodes=anime.total_episodes,
        cover_image_url=anime.cover_image_url,
        genres=anime.genres,
        synopsis=anime.synopsis,
        score=anime.score,
    )


def _faction_to_detail(faction: Faction) -> AdminFactionDetail:
    return AdminFactionDetail(
        id=faction.id,
        anime_id=faction.anime_id,
        name=faction.name,
        description=faction.description,
        parent_id=faction.parent_id,
        first_revealed_at=faction.first_revealed_at,
    )


async def _validate_faction_parent(
    db: AsyncSession, anime_id: int, parent_id: int | None, *, faction_id: int | None = None
) -> None:
    if parent_id is None:
        return
    if parent_id == faction_id:
        raise InvalidFactionHierarchyError("A faction cannot be its own parent.")
    parent = await db.get(Faction, parent_id)
    if parent is None:
        raise FactionNotFoundError(f"No faction with id {parent_id}")
    if parent.anime_id != anime_id:
        raise InvalidFactionHierarchyError("Parent faction must belong to the same anime.")
    if parent.parent_id is not None:
        raise InvalidFactionHierarchyError(
            "Factions only support one level of nesting -- the chosen parent is "
            "itself a child faction."
        )


async def create_faction(
    db: AsyncSession,
    anime_id: int,
    name: str,
    description: str | None,
    parent_id: int | None,
    first_revealed_at: str | None,
) -> AdminFactionDetail:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")

    await _validate_faction_parent(db, anime_id, parent_id)

    faction = Faction(
        anime_id=anime_id,
        name=name,
        description=description,
        parent_id=parent_id,
        first_revealed_at=first_revealed_at,
    )
    db.add(faction)
    await db.commit()
    await db.refresh(faction)
    return _faction_to_detail(faction)


async def update_faction(
    db: AsyncSession,
    faction_id: int,
    name: str,
    description: str | None,
    parent_id: int | None,
    first_revealed_at: str | None,
) -> AdminFactionDetail:
    faction = await db.get(Faction, faction_id)
    if faction is None:
        raise FactionNotFoundError(f"No faction with id {faction_id}")

    await _validate_faction_parent(db, faction.anime_id, parent_id, faction_id=faction_id)

    faction.name = name
    faction.description = description
    faction.parent_id = parent_id
    faction.first_revealed_at = first_revealed_at
    await db.commit()
    return _faction_to_detail(faction)


async def delete_faction(db: AsyncSession, faction_id: int) -> None:
    """Deletes the faction, handling both dependents explicitly rather than relying
    on the FK columns' declared ondelete behavior: SQLite only enforces
    ondelete=SET NULL/CASCADE when PRAGMA foreign_keys=ON is set per-connection,
    which this app never does (existing cascades that "just work" — e.g. deleting
    an Anime — do so via SQLAlchemy's own ORM-level relationship(cascade=...),
    which is independent of the DB and unaffected by this). Without handling it
    here, the faction row would vanish while character.faction_id and any child
    faction's parent_id kept pointing at a now-nonexistent id.

    Characters directly on this faction (or on any of its children — the
    hierarchy is enforced elsewhere as strictly two-tier, so there's never a
    grandchild to worry about) are unassigned, matching faction_id's declared
    SET NULL intent — the data-integrity report then flags them for
    reassignment. Child factions are deleted outright, matching parent_id's
    declared CASCADE intent.
    """
    faction = await db.get(Faction, faction_id)
    if faction is None:
        raise FactionNotFoundError(f"No faction with id {faction_id}")

    child_result = await db.execute(select(Faction.id).where(Faction.parent_id == faction_id))
    child_ids = [row[0] for row in child_result.all()]
    affected_faction_ids = [faction_id, *child_ids]

    await db.execute(
        update(Character)
        .where(Character.faction_id.in_(affected_faction_ids))
        .values(faction_id=None)
    )
    if child_ids:
        await db.execute(delete(Faction).where(Faction.id.in_(child_ids)))
    await db.delete(faction)
    await db.commit()


def _character_to_detail(character: Character) -> AdminCharacterDetail:
    return AdminCharacterDetail(
        id=character.id,
        anime_id=character.anime_id,
        name=character.name,
        role=character.role,
        height=character.height,
        avatar_url=character.avatar_url,
        bounty=character.bounty,
        power=character.power,
        backstory=character.backstory,
        faction_id=character.faction_id,
        first_revealed_at=character.first_revealed_at,
    )


async def list_anime_characters(db: AsyncSession, anime_id: int) -> list[AdminCharacterDetail]:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")
    stmt = select(Character).where(Character.anime_id == anime_id).order_by(Character.name)
    result = await db.execute(stmt)
    return [_character_to_detail(character) for character in result.scalars().all()]


async def _validate_character_write(
    db: AsyncSession, anime: Anime, faction_id: int | None, first_revealed_at: str
) -> None:
    """Shared by create and update: the same checks fix_character_checkpoint and
    fix_character_faction already enforce, so a character can never end up in a
    state the data-integrity report would immediately re-flag."""
    if faction_id is not None:
        faction = await db.get(Faction, faction_id)
        if faction is None:
            raise FactionNotFoundError(f"No faction with id {faction_id}")
        if faction.anime_id != anime.id:
            raise InvalidFixError("That faction belongs to a different anime than this character.")

    reason = _checkpoint_out_of_range_reason(first_revealed_at, anime.season_episode_counts)
    if reason:
        raise InvalidFixError(f"'{first_revealed_at}' is invalid: {reason}")


async def create_character(
    db: AsyncSession,
    anime_id: int,
    name: str,
    role: str | None,
    height: str | None,
    avatar_url: str | None,
    bounty: str | None,
    power: str | None,
    backstory: str | None,
    faction_id: int | None,
    first_revealed_at: str,
) -> AdminCharacterDetail:
    anime = await db.get(Anime, anime_id)
    if anime is None:
        raise AnimeNotFoundError(f"No anime with id {anime_id}")

    await _validate_character_write(db, anime, faction_id, first_revealed_at)

    character = Character(
        anime_id=anime_id,
        name=name,
        role=role,
        height=height,
        avatar_url=avatar_url,
        bounty=bounty,
        power=power,
        backstory=backstory,
        faction_id=faction_id,
        first_revealed_at=first_revealed_at,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return _character_to_detail(character)


async def update_character(
    db: AsyncSession,
    character_id: int,
    name: str,
    role: str | None,
    height: str | None,
    avatar_url: str | None,
    bounty: str | None,
    power: str | None,
    backstory: str | None,
    faction_id: int | None,
    first_revealed_at: str,
) -> AdminCharacterDetail:
    character = await db.get(Character, character_id)
    if character is None:
        raise CharacterNotFoundError(f"No character with id {character_id}")

    anime = await db.get(Anime, character.anime_id)
    await _validate_character_write(db, anime, faction_id, first_revealed_at)

    character.name = name
    character.role = role
    character.height = height
    character.avatar_url = avatar_url
    character.bounty = bounty
    character.power = power
    character.backstory = backstory
    character.faction_id = faction_id
    character.first_revealed_at = first_revealed_at
    await db.commit()
    return _character_to_detail(character)


async def delete_character(db: AsyncSession, character_id: int) -> None:
    character = await db.get(Character, character_id)
    if character is None:
        raise CharacterNotFoundError(f"No character with id {character_id}")
    await db.delete(character)
    await db.commit()
