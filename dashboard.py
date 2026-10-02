"""Painel Streamlit interno para operação e auditoria da modernização."""

from __future__ import annotations

import os
from typing import Any

import psycopg
import requests
import streamlit as st
from psycopg.rows import dict_row

API_URL = os.getenv("PIPELINE_API_URL", "http://localhost:8000").rstrip("/")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:55432/modernization",
)
REQUEST_TIMEOUT_SECONDS = float(os.getenv("DASHBOARD_REQUEST_TIMEOUT_SECONDS", "30"))


def _api_url(path: str) -> str:
    return f"{API_URL}{path}"


def _request_json(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    """Call FastAPI and return JSON, preserving useful HTTP error details."""

    response = requests.request(
        method,
        _api_url(path),
        timeout=REQUEST_TIMEOUT_SECONDS,
        **kwargs,
    )
    try:
        body = response.json()
    except ValueError:
        body = {"message": response.text or "Resposta não JSON"}
    if not response.ok:
        detail = body.get("message") if isinstance(body, dict) else str(body)
        raise requests.HTTPError(f"HTTP {response.status_code}: {detail}", response=response)
    if not isinstance(body, dict):
        raise requests.RequestException("A API retornou um JSON inesperado")
    return body


def modernize(source_code: str, provider: str) -> dict[str, Any]:
    return _request_json(
        "POST",
        "/modernize",
        json={"source_code": source_code, "provider": provider},
    )


def fetch_metrics() -> dict[str, Any]:
    return _request_json("GET", "/evaluation")


def _read_history(status: str) -> list[dict[str, Any]]:
    """Read a small, recent audit window without loading the whole source code."""

    query = """
        SELECT id, status, created_at,
               report->>'generation_mode' AS generation_mode,
               report->'errors' AS errors,
               report
          FROM modernization_history
         WHERE (%s = 'all' OR status = %s)
         ORDER BY created_at DESC, id DESC
         LIMIT 100
    """
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as connection, connection.cursor() as cursor:
        cursor.execute(query, (status, status))
        return list(cursor.fetchall())


def _render_submission_tab() -> None:
    st.subheader("Submissão e teste")
    st.caption(f"Backend configurado em: `{API_URL}`")
    source_code = st.text_area(
        "Cole aqui a rotina PL/pgSQL legado",
        height=360,
        placeholder="CREATE OR REPLACE FUNCTION ...",
    )
    provider = st.selectbox("Provedor da LLM", ["gemini", "openrouter"])

    if st.button("Executar Modernização", type="primary"):
        if not source_code.strip():
            st.warning("Informe o código PL/pgSQL antes de executar.")
            return
        with st.spinner("Executando pipeline..."):
            try:
                result = modernize(source_code, provider)
            except requests.ConnectionError:
                st.error(f"Não foi possível conectar à API em {API_URL}.")
            except requests.Timeout:
                st.error("A API excedeu o tempo limite de resposta.")
            except requests.HTTPError as exc:
                st.error(f"A API recusou a execução: {exc}")
            except requests.RequestException as exc:
                st.error(f"Erro de comunicação com a API: {exc}")
            else:
                st.session_state["last_modernization"] = result

    result = st.session_state.get("last_modernization")
    if result:
        status = result.get("status", "unknown")
        st.write(f"Status: **{status}** · Run ID: **{result.get('run_id', 'n/a')}**")
        if result.get("generated_code"):
            st.code(result["generated_code"], language="python")
        st.json(result.get("report", result))


def _render_metrics_tab() -> None:
    st.subheader("Métricas de evaluation")
    should_refresh = st.button("Atualizar Métricas")
    if should_refresh or "metrics" not in st.session_state:
        try:
            st.session_state["metrics"] = fetch_metrics()
        except requests.ConnectionError:
            st.error(f"Não foi possível conectar à API em {API_URL}.")
            return
        except requests.RequestException as exc:
            st.error(f"Falha ao consultar métricas: {exc}")
            return

    payload = st.session_state.get("metrics", {})
    metrics = payload.get("metrics", {})
    failures = metrics.get("failures_by_stage", {})
    total = int(metrics.get("total_runs", 0))
    first_pass = int(metrics.get("first_attempt_static_approval", 0))
    repaired_pass = int(metrics.get("after_repair_static_approval", 0))
    passed = first_pass + repaired_pass
    success_rate = (passed / total * 100) if total else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Denominador", total)
    col2.metric("Passaram na validação", passed)
    col3.metric("Falharam no parsing", int(failures.get("parsing", 0)))
    col4.metric("Falharam na validação", int(failures.get("validation", 0)))
    st.metric("Taxa de aprovação estática", f"{success_rate:.1f}%")

    st.bar_chart(
        {
            "Execuções": {
                "Aprovadas": passed,
                "Parsing": int(failures.get("parsing", 0)),
                "Validação": int(failures.get("validation", 0)),
                "Geração": int(failures.get("generation", 0)),
                "Reparo": int(failures.get("repair", 0)),
            }
        }
    )
    st.caption(
        "O denominador inclui todas as execuções terminais. Falhas por etapa são "
        "contagens de eventos e podem se sobrepor na mesma execução."
    )
    if payload.get("limitations"):
        with st.expander("Limitações declaradas pela API"):
            st.write(payload["limitations"])


def _render_audit_tab() -> None:
    st.subheader("Auditoria e histórico")
    filter_label = st.selectbox(
        "Filtrar registros",
        ["Todos", "Falhas (failure)", "Sucesso", "Parcial", "Pendente"],
    )
    status = {
        "Todos": "all",
        "Falhas (failure)": "failure",
        "Sucesso": "success",
        "Parcial": "partial",
        "Pendente": "pending",
    }[filter_label]
    try:
        rows = _read_history(status)
    except psycopg.OperationalError:
        st.error("Não foi possível conectar ao PostgreSQL para consultar o histórico.")
        return
    except psycopg.Error as exc:
        st.error(f"Erro ao consultar modernization_history: {exc}")
        return

    if not rows:
        st.info("Nenhum registro encontrado para este filtro.")
        return

    table_rows = [
        {
            "id": row["id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "generation_mode": row["generation_mode"],
        }
        for row in rows
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        "Selecione um registro para ver os detalhes",
        [row["id"] for row in rows],
        format_func=lambda run_id: f"run_id={run_id}",
    )
    selected = next(row for row in rows if row["id"] == selected_id)
    report = selected.get("report") or {}
    errors = report.get("errors") or []
    failed_nodes = sorted(
        {error.get("stage") for error in errors if isinstance(error, dict) and error.get("stage")}
    )
    if failed_nodes:
        st.error(f"Nós com erro: {', '.join(failed_nodes)}")
    else:
        st.info("Este registro não possui erro de etapa declarado.")
    with st.expander("Relatório JSONB completo", expanded=True):
        st.json(report)
    if errors:
        with st.expander("Erros detalhados"):
            st.json(errors)


def main() -> None:
    st.set_page_config(page_title="SQL → Python | Operação", page_icon="🔎", layout="wide")
    st.title("Pipeline SQL → Python")
    st.caption("Painel interno de operação, avaliação e auditoria Human-in-the-loop")

    submission_tab, metrics_tab, audit_tab = st.tabs(
        ["Submissão e Teste", "Métricas (Evaluation)", "Auditoria (Histórico)"]
    )
    with submission_tab:
        _render_submission_tab()
    with metrics_tab:
        _render_metrics_tab()
    with audit_tab:
        _render_audit_tab()


if __name__ == "__main__":
    main()
