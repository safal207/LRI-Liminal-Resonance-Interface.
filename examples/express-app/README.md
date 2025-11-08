# Express + LRI Demo Application

> Example Express server that shows how to integrate the `node-lri` middleware, parse LCE metadata, and shape responses based on intent.

## Quick start

1. Install the workspace dependencies from the repository root:

   ```bash
   npm install
   ```

2. (Optional) Rebuild the SDK if you are modifying it alongside the example:

   ```bash
   npm run build --workspace node-lri
   ```

3. Start the Express example:

   ```bash
   cd examples/express-app
   npm install
   npm run dev
   ```

The dev server listens on <http://localhost:3000>. The console prints helpful curl commands when it boots.

## Crafting LCE headers

You can generate a Base64 LCE header with the helper shipped in the SDK:

```bash
node -e "const { createLCEHeader } = require('node-lri'); const lce = { v: 1, intent: { type: 'ask', goal: 'Demo request' }, policy: { consent: 'private' } }; console.log(createLCEHeader(lce));"
```

Store the output in a shell variable for the examples below:

```bash
LCE=$(node -e "const { createLCEHeader } = require('node-lri'); const lce = { v: 1, intent: { type: 'ask', goal: 'Demo request' }, policy: { consent: 'private' } }; process.stdout.write(createLCEHeader(lce));")
```

## Demo requests and responses

### 1. `GET /ping`

Health-check endpoint that flips a boolean when a valid LCE header is present.

```bash
curl -i http://localhost:3000/ping
```

Expected response (timestamp varies):

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{
  "ok": true,
  "timestamp": "2025-01-15T10:30:00.000Z",
  "receivedLCE": false
}
```

Send the same request with an LCE header:

```bash
curl -i -H "LCE: $LCE" http://localhost:3000/ping
```

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{
  "ok": true,
  "timestamp": "2025-01-15T10:30:01.000Z",
  "receivedLCE": true
}
```

### 2. `POST /echo`

Mirrors the JSON body and responds with a server-generated LCE header that continues the thread.

```bash
curl -i -X POST http://localhost:3000/echo \
  -H "Content-Type: application/json" \
  -H "LCE: $LCE" \
  -d '{"message": "Hello LRI!"}'
```

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
LCE: <Base64 header with follow-up metadata>

{
  "echo": {
    "message": "Hello LRI!"
  },
  "lce": {
    "v": 1,
    "intent": {
      "type": "tell",
      "goal": "Echo response"
    },
    "affect": {
      "tags": [
        "helpful"
      ]
    },
    "memory": {
      "thread": "<copied-from-request>",
      "t": "2025-01-15T10:30:02.000Z"
    },
    "policy": {
      "consent": "private"
    }
  }
}
```

To inspect the response header:

```bash
curl -i -X POST http://localhost:3000/echo \
  -H "Content-Type: application/json" \
  -H "LCE: $LCE" \
  -d '{"message": "Inspect headers"}' | \
  grep '^LCE:' | \
  cut -d' ' -f2 | \
  base64 --decode
```

If you omit the `LCE` header while the middleware is configured with `required: true`, the API responds with:

```http
HTTP/1.1 428 Precondition Required
Content-Type: application/json; charset=utf-8

{
  "error": "LCE header required",
  "header": "LCE"
}
```

### 3. `GET /api/data`

Endpoint that tailors the payload based on the request intent.

```bash
SYNC_LCE=$(node -e "const { createLCEHeader } = require('node-lri'); const lce = { v: 1, intent: { type: 'sync' }, policy: { consent: 'private' }, qos: { coherence: 0.9 } }; process.stdout.write(createLCEHeader(lce));")
```

Ask for data:

```bash
curl -H "LCE: $LCE" http://localhost:3000/api/data
```

Response:

```json
{
  "message": "Here is the data you requested",
  "data": [1, 2, 3, 4, 5]
}
```

Synchronize context:

```bash
curl -H "LCE: $SYNC_LCE" http://localhost:3000/api/data
```

Response:

```json
{
  "message": "Context synchronized",
  "coherence": 0.9
}
```

## Troubleshooting

- **422 Invalid LCE** – Ensure your JSON payload matches the schema. Missing intent types or malformed fields will trigger validation errors when `validate: true` is enabled.
- **428 LCE header required** – If you enable the `required` option in `index.ts`, every request must include the header.
- **400 Malformed LCE header** – Verify that the header value is Base64 encoded JSON.

## Next steps

- Explore the WebSocket example in [`examples/ws-echo`](../ws-echo/).
- Inspect the middleware implementation in [`packages/node-lri/src/middleware.ts`](../../packages/node-lri/src/middleware.ts).
- Read the LCE schema reference in [`schemas/lce-v0.1.json`](../../schemas/lce-v0.1.json).

MIT © LRI Contributors
