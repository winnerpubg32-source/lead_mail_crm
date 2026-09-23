import { Component, type ErrorInfo, type ReactNode } from 'react';

import { ErrorState } from '@/components/feedback/ErrorState';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Rendered instead of the default panel (optional). */
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Catches render-time errors so one broken panel cannot blank the whole
 * dashboard. Wrap individual dashboard sections with it.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[OutreachOS] Unhandled UI error:', error, info.componentStack);
  }

  private readonly reset = (): void => this.setState({ error: null });

  override render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    if (this.props.fallback) return this.props.fallback(error, this.reset);

    return (
      <ErrorState
        title="This section failed to render"
        description="The rest of the dashboard is unaffected. Reload the section to try again."
        details={error.message}
        onRetry={this.reset}
      />
    );
  }
}
