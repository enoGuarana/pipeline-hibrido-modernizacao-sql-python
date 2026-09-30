"""Grafo mínimo tipado; os nós são contratos para a próxima fatia de implementação."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from .state import PipelineState


def parse_node(state: PipelineState) -> dict[str, Any]:
    raise NotImplementedError("Parsing ainda não implementado")


def semantic_analysis_node(state: PipelineState) -> dict[str, Any]:
    raise NotImplementedError("Análise semântica ainda não implementada")


def generation_node(state: PipelineState) -> dict[str, Any]:
    raise NotImplementedError("Geração ainda não implementada")


def validation_node(state: PipelineState) -> dict[str, Any]:
    raise NotImplementedError("Validação ainda não implementada")


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("parsing", parse_node)
    graph.add_node("semantic_analysis", semantic_analysis_node)
    graph.add_node("generation", generation_node)
    graph.add_node("validation", validation_node)
    graph.add_edge(START, "parsing")
    graph.add_edge("parsing", "semantic_analysis")
    graph.add_edge("semantic_analysis", "generation")
    graph.add_edge("generation", "validation")
    graph.add_edge("validation", END)
    return graph.compile()

