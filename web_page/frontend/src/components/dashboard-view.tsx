"use client";

import { useEffect, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Play,
  Plus,
  RefreshCw,
  X,
  Loader2,
  ChevronRight,
  Clock,
  CheckCircle2,
  XCircle,
  Activity,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  ResponsiveContainer,
  Cell,
  Tooltip as RechartsTooltip,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppSidebar } from "@/components/app-sidebar";
import { ReportsTable } from "@/components/reports-table";

/* ─── Types ─────────────────────────────────────────────────────────────── */
interface Stats {
  total: number;
  passed: number;
  failed: number;
  running: number;
  avg_duration: number;
  pass_rate: number;
}
interface TestRun {
  id: number;
  test_type: string;
  status: string;
  duration_seconds: number | null;
  started_at: string;
  finished_at: string | null;
}
interface Report {
  filename: string;
  size: number;
  modified: number;
  type: string;
}
interface DashboardViewProps {
  onSignOut: () => void;
}

/* ─── Helpers ────────────────────────────────────────────────────────────── */
function fmtDur(s: number | null) {
  if (!s) return "—";
  const m = Math.floor(s / 60);
  const sec = Math.round(s % 60);
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
}
function fmtDate(d: string) {
  return new Date(d).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

/* Status helpers */
const statusConfig: Record<string, { label: string; dot: string; badge: string }> = {
  PASSED:  { label: "Passed",  dot: "bg-emerald-500", badge: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800" },
  FAILED:  { label: "Failed",  dot: "bg-red-500",     badge: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-800" },
  RUNNING: { label: "Running", dot: "bg-blue-500 animate-pulse", badge: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400 dark:border-blue-800" },
};

/* ─── Placeholder chart data ─────────────────────────────────────────────── */
const WEEK_DATA = [
  { day: "Mon", passed: 8,  failed: 1 },
  { day: "Tue", passed: 12, failed: 0 },
  { day: "Wed", passed: 7,  failed: 3 },
  { day: "Thu", passed: 15, failed: 1 },
  { day: "Fri", passed: 10, failed: 2 },
  { day: "Sat", passed: 5,  failed: 0 },
  { day: "Sun", passed: 9,  failed: 1 },
];

/* ─── Sub-components ─────────────────────────────────────────────────────── */

function StatCard({
  label,
  value,
  delta,
  direction,
  icon: Icon,
}: {
  label: string;
  value: string;
  delta: string;
  direction: "up" | "down" | "neutral";
  icon: React.ElementType;
}) {
  const DeltaIcon =
    direction === "up" ? TrendingUp : direction === "down" ? TrendingDown : Minus;
  const deltaColor =
    direction === "up"
      ? "text-emerald-600 dark:text-emerald-400"
      : direction === "down"
      ? "text-red-600 dark:text-red-400"
      : "text-muted-foreground";

  return (
    <div className="rounded-lg border border-border bg-card p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <div className="size-7 rounded-md bg-muted flex items-center justify-center">
          <Icon className="size-3.5 text-muted-foreground" />
        </div>
      </div>
      <div>
        <p className="text-2xl font-semibold text-foreground tracking-tight">{value}</p>
        <div className={`flex items-center gap-1 mt-1 text-xs ${deltaColor}`}>
          <DeltaIcon className="size-3" />
          <span>{delta}</span>
        </div>
      </div>
    </div>
  );
}

/* Custom bar chart tooltip */
function ChartTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card shadow-sm px-3 py-2 text-xs">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 text-muted-foreground">
          <span
            className="inline-block size-1.5 rounded-full"
            style={{ background: p.color }}
          />
          {p.name}: <span className="text-foreground font-medium">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

/* Run modal */
function RunModal({
  selectedTest,
  companyCount,
  setCompanyCount,
  loading,
  onRun,
  onClose,
}: {
  selectedTest: string;
  companyCount: number;
  setCompanyCount: (n: number) => void;
  loading: boolean;
  onRun: () => void;
  onClose: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black/40 backdrop-blur-[2px] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.97, opacity: 0, y: 4 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.97, opacity: 0, y: 4 }}
        transition={{ duration: 0.15 }}
        className="w-full max-w-sm rounded-xl border border-border bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-border">
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              Run {selectedTest.charAt(0).toUpperCase() + selectedTest.slice(1)} Test
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Company Onboarding module
            </p>
          </div>
          <button
            onClick={onClose}
            className="size-6 rounded-md flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          >
            <X className="size-3.5" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {selectedTest === "creation" && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">
                Number of companies
              </label>
              <select
                value={companyCount}
                onChange={(e) => setCompanyCount(Number(e.target.value))}
                className="w-full h-8 text-xs rounded-md border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {[1, 2, 3, 5, 10, 20].map((n) => (
                  <option key={n} value={n}>
                    {n} {n === 1 ? "company" : "companies"}
                  </option>
                ))}
              </select>
            </div>
          )}
          <p className="text-xs text-muted-foreground">
            The test runs in the background. Results appear in the run history below.
          </p>
        </div>

        <div className="flex items-center justify-end gap-2 px-5 pb-5">
          <Button variant="outline" size="sm" className="text-xs h-7" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" className="text-xs h-7" onClick={onRun} disabled={loading}>
            {loading ? (
              <Loader2 className="size-3 animate-spin mr-1" />
            ) : (
              <Play className="size-3 mr-1" />
            )}
            {loading ? "Starting…" : "Start test"}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ─── Main dashboard ─────────────────────────────────────────────────────── */
