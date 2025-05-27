// dev-tools/debug.ts
import createDebug from 'debug';

// enable via DEBUG=app:* npm start
export const debug = createDebug('app:core');
export const debugTasks = createDebug('app:tasks');
