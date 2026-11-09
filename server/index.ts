import { randomUUID } from 'node:crypto';
import { readFile, rename, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import express, { type ErrorRequestHandler } from 'express';
import { parse } from 'lossless-json';

interface MessageConfig {
  channelId: string;
  messageId: string;
  stateSelections: string[];
  embed: MessageEmbedConfig;
  image: MessageImageConfig
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

interface ConfigFileItem {
  channelId: unknown;
  messageId: unknown;
  stateSelections: string[];
  embed: MessageEmbedConfig;
  image: MessageImageConfig;
}

const projectRoot = dirname(dirname(dirname(fileURLToPath(import.meta.url)))) +  "\\dmv vgc calendar\\";
const configPath = join(projectRoot, 'configs', 'messageConfigs.json');
const statesPath = join(projectRoot, 'configs', 'states.json');
const webPath = join(projectRoot, 'dist', 'web', 'browser');
const port = Number(process.env['PORT'] ?? 3000);
const app = express();

app.disable('x-powered-by');
app.use(express.json({ limit: '100kb' }));

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function idAsString(value: unknown): string | null {
  if (typeof value !== 'string' && typeof value !== 'number' && typeof value !== 'object') {
    return null;
  }
  const id = String(value);
  return /^[1-9]\d{0,19}$/.test(id) ? id : null;
}

function isMessageEmbedConfig(value: unknown): value is MessageEmbedConfig {
  return isRecord(value)
    && typeof value['title'] === 'string'
    && value['title'].length <= 35
    && typeof value['schedView'] === 'string'
    && typeof value['friendlySchedView'] === 'string'
    && typeof value['allCalView'] === 'string'
}

function isMessageImageConfig(value: unknown): value is MessageImageConfig {
  return isRecord(value)
    && typeof value['title'] === 'string'
    && typeof value['headerGradientStartColor'] === 'string'
    && typeof value['headerGradientEndColor'] === 'string'
    && typeof value['imageBackgroundColor'] === 'string'
    && typeof value['textPrimaryColor'] === 'string'
    && typeof value['headerTextColor'] === 'string'
    && typeof value['locationTextColor'] === 'string'
    && typeof value['rowBackgroundColor'] === 'string'
    && typeof value['highlightColor'] === 'string'
}

function isMessageConfig(value: unknown): value is ConfigFileItem {
  return isRecord(value)
    && idAsString(value['channelId']) !== null
    && idAsString(value['messageId']) !== null
    && Array.isArray(value['stateSelections'])
    && value['stateSelections'].every((state: unknown) => typeof state === 'string')
    && isMessageEmbedConfig(value['embed'])
    && isMessageImageConfig(value['image']);
}

async function readStates(): Promise<string[]> {
  const contents = await readFile(statesPath, 'utf8');
  const parsed: unknown = JSON.parse(contents);
  if (!isRecord(parsed)) {
    throw new Error('configs/states.json must contain an object of state names.');
  }
  return Object.keys(parsed);
}

async function readConfigs(): Promise<MessageConfig[]> {
  const contents = await readFile(configPath, 'utf8');
  const parsed: unknown = parse(contents);
  if (!Array.isArray(parsed) || !parsed.every(isMessageConfig)) {
    throw new Error('configs/messageConfigs.json must contain an array of valid message configurations.');
  }

  return parsed.map((item) => {
    const channelId = idAsString(item.channelId);
    const messageId = idAsString(item.messageId);
    if (channelId === null || messageId === null) {
      throw new Error('configs/messageConfigs.json contains an invalid Discord ID.');
    }
    return {
      channelId,
      messageId,
      stateSelections: item.stateSelections,
      embed: item.embed,
      image: item.image
    };
  });
}

function isValidMessageConfig(value: unknown, states: Set<string>): value is MessageConfig {
  if (!isRecord(value)) {
    return false;
  }
  const channelId = value['channelId'];
  const messageId = value['messageId'];
  const stateSelections = value['stateSelections'];
  return typeof channelId === 'string'
    && /^[1-9]\d{0,19}$/.test(channelId)
    && typeof messageId === 'string'
    && /^[1-9]\d{0,19}$/.test(messageId)
    && Array.isArray(stateSelections)
    && stateSelections.every((state: unknown) => typeof state === 'string' && states.has(state))
    && new Set(stateSelections).size === stateSelections.length
    && isMessageEmbedConfig(value['embed'])
    && isMessageImageConfig(value['image']);

}

function serializeConfigs(items: MessageConfig[]): string {
  const records = items.map((item) => {
    const stateSelections = JSON.stringify(item.stateSelections, null, 2).replace(/\n/g, '\n    ');
    return [
      '  {',
      `    "channelId": ${item.channelId},`,
      `    "messageId": ${item.messageId},`,
      `    "stateSelections": ${stateSelections},`,
      `    "embed": ${JSON.stringify(item.embed, null, 2).replace(/\n/g, '\n    ')},`,
      `    "image": ${JSON.stringify(item.image, null, 2).replace(/\n/g, '\n    ')}`,
      '  }',
    ].join('\n');
  });
  return `[\n${records.join(',\n')}\n]\n`;
}

app.get('/api/message-configs', async (_request, response) => {
  const [items, states] = await Promise.all([readConfigs(), readStates()]);
  response.json({ items, states });
});

app.put('/api/message-configs', async (request, response) => {
  if (!isRecord(request.body) || !Array.isArray(request.body['items'])) {
    response.status(400).json({ error: 'Request must contain an items array.' });
    return;
  }

  const states = new Set(await readStates());
  const items: unknown[] = request.body['items'];
  if (!items.every((item) => isValidMessageConfig(item, states))) {
    response.status(400).json({
      error: 'Each item needs valid numeric IDs, a title, valid embed fields,valid image fields, and only known, non-duplicate states.',
    });
    return;
  }

  const configs = items as MessageConfig[];
  if (new Set(configs.map((item) => item.channelId)).size !== configs.length) {
    response.status(400).json({ error: 'Each configuration must use a unique channel ID.' });
    return;
  }

  const temporaryPath = join(dirname(configPath), `.messageConfigs.${randomUUID()}.tmp`);
  await writeFile(temporaryPath, serializeConfigs(configs), 'utf8');
  await rename(temporaryPath, configPath);
  response.json({ ok: true });
});

app.use(express.static(webPath));
app.get(/.*/, (_request, response, next) => {
  response.sendFile(join(webPath, 'index.html'), (error) => {
    if (error) {
      next(error);
    }
  });
});

const errorHandler: ErrorRequestHandler = (error: unknown, _request, response, _next) => {
  const status = isRecord(error) && typeof error['status'] === 'number' ? error['status'] : 500;
  if (status >= 500) {
    console.error('Request failed:', error);
  }
  response.status(status).json({
    error: status >= 500 ? 'The server could not complete the request.' : 'Invalid request.',
  });
};
app.use(errorHandler);

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error('PORT must be an integer between 1 and 65535.');
}

createServer(app).listen(port, '127.0.0.1', () => {
  console.log(`Message config editor available at http://127.0.0.1:${port}`);
});
