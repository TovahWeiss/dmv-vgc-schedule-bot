import { randomUUID } from 'node:crypto';
import { readFile, rename, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { basename, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import express, { type ErrorRequestHandler } from 'express';
import { parse } from 'lossless-json';

interface MessageConfig {
  channelId: string;
  messageId: string;
  stateSelections: string[];
  graphicTitle: string;
  embed: MessageEmbedConfig;
}

interface MessageEmbedConfig {
  title: string;
  schedView: string;
  friendlySchedView: string;
  allCalView: string;
}

interface ConfigFileItem {
  channelId: unknown;
  messageId: unknown;
  stateSelections: string[];
  graphicTitle: string;
  embed: MessageEmbedConfig;
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
    && value['title'].length <= 256
    && typeof value['schedView'] === 'string'
    && value['schedView'].length <= 2048
    && typeof value['friendlySchedView'] === 'string'
    && value['friendlySchedView'].length <= 2048
    && typeof value['allCalView'] === 'string'
    && value['allCalView'].length <= 2048
}

function isMessageConfig(value: unknown): value is ConfigFileItem {
  return isRecord(value)
    && idAsString(value['channelId']) !== null
    && idAsString(value['messageId']) !== null
    && Array.isArray(value['stateSelections'])
    && value['stateSelections'].every((state: unknown) => typeof state === 'string')
    && typeof value['graphicTitle'] === 'string'
    && isMessageEmbedConfig(value['embed']);
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
      graphicTitle: item.graphicTitle,
      embed: item.embed,
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
  const graphicTitle = value['graphicTitle'];
  return typeof channelId === 'string'
    && /^[1-9]\d{0,19}$/.test(channelId)
    && typeof messageId === 'string'
    && /^[1-9]\d{0,19}$/.test(messageId)
    && Array.isArray(stateSelections)
    && stateSelections.every((state: unknown) => typeof state === 'string' && states.has(state))
    && new Set(stateSelections).size === stateSelections.length
    && typeof graphicTitle === 'string'
    && graphicTitle.trim().length > 0
    && graphicTitle.length <= 200
    && isMessageEmbedConfig(value['embed']);
}

function serializeConfigs(items: MessageConfig[]): string {
  const records = items.map((item) => {
    const stateSelections = JSON.stringify(item.stateSelections, null, 2).replace(/\n/g, '\n    ');
    return [
      '  {',
      `    "channelId": ${item.channelId},`,
      `    "messageId": ${item.messageId},`,
      `    "stateSelections": ${stateSelections},`,
      `    "graphicTitle": ${JSON.stringify(item.graphicTitle)},`,
      `    "embed": ${JSON.stringify(item.embed, null, 2).replace(/\n/g, '\n    ')}`,
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
      error: 'Each item needs valid numeric IDs, a title, valid embed fields, and only known, non-duplicate states.',
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
