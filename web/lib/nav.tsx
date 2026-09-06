import {
  LayoutDashboard,
  ScanSearch,
  Trophy,
  Users,
  Briefcase,
  History,
  GitCompareArrows,
  Gauge,
  Settings,
} from "lucide-react";

export interface NavEntry {
  href: string;
  label: string;
  icon: React.ReactNode;
  section: "Evaluate" | "Records" | "Intelligence" | "System";
  ready?: boolean; // built in this pass
}

export const NAV: NavEntry[] = [
  { href: "/overview", label: "Overview", icon: <LayoutDashboard className="h-4.5 w-4.5" />, section: "Evaluate", ready: true },
  { href: "/analysis", label: "Candidate Analysis", icon: <ScanSearch className="h-4.5 w-4.5" />, section: "Evaluate", ready: true },
  { href: "/leaderboard", label: "Talent Leaderboard", icon: <Trophy className="h-4.5 w-4.5" />, section: "Evaluate", ready: true },
  { href: "/candidates", label: "Candidate History", icon: <Users className="h-4.5 w-4.5" />, section: "Records", ready: true },
  { href: "/jobs", label: "Job Offers", icon: <Briefcase className="h-4.5 w-4.5" />, section: "Records", ready: true },
  { href: "/history", label: "Analysis History", icon: <History className="h-4.5 w-4.5" />, section: "Records", ready: true },
  { href: "/insights", label: "AI Insights", icon: <GitCompareArrows className="h-4.5 w-4.5" />, section: "Intelligence", ready: true },
  { href: "/quality", label: "AI Quality Center", icon: <Gauge className="h-4.5 w-4.5" />, section: "Intelligence", ready: true },
  { href: "/settings", label: "Settings", icon: <Settings className="h-4.5 w-4.5" />, section: "System", ready: true },
];

export const NAV_SECTIONS = ["Evaluate", "Records", "Intelligence", "System"] as const;
