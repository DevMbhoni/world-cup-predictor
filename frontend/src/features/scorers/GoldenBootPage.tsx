import { useQuery } from "@tanstack/react-query";
import { Award, Crown, Target, TrendingUp } from "lucide-react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { getGoldenBootSimulation } from "../../api/scorers";
import type { GoldenBootPlayer } from "../../types/api";

export default function GoldenBootPage() {
    const goldenBootQuery = useQuery({
        queryKey: ["golden-boot-simulation"],
        queryFn: () => getGoldenBootSimulation(30),
    });

    const players = goldenBootQuery.data?.results ?? [];
    const topPlayers = players.slice(0, 10);
    const leader = players[0];

    if (goldenBootQuery.isLoading) {
        return <PageState title="Golden Boot" message="Loading Golden Boot simulation..." />;
    }

    if (goldenBootQuery.isError) {
        return (
            <PageState
                title="Golden Boot"
                message="Could not load Golden Boot simulation. Check that the FastAPI service is running."
            />
        );
    }

    return (
        <div className="space-y-6">
            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sky-600">
                            Golden Boot
                        </p>
                        <h2 className="mt-3 text-3xl font-semibold text-slate-950">
                            Top scorer simulation
                        </h2>
                        <p className="mt-3 max-w-3xl text-slate-600">
                            The model starts with current tournament goals, simulates the remaining
                            bracket, allocates future goals to likely scorers, and counts who finishes top.
                        </p>
                    </div>

                    {leader && (
                        <div className="rounded-3xl border border-amber-400/20 bg-amber-400/10 px-5 py-4">
                            <p className="text-sm text-amber-700">Current favourite</p>
                            <p className="mt-1 text-2xl font-semibold text-slate-950">
                                {leader.player_name}
                            </p>
                            <p className="mt-1 text-sm text-slate-700">
                                {leader.team_name} · {toPercent(leader.golden_boot_probability)}
                            </p>
                        </div>
                    )}
                </div>
            </section>

            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                    <div className="flex items-center gap-3">
                        <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-3 text-amber-600">
                            <Crown size={22} />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold text-slate-950">
                                Golden Boot probabilities
                            </h3>
                            <p className="text-sm text-slate-600">
                                Top 10 players by simulated Golden Boot chance.
                            </p>
                        </div>
                    </div>

                    <div className="mt-6 h-[380px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={topPlayers}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                                <XAxis
                                    dataKey="player_name"
                                    stroke="#94a3b8"
                                    tick={{ fontSize: 11 }}
                                    interval={0}
                                    angle={-25}
                                    textAnchor="end"
                                    height={95}
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
                                        color: "#fff",
                                    }}
                                    formatter={(value) => [
                                        toPercent(Number(value)),
                                        "Golden Boot probability",
                                    ]}
                                    labelFormatter={(label) => String(label)}
                                />
                                <Bar
                                    dataKey="golden_boot_probability"
                                    radius={[10, 10, 0, 0]}
                                    fill="#f59e0b"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>

                <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                    <div className="flex items-center gap-3">
                        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3 text-sky-600">
                            <Award size={22} />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold text-slate-950">Race leaders</h3>
                            <p className="text-sm text-slate-600">
                                Current goals and expected final totals.
                            </p>
                        </div>
                    </div>

                    <div className="mt-6 space-y-3">
                        {topPlayers.slice(0, 7).map((player, index) => (
                            <LeaderCard key={player.player_id} player={player} rank={index + 1} />
                        ))}
                    </div>
                </section>
            </div>

            <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-2xl shadow-black/20">
                <div className="flex items-center gap-3">
                    <div className="rounded-2xl border border-blue-500/20 bg-blue-500/10 p-3 text-blue-600">
                        <Target size={22} />
                    </div>
                    <div>
                        <h3 className="text-xl font-semibold text-slate-950">
                            Golden Boot simulation table
                        </h3>
                        <p className="text-sm text-slate-600">
                            Player-level probabilities from the Monte Carlo scorer simulation.
                        </p>
                    </div>
                </div>

                <div className="mt-6 overflow-x-auto">
                    <table className="w-full min-w-[980px] border-separate border-spacing-y-2">
                        <thead>
                            <tr className="text-left text-xs uppercase tracking-[0.2em] text-slate-500">
                                <th className="px-4 py-3">Player</th>
                                <th className="px-4 py-3">Team</th>
                                <th className="px-4 py-3">Position</th>
                                <th className="px-4 py-3">Current goals</th>
                                <th className="px-4 py-3">Expected goals</th>
                                <th className="px-4 py-3">Golden Boot</th>
                                <th className="px-4 py-3">Top 3</th>
                                <th className="px-4 py-3">Minutes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {players.map((player) => (
                                <tr key={player.player_id} className="bg-slate-50">
                                    <td className="rounded-l-2xl px-4 py-4 font-medium text-slate-950">
                                        {player.player_name}
                                    </td>
                                    <td className="px-4 py-4 text-slate-700">{player.team_name}</td>
                                    <td className="px-4 py-4 text-slate-700">{player.position}</td>
                                    <td className="px-4 py-4 text-slate-700">{player.current_goals}</td>
                                    <td className="px-4 py-4 text-slate-700">
                                        {player.expected_final_goals.toFixed(2)}
                                    </td>
                                    <td className="px-4 py-4 text-amber-600">
                                        {toPercent(player.golden_boot_probability)}
                                    </td>
                                    <td className="px-4 py-4 text-sky-600">
                                        {toPercent(player.top_3_probability)}
                                    </td>
                                    <td className="rounded-r-2xl px-4 py-4 text-slate-700">
                                        {player.minutes_played}
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

function LeaderCard({
    player,
    rank,
}: {
    player: GoldenBootPlayer;
    rank: number;
}) {
    return (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <p className="text-sm text-slate-500">Rank {rank}</p>
                    <p className="mt-1 font-semibold text-slate-950">{player.player_name}</p>
                    <p className="mt-1 text-sm text-slate-600">
                        {player.team_name} · {player.current_goals} current goals
                    </p>
                </div>
                <p className="text-xl font-semibold text-amber-600">
                    {toPercent(player.golden_boot_probability)}
                </p>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-slate-50 p-3">
                    <p className="text-slate-500">Expected final</p>
                    <p className="mt-1 font-semibold text-slate-950">
                        {player.expected_final_goals.toFixed(2)}
                    </p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                    <p className="text-slate-500">Top 3 chance</p>
                    <p className="mt-1 font-semibold text-sky-600">
                        {toPercent(player.top_3_probability)}
                    </p>
                </div>
            </div>
        </div>
    );
}

function toPercent(value: number | undefined) {
    return `${((value ?? 0) * 100).toFixed(1)}%`;
}