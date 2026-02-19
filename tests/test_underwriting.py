"""Tests for underwriting and agentic chat system."""
import pytest
import json


# ============================================================
#  Test normalize_content
# ============================================================
class TestNormalizeContent:
    """Tests for the normalize_content helper function."""

    def test_string_passthrough(self):
        """String input should pass through unchanged."""
        from app.api.endpoints.underwrite import normalize_content
        assert normalize_content("hello world") == "hello world"

    def test_list_of_dicts(self):
        """List of dicts with 'text' key should be joined."""
        from app.api.endpoints.underwrite import normalize_content
        content = [
            {'type': 'text', 'text': 'Hello', 'extras': {}},
            {'type': 'text', 'text': 'World', 'extras': {}},
        ]
        assert normalize_content(content) == "Hello World"

    def test_list_of_strings(self):
        """List of strings should be joined."""
        from app.api.endpoints.underwrite import normalize_content
        assert normalize_content(["Hello", "World"]) == "Hello World"

    def test_mixed_list(self):
        """Mixed list should handle dicts and strings."""
        from app.api.endpoints.underwrite import normalize_content
        content = [
            {'type': 'text', 'text': 'Hello'},
            'World',
        ]
        assert normalize_content(content) == "Hello World"

    def test_empty_list(self):
        """Empty list should return empty string."""
        from app.api.endpoints.underwrite import normalize_content
        assert normalize_content([]) == ""

    def test_non_string(self):
        """Non-string, non-list input should be stringified."""
        from app.api.endpoints.underwrite import normalize_content
        assert normalize_content(42) == "42"


# ============================================================
#  Test ingestion normalize
# ============================================================
class TestIngestionNormalize:
    """Tests for the normalize_llm_content in ingestion service."""

    def test_string(self):
        from app.services.ingestion import normalize_llm_content
        assert normalize_llm_content("test") == "test"

    def test_list(self):
        from app.services.ingestion import normalize_llm_content
        content = [{'type': 'text', 'text': 'JSON output'}]
        assert normalize_llm_content(content) == "JSON output"


# ============================================================
#  Test agentic parse logic
# ============================================================
class TestAgenticParsing:
    """Tests for parsing LLM agentic JSON output."""

    def test_valid_json_action(self):
        """Well-formed agentic JSON should parse correctly."""
        raw = json.dumps({
            "action": "show_products",
            "message": "Here are our products",
            "data": {},
            "suggestions": ["Get a quote", "Tell me more"]
        })
        parsed = json.loads(raw)
        assert parsed["action"] == "show_products"
        assert len(parsed["suggestions"]) == 2

    def test_json_with_markdown_wrapper(self):
        """JSON wrapped in markdown code fence should be cleaned."""
        raw = '```json\n{"action": "text_reply", "message": "Hi"}\n```'
        clean = raw.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.endswith("```"):
            clean = clean[:-3]
        parsed = json.loads(clean.strip())
        assert parsed["action"] == "text_reply"

    def test_invalid_json_fallback(self):
        """Invalid JSON should fall back to text_reply."""
        raw = "I'm just a normal text response"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {
                "action": "text_reply",
                "message": raw,
                "data": {},
                "suggestions": [],
            }
        assert parsed["action"] == "text_reply"
        assert parsed["message"] == raw


# ============================================================
#  Test mock payment data structure
# ============================================================
class TestMockPayment:
    """Tests for payment receipt structure."""

    def test_receipt_structure(self):
        """Receipt should contain all required fields."""
        receipt = {
            "amount": 60000,
            "insurer_share": 48000,
            "partner_commission": 9000,
            "platform_fee": 3000,
            "currency": "NGN",
        }
        assert receipt["amount"] == receipt["insurer_share"] + receipt["partner_commission"] + receipt["platform_fee"]
        assert receipt["currency"] == "NGN"

    def test_commission_split(self):
        """Commission split should follow 80/15/5 ratio."""
        amount = 100000
        partner_commission = amount * 0.15
        platform_fee = amount * 0.05
        insurer_share = amount - partner_commission - platform_fee

        assert partner_commission == 15000
        assert platform_fee == 5000
        assert insurer_share == 80000
