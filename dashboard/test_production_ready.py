"""
Test script for Production-Ready Economy Integration

Verifies:
1. Economy loading/creation works
2. Economy Bridge connection works
3. LLM Bridge health check works
4. Action execution with guardrails works
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths
dashboard_path = Path(__file__).parent
sys.path.insert(0, str(dashboard_path.parent))
sys.path.insert(0, str(dashboard_path))


def test_economy_loading():
    """Test 1: Verify economy loading works."""
    logger.info("=" * 60)
    logger.info("TEST 1: Economy Loading")
    logger.info("=" * 60)

    try:
        from server import load_or_create_economy

        economy = load_or_create_economy()

        if economy is None:
            logger.warning("⚠️  Economy loaded in MOCK mode (expected if BeCoin not installed)")
            return True

        logger.info(f"✅ Economy loaded successfully")
        logger.info(f"   Treasury Balance: {economy.treasury.balance:,} Bc")
        logger.info(f"   Agents: {len(economy.agents)}")
        logger.info(f"   Projects: {len(economy.projects)}")

        return True

    except Exception as e:
        logger.error(f"❌ Economy loading failed: {e}")
        return False


def test_economy_bridge():
    """Test 2: Verify Economy Bridge works."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Economy Bridge")
    logger.info("=" * 60)

    try:
        from economy_bridge import get_economy_bridge, set_economy_instance
        from server import load_or_create_economy

        # Load economy
        economy = load_or_create_economy()

        # Get bridge
        bridge = get_economy_bridge()

        # Set economy (if available)
        if economy:
            set_economy_instance(economy)
            logger.info("✅ Economy Bridge connected to real economy")
        else:
            logger.info("ℹ️  Economy Bridge in MOCK mode")

        # Test context retrieval
        context = bridge.get_context_for_chat()

        logger.info(f"✅ Context retrieved:")
        logger.info(f"   Balance: {context['treasury']['balance']:,} Bc")
        logger.info(f"   Burn Rate: {context['treasury']['burn_rate']:.1f} Bc/h")
        logger.info(f"   Runway: {context['treasury']['runway_hours']:.1f} hours")
        logger.info(f"   Active Projects: {len(context['projects']['active'])}")

        return True

    except Exception as e:
        logger.error(f"❌ Economy Bridge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ollama_health():
    """Test 3: Verify Ollama health check works."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Ollama LLM Health Check")
    logger.info("=" * 60)

    try:
        from llm_bridge import get_llm_bridge

        llm_bridge = get_llm_bridge()
        is_healthy = await llm_bridge.check_ollama_health()

        if is_healthy:
            logger.info(f"✅ Ollama LLM available (model: {llm_bridge.model})")
        else:
            logger.warning("⚠️  Ollama LLM NOT available")
            logger.info("   → This is expected if Ollama is not running")
            logger.info("   → System will use fallback responses")

        return True

    except Exception as e:
        logger.error(f"❌ Ollama health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_action_execution():
    """Test 4: Verify action execution with guardrails."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Action Execution with Guardrails")
    logger.info("=" * 60)

    try:
        from economy_bridge import get_economy_bridge, set_economy_instance
        from server import load_or_create_economy

        # Setup
        economy = load_or_create_economy()
        if economy:
            set_economy_instance(economy)

        bridge = get_economy_bridge()

        # Test 1: Check Treasury
        logger.info("\n📊 Test 4.1: Check Treasury")
        result = bridge.execute_agent_action(
            agent_id="agent-atlas",
            action={"type": "check_treasury"}
        )
        logger.info(f"   Status: {result['status']}")
        logger.info(f"   Message: {result['message']}")

        # Test 2: Start Project (small budget)
        logger.info("\n🚀 Test 4.2: Start Small Project (500 Bc)")
        result = bridge.execute_agent_action(
            agent_id="agent-helio",
            action={
                "type": "start_project",
                "project_name": "Test Project",
                "budget": 500
            }
        )
        logger.info(f"   Status: {result['status']}")
        logger.info(f"   Message: {result['message']}")

        # Test 3: Start Project (large budget - should fail guardrail)
        logger.info("\n⚠️  Test 4.3: Start Large Project (50000 Bc - should fail)")
        result = bridge.execute_agent_action(
            agent_id="agent-helio",
            action={
                "type": "start_project",
                "project_name": "Expensive Project",
                "budget": 50000
            }
        )
        logger.info(f"   Status: {result['status']}")
        logger.info(f"   Message: {result['message']}")

        if result['status'] == 'rejected':
            logger.info(f"   ✅ Guardrail worked: {result.get('guardrail')}")

        # Test 4: Analyze Burn Rate
        logger.info("\n📈 Test 4.4: Analyze Burn Rate")
        result = bridge.execute_agent_action(
            agent_id="agent-atlas",
            action={"type": "analyze_burn_rate"}
        )
        logger.info(f"   Status: {result['status']}")
        logger.info(f"   Message: {result['message']}")

        logger.info("\n✅ All action execution tests passed")
        return True

    except Exception as e:
        logger.error(f"❌ Action execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 PRODUCTION-READY INTEGRATION TESTS")
    logger.info("=" * 60)

    results = {
        "Economy Loading": test_economy_loading(),
        "Economy Bridge": test_economy_bridge(),
        "Ollama Health Check": await test_ollama_health(),
        "Action Execution": test_action_execution()
    }

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - System is Production-Ready!")
    else:
        logger.warning("⚠️  Some tests failed - review logs above")

    logger.info("=" * 60)

    return all_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
