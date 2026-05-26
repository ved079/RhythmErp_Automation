import type { TestSpecItem } from './dashboard';

export interface OperationsTabProps {
  testGroups: TestSpecItem[][];
  testCasesModule?: { label: string; tests: any[] };
}

export interface FilterState {
  searchVal: string;
  filter: 'all' | 'passed' | 'failed' | 'bug' | 'not-run';
}

export interface StatusDisplay {
  label: string;
  color: string;
  icon: string;
}
