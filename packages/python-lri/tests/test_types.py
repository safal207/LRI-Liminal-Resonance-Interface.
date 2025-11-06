"""
Type/Model tests for python-lri
"""

import pytest
from pydantic import ValidationError

from lri.types import (
    LCE,
    Intent,
    Affect,
    Meaning,
    Trust,
    Memory,
    Policy,
    QoS,
    Trace,
)


class TestIntent:
    """Test Intent model"""

    def test_minimal_intent(self):
        """Test minimal intent with just type"""
        intent = Intent(type="tell")
        assert intent.type == "tell"
        assert intent.goal is None

    def test_intent_with_goal(self):
        """Test intent with goal"""
        intent = Intent(type="ask", goal="Get weather")
        assert intent.type == "ask"
        assert intent.goal == "Get weather"

    def test_all_intent_types(self):
        """Test all valid intent types"""
        valid_types = [
            "ask",
            "tell",
            "propose",
            "confirm",
            "notify",
            "sync",
            "plan",
            "agree",
            "disagree",
            "reflect",
        ]

        for intent_type in valid_types:
            intent = Intent(type=intent_type)
            assert intent.type == intent_type

    def test_invalid_intent_type(self):
        """Test invalid intent type raises error"""
        with pytest.raises(ValidationError):
            Intent(type="invalid")


class TestAffect:
    """Test Affect model"""

    def test_affect_with_pad(self):
        """Test affect with PAD values"""
        affect = Affect(pad=(0.5, 0.3, 0.1))
        assert affect.pad == (0.5, 0.3, 0.1)

    def test_affect_with_tags(self):
        """Test affect with tags"""
        affect = Affect(tags=["curious", "casual"])
        assert affect.tags == ["curious", "casual"]

    def test_affect_full(self):
        """Test affect with both PAD and tags"""
        affect = Affect(pad=(0.3, 0.2, 0.1), tags=["analytical"])
        assert affect.pad == (0.3, 0.2, 0.1)
        assert affect.tags == ["analytical"]

    def test_pad_validation_length(self):
        """Test PAD array must have exactly 3 values"""
        with pytest.raises(ValidationError):
            Affect(pad=(0.5, 0.3))  # Only 2 values

        with pytest.raises(ValidationError):
            Affect(pad=(0.5, 0.3, 0.1, 0.2))  # 4 values

    def test_pad_validation_range(self):
        """Test PAD values must be in [-1, 1]"""
        with pytest.raises(ValidationError):
            Affect(pad=(2.0, 0.0, 0.0))  # Out of range

        with pytest.raises(ValidationError):
            Affect(pad=(0.0, -1.5, 0.0))  # Out of range


class TestPolicy:
    """Test Policy model"""

    def test_minimal_policy(self):
        """Test minimal policy with just consent"""
        policy = Policy(consent="private")
        assert policy.consent == "private"

    def test_all_consent_levels(self):
        """Test all valid consent levels"""
        levels = ["private", "team", "public"]

        for level in levels:
            policy = Policy(consent=level)
            assert policy.consent == level

    def test_policy_with_share(self):
        """Test policy with share list"""
        policy = Policy(consent="team", share=["service-1", "service-2"])
        assert policy.share == ["service-1", "service-2"]

    def test_policy_with_dp(self):
        """Test policy with DP parameters"""
        policy = Policy(consent="public", dp="epsilon=1.0")
        assert policy.dp == "epsilon=1.0"

    def test_invalid_consent(self):
        """Test invalid consent level raises error"""
        with pytest.raises(ValidationError):
            Policy(consent="invalid")


class TestQoS:
    """Test QoS model"""

    def test_qos_with_coherence(self):
        """Test QoS with coherence score"""
        qos = QoS(coherence=0.87)
        assert qos.coherence == 0.87

    def test_coherence_range(self):
        """Test coherence must be in [0, 1]"""
        # Valid
        qos = QoS(coherence=0.0)
        assert qos.coherence == 0.0

        qos = QoS(coherence=1.0)
        assert qos.coherence == 1.0

        # Invalid
        with pytest.raises(ValidationError):
            QoS(coherence=-0.1)

        with pytest.raises(ValidationError):
            QoS(coherence=1.5)


class TestLCE:
    """Test LCE model"""

    def test_minimal_lce(self):
        """Test minimal valid LCE"""
        lce = LCE(
            v=1, intent=Intent(type="tell"), policy=Policy(consent="private")
        )

        assert lce.v == 1
        assert lce.intent.type == "tell"
        assert lce.policy.consent == "private"

    def test_full_lce(self):
        """Test LCE with all fields"""
        lce = LCE(
            v=1,
            intent=Intent(type="ask", goal="Get weather"),
            affect=Affect(pad=(0.3, 0.2, 0.1), tags=["curious"]),
            meaning=Meaning(topic="weather", ontology="https://schema.org/WeatherForecast"),
            trust=Trust(proof="test-proof", attest=["attestation"]),
            memory=Memory(
                thread="550e8400-e29b-41d4-a716-446655440000",
                t="2025-01-15T10:30:00Z",
                ttl="PT1H",
            ),
            policy=Policy(consent="team", share=["service-1"], dp="epsilon=1.0"),
            qos=QoS(coherence=0.87, stability="high"),
            trace=Trace(hop=2, provenance=["client", "gateway"]),
            sig="test-signature",
        )

        assert lce.v == 1
        assert lce.intent.type == "ask"
        assert lce.affect.pad == (0.3, 0.2, 0.1)
        assert lce.policy.consent == "team"
        assert lce.qos.coherence == 0.87

    def test_lce_version_defaults_to_1(self):
        """Test LCE version defaults to 1 if not provided"""
        lce = LCE(intent=Intent(type="tell"), policy=Policy(consent="private"))
        assert lce.v == 1

    def test_lce_missing_intent(self):
        """Test LCE validation fails without intent"""
        with pytest.raises(ValidationError):
            LCE(v=1, policy=Policy(consent="private"))

    def test_lce_missing_policy(self):
        """Test LCE validation fails without policy"""
        with pytest.raises(ValidationError):
            LCE(v=1, intent=Intent(type="tell"))

    def test_lce_wrong_version(self):
        """Test LCE validation fails with wrong version"""
        with pytest.raises(ValidationError):
            LCE(
                v=2,  # Only v=1 is valid
                intent=Intent(type="tell"),
                policy=Policy(consent="private"),
            )

    def test_lce_extra_fields_forbidden(self):
        """Test LCE forbids extra fields"""
        with pytest.raises(ValidationError):
            LCE(
                v=1,
                intent=Intent(type="tell"),
                policy=Policy(consent="private"),
                extra_field="not-allowed",
            )

    def test_lce_serialization(self):
        """Test LCE can be serialized to JSON"""
        lce = LCE(
            v=1, intent=Intent(type="tell"), policy=Policy(consent="private")
        )

        json_str = lce.model_dump_json()
        assert '"v":1' in json_str
        assert '"type":"tell"' in json_str

    def test_lce_deserialization(self):
        """Test LCE can be deserialized from dict"""
        data = {"v": 1, "intent": {"type": "ask"}, "policy": {"consent": "private"}}

        lce = LCE.model_validate(data)
        assert lce.v == 1
        assert lce.intent.type == "ask"

    def test_lce_exclude_none(self):
        """Test LCE serialization excludes None values"""
        lce = LCE(
            v=1, intent=Intent(type="tell"), policy=Policy(consent="private")
        )

        dumped = lce.model_dump(exclude_none=True)
        assert "affect" not in dumped
        assert "meaning" not in dumped
        assert "qos" not in dumped
