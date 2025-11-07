# @lri/openai Demo

Interactive demos showing how **LRI (Liminal Resonance Interface)** improves OpenAI interactions.

## 🚀 Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Add your OpenAI API key
cp .env.example .env
# Edit .env and add your key

# 3. Run demos
npm run demo
```

## 📋 Demos

### Demo 1: Basic Usage
Shows how to add intent and affect to OpenAI calls.

### Demo 2: Comparison
Side-by-side: plain OpenAI vs LRI-enhanced. See the difference!

### Demo 3: Emotional Adaptation
Same question, different emotional states → different AI responses.

### Demo 4: Session Tracking
Multi-turn conversation with context preservation.

## 🎯 What You'll Learn

- ✅ How to wrap OpenAI client with LRI
- ✅ Using intent types (ask, tell, propose, reflect)
- ✅ Adding emotional context (affect tags)
- ✅ Privacy control (consent levels)
- ✅ Session/thread tracking

## 💡 Key Insights

**Without LRI:**
```typescript
const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'My code crashed!' }]
});
// AI doesn't know if you're frustrated or just informing
```

**With LRI:**
```typescript
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'My code crashed!' }],
  lri: {
    intent: 'ask',  // You want help
    affect: { tags: ['frustrated', 'urgent'] },  // You're stressed
    consent: 'private'  // Keep this private
  }
});
// AI adapts its tone and urgency accordingly
```

## 🧪 Expected Results

You'll see AI responses change based on:
- **Intent**: Asking vs telling gets different response styles
- **Affect**: Frustrated users get more empathetic, direct help
- **Context**: Multi-turn conversations maintain coherence

## 📚 Learn More

- [@lri/openai Package](../../packages/lri-openai)
- [LRI Documentation](https://lri.dev/docs)
- [OpenAI API](https://platform.openai.com/docs)

---

🪷 **Part of the LRI project** - Layer 8 semantic protocol for human-AI communication
