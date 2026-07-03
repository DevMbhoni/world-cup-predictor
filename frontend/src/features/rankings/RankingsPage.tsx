import { useQuery } from "@tanstack/react-query";
import { BarChart3, Medal, ShieldCheck } from "lucide-react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { getTeamRankings } from "../../api/rankings";
import type { TeamRanking } from "../../types/api";

export default function RankingsPage() {
    const rankingsQuery = useQuery({
        queryKey: ["team-rankings"],
        queryFn: () => getTeamRankings(50),
    });

    const teams = rankingsQuery.data?.results ?? [];
    const topTeams = teams.slice(0, 12);

    if (rankingsQuery.isLoading) {
        return <PageState title="Team rankings" message="Loading Elo rankings..." />;
    }

    if (rankingsQuery.isError) {
        return (
            <PageState
                title="Team rankings"
                message="Could not load team rankings. Check that the FastAPI service is running."
            />
        );
    }

    return (
        <div className="space-y-6">
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sky-600">
                            Team rankings
                        </p>
                        <h2 className="mt-3 text-3xl font-semibold text-slate-950">
                            Elo-based team strength
                        </h2>
                        <p className="mt-3 max-w-3xl text-slate-600">
                            Current team strength ranking generated from historic international match results.
                            These ratings are used as part of the match prediction and tournament simulation pipeline.
                        </p>
                    </div>

                    {teams[0] && (
                        <div className="rounded-3xl border border-amber-400/20 bg-amber-400/10 px-5 py-4">
                            <p className="text-sm text-amber-700">Current number one</p>
                            <p className="mt-1 text-2xl font-semibold text-slate-950">
                                {teams[0].team}
                            </p>
                            <p className="mt-1 text-sm text-slate-700">
                                {teams[0].elo_rating.toFixed(2)} Elo
                            </p>
                        </div>
                    )}
                </div>
            </section>

            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                    <div className="flex items-center gap-3">
                        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3 text-sky-600">
                            <BarChart3 size={22} />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold text-slate-950">
                                Top Elo ratings
                            </h3>
                            <p className="text-sm text-slate-600">
                                Top 12 teams by current Elo rating.
                            </p>
                        </div>
                    </div>

                    <div className="mt-6 h-[380px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topTeams}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                                <XAxis
                                    dataKey="team"
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    interval={0}
                                    angle={-25}
                                    textAnchor="end"
                                    height={90}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    domain={["dataMin - 40", "dataMax + 20"]}
                                />
                                <Tooltip
                                    contentStyle={{
                                        color: "#fff",
                                        border: "1px solid rgba(255,255,255,0.1)",
                                        borderRadius: "16px",
                                    }}
                                    formatter={(value) => [
                                        Number(value).toFixed(2),
                                        "Elo rating",
                                    ]}
                                />
                                <Bar
                                    dataKey="elo_rating"
                                    radius={[10, 10, 0, 0]}
                                    fill="#22d3ee"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>

                <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                    <div className="flex items-center gap-3">
                        <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-3 text-amber-600">
                            <Medal size={22} />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold text-slate-950">
                                Top ranked teams
                            </h3>
                            <p className="text-sm text-slate-600">
                                Highest Elo teams in the current model output.
                            </p>
                        </div>
                    </div>

                    <div className="mt-6 space-y-3">
                        {topTeams.slice(0, 8).map((team, index) => (
                            <RankingCard key={team.team} team={team} rank={index + 1} />
                        ))}
                    </div>
                </section>
            </div>

            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex items-center gap-3">
                    <div className="rounded-2xl border border-blue-500/20 bg-blue-500/10 p-3 text-blue-600">
                        <ShieldCheck size={22} />
                    </div>
                    <div>
                        <h3 className="text-xl font-semibold text-slate-950">
                            Full ranking table
                        </h3>
                        <p className="text-sm text-slate-600">
                            Elo ratings from the processed model output.
                        </p>
                    </div>
                </div>

                <div className="mt-6 overflow-x-auto">
                    <table className="w-full min-w-[760px] border-separate border-spacing-y-2">
                        <thead>
                            <tr className="text-left text-xs uppercase tracking-[0.2em] text-slate-500">
                                <th className="px-4 py-3">Rank</th>
                                <th className="px-4 py-3">Team</th>
                                <th className="px-4 py-3">Elo rating</th>
                                <th className="px-4 py-3">Last match date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {teams.map((team, index) => (
                                <tr key={team.team} className="bg-slate-50">
                                    <td className="rounded-l-2xl px-4 py-4 text-slate-700">
                                        {team.elo_rank ?? index + 1}
                                    </td>
                                    <td className="px-4 py-4 font-medium text-slate-950">
                                        {team.team}
                                    </td>
                                    <td className="px-4 py-4 text-sky-600">
                                        {team.elo_rating.toFixed(2)}
                                    </td>
                                    <td className="rounded-r-2xl px-4 py-4 text-slate-700">
                                        {team.date ?? "Unavailable"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}

function RankingCard({ team, rank }: { team: TeamRanking; rank: number }) {
    return (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-4">
                <div>
                    <p className="text-sm text-slate-500">Rank {rank}</p>
                    <p className="mt-1 font-semibold text-slate-950">{team.team}</p>
                </div>
                <p className="text-xl font-semibold text-sky-600">
                    {team.elo_rating.toFixed(0)}
                </p>
            </div>

            <div className="mt-3 h-2 rounded-full bg-slate-800">
                <div
                    className="h-2 rounded-full bg-cyan-400"
                    style={{
                        width: `${Math.min(Math.max((team.elo_rating - 1500) / 7, 8), 100)}%`,
                    }}
                />
            </div>
        </div>
    );
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