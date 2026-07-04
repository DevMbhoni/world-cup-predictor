import { useQuery } from "@tanstack/react-query";
import {
    Activity,
    BarChart3,
    Code2,
    Database,
    ExternalLink,
    GitBranch,
    GraduationCap,
    LayoutDashboard,
    Mail,
    Search,
    Trophy,
} from "lucide-react";
import { getApiHealth } from "../api/health";

type AppShellProps = {
    activePage: PageKey;
    onPageChange: (page: PageKey) => void;
    children: React.ReactNode;
};

export type PageKey =
    | "dashboard"
    | "predictor"
    | "tournament"
    | "bracket"
    | "golden-boot"
    | "rankings";

const navigationItems: {
    key: PageKey;
    label: string;
    icon: React.ReactNode;
}[] = [
        {
            key: "dashboard",
            label: "Dashboard",
            icon: <LayoutDashboard size={18} />,
        },
        {
            key: "predictor",
            label: "Predictor",
            icon: <Search size={18} />,
        },
        {
            key: "tournament",
            label: "Tournament",
            icon: <Trophy size={18} />,
        },
        {
            key: "bracket",
            label: "Bracket",
            icon: <GitBranch size={18} />,
        },
        {
            key: "golden-boot",
            label: "Golden Boot",
            icon: <Activity size={18} />,
        },
        {
            key: "rankings",
            label: "Rankings",
            icon: <BarChart3 size={18} />,
        },
    ];

export default function AppShell({
    activePage,
    onPageChange,
    children,
}: AppShellProps) {
    const healthQuery = useQuery({
        queryKey: ["api-health"],
        queryFn: getApiHealth,
        refetchInterval: 30000,
        retry: 1,
    });

    const apiOnline = healthQuery.isSuccess;

    return (
        <main className="min-h-screen text-slate-950">
            <header className="border-b border-black bg-black text-white">
                <div className="fwc-pattern h-2 w-full" />

                <div className="mx-auto flex max-w-7xl flex-col gap-7 px-5 py-8">
                    <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.48em] text-[#00e0c6]">
                                World Cup Predictor
                            </p>

                            <h1 className="mt-4 max-w-4xl text-3xl font-black tracking-tight text-white md:text-6xl">
                                Predict the match.
                                <br />
                                Simulate the tournament.
                            </h1>

                            <p className="mt-5 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">
                                Machine learning intelligence for match outcomes, scorelines,
                                knockout paths, team strength, and the Golden Boot race.
                            </p>
                        </div>

                        <div
                            className={`flex w-fit items-center gap-3 rounded-full border px-5 py-3 text-sm font-semibold ${apiOnline
                                    ? "border-[#00e0c6] bg-[#00e0c6] text-black"
                                    : "border-[#ff2a1a] bg-[#ff2a1a] text-white"
                                }`}
                        >
                            <Activity size={18} />
                            <span>{apiOnline ? "API connected" : "API offline"}</span>
                        </div>
                    </div>

                    <nav className="flex gap-2 overflow-x-auto rounded-3xl border border-white/15 bg-white/5 p-2">
                        {navigationItems.map((item) => {
                            const isActive = activePage === item.key;

                            return (
                                <button
                                    key={item.key}
                                    type="button"
                                    onClick={() => onPageChange(item.key)}
                                    className={`flex shrink-0 items-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition ${isActive
                                            ? "bg-[#2f54eb] text-white"
                                            : "text-slate-300 hover:bg-white/10 hover:text-white"
                                        }`}
                                >
                                    {item.icon}
                                    {item.label}
                                </button>
                            );
                        })}
                    </nav>
                </div>
            </header>

            <div className="fwc-pattern-soft h-20 w-full opacity-100" />

            <section className="mx-auto max-w-7xl px-5 py-10">{children}</section>

            <Footer />
        </main>
    );
}

function Footer() {
    const year = new Date().getFullYear();

    return (
        <footer className="mt-14 border-t-8 border-[#6a00ff] bg-black text-white">
            <div className="fwc-pattern h-2 w-full" />

            <div className="mx-auto max-w-7xl px-5 py-12">
                <div className="grid gap-10 lg:grid-cols-[1.3fr_0.8fr_0.8fr]">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.38em] text-[#00e0c6]">
                            About the developer
                        </p>

                        <h2 className="mt-4 text-3xl font-black text-white">
                            Mbhoni Shipalana
                        </h2>

                        <p className="mt-2 text-sm font-semibold text-[#bef20a]">
                            Graduate Software Engineer and Data Analyst
                        </p>

                        <p className="mt-5 max-w-2xl text-sm leading-7 text-slate-300">
                            BSc Computer Science and Statistics graduate from Nelson Mandela
                            University. This project combines software engineering, machine
                            learning, statistical modelling, API development, data processing,
                            and interactive frontend visualisation.
                        </p>

                        <div className="mt-6 flex flex-wrap gap-3">
                            <FooterLink
                                href="https://www.linkedin.com/in/mbhoni-shipalana-83b9b826b"
                                label="LinkedIn"
                            />

                            <FooterLink
                                href="https://github.com/DevMbhoni"
                                label="GitHub"
                            />

                            <FooterLink
                                href="mailto:shipalanambhoniii@gmail.com"
                                label="Email"
                                icon={<Mail size={17} />}
                            />

                            <FooterLink
                                href="https://student-success-predictor-beige.vercel.app"
                                label="Portfolio Project"
                                icon={<ExternalLink size={17} />}
                            />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-400">
                            Project stack
                        </h3>

                        <div className="mt-5 space-y-4 text-sm text-slate-300">
                            <InfoRow
                                icon={<Code2 size={17} />}
                                text="React, TypeScript, Tailwind CSS"
                            />

                            <InfoRow
                                icon={<Database size={17} />}
                                text="Python, FastAPI, Scikit-learn"
                            />

                            <InfoRow
                                icon={<BarChart3 size={17} />}
                                text="Elo, classifier, Poisson and Monte Carlo models"
                            />

                            <InfoRow
                                icon={<Trophy size={17} />}
                                text="World Cup match and tournament intelligence"
                            />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-400">
                            Education
                        </h3>

                        <div className="mt-5 rounded-3xl border border-white/15 bg-white/5 p-5">
                            <div className="flex items-center gap-3 text-[#00e0c6]">
                                <GraduationCap size={21} />
                                <p className="font-semibold">Nelson Mandela University</p>
                            </div>

                            <p className="mt-4 text-sm leading-7 text-slate-300">
                                BSc Computer Science and Statistics. Former Student Assistant
                                supporting C#, Java, Data Structures, and Computing Fundamentals.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="mt-10 flex flex-col justify-between gap-4 border-t border-white/15 pt-7 text-sm text-slate-400 md:flex-row">
                    <p>© {year} Mbhoni Shipalana. All rights reserved.</p>

                    <p>
                        Portfolio machine learning and software engineering project.
                    </p>
                </div>
            </div>
        </footer>
    );
}

function FooterLink({
    href,
    label,
    icon,
}: {
    href: string;
    label: string;
    icon?: React.ReactNode;
}) {
    return (
        <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-white transition hover:border-[#00e0c6] hover:bg-[#00e0c6] hover:text-black"
        >
            {icon}
            {label}
        </a>
    );
}

function InfoRow({
    icon,
    text,
}: {
    icon: React.ReactNode;
    text: string;
}) {
    return (
        <div className="flex items-start gap-3">
            <div className="mt-0.5 text-[#2f54eb]">{icon}</div>
            <p>{text}</p>
        </div>
    );
}