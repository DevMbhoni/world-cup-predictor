import { useQuery } from "@tanstack/react-query";
import { GitBranch, ShieldCheck } from "lucide-react";
import { getTournamentBracket } from "../../api/tournament";
import type { BracketMatch, BracketTeam } from "../../types/api";

const leftRounds = [
    { title: "Round of 32", matchIds: [75, 78, 73, 76, 84, 83, 82, 81] },
    { title: "Round of 16", matchIds: [89, 90, 91, 92] },
    { title: "Quarter-finals", matchIds: [97, 98] },
    { title: "Semi-finals", matchIds: [101] },
];

const rightRounds = [
    { title: "Semi-finals", matchIds: [102] },
    { title: "Quarter-finals", matchIds: [99, 100] },
    { title: "Round of 16", matchIds: [93, 94, 95, 96] },
    { title: "Round of 32", matchIds: [74, 77, 79, 80, 87, 86, 85, 88] },
];

export default function BracketPage() {
    const bracketQuery = useQuery({
        queryKey: ["tournament-bracket"],
        queryFn: getTournamentBracket,
    });

    const matches = bracketQuery.data?.matches ?? [];

    if (bracketQuery.isLoading) {
        return <PageState title="Tournament bracket" message="Loading bracket..." />;
    }

    if (bracketQuery.isError) {
        return (
            <PageState
                title="Tournament bracket"
                message="Could not load bracket. Check that the FastAPI service is running."
            />
        );
    }

    const matchMap = new Map(matches.map((match) => [match.match_id, match]));
    const finalMatch = matches.find((match) => match.stage_id === 7);
    const thirdPlaceMatch = matches.find((match) => match.stage_id === 6);

    return (
        <div className="space-y-6">
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sky-600">
                            Tournament bracket
                        </p>
                        <h2 className="mt-3 text-3xl font-semibold text-slate-950">
                            Live knockout bracket
                        </h2>
                        <p className="mt-3 max-w-3xl text-slate-600">
                            Completed source matches resolve to real teams. Unplayed source
                            matches stay as placeholders, with model projection shown underneath.
                        </p>
                    </div>
                </div>
            </section>

            <section className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-2xl shadow-black/20">
                <div className="mb-6 flex items-center gap-3">
                    <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3 text-sky-600">
                        <GitBranch size={22} />
                    </div>
                    <div>
                        <h3 className="text-xl font-semibold text-slate-950">Bracket path</h3>
                        <p className="text-sm text-slate-600">
                            Scroll horizontally if the full bracket does not fit on screen.
                        </p>
                    </div>
                </div>

                <div className="overflow-x-auto pb-5">
                    <div className="grid min-w-[1680px] grid-cols-[1fr_1fr_1fr_1fr_260px_1fr_1fr_1fr_1fr] gap-5">
                        {leftRounds.map((round, roundIndex) => (
                            <BracketColumn
                                key={round.title}
                                title={round.title}
                                matchIds={round.matchIds}
                                matchMap={matchMap}
                                side="left"
                                roundIndex={roundIndex}
                            />
                        ))}

                        <div className="flex flex-col justify-center gap-5 pt-12">
                            <p className="text-center text-sm font-semibold text-slate-950">Final</p>

                            {finalMatch ? (
                                <FinalCard match={finalMatch} matchMap={matchMap} />
                            ) : (
                                <PlaceholderMatchCard matchId={104} />
                            )}

                            {thirdPlaceMatch && (
                                <div>
                                    <p className="mb-2 text-center text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">
                                        Third-place
                                    </p>
                                    <FinalCard match={thirdPlaceMatch} matchMap={matchMap} compact />
                                </div>
                            )}
                        </div>

                        {rightRounds.map((round, roundIndex) => (
                            <BracketColumn
                                key={round.title}
                                title={round.title}
                                matchIds={round.matchIds}
                                matchMap={matchMap}
                                side="right"
                                roundIndex={roundIndex}
                            />
                        ))}
                    </div>
                </div>
            </section>

            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="mb-5 flex items-center gap-3">
                    <div className="rounded-2xl border border-blue-500/20 bg-blue-500/10 p-3 text-blue-600">
                        <ShieldCheck size={22} />
                    </div>
                    <div>
                        <h3 className="text-xl font-semibold text-slate-950">Match list</h3>
                        <p className="text-sm text-slate-600">
                            Full knockout match data from the bracket endpoint.
                        </p>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full min-w-[980px] border-separate border-spacing-y-2">
                        <thead>
                            <tr className="text-left text-xs uppercase tracking-[0.2em] text-slate-500">
                                <th className="px-4 py-3">Match</th>
                                <th className="px-4 py-3">Stage</th>
                                <th className="px-4 py-3">Home</th>
                                <th className="px-4 py-3">Away</th>
                                <th className="px-4 py-3">Score</th>
                                <th className="px-4 py-3">Winner</th>
                                <th className="px-4 py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {matches.map((match) => {
                                const homeResolved = resolveBracketSlot(
                                    match.home_team,
                                    match,
                                    matchMap
                                );
                                const awayResolved = resolveBracketSlot(
                                    match.away_team,
                                    match,
                                    matchMap
                                );

                                return (
                                    <tr key={match.match_id} className="bg-slate-50">
                                        <td className="rounded-l-2xl px-4 py-4 text-slate-700">
                                            {match.match_id}
                                        </td>
                                        <td className="px-4 py-4 text-slate-700">
                                            {match.stage_name}
                                        </td>
                                        <td className="px-4 py-4 font-medium text-slate-950">
                                            {homeResolved.displayName}
                                        </td>
                                        <td className="px-4 py-4 font-medium text-slate-950">
                                            {awayResolved.displayName}
                                        </td>
                                        <td className="px-4 py-4 text-slate-700">
                                            {formatScore(match)}
                                        </td>
                                        <td className="px-4 py-4 text-sky-600">
                                            {getWinnerDisplay(match, matchMap)}
                                        </td>
                                        <td className="rounded-r-2xl px-4 py-4">
                                            <StatusBadge match={match} />
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}

function BracketColumn({
    title,
    matchIds,
    matchMap,
    side,
    roundIndex,
}: {
    title: string;
    matchIds: number[];
    matchMap: Map<number, BracketMatch>;
    side: "left" | "right";
    roundIndex: number;
}) {
    const spacingClass =
        matchIds.length === 8
            ? "gap-4"
            : matchIds.length === 4
                ? "gap-16 pt-14"
                : matchIds.length === 2
                    ? "gap-44 pt-40"
                    : "pt-[320px]";

    return (
        <div>
            <p className="mb-4 text-center text-sm font-semibold text-slate-950">
                {title}
            </p>

            <div className={`flex flex-col ${spacingClass}`}>
                {matchIds.map((matchId) => {
                    const match = matchMap.get(matchId);

                    return (
                        <div
                            key={matchId}
                            className={`relative ${side === "left" ? "bracket-left" : "bracket-right"
                                } ${roundIndex > 0 ? "has-connector" : ""}`}
                        >
                            {match ? (
                                <BracketMatchCard match={match} matchMap={matchMap} />
                            ) : (
                                <PlaceholderMatchCard matchId={matchId} />
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function BracketMatchCard({
    match,
    matchMap,
}: {
    match: BracketMatch;
    matchMap: Map<number, BracketMatch>;
}) {
    const homeResolved = resolveBracketSlot(match.home_team, match, matchMap);
    const awayResolved = resolveBracketSlot(match.away_team, match, matchMap);

    return (
        <div className="relative z-10 rounded-3xl border border-slate-200 bg-white p-4 shadow-xl shadow-black/20">
            <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                    M{match.match_id}
                </p>
                <StatusBadge match={match} />
            </div>

            <div className="space-y-2">
                <TeamRow
                    team={match.home_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={homeResolved.resolvedTeamId === match.winner.team_id}
                />

                <TeamRow
                    team={match.away_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={awayResolved.resolvedTeamId === match.winner.team_id}
                />
            </div>
        </div>
    );
}

function FinalCard({
    match,
    matchMap,
    compact = false,
}: {
    match: BracketMatch;
    matchMap: Map<number, BracketMatch>;
    compact?: boolean;
}) {
    const homeResolved = resolveBracketSlot(match.home_team, match, matchMap);
    const awayResolved = resolveBracketSlot(match.away_team, match, matchMap);

    return (
        <div
            className={`rounded-[2rem] border border-amber-400/20 bg-amber-400/10 p-5 shadow-xl shadow-black/20 ${compact ? "" : "min-h-[190px]"
                }`}
        >
            <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-amber-700">
                    M{match.match_id}
                </p>
                <StatusBadge match={match} />
            </div>

            <div className="space-y-2">
                <TeamRow
                    team={match.home_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={homeResolved.resolvedTeamId === match.winner.team_id}
                />

                <TeamRow
                    team={match.away_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={awayResolved.resolvedTeamId === match.winner.team_id}
                />
            </div>

            {getWinnerDisplay(match, matchMap) !== "Pending" && (
                <div className="mt-4 rounded-2xl border border-amber-400/20 bg-slate-50 px-3 py-2">
                    <p className="text-xs text-amber-700">
                        {match.winner.is_projected ? "Projected winner" : "Winner"}
                    </p>
                    <p className="mt-1 text-sm font-semibold text-slate-950">
                        {getWinnerDisplay(match, matchMap)}
                    </p>
                </div>
            )}
        </div>
    );
}

function TeamRow({
    team,
    match,
    matchMap,
    isWinner,
}: {
    team: BracketTeam;
    match: BracketMatch;
    matchMap: Map<number, BracketMatch>;
    isWinner: boolean;
}) {
    const resolved = resolveBracketSlot(team, match, matchMap);

    return (
        <div
            className={`flex items-center justify-between gap-3 rounded-2xl border px-3 py-3 ${isWinner
                    ? "border-cyan-400/25 bg-cyan-400/10"
                    : "border-slate-200 bg-slate-50"
                }`}
        >
            <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-950">
                    {resolved.displayName}
                </p>

                {resolved.projectedName && (
                    <p className="mt-1 truncate text-xs text-amber-600">
                        Projection: {resolved.projectedName}
                    </p>
                )}
            </div>

            <div className="shrink-0 text-right">
                {team.score !== null && team.score !== undefined ? (
                    <p className="text-lg font-semibold text-slate-950">{team.score}</p>
                ) : (
                    <p className="text-xs text-slate-500">TBD</p>
                )}
            </div>
        </div>
    );
}

function PlaceholderMatchCard({ matchId }: { matchId: number }) {
    return (
        <div className="relative z-10 rounded-3xl border border-slate-200 bg-white p-4 shadow-xl shadow-black/20">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                M{matchId}
            </p>
            <div className="mt-3 space-y-2">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-500">
                    To be decided
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-500">
                    To be decided
                </div>
            </div>
        </div>
    );
}

function StatusBadge({ match }: { match: BracketMatch }) {
    const label = match.is_completed
        ? "Completed"
        : match.winner.is_projected
            ? "Projected"
            : "Scheduled";

    const style = match.is_completed
        ? "border-cyan-400/20 bg-cyan-400/10 text-sky-700"
        : match.winner.is_projected
            ? "border-amber-400/20 bg-amber-400/10 text-amber-200"
            : "border-slate-500/20 bg-slate-500/10 text-slate-700";

    return (
        <span className={`rounded-full border px-3 py-1 text-xs font-medium ${style}`}>
            {label}
        </span>
    );
}

function resolveBracketSlot(
    team: BracketTeam,
    match: BracketMatch,
    matchMap: Map<number, BracketMatch>
) {
    if (match.is_completed && team.team_name) {
        return {
            displayName: team.team_name,
            projectedName: null as string | null,
            resolvedTeamId: team.team_id,
        };
    }

    if (team.is_confirmed && team.team_name) {
        return {
            displayName: team.team_name,
            projectedName: null as string | null,
            resolvedTeamId: team.team_id,
        };
    }

    if (team.team_name && !team.source?.source_match_id && !team.projection) {
        return {
            displayName: team.team_name,
            projectedName: null as string | null,
            resolvedTeamId: team.team_id,
        };
    }

    const sourceMatchId = team.source?.source_match_id;
    const sourceType = team.source?.source_type;
    const sourceMatch = sourceMatchId ? matchMap.get(sourceMatchId) : undefined;

    if (sourceMatch?.is_completed) {
        const sourceResult =
            sourceType === "loser" ? sourceMatch.loser : sourceMatch.winner;

        if (sourceResult?.team_name) {
            return {
                displayName: sourceResult.team_name,
                projectedName: null as string | null,
                resolvedTeamId: sourceResult.team_id,
            };
        }
    }

    if (team.source?.label) {
        return {
            displayName: normalizeSourceLabel(team.source.label),
            projectedName: getProjectionName(team),
            resolvedTeamId: null as number | null,
        };
    }

    return {
        displayName: team.team_name ?? "To be decided",
        projectedName: getProjectionName(team),
        resolvedTeamId: team.team_id,
    };
}

function getProjectionName(team: BracketTeam) {
    if (team.projection?.team_name) {
        return team.projection.team_name;
    }

    if (team.source?.label && team.team_name && team.team_name !== team.source.label) {
        return team.team_name;
    }

    return null;
}

function getWinnerDisplay(
    match: BracketMatch,
    matchMap: Map<number, BracketMatch>
) {
    if (match.is_completed && match.winner.team_name) {
        return match.winner.team_name;
    }

    if (!match.winner.is_projected && match.winner.team_name) {
        return match.winner.team_name;
    }

    if (match.winner.team_name) {
        return match.winner.team_name;
    }

    const homeResolved = resolveBracketSlot(match.home_team, match, matchMap);
    const awayResolved = resolveBracketSlot(match.away_team, match, matchMap);

    if (
        homeResolved.resolvedTeamId &&
        homeResolved.resolvedTeamId === match.winner.team_id
    ) {
        return homeResolved.displayName;
    }

    if (
        awayResolved.resolvedTeamId &&
        awayResolved.resolvedTeamId === match.winner.team_id
    ) {
        return awayResolved.displayName;
    }

    return "Pending";
}

function normalizeSourceLabel(label: string) {
    return label
        .replace("Winner match", "Winner of match")
        .replace("Loser match", "Loser of match");
}

function formatScore(match: BracketMatch) {
    const home = match.home_team.score;
    const away = match.away_team.score;

    if (home === null || home === undefined || away === null || away === undefined) {
        return "Pending";
    }

    return `${home} - ${away}`;
}

function PageState({ title, message }: { title: string; message: string }) {
    return (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sky-600">
                {title}
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-slate-950">{message}</h2>
        </section>
    );
}