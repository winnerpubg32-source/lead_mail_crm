import {
  AlertTriangle,
  BarChart3,
  Briefcase,
  Building2,
  CalendarClock,
  FileSpreadsheet,
  LayoutDashboard,
  LayoutTemplate,
  Mail,
  MailQuestion,
  Megaphone,
  Settings,
  ShieldBan,
  Sparkles,
  Target,
  Users,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  /** Route the sidebar links to (also the single source for breadcrumbs). */
  path: string;
  label: string;
  icon: LucideIcon;
  /** Short helper text used by the placeholder pages and the command hint. */
  description: string;
  /** "live" ships in Phase 1, "soon" is a placeholder module. */
  status: 'live' | 'soon';
  /** Optional counter/badge rendered on the right of the nav item. */
  badge?: string;
}

export interface NavSection {
  id: string;
  label?: string;
  items: NavItem[];
}

/**
 * Single source of truth for the sidebar, breadcrumbs and the route registry.
 * Adding a module in a later phase means adding one entry here.
 */
export const navigation: NavSection[] = [
  {
    id: 'overview',
    label: 'Overview',
    items: [
      {
        path: '/dashboard',
        label: 'Dashboard',
        icon: LayoutDashboard,
        description: 'Outreach performance, capacity and pipeline at a glance.',
        status: 'live',
      },
    ],
  },
  {
    id: 'lead-database',
    label: 'Lead database',
    items: [
      {
        path: '/leads',
        label: 'Leads',
        icon: Target,
        description: 'Qualified prospects, scores and outreach status.',
        status: 'live',
      },
      {
        path: '/companies',
        label: 'Companies',
        icon: Building2,
        description: 'Imported businesses with industry, city and state.',
        status: 'live',
      },
      {
        path: '/contacts',
        label: 'Contacts',
        icon: Users,
        description: 'Decision makers, e-mail addresses and phone numbers.',
        status: 'live',
      },
      {
        path: '/imports',
        label: 'Imports',
        icon: FileSpreadsheet,
        description: 'CSV and XLSX ingestion with automatic column mapping.',
        status: 'live',
      },
      {
        path: '/data-quality',
        label: 'Data quality',
        icon: AlertTriangle,
        description: 'Normalization, duplicate detection and data-health dashboard.',
        status: 'live',
      },
      {
        path: '/duplicates',
        label: 'Duplicate review',
        icon: ShieldBan,
        description: 'Review and merge potential duplicate leads.',
        status: 'live',
      },
      {
        path: '/missing-email',
        label: 'Missing e-mail',
        icon: MailQuestion,
        description: 'Leads without a deliverable e-mail address, awaiting enrichment.',
        status: 'live',
      },
    ],
  },
  {
    id: 'outreach',
    label: 'Outreach',
    items: [
      {
        path: '/campaigns',
        label: 'Campaigns',
        icon: Megaphone,
        description: 'Sequences, audiences and sending schedules.',
        status: 'soon',
      },
      {
        path: '/email',
        label: 'Email',
        icon: Mail,
        description: 'Mailboxes, SMTP delivery and the 90/day sending budget.',
        status: 'soon',
      },
      {
        path: '/follow-ups',
        label: 'Follow-ups',
        icon: CalendarClock,
        description: 'Automated follow-up steps and manual reminders.',
        status: 'soon',
      },
    ],
  },
  {
    id: 'revenue',
    label: 'Revenue',
    items: [
      {
        path: '/crm',
        label: 'CRM',
        icon: Briefcase,
        description: 'Deals, notes, tasks and the full activity timeline.',
        status: 'soon',
      },
      {
        path: '/analytics',
        label: 'Analytics',
        icon: BarChart3,
        description: 'Reply rates, meetings and pipeline reporting.',
        status: 'soon',
      },
    ],
  },
  {
    id: 'toolkit',
    label: 'Toolkit',
    items: [
      {
        path: '/templates',
        label: 'Templates',
        icon: LayoutTemplate,
        description: 'Reusable e-mail templates and step variants.',
        status: 'soon',
      },
      {
        path: '/ai',
        label: 'AI',
        icon: Sparkles,
        description: 'Personalisation prompts, models and qualification.',
        status: 'soon',
      },
      {
        path: '/suppression',
        label: 'Suppression',
        icon: ShieldBan,
        description: 'Do-not-contact list: unsubscribes and hard bounces.',
        status: 'soon',
      },
    ],
  },
  {
    id: 'workspace',
    label: 'Workspace',
    items: [
      {
        path: '/settings',
        label: 'Settings',
        icon: Settings,
        description: 'Workspace, sending limits, team and integrations.',
        status: 'soon',
      },
    ],
  },
];

/** Flattened lookup used by breadcrumbs and the router. */
export const navigationItems: NavItem[] = navigation.flatMap((section) => section.items);

export function findNavItem(pathname: string): NavItem | undefined {
  return navigationItems.find(
    (item) => pathname === item.path || pathname.startsWith(`${item.path}/`),
  );
}
