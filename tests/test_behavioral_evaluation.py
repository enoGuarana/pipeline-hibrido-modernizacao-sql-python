from decimal import Decimal

from pipeline.behavioral_evaluation import BehavioralObservation, compare_observations


def test_equal_observations_preserve_decimal_and_declared_volatile_fields():
    legacy = BehavioralObservation(
        return_value=Decimal("10.20"),
        table_state={"log_auditoria": {"id": 10, "criado_em": "2026-10-01T10:00:00"}},
    )
    translated = BehavioralObservation(
        return_value=Decimal("10.20"),
        table_state={"log_auditoria": {"id": 99, "criado_em": "2026-10-01T10:01:00"}},
    )

    result = compare_observations(
        legacy,
        translated,
        volatile_paths={"$.state.log_auditoria.id", "$.state.log_auditoria.criado_em"},
    )

    assert result.equivalent is True
    assert result.differences == ()
    assert result.normalized_paths == (
        "$.state.log_auditoria.criado_em",
        "$.state.log_auditoria.id",
    )


def test_undeclared_state_difference_is_not_hidden():
    legacy = BehavioralObservation(return_value=[{"id": 1}], table_state={"contas": {"saldo": "10.00"}})
    translated = BehavioralObservation(return_value=[{"id": 1}], table_state={"contas": {"saldo": "9.00"}})

    result = compare_observations(legacy, translated)

    assert result.equivalent is False
    assert "legacy=" in result.differences[0]
