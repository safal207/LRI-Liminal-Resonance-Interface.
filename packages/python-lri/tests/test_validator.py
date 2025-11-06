"""
Validator tests for python-lri
"""

import pytest
from lri.validator import validate_lce


class TestValidateLCE:
    """Test validate_lce function"""

    def test_valid_minimal_lce(self):
        """Test validation of minimal LCE"""
        lce = {"v": 1, "intent": {"type": "tell"}, "policy": {"consent": "private"}}

        errors = validate_lce(lce)
        assert errors is None

    def test_valid_full_lce(self):
        """Test validation of full LCE"""
        lce = {
            "v": 1,
            "intent": {"type": "ask", "goal": "Get data"},
            "affect": {"pad": [0.5, 0.3, 0.1], "tags": ["curious"]},
            "meaning": {"topic": "weather"},
            "trust": {"proof": "proof"},
            "memory": {"thread": "uuid", "t": "2025-01-15T10:30:00Z"},
            "policy": {"consent": "team", "share": ["service-1"]},
            "qos": {"coherence": 0.9},
            "trace": {"hop": 1},
            "sig": "signature",
        }

        errors = validate_lce(lce)
        assert errors is None

    def test_all_intent_types(self):
        """Test all valid intent types"""
        intent_types = [
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

        for intent_type in intent_types:
            lce = {
                "v": 1,
                "intent": {"type": intent_type},
                "policy": {"consent": "private"},
            }
            errors = validate_lce(lce)
            assert errors is None, f"Intent type {intent_type} should be valid"

    def test_all_consent_levels(self):
        """Test all valid consent levels"""
        consent_levels = ["private", "team", "public"]

        for consent in consent_levels:
            lce = {"v": 1, "intent": {"type": "tell"}, "policy": {"consent": consent}}
            errors = validate_lce(lce)
            assert errors is None, f"Consent level {consent} should be valid"

    def test_missing_version(self):
        """Test error when version is missing"""
        lce = {"intent": {"type": "tell"}, "policy": {"consent": "private"}}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("v" in err["path"] for err in errors)

    def test_wrong_version(self):
        """Test error when version is wrong"""
        lce = {"v": 2, "intent": {"type": "tell"}, "policy": {"consent": "private"}}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("must be 1" in err["message"] for err in errors)

    def test_missing_intent(self):
        """Test error when intent is missing"""
        lce = {"v": 1, "policy": {"consent": "private"}}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("intent" in err["path"] for err in errors)

    def test_missing_intent_type(self):
        """Test error when intent type is missing"""
        lce = {"v": 1, "intent": {}, "policy": {"consent": "private"}}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("type" in err["path"] for err in errors)

    def test_invalid_intent_type(self):
        """Test error for invalid intent type"""
        lce = {
            "v": 1,
            "intent": {"type": "invalid-type"},
            "policy": {"consent": "private"},
        }

        errors = validate_lce(lce)
        assert errors is not None
        assert any("Invalid intent type" in err["message"] for err in errors)

    def test_missing_policy(self):
        """Test error when policy is missing"""
        lce = {"v": 1, "intent": {"type": "tell"}}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("policy" in err["path"] for err in errors)

    def test_missing_consent(self):
        """Test error when consent is missing"""
        lce = {"v": 1, "intent": {"type": "tell"}, "policy": {}}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("consent" in err["path"] for err in errors)

    def test_invalid_consent(self):
        """Test error for invalid consent level"""
        lce = {
            "v": 1,
            "intent": {"type": "tell"},
            "policy": {"consent": "invalid"},
        }

        errors = validate_lce(lce)
        assert errors is not None
        assert any("Invalid consent level" in err["message"] for err in errors)

    def test_invalid_pad_length(self):
        """Test error for invalid PAD array length"""
        # Too few
        lce = {
            "v": 1,
            "intent": {"type": "tell"},
            "affect": {"pad": [0.5, 0.3]},
            "policy": {"consent": "private"},
        }

        errors = validate_lce(lce)
        assert errors is not None
        assert any("PAD must be array of 3 numbers" in err["message"] for err in errors)

        # Too many
        lce["affect"]["pad"] = [0.5, 0.3, 0.1, 0.2]
        errors = validate_lce(lce)
        assert errors is not None

    def test_invalid_pad_range(self):
        """Test error for PAD values out of range"""
        lce = {
            "v": 1,
            "intent": {"type": "tell"},
            "affect": {"pad": [2.0, 0.0, 0.0]},  # Out of range
            "policy": {"consent": "private"},
        }

        errors = validate_lce(lce)
        assert errors is not None
        assert any("PAD values must be numbers in range" in err["message"] for err in errors)

    def test_invalid_coherence_range(self):
        """Test error for coherence out of range"""
        lce = {
            "v": 1,
            "intent": {"type": "tell"},
            "policy": {"consent": "private"},
            "qos": {"coherence": 1.5},  # Out of range
        }

        errors = validate_lce(lce)
        assert errors is not None
        assert any("Coherence must be number in range" in err["message"] for err in errors)

    def test_intent_not_object(self):
        """Test error when intent is not an object"""
        lce = {"v": 1, "intent": "not-an-object", "policy": {"consent": "private"}}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("Intent must be an object" in err["message"] for err in errors)

    def test_policy_not_object(self):
        """Test error when policy is not an object"""
        lce = {"v": 1, "intent": {"type": "tell"}, "policy": "not-an-object"}

        errors = validate_lce(lce)
        assert errors is not None
        assert any("Policy must be an object" in err["message"] for err in errors)