export function DashboardView({ onSignOut }: DashboardViewProps) {
  const [stats, setStats] = useState<Stats>({
    total: 0, passed: 0, failed: 0, running: 0, avg_duration: 0, pass_rate: 0,
  });
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedTest, setSelectedTest] = useState("creation");
  const [companyCount, setCompanyCount] = useState(1);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [s, r, rp] = await Promise.all([
        fetch("/api/stats"),
        fetch("/api/runs"),
        fetch("/api/reports"),
      ]);
      setStats(await s.json());
      setRuns(await r.json());
      setReports(await rp.json());
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("pacs_user");
    if (!stored) { onSignOut(); return; }
    loadData();
    const iv = setInterval(loadData, 5000);
    return () => clearInterval(iv);
  }, [loadData, onSignOut]);

  async function handleRun() {
    setLoading(true);
    setShowModal(false);
    try {
      const res = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ testType: selectedTest, companyCount }),
      });
      const data = await res.json();
      if (data.success) {
        toast.success(data.message);
        setTimeout(loadData, 2000);
      } else {
        toast.error(data.error || "Failed to start test");
      }
    } catch {
      toast.error("Failed to start test");
    } finally {
      setLoading(false);
    }
  }

  function openModal(type: string) {
    setSelectedTest(type);
    setShowModal(true);
  }

  const statCards = [
    {
      label: "Total runs",
      value: String(stats.total),
      delta: `${stats.running} running now`,
      direction: "neutral" as const,
      icon: Activity,
    },
    {
      label: "Pass rate",
      value: `${stats.pass_rate}%`,
      delta: `${stats.passed} passed`,
      direction: "up" as const,
      icon: CheckCircle2,
    },
    {
      label: "Failed",
      value: String(stats.failed),
      delta: stats.failed > 0 ? "Needs attention" : "All clear",
      direction: stats.failed > 0 ? ("down" as const) : ("neutral" as const),
      icon: XCircle,
    },
    {
      label: "Avg duration",
      value: fmtDur(stats.avg_duration),
      delta: "per test run",
      direction: "neutral" as const,
      icon: Clock,
    },
  ];

  return (
    <TooltipProvider>
      <SidebarProvider>
        <div className="flex min-h-screen w-full bg-background">
          <AppSidebar onSignOut={onSignOut} />

          <div className="flex-1 flex flex-col min-w-0">
            {/* Top bar */}
            <header className="sticky top-0 z-30 h-12 flex items-center gap-3 border-b border-border bg-background/95 backdrop-blur px-4">
              <SidebarTrigger className="size-7 text-muted-foreground hover:text-foreground" />
              <div className="h-4 w-px bg-border" />
              <div className="flex items-center gap-1.5 text-sm">
                <span className="text-muted-foreground">Dashboard</span>
                <ChevronRight className="size-3 text-muted-foreground/50" />
                <span className="text-foreground font-medium">Company Onboarding</span>
              </div>

              <div className="ml-auto flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1.5"
                  onClick={loadData}
                >
                  <RefreshCw className="size-3" />
                  Refresh
                </Button>
                <Button
                  size="sm"
                  className="h-7 text-xs gap-1.5"
                  onClick={() => openModal("creation")}
                >
                  <Plus className="size-3" />
                  New run
                </Button>
              </div>
            </header>

            {/* Page content */}
            <main className="flex-1 p-5 space-y-5">
              {/* Stat cards */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-2 lg:grid-cols-4 gap-3"
              >
                {statCards.map((c) => (
                  <StatCard key={c.label} {...c} />
                ))}
              </motion.div>

              {/* Charts + quick actions row */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.08 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-3"
              >
                {/* Bar chart — spans 2 cols */}
                <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm font-medium text-foreground">Runs this week</p>
                      <p className="text-xs text-muted-foreground mt-0.5">Pass / fail by day</p>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1.5">
                        <span className="size-2 rounded-sm bg-emerald-500/70 inline-block" />
                        Passed
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="size-2 rounded-sm bg-red-400/70 inline-block" />
                        Failed
                      </span>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={120}>
                    <BarChart data={WEEK_DATA} barSize={8} barGap={2} barCategoryGap="30%">
                      <XAxis
                        dataKey="day"
                        tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <RechartsTooltip content={<ChartTooltip />} cursor={false} />
                      <Bar dataKey="passed" name="Passed" stackId="a" radius={[0, 0, 0, 0]}>
                        {WEEK_DATA.map((_, i) => (
                          <Cell key={i} fill="rgb(52 211 153 / 0.7)" />
                        ))}
                      </Bar>
                      <Bar dataKey="failed" name="Failed" stackId="a" radius={[3, 3, 0, 0]}>
                        {WEEK_DATA.map((_, i) => (
                          <Cell key={i} fill="rgb(248 113 113 / 0.7)" />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Quick actions panel */}
                <div className="rounded-lg border border-border bg-card p-4 flex flex-col">
                  <p className="text-sm font-medium text-foreground mb-1">Quick actions</p>
                  <p className="text-xs text-muted-foreground mb-4">Launch a test run</p>
                  <div className="flex flex-col gap-2 flex-1">
                    {[
                      { label: "Creation test", sub: "Create new company records", type: "creation", icon: Plus },
                      { label: "Update test", sub: "Update existing data", type: "update", icon: RefreshCw },
                      { label: "Full suite", sub: "End-to-end run", type: "full", icon: Play },
                    ].map((a) => (
                      <button
                        key={a.type}
                        onClick={() => openModal(a.type)}
                        className="flex items-center gap-3 rounded-md border border-border bg-background hover:bg-accent/60 px-3 py-2.5 text-left transition-colors group"
                      >
                        <div className="size-6 rounded-md bg-muted flex items-center justify-center flex-shrink-0">
                          <a.icon className="size-3 text-muted-foreground group-hover:text-foreground transition-colors" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-foreground leading-none">{a.label}</p>
                          <p className="text-[10px] text-muted-foreground mt-0.5 leading-none">{a.sub}</p>
                        </div>
                        <ChevronRight className="size-3 text-muted-foreground ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Recent runs table */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.16 }}
                className="rounded-lg border border-border bg-card overflow-hidden"
              >
                <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                  <div>
                    <p className="text-sm font-medium text-foreground">Recent runs</p>
                    <p className="text-xs text-muted-foreground mt-0.5">Latest test results</p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border">
                        {["ID", "Type", "Status", "Duration", "Started"].map((h) => (
                          <th
                            key={h}
                            className="text-left px-4 py-2.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wider whitespace-nowrap"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {runs.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground text-xs">
                            No runs yet — click <strong>New run</strong> to get started.
                          </td>
                        </tr>
                      ) : (
                        runs.slice(0, 10).map((r, i) => {
                          const sc = statusConfig[r.status] ?? statusConfig.RUNNING;
                          return (
                            <tr
                              key={r.id}
                              className="border-b border-border/50 last:border-0 hover:bg-muted/30 transition-colors"
                            >
                              <td className="px-4 py-2.5 font-mono text-muted-foreground">
                                #{r.id}
                              </td>
                              <td className="px-4 py-2.5 font-medium text-foreground capitalize">
                                {r.test_type}
                              </td>
                              <td className="px-4 py-2.5">
                                <span
                                  className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border text-[10px] font-medium ${sc.badge}`}
                                >
                                  <span className={`size-1.5 rounded-full ${sc.dot}`} />
                                  {sc.label}
                                </span>
                              </td>
                              <td className="px-4 py-2.5 font-mono text-muted-foreground">
                                {fmtDur(r.duration_seconds)}
                              </td>
                              <td className="px-4 py-2.5 text-muted-foreground">
                                {fmtDate(r.started_at)}
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </motion.div>

              {/* Reports */}
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.22 }}
              >
                <ReportsTable reports={reports} />
              </motion.div>
            </main>

            <footer className="border-t border-border py-3 px-5 text-[10px] text-muted-foreground/60 flex items-center gap-2">
              <span>PACS Automation Portal</span>
              <span>·</span>
              <span>v1.0</span>
              <span>·</span>
              <span>2026</span>
            </footer>
          </div>
        </div>

        <AnimatePresence>
          {showModal && (
            <RunModal
              selectedTest={selectedTest}
              companyCount={companyCount}
              setCompanyCount={setCompanyCount}
              loading={loading}
              onRun={handleRun}
              onClose={() => setShowModal(false)}
            />
          )}
        </AnimatePresence>
      </SidebarProvider>
    </TooltipProvider>
  );
}