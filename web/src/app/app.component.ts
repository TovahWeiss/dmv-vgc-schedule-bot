import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface MessageConfig {
  channelId: string;
  messageId: string;
  stateSelections: string[];
  graphicTitle: string;
}

interface ConfigResponse {
  items: MessageConfig[];
  states: string[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [FormsModule],
  template: `
    <main class="page-shell">
      <header class="topbar">
        <a class="brand" href="/" aria-label="Message config editor home">
          <span class="brand-mark">M</span>
          <span>DMV VGC <span class="brand-muted">/ CONFIG</span></span>
        </a>
        <span class="server-status" [class.online]="!loading && !error">
          <span class="status-dot"></span>
          {{ loading ? 'Connecting' : error ? 'Connection issue' : 'Local config' }}
        </span>
      </header>

      @if (error) {
        <div class="notice notice-error" role="alert">
          <span class="notice-icon">!</span>
          <span>{{ error }}</span>
          <button type="button" class="notice-action" (click)="loadConfigs()">Try again</button>
        </div>
      }

      @if (saved) {
        <div class="notice notice-success" role="status">Changes saved to configs/messageConfigs.json</div>
      }

      @if (loading) {
        <div class="loading-panel"><span class="spinner"></span> Loading configurations…</div>
      } @else {
        <section class="config-list" aria-label="Message configurations">
          @for (config of configs; track $index; let i = $index) {
            <article class="config-card">
              <div class="card-heading">
                <div class="card-index">Calendar: <span>{{ config.graphicTitle }}</span></div>
              </div>

              <div class="fields-row">
                <label class="field title-field">
                  <span class="field-label">Graphic title <span class="required">REQUIRED</span></span>
                  <input [(ngModel)]="config.graphicTitle" maxlength="200" placeholder="Upcoming premier events" [name]="'title-' + i">
                  <span class="field-hint">Shown at the top of the event graphic</span>
                </label>
              </div>

              <div class="states-section">
                <div class="states-heading">
                  <div>
                    <span class="field-label">Included states</span>
                    <span class="field-hint">Select the states and regions shown for this message.</span>
                  </div>
                  <span class="selection-count">{{ config.stateSelections.length }} selected</span>
                </div>
                <div class="states-grid">
                  @for (state of states; track state) {
                    <label class="state-option" [class.selected]="config.stateSelections.includes(state)">
                      <input
                        type="checkbox"
                        [checked]="config.stateSelections.includes(state)"
                        (change)="toggleState(config, state, $event)">
                      <span class="checkmark"></span>
                      <span>{{ state }}</span>
                    </label>
                  }
                </div>
              </div>
            </article>
          }
        </section>
      }

      @if (!loading && !error) {
        <footer class="savebar">
          <span class="save-hint">Your edits aren't live until you save.</span>
          <button class="button button-primary save-button" type="button" (click)="saveConfigs()" [disabled]="saving">
            @if (saving) { <span class="spinner spinner-light"></span> Saving… } @else { Save changes <span aria-hidden="true">→</span> }
          </button>
        </footer>
      }
    </main>
  `,
})
export class AppComponent implements OnInit {
  private readonly http = inject(HttpClient);

  configs: MessageConfig[] = [];
  states: string[] = [];
  loading = true;
  saving = false;
  saved = false;
  error?:string = undefined;

  ngOnInit(): void {
    this.loadConfigs();
  }

  loadConfigs(): void {
    this.loading = true;
    this.error = '';
    this.saved = false;
    this.http.get<ConfigResponse>('/api/message-configs').subscribe({
      next: (response) => {
        this.configs = response.items.map((item) => ({
          ...item,
          stateSelections: [...item.stateSelections],
        }));
        this.states = response.states;
        this.loading = false;
      },
      error: (error: HttpErrorResponse) => {
        this.error = this.errorMessage(error);
        this.loading = false;
      },
    });
  }

  addConfig(): void {
    this.saved = false;
    this.configs = [
      ...this.configs,
      { channelId: '', messageId: '', stateSelections: [], graphicTitle: '' },
    ];
  }

  removeConfig(index: number): void {
    this.saved = false;
    this.configs = this.configs.filter((_, currentIndex) => currentIndex !== index);
  }

  toggleState(config: MessageConfig, state: string, event: Event): void {
    const input = event.target;
    if (!(input instanceof HTMLInputElement)) {
      return;
    }

    this.saved = false;
    config.stateSelections = input.checked
      ? [...config.stateSelections, state]
      : config.stateSelections.filter((selected) => selected !== state);
  }

  saveConfigs(): void {
    this.saving = true;
    this.saved = false;
    this.error = '';
    this.http.put('/api/message-configs', { items: this.configs }).subscribe({
      next: () => {
        this.saving = false;
        this.saved = true;
      },
      error: (error: HttpErrorResponse) => {
        this.error = this.errorMessage(error);
        this.saving = false;
      },
    });
  }

  private errorMessage(error: HttpErrorResponse): string {
    if (typeof error.error?.error === 'string') {
      return error.error.error;
    }
    return error.status
      ? `The server returned an error (${error.status}). Check the Node server and try again.`
      : 'Could not reach the Node server. Start the app with npm run dev and try again.';
  }
}
