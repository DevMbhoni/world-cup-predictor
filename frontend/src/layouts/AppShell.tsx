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
    return (
        <main className="min-h-screen text-slate-950">
            <header className="bg-[#081426] text-white shadow-sm">
                <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-7">
                    <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.45em] text-sky-300">
                                World Cup Predictor
                            </p>

                            <h1 className="mt-3 max-w-3xl text-3xl font-semibold tracking-tight text-white md:text-5xl">
                                Match predictions, tournament paths, and Golden Boot intelligence.
                            </h1>

                            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-700 md:text-base">
                                A machine learning dashboard for 2026 World Cup outcomes,
                                scorelines, market probabilities, simulations, and player awards.
                            </p>
                        </div>

                        <div className="flex w-fit items-center gap-3 rounded-2xl border border-sky-300/25 bg-sky-400/10 px-4 py-3 text-sm text-sky-100">
                            <Activity size={18} className="text-sky-300" />
                            <span>FastAPI connected</span>
                        </div>
                    </div>

                    <nav className="flex gap-2 overflow-x-auto rounded-3xl border border-slate-200 bg-white/8 p-2">
                        {navigationItems.map((item) => {
                            const isActive = activePage === item.key;

                            return (
                                <button
                                    key={item.key}
                                    type="button"
                                    onClick={() => onPageChange(item.key)}
                                    className={`flex shrink-0 items-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition ${isActive
                                            ? "bg-sky-400 text-slate-950 shadow-sm"
                                            : "text-slate-200 hover:bg-white/10 hover:text-white"
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

            <section className="mx-auto max-w-7xl px-5 py-8">{children}</section>

            <Footer />
        </main>
    );
}

function Footer() {
    const year = new Date().getFullYear();

    return (
        <footer className="mt-12 border-t border-slate-200 bg-white">
            <div className="mx-auto max-w-7xl px-5 py-10">
                <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr_0.8fr]">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sky-600">
                            About the developer
                        </p>

                        <h2 className="mt-3 text-2xl font-semibold text-slate-950">
                            Mbhoni Shipalana
                        </h2>

                        <p className="mt-2 text-sm font-medium text-slate-700">
                            Graduate Software Engineer and Data Analyst
                        </p>

                        <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600">
                            BSc Computer Science and Statistics graduate from Nelson Mandela
                            University. This project demonstrates full-stack software
                            engineering, machine learning, data processing, API development,
                            and frontend dashboard design.
                        </p>

                        <div className="mt-5 flex flex-wrap gap-3">
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
                        <h3 className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">
                            Project stack
                        </h3>

                        <div className="mt-4 space-y-3 text-sm text-slate-600">
                            <InfoRow icon={<Code2 size={17} />} text="React, TypeScript, Tailwind CSS" />
                            <InfoRow icon={<Database size={17} />} text="Python, FastAPI, Scikit-learn" />
                            <InfoRow icon={<BarChart3 size={17} />} text="Elo, classifier, Poisson, simulation models" />
                            <InfoRow icon={<Trophy size={17} />} text="World Cup match and tournament analytics" />
                        </div>
                    </div>

                    <div>
                        <h3 className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">
                            Education
                        </h3>

                        <div className="mt-4 rounded-3xl border border-slate-200 bg-slate-50 p-5">
                            <div className="flex items-center gap-3 text-sky-700">
                                <GraduationCap size={20} />
                                <p className="font-semibold">Nelson Mandela University</p>
                            </div>

                            <p className="mt-3 text-sm leading-6 text-slate-600">
                                BSc Computer Science and Statistics. Former Student Assistant
                                supporting C#, Java, Data Structures, and Computing Fundamentals.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="mt-8 flex flex-col justify-between gap-3 border-t border-slate-200 pt-6 text-sm text-slate-500 md:flex-row">
                    <p>© {year} Mbhoni Shipalana. All rights reserved.</p>
                    <p>Built as a portfolio machine learning and software engineering project.</p>
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
            className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-sky-300 hover:bg-sky-50 hover:text-sky-700"
        >
            {icon}
            {label}
        </a>
    );
}

function InfoRow({ icon, text }: { icon: React.ReactNode; text: string }) {
    return (
        <div className="flex items-start gap-3">
            <div className="mt-0.5 text-sky-600">{icon}</div>
            <p>{text}</p>
        </div>
    );
}