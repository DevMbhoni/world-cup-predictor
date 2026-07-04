import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
    CheckCircle2,
    ChevronDown,
    Search,
    Shield,
    Swords,
    TrendingUp,
} from "lucide-react";
import { getTeams } from "../../api/teams";
import { predictMatch } from "../../api/matches";
import type { PredictionResult } from "../../types/api";

export default function MatchPredictor() {
    const [homeTeam, setHomeTeam] = useState("Canada");
    const [awayTeam, setAwayTeam] = useState("Morocco");
    const [submittedMatch, setSubmittedMatch] = useState<{
        home: string;
        away: string;
    } | null>(null);

    const teamsQuery = useQuery({
        queryKey: ["teams"],
        queryFn: getTeams,
    });

    const predictionQuery = useQuery({
        queryKey: ["match-prediction", submittedMatch?.home, submittedMatch?.away],
        queryFn: () =>
            predictMatch(submittedMatch?.home ?? "", submittedMatch?.away ?? ""),
        enabled: Boolean(submittedMatch),
    });

    const teams = useMemo(() => teamsQuery.data?.results ?? [], [teamsQuery.data]);
    const teamNames = teams.map((team) => team.team_name);

    function handleSubmit(event: React.FormEvent) {
        event.preventDefault();

        if (!homeTeam || !awayTeam || homeTeam === awayTeam) {
            return;
        }

        setSubmittedMatch({
            home: homeTeam,
            away: awayTeam,
        });
    }

    const prediction = predictionQuery.data?.prediction;

    return (
        <div className="grid gap-6 xl:grid-cols-[430px_1fr]">
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/30">
                <div className="flex items-center gap-4">
                    <div className="rounded-2xl border border-cyan-400/20 bg-[#00e0c6]/10 p-3 text-[#2f54eb]">
                        <Swords size={22} />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-slate-950">Match predictor</h2>
                        <p className="mt-1 text-sm text-slate-600">
                            Select two teams and run the full prediction model.
                        </p>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="mt-7 space-y-5">
                    <TeamCombobox
                        label="Home team"
                        value={homeTeam}
                        onChange={setHomeTeam}
                        teams={teamNames}
                        disabled={teamsQuery.isLoading}
                    />

                    <TeamCombobox
                        label="Away team"
                        value={awayTeam}
                        onChange={setAwayTeam}
                        teams={teamNames}
                        disabled={teamsQuery.isLoading}
                    />

                    {homeTeam === awayTeam && (
                        <p className="rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                            Select two different teams.
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={
                            predictionQuery.isFetching ||
                            teamsQuery.isLoading ||
                            !homeTeam ||
                            !awayTeam ||
                            homeTeam === awayTeam
                        }
                        className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#00e0c6] px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-50"
                    >
                        <Search size={18} />
                        {predictionQuery.isFetching ? "Predicting..." : "Predict match"}
                    </button>
                </form>

                <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-medium text-slate-950">Model stack</p>
                    <div className="mt-4 space-y-3 text-sm text-slate-600">
                        <ModelStackItem label="Calibrated 1X2 classifier" />
                        <ModelStackItem label="Poisson scoreline model" />
                        <ModelStackItem label="Market probability models" />
                        <ModelStackItem label="Blended final prediction" />
                    </div>
                </div>

                {teamsQuery.isError && (
                    <p className="mt-4 rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                        Could not load teams. Check that FastAPI is running on port 8000.
                    </p>
                )}
            </section>

            <section className="min-h-[640px] rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/30">
                {!prediction && !predictionQuery.isError && (
                    <div className="flex h-full min-h-[560px] items-center justify-center text-center">
                        <div>
                            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl border border-cyan-400/20 bg-[#00e0c6]/10 text-[#2f54eb]">
                                <TrendingUp size={28} />
                            </div>
                            <h3 className="mt-5 text-2xl font-semibold text-slate-950">
                                Prediction results will appear here
                            </h3>
                            <p className="mt-3 max-w-md text-sm leading-6 text-slate-600">
                                The model combines classifier probabilities, expected goals,
                                scoreline simulation, and market probabilities.
                            </p>
                        </div>
                    </div>
                )}

                {predictionQuery.isError && (
                    <div className="rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                        Prediction failed. Check the backend logs for the exact error.
                    </div>
                )}

                {prediction && <PredictionPanel prediction={prediction} />}
            </section>
        </div>
    );
}

function ModelStackItem({ label }: { label: string }) {
    return (
        <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-[#2f54eb]" />
            <span>{label}</span>
        </div>
    );
}

type TeamComboboxProps = {
    label: string;
    value: string;
    onChange: (value: string) => void;
    teams: string[];
    disabled: boolean;
};

function TeamCombobox({
    label,
    value,
    onChange,
    teams,
    disabled,
}: TeamComboboxProps) {
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState("");

    const filteredTeams = teams
        .filter((team) => team.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 12);

    function selectTeam(team: string) {
        onChange(team);
        setQuery("");
        setOpen(false);
    }

    return (
        <div className="relative">
            <label className="text-sm font-medium text-slate-700">{label}</label>

            <button
                type="button"
                disabled={disabled}
                onClick={() => setOpen((current) => !current)}
                className="mt-2 flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-slate-950 outline-none transition hover:border-cyan-400/40 disabled:opacity-50"
            >
                <span>{value || "Select team"}</span>
                <ChevronDown size={18} className="text-slate-600" />
            </button>

            {open && (
                <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-black/50">
                    <div className="border-b border-slate-200 p-3">
                        <input
                            autoFocus
                            value={query}
                            onChange={(event) => setQuery(event.target.value)}
                            placeholder="Search team"
                            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-cyan-400 transition placeholder:text-slate-500 focus:ring-2"
                        />
                    </div>

                    <div className="max-h-72 overflow-y-auto p-2">
                        {filteredTeams.map((team) => (
                            <button
                                key={team}
                                type="button"
                                onClick={() => selectTeam(team)}
                                className="block w-full rounded-xl px-3 py-2 text-left text-sm text-slate-200 transition hover:bg-[#00e0c6]/10 hover:text-sky-700"
                            >
                                {team}
                            </button>
                        ))}

                        {filteredTeams.length === 0 && (
                            <p className="px-3 py-3 text-sm text-slate-500">No teams found.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function PredictionPanel({ prediction }: { prediction: PredictionResult }) {
    const final = prediction.final_prediction;
    const expectedGoals = prediction.scoreline_model.expected_goals;

    return (
        <div>
            <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-6 lg:flex-row">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[#2f54eb]">
                        Final prediction
                    </p>
                    <h2 className="mt-3 text-3xl font-semibold text-slate-950 md:text-4xl">
                        {formatResult(
                            final.result,
                            prediction.match.home_team,
                            prediction.match.away_team
                        )}
                    </h2>
                    <p className="mt-3 text-sm text-slate-600">
                        Confidence: {final.confidence}. Model agreement:{" "}
                        {prediction.model_agreement.agree ? "Agree" : "Disagree"}.
                    </p>
                </div>

                <div className="rounded-3xl border border-amber-400/20 bg-[#ff651f]/10 px-6 py-4 lg:text-right">
                    <p className="text-sm text-amber-700">Prediction probability</p>
                    <p className="mt-1 text-4xl font-semibold text-slate-950">
                        {final.probability_percent}%
                    </p>
                </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-3">
                <ProbabilityCard
                    label={`${prediction.match.home_team} win`}
                    value={final.probabilities_percent.home_win}
                    accent="cyan"
                />
                <ProbabilityCard
                    label="Draw"
                    value={final.probabilities_percent.draw}
                    accent="gold"
                />
                <ProbabilityCard
                    label={`${prediction.match.away_team} win`}
                    value={final.probabilities_percent.away_win}
                    accent="red"
                />
            </div>

            <div className="mt-6 grid gap-4 xl:grid-cols-2">
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                    <div className="flex items-center gap-2 text-slate-700">
                        <Shield size={18} className="text-[#2f54eb]" />
                        <h3 className="font-semibold text-slate-950">Expected goals</h3>
                    </div>

                    <div className="mt-5 grid grid-cols-2 gap-3">
                        <ExpectedGoalCard
                            team={prediction.match.home_team}
                            value={expectedGoals.home}
                        />
                        <ExpectedGoalCard
                            team={prediction.match.away_team}
                            value={expectedGoals.away}
                        />
                    </div>
                </div>

                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                    <h3 className="font-semibold text-slate-950">Market probabilities</h3>
                    <div className="mt-4 space-y-3">
                        <MarketRow
                            label="Over 2.5 goals"
                            value={prediction.markets.poisson_percent.over_2_5}
                        />
                        <MarketRow
                            label="Both teams to score"
                            value={prediction.markets.poisson_percent.both_teams_score}
                        />
                        <MarketRow
                            label={`${prediction.match.home_team} clean sheet`}
                            value={prediction.markets.poisson_percent.home_clean_sheet}
                        />
                        <MarketRow
                            label={`${prediction.match.away_team} clean sheet`}
                            value={prediction.markets.poisson_percent.away_clean_sheet}
                        />
                    </div>
                </div>
            </div>

            <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                <h3 className="font-semibold text-slate-950">Most likely scorelines</h3>
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                    {prediction.scoreline_model.top_scorelines.slice(0, 5).map((item) => (
                        <div
                            key={`${item.scoreline}-${item.probability}`}
                            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                        >
                            <p className="text-2xl font-semibold text-slate-950">{item.scoreline}</p>
                            <p className="mt-1 text-sm text-slate-600">
                                {item.probability_percent}%
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function ProbabilityCard({
    label,
    value,
    accent,
}: {
    label: string;
    value: number;
    accent: "cyan" | "gold" | "red";
}) {
    const barClass = {
        cyan: "bg-[#00e0c6]",
        gold: "bg-[#ff651f]",
        red: "bg-[#ff2a1a]",
    };

    return (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-600">{label}</p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">{value}%</p>
            <div className="mt-4 h-2 rounded-full bg-slate-800">
                <div
                    className={`h-2 rounded-full ${barClass[accent]}`}
                    style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
                />
            </div>
        </div>
    );
}

function ExpectedGoalCard({ team, value }: { team: string; value: number }) {
    return (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm text-slate-600">{team}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-950">{value}</p>
        </div>
    );
}

function MarketRow({ label, value }: { label: string; value: number }) {
    return (
        <div>
            <div className="flex justify-between gap-4 text-sm">
                <span className="text-slate-600">{label}</span>
                <span className="font-medium text-slate-950">{value}%</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-slate-800">
                <div
                    className="h-2 rounded-full bg-[#00e0c6]"
                    style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
                />
            </div>
        </div>
    );
}

function formatResult(result: string, homeTeam: string, awayTeam: string) {
    if (result === "HOME_WIN") return `${homeTeam} win`;
    if (result === "AWAY_WIN") return `${awayTeam} win`;
    return "Draw";
}