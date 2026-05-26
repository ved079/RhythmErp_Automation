'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  name?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`ErrorBoundary ${this.props.name || 'component'}:`, error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="p-6 rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/20 text-center">
          <h3 className="text-lg font-semibold text-red-800 dark:text-red-300">Something went wrong</h3>
          <p className="text-sm text-red-600 dark:text-red-400 mt-2">
            {this.props.name ? `${this.props.name} failed to load` : 'Component failed to load'}
          </p>
          <button
            onClick={this.handleReset}
            className="mt-4 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
