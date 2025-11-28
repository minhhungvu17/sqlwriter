import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';

@customElement('vanna-status-bar')
export class VannaStatusBar extends LitElement {
  static styles = [
    vannaDesignTokens,
    css`
      :host {
        display: block;
        /* Ready (default) – teal */
        background: rgba(21, 168, 168, 0.12);
        border: 2px solid var(--vanna-teal);
        border-radius: var(--vanna-border-radius-xl);
        padding: var(--vanna-space-2) var(--vanna-space-3);
        margin-bottom: var(--vanna-space-4);
        font-family: var(--vanna-font-family-default);
        font-size: 14px;
        font-weight: 500;
        color: var(--vanna-navy);
        backdrop-filter: blur(12px);
        box-shadow: var(--vanna-shadow-lg);
        
        /* Animation properties */
        opacity: 1;
        transform: translateY(0) scale(1);
        max-height: 200px;
        overflow: hidden;
        transition: 
          opacity var(--vanna-duration-300) cubic-bezier(0.4, 0, 0.2, 1),
          transform var(--vanna-duration-300) cubic-bezier(0.4, 0, 0.2, 1),
          max-height var(--vanna-duration-300) ease,
          margin var(--vanna-duration-300) ease,
          padding var(--vanna-duration-300) ease,
          box-shadow var(--vanna-duration-200) ease;
      }

      /* Hide when there's no actual content */
      :host(.no-content) {
        opacity: 0;
        transform: translateY(-8px) scale(0.95);
        max-height: 0;
        margin: 0;
        padding: 0;
        pointer-events: none;
      }

      :host(:empty) {
        display: none;
      }

      /* Entrance animation when content appears */
      :host(.entering) {
        animation: statusEnter var(--vanna-duration-300) ease-out;
      }

      /* Exit animation when content disappears */
      :host(.exiting) {
        animation: statusExit var(--vanna-duration-300) ease-in;
      }

      @keyframes statusEnter {
        0% {
          opacity: 0;
          transform: translateY(-12px) scale(0.9);
          max-height: 0;
        }
        50% {
          opacity: 0.8;
          transform: translateY(-2px) scale(1.02);
        }
        100% {
          opacity: 1;
          transform: translateY(0) scale(1);
          max-height: 200px;
        }
      }

      @keyframes statusExit {
        0% {
          opacity: 1;
          transform: translateY(0) scale(1);
          max-height: 200px;
        }
        50% {
          opacity: 0.5;
          transform: translateY(-4px) scale(0.98);
        }
        100% {
          opacity: 0;
          transform: translateY(-12px) scale(0.9);
          max-height: 0;
        }
      }

      /* Thinking – gray */
      :host([status="working"]) {
        background: #e5e7eb; /* Tailwind gray-200 equivalent */
        border-color: #9ca3af; /* gray-400 */
        color: #374151; /* gray-700 */
        box-shadow: var(--vanna-shadow-xl);
      }

      :host([status="error"]) {
        background: linear-gradient(135deg, var(--vanna-accent-negative-subtle) 0%, rgba(239, 68, 68, 0.15) 100%);
        border-color: var(--vanna-accent-negative-default);
        color: var(--vanna-accent-negative-stronger);
        box-shadow: 
          var(--vanna-shadow-xl),
          0 0 0 2px rgba(239, 68, 68, 0.3),
          0 0 20px rgba(239, 68, 68, 0.2);
        animation: errorShake 0.5s ease-in-out, errorGlow 2s ease-in-out;
      }

      /* Done/Success – teal */
      :host([status="success"]) {
        background: var(--vanna-teal);
        border-color: var(--vanna-teal);
        color: white;
        box-shadow: var(--vanna-shadow-xl);
        animation: successPulse 0.6s ease-out;
      }

      @keyframes errorShake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
        20%, 40%, 60%, 80% { transform: translateX(4px); }
      }

      @keyframes successPulse {
        0% { 
          transform: scale(1); 
        }
        50% { 
          transform: scale(1.05); 
        }
        100% { 
          transform: scale(1); 
        }
      }

      .status-content {
        display: flex;
        align-items: center;
        gap: var(--vanna-space-3);
        animation: contentFadeIn var(--vanna-duration-200) ease-out;
      }

      @keyframes contentFadeIn {
        0% {
          opacity: 0;
          transform: translateY(4px);
        }
        100% {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: var(--vanna-border-radius-full);
        background: var(--vanna-accent-primary-default);
        flex-shrink: 0;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5), 0 2px 8px rgba(0, 0, 0, 0.15);
      }

      .status-indicator.working {
        background: white;
        animation: workingPulse 1.5s ease-in-out infinite;
      }

      .status-indicator.error {
        background: linear-gradient(45deg, var(--vanna-accent-negative-default), var(--vanna-accent-negative-stronger));
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5), 0 0 8px rgba(239, 68, 68, 0.4);
      }

      .status-indicator.success {
        background: linear-gradient(45deg, var(--vanna-accent-positive-default), var(--vanna-accent-positive-stronger));
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5), 0 0 8px rgba(16, 185, 129, 0.4);
      }

      .spinner {
        width: 16px;
        height: 16px;
        border: 3px solid rgba(107, 114, 128, 0.3); /* gray */
        border-top-color: #6b7280; /* gray-500 */
        border-radius: var(--vanna-border-radius-full);
        animation: spin 1s linear infinite, spinnerGlow 2s ease-in-out infinite;
        flex-shrink: 0;
      }

      .status-text {
        flex: 1;
        font-weight: 600;
        line-height: 1.4;
        letter-spacing: 0.01em;
      }

      .status-detail {
        display: none; /* Hide detail text on the right */
      }

      .status-actions {
        display: flex;
        align-items: center;
        gap: var(--vanna-space-2);
        margin-left: auto;
      }

      .status-button {
        padding: var(--vanna-space-1) var(--vanna-space-2);
        border: 1px solid var(--vanna-outline-default);
        border-radius: var(--vanna-border-radius-sm);
        background: var(--vanna-background-subtle);
        color: var(--vanna-foreground-dimmer);
        font-size: 11px;
        font-weight: 500;
        cursor: pointer;
        transition: all var(--vanna-duration-150) ease;
      }

      .status-button:hover {
        background: var(--vanna-background-higher);
        border-color: var(--vanna-outline-hover);
        color: var(--vanna-foreground-default);
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      @keyframes pulse {
        0%, 100% {
          opacity: 1;
          transform: scale(1);
        }
        50% {
          opacity: 0.6;
          transform: scale(1.1);
        }
      }

      @keyframes workingPulse {
        0%, 100% {
          opacity: 1;
          transform: scale(1);
          box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8), 0 2px 8px rgba(255, 255, 255, 0.3);
        }
        50% {
          opacity: 0.9;
          transform: scale(1.2);
          box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.9), 0 4px 12px rgba(255, 255, 255, 0.5);
        }
      }

      @keyframes spinnerGlow {
        0%, 100% {
          filter: drop-shadow(0 0 2px rgba(107, 114, 128, 0.5));
        }
        50% {
          filter: drop-shadow(0 0 6px rgba(107, 114, 128, 0.8));
        }
      }

      @keyframes errorGlow {
        0% {
          box-shadow: 
            var(--vanna-shadow-xl),
            0 0 0 2px rgba(239, 68, 68, 0.3),
            0 0 20px rgba(239, 68, 68, 0.2);
        }
        50% {
          box-shadow: 
            var(--vanna-shadow-2xl),
            0 0 0 3px rgba(239, 68, 68, 0.4),
            0 0 30px rgba(239, 68, 68, 0.3);
        }
        100% {
          box-shadow: 
            var(--vanna-shadow-xl),
            0 0 0 2px rgba(239, 68, 68, 0.3),
            0 0 20px rgba(239, 68, 68, 0.2);
        }
      }

      @keyframes successGlow {
        0% {
          box-shadow: 
            var(--vanna-shadow-xl),
            0 0 0 2px rgba(16, 185, 129, 0.3),
            0 0 20px rgba(16, 185, 129, 0.2);
        }
        50% {
          box-shadow: 
            var(--vanna-shadow-2xl),
            0 0 0 3px rgba(16, 185, 129, 0.4),
            0 0 30px rgba(16, 185, 129, 0.3);
        }
        100% {
          box-shadow: 
            var(--vanna-shadow-xl),
            0 0 0 2px rgba(16, 185, 129, 0.3),
            0 0 20px rgba(16, 185, 129, 0.2);
        }
      }

      /* Dark theme overrides */
      :host([theme="dark"]) {
        background: var(--vanna-background-higher);
        border-color: var(--vanna-outline-default);
      }

      :host([theme="dark"]) .status-button {
        background: var(--vanna-background-highest);
        border-color: var(--vanna-outline-default);
      }

      :host([theme="dark"]) .status-button:hover {
        background: var(--vanna-background-highest);
        border-color: var(--vanna-outline-hover);
      }
    `
  ];

