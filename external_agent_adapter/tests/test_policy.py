import pytest

from external_agent_adapter import AgentExecutionPolicy, PolicyError


def test_default_policy_is_conservative_and_immutable():
    policy = AgentExecutionPolicy()

    assert policy.allowed_operations == frozenset()
    assert not policy.permits("status")
    with pytest.raises(PolicyError):
        policy.require("status")
    with pytest.raises(AttributeError):
        policy.allowed_operations.add("status")


def test_explicit_read_permission_allows_only_reads():
    policy = AgentExecutionPolicy.read_only()

    assert policy.permits("status")
    assert policy.permits("get_storage")
    assert not policy.permits("set_storage")


def test_explicit_mutation_and_storage_delete_permissions():
    policy = AgentExecutionPolicy.explicit(
        {"create_investigation", "update_investigation", "set_storage", "delete_storage"}
    )

    for operation in policy.MUTATING_OPERATIONS:
        assert policy.permits(operation)


def test_unknown_and_investigation_delete_operations_are_rejected():
    with pytest.raises(ValueError, match="Unknown"):
        AgentExecutionPolicy.explicit({"restart_system"})
    with pytest.raises(ValueError, match="Unknown"):
        AgentExecutionPolicy.explicit({"delete_investigation"})
    with pytest.raises(ValueError, match="Unknown"):
        AgentExecutionPolicy().require("delete_investigation")


def test_policy_decisions_are_deterministic_and_side_effect_free():
    policy = AgentExecutionPolicy.explicit({"status"})

    assert policy.permits("status") is True
    assert policy.permits("status") is True
    assert policy.allowed_operations == frozenset({"status"})