import { Component, type ReactNode, type ErrorInfo } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
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
    console.error("[ErrorBoundary]", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="mx-auto max-w-md text-center">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Something went wrong
            </h1>
            <p className="mt-3 text-gray-500 dark:text-gray-400">
              An unexpected error occurred. Please refresh the page and try
              again.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 rounded-lg bg-primary-600 px-6 py-2 text-white hover:bg-primary-700"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