  @property() status: 'idle' | 'working' | 'error' | 'success' = 'idle';
  @property() message = '';
  @property() detail = '';
  @property() theme = 'light';

  private _previousHasContent = false;
  private _enterTimeout: number | null = null;
  private _exitTimeout: number | null = null;
  private _lastUpdateTime = 0;

  private _shouldSuppressDisplay(): boolean {
    const messageText = this.message?.toString() ?? '';
    if (!messageText.trim()) {
      return false;
    }
    // Generic suppressions regardless of status
    const genericSuppressions = [
      /\bfound\s+\d+\s+similar\s+pattern(?:s)?(?:\s+message)?\b/i,
      /\bfound\s+similar\s+pattern(?:s)?\b/i,
      /\bsimilar\s+pattern(?:s)?\s+found\b/i
    ];
    if (genericSuppressions.some((re) => re.test(messageText))) {
      return true;
    }
    switch (this.status) {
      case 'working':
        return /processing\s+your\s+request/i.test(messageText) ||
               /processing\s+request/i.test(messageText);
      case 'success':
        return /response\s+complete/i.test(messageText) ||
               /\bcompleted\b/i.test(messageText);
      case 'error':
        return /\berror\b/i.test(messageText) ||
               /something\s+went\s+wrong/i.test(messageText);
      default:
        return false;
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();

    // Clean up pending animation timeouts when component is removed
    if (this._enterTimeout !== null) {
      clearTimeout(this._enterTimeout);
      this._enterTimeout = null;
    }
    if (this._exitTimeout !== null) {
      clearTimeout(this._exitTimeout);
      this._exitTimeout = null;
    }
  }

  updated(_changedProperties: Map<string | number | symbol, unknown>) {
    // Update CSS class based on content
    const hasContent =
      (this.status === 'working' ||
        this.status === 'success' ||
        this.status === 'error') &&
      !this._shouldSuppressDisplay();

    // Cancel any pending animation timeouts to prevent race conditions
    if (this._enterTimeout !== null) {
      clearTimeout(this._enterTimeout);
      this._enterTimeout = null;
    }
    if (this._exitTimeout !== null) {
      clearTimeout(this._exitTimeout);
      this._exitTimeout = null;
    }

    // Debounce rapid updates to prevent animation jank
    const now = Date.now();
    const timeSinceLastUpdate = now - this._lastUpdateTime;
    const shouldDebounce = timeSinceLastUpdate < 100; // 100ms debounce

    // Handle animation classes
    if (hasContent !== this._previousHasContent) {
      if (hasContent) {
        // Content appeared - animate in
        this.classList.remove('no-content', 'exiting');

        if (!shouldDebounce) {
          // Only animate if not rapid-firing
          this.classList.add('entering');

          // Remove entering class after animation
          this._enterTimeout = window.setTimeout(() => {
            this.classList.remove('entering');
            this._enterTimeout = null;
          }, 300);
        }
      } else {
        // Content disappeared - animate out
        this.classList.remove('entering');

        if (!shouldDebounce) {
          // Only animate if not rapid-firing
          this.classList.add('exiting');

          // Add no-content class after animation
          this._exitTimeout = window.setTimeout(() => {
            this.classList.remove('exiting');
            this.classList.add('no-content');
            this._exitTimeout = null;
          }, 300);
        } else {
          // If rapid-firing, skip animation and go straight to no-content
          this.classList.add('no-content');
        }
      }
    } else if (!hasContent) {
      // Ensure no-content class is applied when no content
      this.classList.add('no-content');
    }

    this._previousHasContent = hasContent;
    this._lastUpdateTime = now;
  }

  render() {
    // Derive a single display message from status only
    let displayMessage = '';
    if (this.status === 'working') {
      displayMessage = 'Processing your request...';
    } else if (this.status === 'success') {
      displayMessage = 'Response complete';
    } else if (this.status === 'error') {
      displayMessage = 'Error';
    } else {
      // idle or unknown -> render nothing
      return html``;
    }
  
    // If status is success and incoming message mentions "Found" or "similar pattern", skip display entirely
    const incomingMessage = this.message?.toString() ?? '';
    if (
      this.status === 'success' &&
      (/\bfound\b/i.test(incomingMessage) || /similar\s+pattern/i.test(incomingMessage))
    ) {
      return html``;
    }

    return html`
      <div class="status-content">
        <span class="status-text">${displayMessage}</span>
      </div>
    `;
    

  }
}