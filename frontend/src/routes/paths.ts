/** Canonical route paths — imported by the router, sidebar and links. */
export const paths = {
  dashboard: '/dashboard',
  leads: '/leads',
  leadDetail: '/leads/:id',
  companies: '/companies',
  contacts: '/contacts',
  imports: '/imports',
  importsHistory: '/imports/history',
  dataQuality: '/data-quality',
  duplicates: '/duplicates',
  missingEmail: '/missing-email',
  campaigns: '/campaigns',
  campaignDetail: '/campaigns/:id',
  templates: '/templates',
  email: '/email',
  followUps: '/follow-ups',
  crm: '/crm',
  analytics: '/analytics',
  ai: '/ai',
  suppression: '/suppression',
  settings: '/settings',
} as const;

export type AppPath = (typeof paths)[keyof typeof paths];
