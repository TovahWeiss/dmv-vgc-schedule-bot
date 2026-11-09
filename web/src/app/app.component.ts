import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface MessageConfig {
  channelId: string;
  messageId: string;
  stateSelections: string[];
  embed: MessageEmbedConfig;
  image: MessageImageConfig;
}

interface MessageEmbedConfig {
  title: string;
  schedView: string;
  friendlySchedView: string;
  allCalView: string;
}

interface MessageImageConfig {
  title: string;
  headerGradientStartColor: string;
  headerGradientEndColor: string;
  imageBackgroundColor: string;
  textPrimaryColor: string;
  headerTextColor: string;
  locationTextColor: string;
  rowBackgroundColor: string;
  highlightColor: string;
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
                <div class="card-index">Calendar: <span>{{ config.image.title }}</span></div>
              </div>

              <div class="fields-row">
                <label class="field title-field">
                  <span class="field-label">Graphic title <span class="required">REQUIRED</span></span>
                  <input [(ngModel)]="config.image.title" maxlength="200" placeholder="Upcoming premier events" [name]="'title-' + i">
                  <span class="field-hint">Shown at the top of the event graphic</span>
                </label>
              </div>

              <section class="embed-section" [attr.aria-labelledby]="'embed-heading-' + i">
                <div class="states-heading">
                  <div>
                    <span class="field-label" [id]="'embed-heading-' + i">Embed fields</span>
                    <span class="field-hint">Edit the title and calendar links shown in this message's embed.</span>
                  </div>
                </div>
                <div class="embed-grid">
                  <label class="field">
                    <span class="field-label">Embed title</span>
                    <input [(ngModel)]="config.embed.title" (ngModelChange)="saved = false" maxlength="35" [name]="'embed-title-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Premier schedule view URL</span>
                    <input [(ngModel)]="config.embed.schedView" (ngModelChange)="saved = false" maxlength="2048" [name]="'sched-view-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Friendly schedule view URL</span>
                    <input [(ngModel)]="config.embed.friendlySchedView" (ngModelChange)="saved = false" maxlength="2048" [name]="'friendly-sched-view-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">All calendars view URL</span>
                    <input [(ngModel)]="config.embed.allCalView" (ngModelChange)="saved = false" maxlength="2048" [name]="'all-cal-view-' + i">
                  </label>
                </div>
              </section>

              <section class="embed-section" [attr.aria-labelledby]="'embed-heading-' + i">
                <div class="states-heading">
                  <div>
                    <span class="field-label" [id]="'embed-heading-' + i">Image fields</span>
                    <span class="field-hint">Edit graphic properties used in the calendar image output for the embed</span>
                  </div>
                </div>
                <label class="field" style="margin-bottom: 1rem;">
                    <span class="field-label">Image title</span>
                    <input [(ngModel)]="config.image.title" (ngModelChange)="saved = false" maxlength="35" [name]="'image-title-' + i">
                </label>
                <div class="image-grid">
                  <label class="field">
                    <span class="field-label">Header gradient start color</span>
                    <input type="color" [(ngModel)]="config.image.headerGradientStartColor" (ngModelChange)="saved = false" [name]="'header-gradient-start-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Header gradient end color</span>
                    <input type="color" [(ngModel)]="config.image.headerGradientEndColor" (ngModelChange)="saved = false" [name]="'header-gradient-end-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Image background color</span>
                    <input type="color" [(ngModel)]="config.image.imageBackgroundColor" (ngModelChange)="saved = false" [name]="'image-background-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Primary text color</span>
                    <input type="color" [(ngModel)]="config.image.textPrimaryColor" (ngModelChange)="saved = false" [name]="'text-primary-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Header text color</span>
                    <input type="color" [(ngModel)]="config.image.headerTextColor" (ngModelChange)="saved = false" [name]="'header-text-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Location text color</span>
                    <input type="color" [(ngModel)]="config.image.locationTextColor" (ngModelChange)="saved = false" [name]="'location-text-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Row background color</span>
                    <input type="color" [(ngModel)]="config.image.rowBackgroundColor" (ngModelChange)="saved = false" [name]="'row-background-' + i">
                  </label>
                  <label class="field">
                    <span class="field-label">Highlight color</span>
                    <input type="color" [(ngModel)]="config.image.highlightColor" (ngModelChange)="saved = false" [name]="'highlight-' + i">
                  </label>
                </div>
              </section>

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

  constructor(private cdr: ChangeDetectorRef){

  }

  ngOnInit(): void {
    this.loadConfigs();
  }

  loadConfigs(): void {
    this.loading = true;
    this.saved = false;
    this.http.get<ConfigResponse>('/api/message-configs').subscribe({
      next: (response) => {
        this.configs = response.items.map((item) => ({
          ...item,
          stateSelections: [...item.stateSelections],
          image: {
            ...item.image,
            headerGradientStartColor: this.colorToHex(item.image.headerGradientStartColor),
            headerGradientEndColor: this.colorToHex(item.image.headerGradientEndColor),
            imageBackgroundColor: this.colorToHex(item.image.imageBackgroundColor),
            textPrimaryColor: this.colorToHex(item.image.textPrimaryColor),
            headerTextColor: this.colorToHex(item.image.headerTextColor),
            locationTextColor: this.colorToHex(item.image.locationTextColor),
            rowBackgroundColor: this.colorToHex(item.image.rowBackgroundColor),
            highlightColor: this.colorToHex(item.image.highlightColor),
          },
        }));
        this.states = response.states;
        this.loading = false;
        this.cdr.detectChanges()
      },
      error: (error: HttpErrorResponse) => {
        this.error = this.errorMessage(error);
        this.loading = false;
      },
    });
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
        this.cdr.detectChanges();
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

  private colorToHex(color: string): string {
    const namedColors: Record<string, string> = {
      black: '#000000',
      dodgerblue: '#1e90ff',
      green: '#008000',
      grey: '#808080',
      red: '#ff0000',
      white: '#ffffff',
    };

    return namedColors[color.toLowerCase()] ?? color;
  }
}
