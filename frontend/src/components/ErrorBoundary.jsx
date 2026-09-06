import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  handleRetry = () => {
    this.setState({ failed: false })
  }

  render() {
    if (!this.state.failed) return this.props.children
    return <main className="message-shell"><div className="message-card"><span className="message-icon">!</span><h1>Something went wrong.</h1><p>Please try again.</p><button className="primary-button" type="button" onClick={this.handleRetry}>Try again <span>↻</span></button></div></main>
  }
}
