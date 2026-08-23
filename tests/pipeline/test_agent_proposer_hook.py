"""
DN CLASSIC — Agent Proposer Hook Test Suite.
Verifies interaction between external agent proposer functions and DN CLASSIC.
"""
from typing import List
from upstream_types import StructureRecord, ProposalSet, AgentProposal, GuardStatus
from upstream_stages import validate_proposal_guard
from upstream_pipeline import default_proposer_hook
from contracts import (
    SemanticMode,
    LifecycleStatus,
    GroundingStatus,
    EpistemicUncertainty,
    SourceSpan,
)


def test_default_proposer_hook():
    records = [
        StructureRecord(
            document_id="doc1.txt",
            text="Hello World",
            normalized_text="Hello World",
            source_hash="h1",
        )
    ]
    props = default_proposer_hook(records)
    assert isinstance(props, ProposalSet)
    assert len(props.proposals) == 1
    p = props.proposals[0]
    assert p.document_id == "doc1.txt"
    assert p.semantic_mode == SemanticMode.CLAIM
    assert len(p.source_spans) == 1
    assert p.source_spans[0].text == "Hello World"


def test_custom_proposer_hook_valid():
    def custom_agent(records: List[StructureRecord]) -> ProposalSet:
        proposals = []
        for r in records:
            # Agent finds the word 'World' at [6:11]
            idx = r.normalized_text.find("World")
            if idx != -1:
                span = SourceSpan(
                    span_id="span-world",
                    text="World",
                    start=idx,
                    end=idx + len("World"),
                )
                proposals.append(
                    AgentProposal(
                        document_id=r.document_id,
                        target_entity_id="entity-world",
                        semantic_mode=SemanticMode.CLAIM,
                        lifecycle_status=LifecycleStatus.ACTIVE,
                        grounding_status=GroundingStatus.GROUNDED_SOURCE_CLAIM,
                        epistemic_uncertainty=EpistemicUncertainty.CLEAR,
                        source_spans=[span],
                    )
                )
        return ProposalSet(proposals=proposals, agent_id="custom-agent-v1")

    records = [
        StructureRecord(
            document_id="sample.txt",
            text="Hello World",
            normalized_text="Hello World",
            source_hash="h1",
        )
    ]
    
    props = custom_agent(records)
    assert len(props.proposals) == 1
    val = validate_proposal_guard(props.proposals[0], records[0])
    assert val.status == GuardStatus.ACCEPT
    assert val.verified_spans[0].text == "World"


def test_custom_proposer_hook_invalid_span_caught():
    def hallucinating_agent(records: List[StructureRecord]) -> ProposalSet:
        return ProposalSet(
            proposals=[
                AgentProposal(
                    document_id=records[0].document_id,
                    source_spans=[
                        SourceSpan(
                            span_id="fake",
                            text="This sentence does not exist",
                            start=0,
                            end=28,
                        )
                    ],
                )
            ]
        )

    records = [
        StructureRecord(
            document_id="sample.txt",
            text="Real source content",
            normalized_text="Real source content",
            source_hash="h1",
        )
    ]
    props = hallucinating_agent(records)
    val = validate_proposal_guard(props.proposals[0], records[0])
    assert val.status == GuardStatus.REJECT
    assert "Grounding failure" in val.reason
