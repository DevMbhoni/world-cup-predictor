import { useQuery } from "@tanstack/react-query";
import { Activity, Crown, Trophy } from "lucide-react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { getTournamentSimulation } from "../../api/tournament";
import type { TournamentTeamSimulation } from "../../types/api";

export default function TournamentPage() {
    const simulationQuery = useQuery({
        queryKey: ["tournament-simulation"],
        queryFn: () => getTournamentSimulation(25),
    });

    const teams = simulationQuery.data?.results ?? [];
    const topTeams = teams.slice(0, 10);

    if (simulationQuery.isLoading) {
        return <PageCard title="Tournament simulation" message="Loading tournament probabilities..." />;
    }

    if (simulationQuery.isError) {
        return (
            <PageCard
                title="Tournament simulation"
                message="Could not load tournament simulation. Check that the FastAPI service is running."
            />
        );
    }

    return (
        <div className="space-y-6">
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[#2f54eb]">
                            Tournament simulation
                        </p>
                        <h2 className="mt-3 text-3xl font-semibold text-slate-950">
                            Live title probabilities
                        </h2>
                        <p className="mt-3 max-w-3xl text-slate-600">
                            Completed matches are locked. Scheduled matches are simulated from
                            the live bracket and scoreline model.
                        </p>
                    </div>

                    <div className="rounded-3xl border border-amber-400/20 bg-[#ff651f]/10 px-5 py-4">
                        <p className="text-sm text-amber-700">Current favourite</p>
                        <p className="mt-1 text-2xl font-semibold text-slate-950">
                            {teams[0]?.team ?? "Unavailable"}
                        </p>
                        <p className="mt-1 text-sm text-slate-700">
                            {toPercent(teams[0]?.winner_probability)} win probability
                        </p>
                    </div>
                </div>
            </section>

            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                    <div className="flex items-center gap-3">
                        <div className="rounded-2xl border border-cyan-400/20 bg-[#00e0c6]/10 p-3 text-[#2f54eb]">
                            <Trophy size={22} />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold text-slate-950">
                                Top winner probabilities
                            </h3>
                            <p className="text-sm text-slate-600">
                                Top 10 teams by simulated tournament win chance.
                            </p>
                        </div>
                    </div>

                    <div className="mt-6 h-[360px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topTeams}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                                <XAxis
                                    dataKey="team"
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    interval={0}
                                    angle={-20}
                                    textAnchor="end"
                                    height={70}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 12 }}
                                    tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`}
                                />
                                <Tooltip
                                    contentStyle={{
                                        color: "#fff",
                                        border: "1px solid rgba(255,255,255,0.1)",
                                        borderRadius: "16px",
                                    }}
                                    formatter={(value) => [`${toPercent(Number(value))}`, "Win probability"]}
                                />
                                <Bar
                                    dataKey="winner_probability"
                                    radius={[10, 10, 0, 0]}
                                    fill="#2f54eb"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>

                <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                    <div className="flex items-center gap-3">
                        <div className="rounded-2xl border border-amber-400/20 bg-[#ff651f]/10 p-3 text-[#ff651f]">
                            <Crown size={22} />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold text-slate-950">Contenders</h3>
                            <p className="text-sm text-slate-600">
                                Highest probability teams still alive.
                            </p>
                        </div>
                    </div>

                    <div className="mt-6 space-y-3">
                        {topTeams.slice(0, 7).map((team, index) => (
                            <ContenderRow key={team.team_id} team={team} rank={index + 1} />
                        ))}
                    </div>
                </section>
            </div>

            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex items-center gap-3">
                    <div className="rounded-2xl border border-blue-500/20 bg-blue-500/10 p-3 text-blue-600">
                        <Activity size={22} />
                    </div>
                    <div>
                        <h3 className="text-xl font-semibold text-slate-950">
                            Full simulation table
                        </h3>
                        <p className="text-sm text-slate-600">
                            Round progression probabilities by team.
                        </p>
                    </div>
                </div>

                <div className="mt-6 overflow-x-auto">
                    <table className="w-full min-w-[900px] border-separate border-spacing-y-2">
                        <thead>
                            <tr className="text-left text-xs uppercase tracking-[0.2em] text-slate-500">
                                <th className="px-4 py-3">Team</th>
                                <th className="px-4 py-3">Status</th>
                                <th className="px-4 py-3">Winner</th>
                                <th className="px-4 py-3">Final</th>
                                <th className="px-4 py-3">Semi-final</th>
                                <th className="px-4 py-3">Quarter-final</th>
                                <th className="px-4 py-3">Round of 16</th>
                            </tr>
                        </thead>
                        <tbody>
                            {teams.map((team) => (
                                <tr key={team.team_id} className="bg-slate-50">
                                    <td className="rounded-l-2xl px-4 py-4 font-medium text-slate-950">
                                        {team.team}
                                    </td>
                                    <td className="px-4 py-4">
                                        <StatusBadge status={team.status} />
                                    </td>
                                    <td className="px-4 py-4 text-slate-700">
                                        {toPercent(team.winner_probability)}
                                    </td>
                                    <td className="px-4 py-4 text-slate-700">
                                        {toPercent(team.final_probability)}
                                    </td>
                                    <td className="px-4 py-4 text-slate-700">
                                        {toPercent(team.semi_final_probability)}
                                    </td>
                                    <td className="px-4 py-4 text-slate-700">
                                        {toPercent(team.quarter_final_probability)}
                                    </td>
                                    <td className="rounded-r-2xl px-4 py-4 text-slate-700">
                                        {toPercent(team.round_of_16_probability)}
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

function PageCard({ title, message }: { title: string; message: string }) {
    return (
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[#2f54eb]">
                {title}
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-slate-950">{message}</h2>
        </section>
    );
}

function ContenderRow({
    team,
    rank,
}: {
    team: TournamentTeamSimulation;
    rank: number;
}) {
    return (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-4">
                <div>
                    <p className="text-sm text-slate-500">Rank {rank}</p>
                    <p className="mt-1 font-semibold text-slate-950">{team.team}</p>
                </div>
                <p className="text-xl font-semibold text-[#2f54eb]">
                    {toPercent(team.winner_probability)}
                </p>
            </div>

            <div className="mt-3 h-2 rounded-full bg-slate-800">
                <div
                    className="h-2 rounded-full bg-[#00e0c6]"
                    style={{
                        width: `${Math.min(Math.max(team.winner_probability * 100, 0), 100)}%`,
                    }}
                />
            </div>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const style =
        status === "Active"
            ? "border-cyan-400/20 bg-[#00e0c6]/10 text-sky-700"
            : status === "Eliminated"
                ? "border-red-400/20 bg-red-500/10 text-red-700"
                : "border-slate-500/20 bg-slate-500/10 text-slate-700";

    return (
        <span className={`rounded-full border px-3 py-1 text-xs font-medium ${style}`}>
            {status}
        </span>
    );
}

function toPercent(value: number | undefined) {
    return `${((value ?? 0) * 100).toFixed(1)}%`;
}