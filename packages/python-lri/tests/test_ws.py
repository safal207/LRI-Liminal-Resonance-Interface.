"""
Tests for WebSocket LHS Protocol
"""

import pytest
import asyncio
from lri import LCE, Intent, Policy
from lri.ws import LRIWSServer, LRIWSClient
from lri.ws.types import LHSHello, LHSMirror, LHSBind, LHSSeal


def test_lhs_hello_creation():
    """Test creating Hello message"""
    hello = LHSHello(
        encodings=["json", "cbor"],
        features=["ltp", "lss"],
        client_id="test-client",
    )

    assert hello.step == "hello"
    assert hello.lri_version == "0.2"
    assert hello.encodings == ["json", "cbor"]
    assert hello.features == ["ltp", "lss"]
    assert hello.client_id == "test-client"


def test_lhs_mirror_creation():
    """Test creating Mirror message"""
    mirror = LHSMirror(
        encoding="json", features=["ltp", "lss"], server_id="test-server"
    )

    assert mirror.step == "mirror"
    assert mirror.lri_version == "0.2"
    assert mirror.encoding == "json"
    assert mirror.features == ["ltp", "lss"]
    assert mirror.server_id == "test-server"


def test_lhs_bind_creation():
    """Test creating Bind message"""
    bind = LHSBind(thread="thread-123", auth="token-abc")

    assert bind.step == "bind"
    assert bind.thread == "thread-123"
    assert bind.auth == "token-abc"


def test_lhs_seal_creation():
    """Test creating Seal message"""
    seal = LHSSeal(session_id="session-456", thread="thread-123", status="ready")

    assert seal.step == "seal"
    assert seal.session_id == "session-456"
    assert seal.thread == "thread-123"
    assert seal.status == "ready"


def test_lhs_hello_serialization():
    """Test Hello message JSON serialization"""
    hello = LHSHello(
        encodings=["json"], features=["ltp"], client_id="test-client"
    )

    json_str = hello.model_dump_json()
    assert "hello" in json_str
    assert "test-client" in json_str

    # Round-trip
    parsed = LHSHello.model_validate_json(json_str)
    assert parsed.step == hello.step
    assert parsed.client_id == hello.client_id


def test_lhs_mirror_serialization():
    """Test Mirror message JSON serialization"""
    mirror = LHSMirror(encoding="cbor", features=["lss"], server_id="test-server")

    json_str = mirror.model_dump_json()
    assert "mirror" in json_str
    assert "cbor" in json_str

    # Round-trip
    parsed = LHSMirror.model_validate_json(json_str)
    assert parsed.encoding == mirror.encoding
    assert parsed.server_id == mirror.server_id


@pytest.mark.asyncio
async def test_server_creation():
    """Test creating WebSocket server"""
    server = LRIWSServer(host="127.0.0.1", port=8765)

    assert server.host == "127.0.0.1"
    assert server.port == 8765
    assert server.encoding == "json"
    assert server.features == ["ltp", "lss"]
    assert server.sessions == {}


@pytest.mark.asyncio
async def test_client_creation():
    """Test creating WebSocket client"""
    client = LRIWSClient(
        url="ws://localhost:8765",
        encodings=["json", "cbor"],
        features=["ltp", "lss"],
        thread_id="thread-123",
    )

    assert client.url == "ws://localhost:8765"
    assert client.encodings == ["json", "cbor"]
    assert client.features == ["ltp", "lss"]
    assert client.thread_id == "thread-123"
    assert client.session_id is None
    assert client.negotiated_encoding is None


