import { createClient } from '@insforge/sdk';

const rawBaseUrl = import.meta.env.VITE_INSFORGE_URL || 'https://your-app.region.insforge.app';
const baseUrl = rawBaseUrl.replace(/\/+$/, '');
const anonKey = import.meta.env.VITE_INSFORGE_ANON_KEY || '';

if (!baseUrl || !anonKey) {
  console.warn(
    'InsForge configuration missing. Set VITE_INSFORGE_URL and VITE_INSFORGE_ANON_KEY in .env'
  );
}

export const insforgeClient = createClient({
  baseUrl,
  anonKey,
});

export const getInvestigationProgressChannel = (userId: string) => `investigation:${userId}:progress`;

// Database table names
export const TABLES = {
  INVESTIGATIONS: 'investigations',
};

// Realtime channels
export const CHANNELS = {
  USER_PROGRESS: getInvestigationProgressChannel,
};
