import { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-xl font-semibold text-slate-800 mb-2">
              Something went wrong
            </h2>
            <p className="text-slate-500 mb-6">
              An unexpected error occurred. Please try refreshing the page.
            </p>
            <button
              onClick={this.handleReset}
              className="
                inline-flex items-center gap-2 px-6 py-3 rounded-xl
                bg-gradient-to-r from-indigo-500 to-violet-500
                text-white font-medium
                hover:from-indigo-600 hover:to-violet-600
                transition-all duration-200
              "
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
