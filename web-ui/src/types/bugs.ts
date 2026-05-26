// Bug Tracker Types

export type BugStatus = 'open' | 'in_progress' | 'resolved' | 'closed' | 'wont_fix';
export type Priority = 'low' | 'medium' | 'high' | 'critical';

export interface Bug {
  id: string;
  title: string;
  description: string;
  status: BugStatus;
  priority: Priority;
  module: string;
  subModule?: string;
  reportedBy: string;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
  steps?: string[];
  expectedBehavior?: string;
  actualBehavior?: string;
  screenshot?: string;
}

export interface BugFilter {
  status?: BugStatus[];
  priority?: Priority[];
  module?: string;
  assignedTo?: string;
  search?: string;
}
