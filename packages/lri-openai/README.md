# @lri/openai

OpenAI SDK wrapper with **LRI (Liminal Resonance Interface)** support. Automatically enriches your OpenAI API calls with semantic metadata for better AI understanding.

## 🎯 Why?

Standard OpenAI calls lack context:
```typescript
// ❌ OpenAI doesn't know if you're asking, commanding, or just chatting
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Fix the bug' }]
});
```

With LRI, add semantic clarity:
```typescript
// ✅ AI knows this is an urgent request with frustration
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Fix the bug' }],
  lri: {
    intent: 'ask',
    affect: { tags: ['urgent', 'frustrated'] },
    consent: 'team'
  }
});
```

**Result:** Better AI responses, fewer misunderstandings, explicit privacy control.

## 📦 Installation

```bash
npm install @lri/openai openai
```

## 🚀 Quick Start

```typescript
import OpenAI from 'openai';
import { withLRI } from '@lri/openai';

// Wrap your OpenAI client
const client = withLRI(new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
}));

// Use normally, with optional LRI metadata
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'How do I center a div?' }
  ],
  lri: {
    intent: 'ask',
    affect: { tags: ['curious', 'confused'] },
    consent: 'private'
  }
});

console.log(response.choices[0].message.content);
```

## 🎨 Features

### Intent Signaling

Tell the AI what you're trying to achieve:

```typescript
// Asking a question
lri: { intent: 'ask' }

// Making a suggestion
lri: { intent: 'propose' }

// Stating facts
lri: { intent: 'tell' }

// Reflecting/reasoning
lri: { intent: 'reflect' }
```

**Available intents:** `ask`, `tell`, `propose`, `confirm`, `notify`, `sync`, `plan`, `agree`, `disagree`, `reflect`

### Affect/Emotion Tags

Express emotional context:

```typescript
// Frustrated user
lri: {
  intent: 'ask',
  affect: { tags: ['frustrated', 'urgent'] }
}

// Curious learner
lri: {
  intent: 'ask',
  affect: { tags: ['curious', 'playful'] }
}

// Analytical researcher
lri: {
  intent: 'ask',
  affect: { tags: ['analytical', 'confident'] }
}
```

### PAD Model (Advanced)

Use the Pleasure-Arousal-Dominance model for precise emotional state:

```typescript
lri: {
  affect: {
    tags: ['frustrated'],
    pad: [
      -0.6,  // Pleasure: negative (unpleasant)
      0.4,   // Arousal: medium (alert)
      -0.2   // Dominance: low (feeling controlled)
    ]
  }
}
```

### Privacy/Consent

Explicit privacy control per message:

```typescript
// Private (default)
lri: { consent: 'private' }  // Don't share with anyone

// Team
lri: { consent: 'team' }  // Can share with team members

// Public
lri: { consent: 'public' }  // Can be made public
```

### Session Tracking

Track conversations across messages:

```typescript
const thread = crypto.randomUUID();

// First message
await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Help me debug this' }],
  lri: { thread, intent: 'ask' }
});

// Follow-up message in same thread
await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'It still doesn\'t work' }],
  lri: { thread, intent: 'tell', affect: { tags: ['frustrated'] } }
});
```

## 💡 Helper Functions

### Intent Helpers

```typescript
import { intents } from '@lri/openai';

// Quick intent creation
lri: intents.ask()  // { intent: 'ask', affect: { tags: ['curious'] }, consent: 'private' }
lri: intents.tell() // { intent: 'tell', affect: { tags: ['neutral'] }, consent: 'private' }
lri: intents.propose() // { intent: 'propose', affect: { tags: ['confident'] }, consent: 'private' }

// With custom affect
lri: intents.ask({ tags: ['urgent', 'frustrated'] })
```

### Affect Presets

```typescript
import { affects } from '@lri/openai';

lri: {
  intent: 'ask',
  affect: affects.frustrated  // Pre-configured PAD + tags
}

// Available presets:
// - curious, frustrated, confident, urgent
// - casual, analytical, empathetic, playful
```

## 🔧 Advanced Usage

### Default LRI Options

Set default options for all requests:

```typescript
const client = withLRI(new OpenAI(), {
  consent: 'private',  // Always private by default
  affect: { tags: ['analytical'] }
});

// These defaults apply to all calls
await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Hello' }],
  // No need to specify consent/affect every time
});
```

### Combining with Existing Code

The wrapper is transparent - use all OpenAI features normally:

```typescript
const client = withLRI(new OpenAI());

// Streaming works
const stream = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Count to 10' }],
  stream: true,
  lri: { intent: 'ask' }
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}

// Functions/tools work
await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'What\'s the weather?' }],
  tools: [{ type: 'function', function: weatherTool }],
  lri: { intent: 'ask', affect: { tags: ['curious'] } }
});

// All other OpenAI methods unchanged
const models = await client.models.list();
const embedding = await client.embeddings.create({ ... });
```

## 📊 Real-World Examples

### Customer Support Bot

```typescript
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'system', content: 'You are a helpful support agent.' },
    { role: 'user', content: 'My order hasn\'t arrived!' }
  ],
  lri: {
    intent: 'ask',
    affect: {
      tags: ['frustrated', 'urgent'],
      pad: [-0.7, 0.8, -0.3]  // Very frustrated, very alert, low control
    },
    consent: 'team'  // Support team can see this
  }
});

// AI will adapt its tone to the frustration level
```

### Code Review Assistant

```typescript
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'Review this code: ...' }
  ],
  lri: {
    intent: 'ask',
    affect: {
      tags: ['analytical', 'confident'],
      pad: [0.2, 0.3, 0.5]  // Neutral-positive, focused, in control
    },
    consent: 'team'
  }
});
```

### Learning/Tutorial Bot

```typescript
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'Explain quantum entanglement' }
  ],
  lri: {
    intent: 'ask',
    affect: {
      tags: ['curious', 'eager'],
      pad: [0.6, 0.5, 0.3]  // Pleasant, energized, moderate control
    },
    consent: 'private'
  }
});

// AI knows to be educational and encouraging
```

## 🔍 How It Works

The wrapper injects LRI metadata as a system message that OpenAI processes:

```typescript
// You write:
{
  messages: [{ role: 'user', content: 'Hello' }],
  lri: { intent: 'ask', affect: { tags: ['curious'] } }
}

// Sent to OpenAI:
{
  messages: [
    {
      role: 'system',
      content: '[LRI Context] Intent: ask | Emotional context: curious | Privacy: private'
    },
    { role: 'user', content: 'Hello' }
  ]
}
```

This makes the AI aware of:
- **Your communicative goal** (intent)
- **Your emotional state** (affect)
- **Privacy expectations** (consent)

Result: **More contextually appropriate responses**.

## 🧪 Testing

```bash
npm test
```

## 📚 Learn More

- [LRI Documentation](https://lri.dev/docs)
- [LRI Specification](https://github.com/lri/lri/blob/main/docs/rfcs/rfc-000.md)
- [OpenAI API Docs](https://platform.openai.com/docs)

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](../../CONTRIBUTING.md)

## 📄 License

MIT

## 🪷 Philosophy

> "Meaning matters more than bytes. By making intent and affect explicit, we bridge the gap between human expression and AI understanding."

Part of the **Liminal Resonance Interface** project - a Layer 8 semantic protocol for human-AI communication.

---

**Made with 🧠 by the LRI community**
