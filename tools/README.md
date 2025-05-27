# Vibe Coding Dev Setup

A shared scaffold for AI-assisted “vibe coding” using Windsurf and Cursor.

## Structure

- `/dev-tools`: common utilities (logger, debug, etc.)
- `/ai-tools`:
  - `prompts/`: AI prompt templates
  - `pipelines/`: workflows/pipelines configurations
  - `snippets/`: reusable code snippets
- `/windsurf`: minimal Windsurf config
- `/cursor`: minimal Cursor config
- `/mcp`: shared modules
- `/tasks`: scheduled tasks
- `/prd`: production runbooks & docs
- `/docs`: reference documentation & AI style rules

## Installation

```bash
npm install chalk debug axios
```

## TypeScript Path Aliases

Add to `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@dev-tools/*": ["dev-tools/*"],
      "@ai-tools/*": ["ai-tools/*"]
    }
  }
}
```

## Usage

Import utilities:

```ts
import { logger, debug } from '@dev-tools';
```

Configure Windsurf and Cursor to point at `/ai-tools`.