@pytest.mark.asyncio
async def test_handshake_and_message_exchange():
    """Test full LHS handshake and message exchange"""
    # Track received messages
    server_received = []
    client_received = []

    async def on_server_message(lce, session_id, thread_id):
        server_received.append((lce, session_id, thread_id))

    async def on_client_message(lce):
        client_received.append(lce)

    # Create server
    server = LRIWSServer(host="127.0.0.1", port=8766)
    server.on_message = on_server_message

    # Start server
    await server.start()

    try:
        # Give server time to start
        await asyncio.sleep(0.1)

        # Create and connect client
        client = LRIWSClient(
            url="ws://127.0.0.1:8766",
            encodings=["json", "cbor"],
            features=["ltp", "lss"],
            thread_id="test-thread-456",
        )

        await client.connect()

        # Verify handshake completed
        assert client.session_id is not None
        assert client.negotiated_encoding in ["json", "cbor"]
        assert len(server.sessions) == 1

        # Send message from client to server
        client_lce = LCE(
            v=1,
            intent=Intent(type="tell", goal="Test message from client"),
            policy=Policy(consent="private"),
        )
        await client.send(client_lce)

        # Give message time to arrive
        await asyncio.sleep(0.1)

        # Verify server received the message
        assert len(server_received) == 1
        received_lce, session_id, thread_id = server_received[0]
        assert received_lce.intent.goal == "Test message from client"
        assert session_id == client.session_id
        assert thread_id == "test-thread-456"

        # Send message from server to client
        server_lce = LCE(
            v=1,
            intent=Intent(type="tell", goal="Test message from server"),
            policy=Policy(consent="private"),
        )

        # Start client listener in background
        async def listen_task():
            client.on_message = on_client_message
            await client.listen()

        listener = asyncio.create_task(listen_task())

        # Send from server
        await server.send(client.session_id, server_lce)

        # Give message time to arrive
        await asyncio.sleep(0.1)

        # Verify client received the message
        assert len(client_received) == 1
        assert client_received[0].intent.goal == "Test message from server"

        # Cleanup
        listener.cancel()
        try:
            await listener
        except asyncio.CancelledError:
            pass

        await client.close()

    finally:
        # Stop server
        await server.stop()


@pytest.mark.asyncio
async def test_multiple_clients():
    """Test server handling multiple clients"""
    # Create server
    server = LRIWSServer(host="127.0.0.1", port=8767)
    await server.start()

    try:
        await asyncio.sleep(0.1)

        # Connect first client
        client1 = LRIWSClient(
            url="ws://127.0.0.1:8767", thread_id="thread-1"
        )
        await client1.connect()

        # Connect second client
        client2 = LRIWSClient(
            url="ws://127.0.0.1:8767", thread_id="thread-2"
        )
        await client2.connect()

        # Verify both sessions are active
        assert len(server.sessions) == 2
        assert client1.session_id != client2.session_id

        # Cleanup
        await client1.close()
        await client2.close()

        # Give time for sessions to cleanup
        await asyncio.sleep(0.1)

        # Verify sessions are removed
        assert len(server.sessions) == 0

    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_encoding_negotiation():
    """Test encoding negotiation in handshake"""
    server = LRIWSServer(host="127.0.0.1", port=8768, encoding="json")
    await server.start()

    try:
        await asyncio.sleep(0.1)

        # Client prefers CBOR
        client = LRIWSClient(
            url="ws://127.0.0.1:8768", encodings=["cbor", "json"]
        )
        await client.connect()

        # Server should pick the first client encoding (cbor)
        assert client.negotiated_encoding == "cbor"

        await client.close()

    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_client_without_thread_id():
    """Test client connecting without thread ID"""
    server = LRIWSServer(host="127.0.0.1", port=8769)
    await server.start()

    try:
        await asyncio.sleep(0.1)

        # Client without thread ID
        client = LRIWSClient(url="ws://127.0.0.1:8769", thread_id=None)
        await client.connect()

        # Should still complete handshake
        assert client.session_id is not None

        await client.close()

    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_send_before_connect():
    """Test sending message before connecting raises error"""
    client = LRIWSClient(url="ws://localhost:9999")

    lce = LCE(
        v=1,
        intent=Intent(type="tell"),
        policy=Policy(consent="private"),
    )

    with pytest.raises(RuntimeError, match="Not connected"):
        await client.send(lce)


@pytest.mark.asyncio
async def test_receive_before_connect():
    """Test receiving message before connecting raises error"""
    client = LRIWSClient(url="ws://localhost:9999")

    with pytest.raises(RuntimeError, match="Not connected"):
        await client.receive()


@pytest.mark.asyncio
async def test_server_send_invalid_session():
    """Test sending to invalid session raises error"""
    server = LRIWSServer(host="127.0.0.1", port=8770)
    await server.start()

    try:
        lce = LCE(
            v=1,
            intent=Intent(type="tell"),
            policy=Policy(consent="private"),
        )

        with pytest.raises(ValueError, match="Session not found"):
            await server.send("invalid-session-id", lce)

    finally:
        await server.stop()
