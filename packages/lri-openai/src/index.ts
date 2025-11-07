/**
 * @lri/openai - OpenAI SDK wrapper with LRI support
 *
 * Automatically enriches OpenAI API calls with LRI semantic metadata:
 * - Intent signaling (ask, tell, propose, etc.)
 * - Affect awareness (emotional context)
 * - Consent policy (privacy settings)
 * - Session tracking (coherence, memory)
 *
 * @example
 * ```typescript
 * import OpenAI from 'openai';
 * import { withLRI } from '@lri/openai';
 *
 * const client = withLRI(new OpenAI());
 *
 * const response = await client.chat.completions.create({
 *   model: 'gpt-4',
 *   messages: [{ role: 'user', content: 'Hello!' }],
 *   lri: {
 *     intent: 'ask',
 *     affect: { tags: ['curious'] },
 *     consent: 'private'
 *   }
 * });
 * ```
 */

import type OpenAI from 'openai';
import type {
  ChatCompletionCreateParamsBase,
  ChatCompletionMessageParam,
  ChatCompletion,
} from 'openai/resources/chat/completions';

/**
 * LRI options for OpenAI requests
 */
export interface LRIOptions {
  /** Communicative intent */
  intent?: 'ask' | 'tell' | 'propose' | 'confirm' | 'notify' | 'sync' | 'plan' | 'agree' | 'disagree' | 'reflect';

  /** Emotional context */
  affect?: {
    /** Semantic tags (e.g., 'curious', 'frustrated') */
    tags?: string[];
    /** Pleasure-Arousal-Dominance values [-1, 1] */
    pad?: [number, number, number];
  };

  /** Privacy/consent level */
  consent?: 'private' | 'team' | 'public';

