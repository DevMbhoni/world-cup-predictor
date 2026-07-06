import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
    ChevronDown,
    ChevronUp,
    GitBranch,
    ShieldCheck,
    Target,
} from "lucide-react";
import { getPredictionHistory } from "../../api/predictions";
import { getTournamentBracket } from "../../api/tournament";
import type {
    BracketMatch,
    BracketTeam,
    KnockoutPredictionHistoryItem,
} from "../../types/api";

const leftRounds = [
    {
        title: "Round of 32",
        matchIds: [75, 78, 73, 76, 84, 83, 82, 81],
    },
    {
        title: "Round of 16",
        matchIds: [90, 89, 93, 94],
    },
    {
        title: "Quarter-finals",
        matchIds: [97, 98],
    },
    {
        title: "Semi-finals",
        matchIds: [101],
    },
];

const rightRounds = [
    {
        title: "Semi-finals",
        matchIds: [102],
    },
    {
        title: "Quarter-finals",
        matchIds: [99, 100],
    },
    {
        title: "Round of 16",
        matchIds: [91, 92, 95, 96],
    },
    {
        title: "Round of 32",
        matchIds: [74, 77, 79, 80, 87, 86, 85, 88],
    },
];

export default function BracketPage() {
    const bracketQuery = useQuery({
        queryKey: ["tournament-bracket"],
        queryFn: getTournamentBracket,
    });

    const predictionQuery = useQuery({
        queryKey: ["knockout-prediction-history"],
        queryFn: getPredictionHistory,
    });

    const matches = bracketQuery.data?.matches ?? [];
    const predictionHistory = predictionQuery.data;

    if (bracketQuery.isLoading) {
        return (
            <PageState
                title="Tournament bracket"
                message="Loading bracket..."
            />
        );
    }

    if (bracketQuery.isError) {
        return (
            <PageState
                title="Tournament bracket"
                message="Could not load bracket. Check that the FastAPI service is running."
            />
        );
    }

    const matchMap = new Map(
        matches.map((match) => [match.match_id, match])
    );

    const predictionMap = new Map<number, KnockoutPredictionHistoryItem>(
        (predictionHistory?.results ?? []).map((prediction) => [
            prediction.match_id,
            prediction,
        ])
    );

    const finalMatch = matches.find(
        (match) => match.stage_id === 7
    );

    const thirdPlaceMatch = matches.find(
        (match) => match.stage_id === 6
    );

    return (
        <div className="space-y-6">
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[#2f54eb]">
                            Tournament bracket
                        </p>

                        <h2 className="mt-3 text-3xl font-semibold text-slate-950">
                            Live knockout bracket
                        </h2>

                        <p className="mt-3 max-w-3xl text-slate-600">
                            Follow the real knockout path, confirmed fixtures,
                            model-projected future rounds, and archived pre-match
                            predictions.
                        </p>
                    </div>
                </div>
            </section>

            <PredictionPerformance
                count={predictionHistory?.count ?? 0}
                completedCount={predictionHistory?.completed_count ?? 0}
                correctCount={predictionHistory?.correct_count ?? 0}
                incorrectCount={predictionHistory?.incorrect_count ?? 0}
                accuracy={predictionHistory?.accuracy ?? null}
                isLoading={predictionQuery.isLoading}
                isError={predictionQuery.isError}
            />

            <section className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-2xl shadow-black/20">
                <div className="mb-6 flex items-center gap-3">
                    <div className="rounded-2xl border border-[#00e0c6]/30 bg-[#00e0c6]/10 p-3 text-[#2f54eb]">
                        <GitBranch size={22} />
                    </div>

                    <div>
                        <h3 className="text-xl font-semibold text-slate-950">
                            Bracket path
                        </h3>

                        <p className="text-sm text-slate-600">
                            The columns follow the actual knockout progression.
                            Scroll horizontally if the full bracket does not fit.
                        </p>
                    </div>
                </div>

                <div className="overflow-x-auto pb-5">
                    <div className="grid min-w-[1880px] grid-cols-[240px_270px_280px_290px_300px_290px_280px_270px_240px] gap-7">
                        {leftRounds.map((round, roundIndex) => (
                            <BracketColumn
                                key={round.title}
                                title={round.title}
                                matchIds={round.matchIds}
                                matchMap={matchMap}
                                predictionMap={predictionMap}
                                side="left"
                                roundIndex={roundIndex}
                            />
                        ))}

                        <div className="flex flex-col justify-center gap-6 pt-12">
                            <p className="text-center text-sm font-semibold text-slate-950">
                                Final
                            </p>

                            {finalMatch ? (
                                <FinalCard
                                    match={finalMatch}
                                    matchMap={matchMap}
                                    prediction={predictionMap.get(finalMatch.match_id)}
                                />
                            ) : (
                                <PlaceholderMatchCard matchId={104} />
                            )}

                            {thirdPlaceMatch && (
                                <div>
                                    <p className="mb-2 text-center text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">
                                        Third-place
                                    </p>

                                    <FinalCard
                                        match={thirdPlaceMatch}
                                        matchMap={matchMap}
                                        prediction={predictionMap.get(
                                            thirdPlaceMatch.match_id
                                        )}
                                        compact
                                    />
                                </div>
                            )}
                        </div>

                        {rightRounds.map((round, roundIndex) => (
                            <BracketColumn
                                key={round.title}
                                title={round.title}
                                matchIds={round.matchIds}
                                matchMap={matchMap}
                                predictionMap={predictionMap}
                                side="right"
                                roundIndex={roundIndex}
                            />
                        ))}
                    </div>
                </div>
            </section>

            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="mb-5 flex items-center gap-3">
                    <div className="rounded-2xl border border-[#2f54eb]/20 bg-[#2f54eb]/10 p-3 text-[#2f54eb]">
                        <ShieldCheck size={22} />
                    </div>

                    <div>
                        <h3 className="text-xl font-semibold text-slate-950">
                            Match list
                        </h3>

                        <p className="text-sm text-slate-600">
                            Full knockout match data with archived model prediction
                            status.
                        </p>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full min-w-[1180px] border-separate border-spacing-y-2">
                        <thead>
                            <tr className="text-left text-xs uppercase tracking-[0.2em] text-slate-500">
                                <th className="px-4 py-3">Match</th>
                                <th className="px-4 py-3">Stage</th>
                                <th className="px-4 py-3">Home</th>
                                <th className="px-4 py-3">Away</th>
                                <th className="px-4 py-3">Score</th>
                                <th className="px-4 py-3">Winner</th>
                                <th className="px-4 py-3">Model prediction</th>
                                <th className="px-4 py-3">Prediction result</th>
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

                                const prediction = predictionMap.get(
                                    match.match_id
                                );

                                return (
                                    <tr
                                        key={match.match_id}
                                        className="bg-slate-50"
                                    >
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

                                        <td className="px-4 py-4 text-[#2f54eb]">
                                            {getWinnerDisplay(match, matchMap)}
                                        </td>

                                        <td className="px-4 py-4 text-slate-700">
                                            {prediction
                                                ? `${prediction.predicted_winner} ${formatPercent(
                                                    prediction.prediction_probability
                                                )}`
                                                : match.stage_id >= 3 && match.is_completed
                                                    ? "Historical prediction unavailable"
                                                    : "Not archived yet"}
                                        </td>

                                        <td className="px-4 py-4">
                                            <PredictionResultBadge
                                                prediction={prediction}
                                            />
                                        </td>

                                        <td className="rounded-r-2xl px-4 py-4">
                                            <StatusBadge
                                                match={match}
                                                matchMap={matchMap}
                                            />
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

function PredictionPerformance({
    count,
    completedCount,
    correctCount,
    incorrectCount,
    accuracy,
    isLoading,
    isError,
}: {
    count: number;
    completedCount: number;
    correctCount: number;
    incorrectCount: number;
    accuracy: number | null;
    isLoading: boolean;
    isError: boolean;
}) {
    return (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
            <div className="flex items-center gap-3">
                <div className="rounded-2xl border border-[#6a00ff]/20 bg-[#6a00ff]/10 p-3 text-[#6a00ff]">
                    <Target size={22} />
                </div>

                <div>
                    <h3 className="text-xl font-semibold text-slate-950">
                        Knockout prediction performance
                    </h3>

                    <p className="text-sm text-slate-600">
                        Accuracy only includes predictions archived before the
                        corresponding match result was available.
                    </p>
                </div>
            </div>

            {isLoading ? (
                <p className="mt-6 text-sm text-slate-500">
                    Loading prediction history...
                </p>
            ) : isError ? (
                <p className="mt-6 text-sm text-[#ff2a1a]">
                    Prediction history could not be loaded.
                </p>
            ) : (
                <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
                    <PerformanceStat
                        label="Tracked"
                        value={String(count)}
                        accent="blue"
                    />

                    <PerformanceStat
                        label="Completed"
                        value={String(completedCount)}
                        accent="purple"
                    />

                    <PerformanceStat
                        label="Correct"
                        value={String(correctCount)}
                        accent="green"
                    />

                    <PerformanceStat
                        label="Incorrect"
                        value={String(incorrectCount)}
                        accent="red"
                    />

                    <PerformanceStat
                        label="Accuracy"
                        value={
                            accuracy === null
                                ? "—"
                                : `${accuracy.toFixed(2)}%`
                        }
                        accent="orange"
                    />
                </div>
            )}
        </section>
    );
}

function PerformanceStat({
    label,
    value,
    accent,
}: {
    label: string;
    value: string;
    accent: "blue" | "purple" | "green" | "red" | "orange";
}) {
    const accentClasses = {
        blue: "border-[#2f54eb]/20 bg-[#2f54eb]/10 text-[#2f54eb]",
        purple:
            "border-[#6a00ff]/20 bg-[#6a00ff]/10 text-[#6a00ff]",
        green:
            "border-[#10c840]/20 bg-[#10c840]/10 text-[#0a8f2f]",
        red: "border-[#ff2a1a]/20 bg-[#ff2a1a]/10 text-[#ff2a1a]",
        orange:
            "border-[#ff651f]/20 bg-[#ff651f]/10 text-[#ff651f]",
    };

    return (
        <div
            className={`rounded-3xl border p-5 ${accentClasses[accent]}`}
        >
            <p className="text-3xl font-black">{value}</p>

            <p className="mt-2 text-xs font-semibold uppercase tracking-[0.2em]">
                {label}
            </p>
        </div>
    );
}

function BracketColumn({
    title,
    matchIds,
    matchMap,
    predictionMap,
    side,
    roundIndex,
}: {
    title: string;
    matchIds: number[];
    matchMap: Map<number, BracketMatch>;
    predictionMap: Map<number, KnockoutPredictionHistoryItem>;
    side: "left" | "right";
    roundIndex: number;
}) {
    const spacingClass =
        matchIds.length === 8
            ? "gap-5"
            : matchIds.length === 4
                ? "gap-[7.5rem] pt-[5rem]"
                : matchIds.length === 2
                    ? "gap-[22rem] pt-[13rem]"
                    : "pt-[31rem]";

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
                            className={`relative ${side === "left"
                                    ? "bracket-left"
                                    : "bracket-right"
                                } ${roundIndex > 0 ? "has-connector" : ""
                                }`}
                        >
                            {match ? (
                                <BracketMatchCard
                                    match={match}
                                    matchMap={matchMap}
                                    prediction={predictionMap.get(matchId)}
                                />
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
    prediction,
}: {
    match: BracketMatch;
    matchMap: Map<number, BracketMatch>;
    prediction?: KnockoutPredictionHistoryItem;
}) {
    const [expanded, setExpanded] = useState(false);

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

    const showHistoricalUnavailable =
        match.stage_id >= 3 &&
        match.is_completed &&
        !prediction;

    return (
        <div className="relative z-10 rounded-3xl border border-slate-200 bg-white p-4 shadow-xl shadow-black/20">
            <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                    M{match.match_id}
                </p>

                <StatusBadge
                    match={match}
                    matchMap={matchMap}
                />
            </div>

            <div className="space-y-2">
                <TeamRow
                    team={match.home_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={
                        homeResolved.resolvedTeamId === match.winner.team_id
                    }
                />

                <TeamRow
                    team={match.away_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={
                        awayResolved.resolvedTeamId === match.winner.team_id
                    }
                />
            </div>

            {prediction && (
                <PredictionSummary prediction={prediction} />
            )}

            {showHistoricalUnavailable && (
                <div className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                        Model history
                    </p>

                    <p className="mt-2 text-xs font-medium text-slate-700">
                        Historical prediction unavailable
                    </p>

                    <p className="mt-1 text-[11px] leading-5 text-slate-500">
                        Pre-match prediction tracking started from M93.
                    </p>
                </div>
            )}

            {prediction && (
                <>
                    <button
                        type="button"
                        onClick={() => setExpanded((current) => !current)}
                        className="mt-3 flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-[#2f54eb]/30 hover:text-[#2f54eb]"
                    >
                        <span>
                            {expanded
                                ? "Hide prediction details"
                                : "View prediction details"}
                        </span>

                        {expanded ? (
                            <ChevronUp size={15} />
                        ) : (
                            <ChevronDown size={15} />
                        )}
                    </button>

                    {expanded && (
                        <PredictionDetails prediction={prediction} />
                    )}
                </>
            )}
        </div>
    );
}

function PredictionSummary({
    prediction,
}: {
    prediction: KnockoutPredictionHistoryItem;
}) {
    return (
        <div className="mt-3 rounded-2xl border border-[#2f54eb]/20 bg-[#2f54eb]/5 p-3">
            <div className="flex items-start justify-between gap-3">
                <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#2f54eb]">
                        Model prediction
                    </p>

                    <p className="mt-1 text-xs font-semibold text-slate-950">
                        {prediction.predicted_winner} to win
                    </p>
                </div>

                <p className="text-xs font-bold text-[#2f54eb]">
                    {formatPercent(prediction.prediction_probability)}
                </p>
            </div>

            {prediction.actual_winner && (
                <div className="mt-3 flex items-center justify-between gap-3 border-t border-[#2f54eb]/10 pt-3">
                    <div>
                        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
                            Actual winner
                        </p>

                        <p className="mt-1 text-xs font-semibold text-slate-950">
                            {prediction.actual_winner}
                        </p>
                    </div>

                    <PredictionResultBadge prediction={prediction} />
                </div>
            )}
        </div>
    );
}

function PredictionDetails({
    prediction,
}: {
    prediction: KnockoutPredictionHistoryItem;
}) {
    return (
        <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
                Outcome probabilities
            </p>

            <div className="mt-3 grid grid-cols-3 gap-2">
                <ProbabilityItem
                    label="Home"
                    value={prediction.home_win_probability}
                />

                <ProbabilityItem
                    label="Draw"
                    value={prediction.draw_probability}
                />

                <ProbabilityItem
                    label="Away"
                    value={prediction.away_win_probability}
                />
            </div>

            <div className="mt-3 border-t border-slate-200 pt-3">
                <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
                    Predicted score
                </p>

                <p className="mt-1 text-sm font-semibold text-slate-950">
                    {prediction.home_team}{" "}
                    {prediction.predicted_home_score ?? "—"} -{" "}
                    {prediction.predicted_away_score ?? "—"}{" "}
                    {prediction.away_team}
                </p>
            </div>

            {prediction.actual_home_score !== null &&
                prediction.actual_away_score !== null && (
                    <div className="mt-3 border-t border-slate-200 pt-3">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
                            Actual result
                        </p>

                        <p className="mt-1 text-sm font-semibold text-slate-950">
                            {prediction.home_team}{" "}
                            {prediction.actual_home_score} -{" "}
                            {prediction.actual_away_score}{" "}
                            {prediction.away_team}
                        </p>
                    </div>
                )}

            <p className="mt-3 text-[10px] leading-4 text-slate-400">
                Archived {formatPredictionDate(prediction.predicted_at)}
            </p>
        </div>
    );
}

function ProbabilityItem({
    label,
    value,
}: {
    label: string;
    value: number;
}) {
    return (
        <div className="rounded-xl bg-slate-50 px-2 py-2 text-center">
            <p className="text-[9px] uppercase tracking-[0.14em] text-slate-500">
                {label}
            </p>

            <p className="mt-1 text-xs font-bold text-slate-950">
                {formatPercent(value)}
            </p>
        </div>
    );
}

function PredictionResultBadge({
    prediction,
}: {
    prediction?: KnockoutPredictionHistoryItem;
}) {
    if (!prediction || prediction.prediction_correct === null) {
        return (
            <span className="text-xs text-slate-500">
                Pending
            </span>
        );
    }

    if (prediction.prediction_correct) {
        return (
            <span className="rounded-full border border-[#10c840]/30 bg-[#10c840]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-[#0a8f2f]">
                Correct
            </span>
        );
    }

    return (
        <span className="rounded-full border border-[#ff2a1a]/30 bg-[#ff2a1a]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-[#ff2a1a]">
            Incorrect
        </span>
    );
}

function FinalCard({
    match,
    matchMap,
    prediction,
    compact = false,
}: {
    match: BracketMatch;
    matchMap: Map<number, BracketMatch>;
    prediction?: KnockoutPredictionHistoryItem;
    compact?: boolean;
}) {
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
        <div
            className={`rounded-[2rem] border border-[#ff651f]/20 bg-[#ff651f]/10 p-5 shadow-xl shadow-black/20 ${compact ? "" : "min-h-[190px]"
                }`}
        >
            <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-[#ff651f]">
                    M{match.match_id}
                </p>

                <StatusBadge
                    match={match}
                    matchMap={matchMap}
                />
            </div>

            <div className="space-y-2">
                <TeamRow
                    team={match.home_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={
                        homeResolved.resolvedTeamId === match.winner.team_id
                    }
                />

                <TeamRow
                    team={match.away_team}
                    match={match}
                    matchMap={matchMap}
                    isWinner={
                        awayResolved.resolvedTeamId === match.winner.team_id
                    }
                />
            </div>

            {prediction && (
                <PredictionSummary prediction={prediction} />
            )}

            {getWinnerDisplay(match, matchMap) !== "Pending" && (
                <div className="mt-4 rounded-2xl border border-[#ff651f]/20 bg-white/70 px-3 py-2">
                    <p className="text-xs text-[#ff651f]">
                        {match.winner.is_projected
                            ? "Projected winner"
                            : "Winner"}
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
    const resolved = resolveBracketSlot(
        team,
        match,
        matchMap
    );

    return (
        <div
            className={`flex items-center justify-between gap-3 rounded-2xl border px-3 py-3 ${isWinner
                    ? "border-[#00e0c6]/30 bg-[#00e0c6]/10"
                    : "border-slate-200 bg-slate-50"
                }`}
        >
            <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-950">
                    {resolved.displayName}
                </p>

                {resolved.projectedName && (
                    <p className="mt-1 truncate text-xs text-[#ff651f]">
                        Projection: {resolved.projectedName}
                    </p>
                )}
            </div>

            <div className="shrink-0 text-right">
                {team.score !== null &&
                    team.score !== undefined ? (
                    <p className="text-lg font-semibold text-slate-950">
                        {team.score}
                    </p>
                ) : (
                    <p className="text-xs text-slate-500">
                        TBD
                    </p>
                )}
            </div>
        </div>
    );
}

function PlaceholderMatchCard({
    matchId,
}: {
    matchId: number;
}) {
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

function isMatchupConfirmed(
    match: BracketMatch,
    matchMap: Map<number, BracketMatch>
) {
    const home = resolveBracketSlot(
        match.home_team,
        match,
        matchMap
    );

    const away = resolveBracketSlot(
        match.away_team,
        match,
        matchMap
    );

    return (
        home.resolvedTeamId !== null &&
        home.resolvedTeamId !== undefined &&
        away.resolvedTeamId !== null &&
        away.resolvedTeamId !== undefined
    );
}

function StatusBadge({
    match,
    matchMap,
}: {
    match: BracketMatch;
    matchMap?: Map<number, BracketMatch>;
}) {
    if (match.is_completed) {
        return (
            <span className="rounded-full border border-[#10c840]/30 bg-[#10c840]/10 px-3 py-1 text-xs font-medium text-[#0a8f2f]">
                Completed
            </span>
        );
    }

    const matchupConfirmed =
        matchMap !== undefined &&
        isMatchupConfirmed(match, matchMap);

    if (matchupConfirmed) {
        return (
            <span className="rounded-full border border-[#2f54eb]/30 bg-[#2f54eb]/10 px-3 py-1 text-xs font-medium text-[#2f54eb]">
                Confirmed
            </span>
        );
    }

    if (match.winner.is_projected) {
        return (
            <span className="rounded-full border border-[#ff651f]/30 bg-[#ff651f]/10 px-3 py-1 text-xs font-medium text-[#ff651f]">
                Projected
            </span>
        );
    }

    return (
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
            Scheduled
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

    if (
        team.team_name &&
        !team.source?.source_match_id &&
        !team.projection
    ) {
        return {
            displayName: team.team_name,
            projectedName: null as string | null,
            resolvedTeamId: team.team_id,
        };
    }

    const sourceMatchId =
        team.source?.source_match_id;

    const sourceType =
        team.source?.source_type;

    const sourceMatch = sourceMatchId
        ? matchMap.get(sourceMatchId)
        : undefined;

    if (sourceMatch?.is_completed) {
        const sourceResult =
            sourceType === "loser"
                ? sourceMatch.loser
                : sourceMatch.winner;

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
            displayName: normalizeSourceLabel(
                team.source.label
            ),
            projectedName: getProjectionName(team),
            resolvedTeamId: null as number | null,
        };
    }

    return {
        displayName:
            team.team_name ?? "To be decided",
        projectedName: getProjectionName(team),
        resolvedTeamId: team.team_id,
    };
}

function getProjectionName(team: BracketTeam) {
    if (team.projection?.team_name) {
        return team.projection.team_name;
    }

    if (
        team.source?.label &&
        team.team_name &&
        team.team_name !== team.source.label
    ) {
        return team.team_name;
    }

    return null;
}

function getWinnerDisplay(
    match: BracketMatch,
    matchMap: Map<number, BracketMatch>
) {
    if (
        match.is_completed &&
        match.winner.team_name
    ) {
        return match.winner.team_name;
    }

    if (
        !match.winner.is_projected &&
        match.winner.team_name
    ) {
        return match.winner.team_name;
    }

    if (match.winner.team_name) {
        return match.winner.team_name;
    }

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

    if (
        homeResolved.resolvedTeamId &&
        homeResolved.resolvedTeamId ===
        match.winner.team_id
    ) {
        return homeResolved.displayName;
    }

    if (
        awayResolved.resolvedTeamId &&
        awayResolved.resolvedTeamId ===
        match.winner.team_id
    ) {
        return awayResolved.displayName;
    }

    return "Pending";
}

function normalizeSourceLabel(label: string) {
    return label
        .replace(
            "Winner match",
            "Winner of match"
        )
        .replace(
            "Loser match",
            "Loser of match"
        );
}

function formatScore(match: BracketMatch) {
    const home = match.home_team.score;
    const away = match.away_team.score;

    if (
        home === null ||
        home === undefined ||
        away === null ||
        away === undefined
    ) {
        return "Pending";
    }

    return `${home} - ${away}`;
}

function formatPercent(value: number) {
    return `${Number(value).toFixed(1)}%`;
}

function formatPredictionDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat("en-ZA", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

function PageState({
    title,
    message,
}: {
    title: string;
    message: string;
}) {
    return (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[#2f54eb]">
                {title}
            </p>

            <h2 className="mt-3 text-3xl font-semibold text-slate-950">
                {message}
            </h2>
        </section>
    );
}