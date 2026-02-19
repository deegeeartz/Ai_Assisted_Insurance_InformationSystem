import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.underwriting import execute_underwriting
from app.schemas.underwrite import UnderwriteRequest, CoverageBlock
from app.models.manual import UnderwritingManual
from langchain_core.messages import AIMessage

# Mock data
MOCKED_DECISION_JSON = """
{
    "status": "approved",
    "premium_monthly": 5000,
    "premium_annual": 60000,
    "coverage_details": {"base": "covered"},
    "reason": "Meets criteria",
    "plain_english_summary": "You are approved.",
    "agent_notes": "Standard risk.",
    "sla_commitments": {"turnaround": "24h"}
}
"""

@pytest.mark.asyncio
async def test_execute_underwriting_approved():
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content=MOCKED_DECISION_JSON)
    
    with patch("app.services.underwriting.get_llm", return_value=mock_llm):
        request = UnderwriteRequest(
            age=30,
            gender="Male",
            occupation="Engineer",
            smoker=False,
            location="Lagos",
            coverage_selection=[CoverageBlock(id="1", name="Life", description="Life cover", base_price=100.0, icon="heart", enabled=True)],
            role="consumer"
        )
        manual = UnderwritingManual(compiled_rules='{"rules": []}')

        # Act
        decision = await execute_underwriting(request, manual)

        # Assert
        assert decision.status == "approved"
        assert decision.premium_monthly == 5000
        assert decision.reason == "Meets criteria"
        
        # Verify LLM was called
        mock_llm.invoke.assert_called_once()

@pytest.mark.asyncio
async def test_execute_underwriting_parsing_error():
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Invalid JSON")
    
    with patch("app.services.underwriting.get_llm", return_value=mock_llm):
        request = UnderwriteRequest(age=30, smoker=False, coverage_selection=[], role="consumer")
        manual = UnderwritingManual(compiled_rules="{}")

        # Act
        decision = await execute_underwriting(request, manual)

        # Assert
        assert decision.status == "referred"
        assert "could not parse" in decision.reason.lower()
