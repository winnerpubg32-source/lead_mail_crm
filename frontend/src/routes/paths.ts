/** Canonical route paths — imported by the router, sidebar and links. */
export const paths = {
  dashboard: '/dashboard',
  leads: '/leads',
  companies: '/companies',
  contacts: '/contacts',
  imports: '/imports',
  campaigns: '/campaigns',
  email: '/email',
  followUps: '/follow-ups',
  crm: '/crm',
  analytics: '/analytics',
  templates: '/templates',
  ai: '/ai',
  suppression: '/suppression',
  settings: '/settings',
} as const;

export type AppPath = (typeof paths)[keyof typeof paths];
