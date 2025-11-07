/**
 * @lri/openai Demo
 *
 * Showcases different use cases:
 * 1. Basic usage with intent/affect
 * 2. Comparing responses with/without LRI
 * 3. Adapting to emotional state
 * 4. Session tracking
 */

import OpenAI from 'openai';
import { withLRI, intents, affects } from '@lri/openai';
import 'dotenv/config';

// Setup
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const client = withLRI(openai);

console.log('═══════════════════════════════════════════════════════');
console.log('📡 @lri/openai Demo - Layer 8 for OpenAI');
console.log('═══════════════════════════════════════════════════════\n');

/**
 * Demo 1: Basic Usage
 */
async function demo1Basic() {
  console.log('🎯 Demo 1: Basic Usage with Intent & Affect\n');

  const response = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [
      { role: 'user', content: 'Explain recursion in programming' }
    ],
    lri: {
      intent: 'ask',
      affect: { tags: ['curious', 'confused'] },
      consent: 'private'
    }
  });

  console.log('User: Explain recursion in programming');
  console.log('LRI: intent=ask, affect=curious,confused\n');
  console.log('AI:', response.choices[0].message.content);
  console.log('\n' + '─'.repeat(60) + '\n');
}

/**
 * Demo 2: Compare with/without LRI
 */
async function demo2Comparison() {
  console.log('🔬 Demo 2: Comparison - With vs Without LRI\n');

  const question = 'My code crashed again!';

  // Without LRI
  console.log('❌ WITHOUT LRI (plain OpenAI):');
  console.log(`User: ${question}\n`);

  const plain = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [
      { role: 'system', content: 'You are a helpful coding assistant.' },
      { role: 'user', content: question }
    ]
  });

  console.log('AI:', plain.choices[0].message.content.substring(0, 200) + '...\n');

  // With LRI
  console.log('✅ WITH LRI (intent + frustration):');
  console.log(`User: ${question}`);
  console.log('LRI: intent=ask, affect=frustrated,urgent\n');

  const lri = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [
      { role: 'system', content: 'You are a helpful coding assistant.' },
      { role: 'user', content: question }
    ],
    lri: {
      intent: 'ask',
      affect: affects.frustrated,
      consent: 'private'
    }
  });

  console.log('AI:', lri.choices[0].message.content.substring(0, 200) + '...\n');
  console.log('👀 Notice: LRI response is more empathetic and direct');
  console.log('\n' + '─'.repeat(60) + '\n');
}

/**
 * Demo 3: Emotional Adaptation
 */
async function demo3Emotional() {
  console.log('💭 Demo 3: Emotional State Adaptation\n');

  const scenarios = [
    {
      state: 'Curious beginner',
      content: 'How do I use async/await?',
      lri: intents.ask({ tags: ['curious', 'eager'] })
    },
    {
      state: 'Frustrated developer',
      content: 'How do I use async/await?',
      lri: intents.ask(affects.frustrated)
    },
    {
      state: 'Confident reviewer',
      content: 'How do I use async/await?',
      lri: intents.ask(affects.confident)
    }
  ];

  for (const scenario of scenarios) {
    console.log(`📍 Scenario: ${scenario.state}`);
    console.log(`User: ${scenario.content}`);
    console.log(`LRI: intent=${scenario.lri.intent}, affect=${scenario.lri.affect?.tags.join(',')}\n`);

    const response = await client.chat.completions.create({
      model: 'gpt-4',
      messages: [
        { role: 'system', content: 'You are a programming teacher.' },
        { role: 'user', content: scenario.content }
      ],
      lri: scenario.lri
    });

    console.log('AI:', response.choices[0].message.content.substring(0, 150) + '...\n');
  }

  console.log('👀 Notice: AI adapts tone based on emotional state');
  console.log('\n' + '─'.repeat(60) + '\n');
}

/**
 * Demo 4: Session Tracking
 */
async function demo4Session() {
  console.log('🧵 Demo 4: Session/Thread Tracking\n');

  const thread = crypto.randomUUID();
  console.log(`Thread ID: ${thread}\n`);

  const conversation = [
    {
      role: 'user',
      content: 'I need help with my React app',
      lri: intents.ask()
    },
    {
      role: 'assistant',
      content: 'I\'d be happy to help! What specifically are you working on?',
      lri: intents.tell()
    },
    {
      role: 'user',
      content: 'State management is confusing me',
      lri: { intent: 'tell', affect: affects.frustrated, thread }
    },
    {
      role: 'assistant',
      content: 'I understand state can be tricky. Let\'s break it down step by step.',
      lri: intents.tell(affects.empathetic)
    },
    {
      role: 'user',
      content: 'OK, so I should use useState() for component state?',
      lri: { intent: 'sync', affect: { tags: ['curious', 'understanding'] }, thread }
    }
  ];

  let messages = [{ role: 'system', content: 'You are a React expert.' }];

  for (const turn of conversation) {
    console.log(`${turn.role === 'user' ? '👤 User' : '🤖 AI'}: ${turn.content}`);

    if (turn.lri) {
      const affectStr = turn.lri.affect?.tags?.join(',') || 'neutral';
      console.log(`   LRI: intent=${turn.lri.intent}, affect=${affectStr}`);
    }

    if (turn.role === 'user') {
      messages.push({ role: 'user', content: turn.content });

      const response = await client.chat.completions.create({
        model: 'gpt-4',
        messages,
        lri: turn.lri
      });

      const aiMessage = response.choices[0].message.content;
      console.log(`🤖 AI: ${aiMessage.substring(0, 100)}...\n`);

      messages.push({ role: 'assistant', content: aiMessage });
    } else {
      messages.push({ role: 'assistant', content: turn.content });
      console.log('');
    }
  }

  console.log('👀 Notice: Conversation context maintained across turns');
  console.log('\n' + '─'.repeat(60) + '\n');
}

/**
 * Run all demos
 */
async function runDemos() {
  if (!process.env.OPENAI_API_KEY) {
    console.error('❌ Error: OPENAI_API_KEY not set');
    console.log('Create a .env file with: OPENAI_API_KEY=your-key-here\n');
    process.exit(1);
  }

  try {
    await demo1Basic();
    await demo2Comparison();
    await demo3Emotional();
    await demo4Session();

    console.log('✅ All demos completed!');
    console.log('\n🪷 LRI brings semantic clarity to AI communication\n');
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.status === 401) {
      console.log('\n💡 Check your OPENAI_API_KEY in .env file\n');
    }
  }
}

runDemos();