  /** Session/thread tracking */
  thread?: string;

  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Extended chat completion params with LRI support
 */
export interface LRIChatCompletionParams extends ChatCompletionCreateParamsBase {
  /** LRI semantic metadata */
  lri?: LRIOptions;
}

/**
 * LRI-enhanced OpenAI client
 */
export interface LRIOpenAI extends OpenAI {
  chat: OpenAI['chat'] & {
    completions: {
      create(params: LRIChatCompletionParams): Promise<ChatCompletion>;
    };
  };
}

/**
 * Convert LRI options to system message
 * This embeds LRI metadata in a way OpenAI can process
 */
function lriToSystemMessage(lri: LRIOptions): string {
  const parts: string[] = [];

  if (lri.intent) {
    parts.push(`Intent: ${lri.intent}`);
  }

  if (lri.affect?.tags && lri.affect.tags.length > 0) {
    parts.push(`Emotional context: ${lri.affect.tags.join(', ')}`);
  }

  if (lri.affect?.pad) {
    const [p, a, d] = lri.affect.pad;
    parts.push(`Affect (PAD): pleasure=${p.toFixed(2)}, arousal=${a.toFixed(2)}, dominance=${d.toFixed(2)}`);
  }

  if (lri.consent) {
    parts.push(`Privacy: ${lri.consent}`);
  }

  if (parts.length === 0) {
    return '';
  }

  return `[LRI Context] ${parts.join(' | ')}`;
}

/**
 * Inject LRI metadata into messages array
 */
function injectLRI(
  messages: ChatCompletionMessageParam[],
  lri: LRIOptions
): ChatCompletionMessageParam[] {
  const lriContext = lriToSystemMessage(lri);

  if (!lriContext) {
    return messages;
  }

  // Check if first message is system message
  if (messages.length > 0 && messages[0].role === 'system') {
    // Append to existing system message
    return [
      {
        ...messages[0],
        content: `${messages[0].content}\n\n${lriContext}`,
      },
      ...messages.slice(1),
    ];
  }

  // Add new system message at start
  return [
    {
      role: 'system',
      content: lriContext,
    },
    ...messages,
  ];
}

/**
 * Wrap OpenAI client with LRI support
 *
 * @param client - Original OpenAI client instance
 * @param defaultLRI - Default LRI options for all requests
 * @returns LRI-enhanced OpenAI client
 *
 * @example
 * ```typescript
 * const client = withLRI(new OpenAI(), {
 *   consent: 'private', // Default to private
 *   affect: { tags: ['neutral'] }
 * });
 *
 * // LRI metadata automatically added
 * const response = await client.chat.completions.create({
 *   model: 'gpt-4',
 *   messages: [{ role: 'user', content: 'Hello' }],
 *   lri: { intent: 'ask', affect: { tags: ['curious'] } }
 * });
 * ```
 */
export function withLRI(
  client: OpenAI,
  defaultLRI: LRIOptions = {}
): LRIOpenAI {
  // Create proxy that intercepts chat.completions.create
  const originalCreate = client.chat.completions.create.bind(client.chat.completions);

  const enhancedCreate = (params: LRIChatCompletionParams): any => {
    // Merge default LRI with request-specific LRI
    const lri: LRIOptions = {
      ...defaultLRI,
      ...params.lri,
      affect: {
        ...defaultLRI.affect,
        ...params.lri?.affect,
        tags: [
          ...(defaultLRI.affect?.tags || []),
          ...(params.lri?.affect?.tags || []),
        ],
      },
    };

    // Inject LRI metadata into messages
    const enhancedMessages = injectLRI(params.messages, lri);

    // Remove lri from params (OpenAI doesn't know about it)
    const { lri: _, ...openaiParams } = params;

    // Call original OpenAI API with enhanced messages
    return originalCreate({
      ...openaiParams,
      messages: enhancedMessages,
    } as any);
  };

  // Return proxied client
  return new Proxy(client, {
    get(target, prop, receiver) {
      if (prop === 'chat') {
        return new Proxy(target.chat, {
          get(chatTarget, chatProp) {
            if (chatProp === 'completions') {
              return new Proxy(chatTarget.completions, {
                get(compTarget, compProp) {
                  if (compProp === 'create') {
                    return enhancedCreate;
                  }
                  return Reflect.get(compTarget, compProp, compTarget);
                },
              });
            }
            return Reflect.get(chatTarget, chatProp, chatTarget);
          },
        });
      }
      return Reflect.get(target, prop, receiver);
    },
  }) as LRIOpenAI;
}

/**
 * Helper function to create common LRI intents
 */
export const intents = {
  /** Ask a question or request information */
  ask: (affect?: LRIOptions['affect']): LRIOptions => ({
    intent: 'ask',
    affect: affect || { tags: ['curious'] },
    consent: 'private',
  }),

  /** Provide information or state facts */
  tell: (affect?: LRIOptions['affect']): LRIOptions => ({
    intent: 'tell',
    affect: affect || { tags: ['neutral'] },
    consent: 'private',
  }),

  /** Suggest an action or approach */
  propose: (affect?: LRIOptions['affect']): LRIOptions => ({
    intent: 'propose',
    affect: affect || { tags: ['confident'] },
    consent: 'private',
  }),

  /** Reflect or reason about something */
  reflect: (affect?: LRIOptions['affect']): LRIOptions => ({
    intent: 'reflect',
    affect: affect || { tags: ['analytical'] },
    consent: 'private',
  }),
};

/**
 * Helper function for common affect states
 */
export const affects = {
  curious: { tags: ['curious'], pad: [0.3, 0.2, 0.1] as [number, number, number] },
  frustrated: { tags: ['frustrated'], pad: [-0.6, 0.4, -0.2] as [number, number, number] },
  confident: { tags: ['confident'], pad: [0.5, 0.3, 0.6] as [number, number, number] },
  urgent: { tags: ['urgent'], pad: [-0.2, 0.8, 0.3] as [number, number, number] },
  casual: { tags: ['casual'], pad: [0.4, -0.3, 0.0] as [number, number, number] },
  analytical: { tags: ['analytical'], pad: [0.0, 0.1, 0.2] as [number, number, number] },
  empathetic: { tags: ['empathetic'], pad: [0.3, -0.1, -0.2] as [number, number, number] },
  playful: { tags: ['playful'], pad: [0.7, 0.5, 0.2] as [number, number, number] },
};

// Export types
export type {
  ChatCompletionCreateParamsBase,
  ChatCompletionMessageParam,
  ChatCompletion,
} from 'openai/resources/chat/completions';
