// dev-tools/logger.ts
import chalk from 'chalk';

const timestamp = () => new Date().toISOString();

export const logger = {
  debug: (msg: string, ...args: any[]) =>
    console.log(chalk.cyan(`[DEBUG] ${timestamp()}`), msg, ...args),
  info: (msg: string, ...args: any[]) =>
    console.log(chalk.green(`[INFO ] ${timestamp()}`), msg, ...args),
  warn: (msg: string, ...args: any[]) =>
    console.warn(chalk.yellow(`[WARN ] ${timestamp()}`), msg, ...args),
  error: (msg: string, ...args: any[]) =>
    console.error(chalk.red(`[ERROR] ${timestamp()}`), msg, ...args),
};
