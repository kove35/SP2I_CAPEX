from app.workflow.engine.workflow_rules import compute_active_step, compute_next_action
from app.workflow.engine.workflow_transitions import assert_transition, can_transition
from app.workflow.schemas.workflow import WorkflowMetrics


def test_allowed_transition_sequence_accepts_next_state():
    assert can_transition("SIMULATION_COMPLETED", "ARBITRAGE_IN_PROGRESS")
    assert can_transition("ARBITRAGE_IN_PROGRESS", "ARBITRAGE_COMPLETED")


def test_invalid_transition_blocks_bypass():
    try:
        assert_transition("SIMULATION_READY", "ORDERED")
    except ValueError as exc:
        assert "Invalid workflow transition" in str(exc)
    else:
        raise AssertionError("Invalid transition should fail")


def test_next_action_after_arbitrage_completed_is_order_generation():
    action = compute_next_action("ARBITRAGE_COMPLETED", WorkflowMetrics(validated_lines=27, pending_lines=0))
    assert action.label == "Generer les commandes fournisseurs"
    assert action.route == "/app/procurement"


def test_active_step_maps_transport_state():
    assert compute_active_step("IN_TRANSIT") == "TRANSPORT"
