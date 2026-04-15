import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  errorMessage: string
  reloadLabel: string
}

interface State {
  hasError: boolean
}

export class ChunkErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error) {
    console.error('ChunkErrorBoundary caught error:', error)
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <div className="mx-6 my-6 p-6 bg-red-900/30 rounded-lg border border-red-700/50">
        <div className="flex items-center gap-3 mb-4">
          <svg className="w-6 h-6 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="text-red-300 text-sm">{this.props.errorMessage}</span>
        </div>
        <button
          onClick={this.handleReload}
          className="px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
        >
          {this.props.reloadLabel}
        </button>
      </div>
    )
  }
}
