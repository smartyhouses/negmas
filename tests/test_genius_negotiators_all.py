import os
from pathlib import Path
import hypothesis.strategies as st
import pkg_resources
import pytest
from hypothesis import given, settings
from py4j.protocol import Py4JNetworkError

from negmas.genius.ginfo import ALL_PASSING_NEGOTIATORS as ALL_NEGOTIATORS
from negmas import (
    Simpatico,
    GeniusNegotiator,
    AspirationNegotiator,
    outcome_as_tuple,
    genius_bridge_is_running,
    load_genius_domain_from_folder,
    TheFawkes,
    Gangster,
    AgentK,
    Yushu,
    Nozomi,
    IAMhaggler,
    AgentX,
    YXAgent,
    Caduceus,
    ParsCat,
    ParsAgent,
    PonPokoAgent,
    RandomDance,
    BetaOne,
    MengWan,
    AgreeableAgent2018,
    Rubick,
    CaduceusDC16,
    Terra,
    AgentHP2,
    GrandmaAgent,
    Ngent,
    Atlas32016,
    MyAgent,
    Farma,
    PokerFace,
    XianFaAgent,
    PhoenixParty,
    AgentBuyong,
    Kawaii,
    Atlas3,
    AgentYK,
    KGAgent,
    E2Agent,
    Group2,
    WhaleAgent,
    DoNA,
    AgentM,
    TMFAgent,
    MetaAgent,
    TheNegotiatorReloaded,
    OMACagent,
    AgentLG,
    CUHKAgent,
    ValueModelAgent,
    NiceTitForTat,
    TheNegotiator,
    AgentK2,
    BRAMAgent,
    IAMhaggler2011,
    Gahboninho,
    HardHeaded,
)
from negmas.genius import GeniusBridge
from negmas.genius import get_genius_agents

TIMELIMIT = 30
STEPLIMIT = 50

AGENTS_WITH_NO_AGREEMENT_ON_SAME_UFUN = tuple()

SKIP_CONDITION = os.environ["NEGMAS_LONG_TEST"]


def do_test_genius_agent(
    AgentClass, must_agree_if_same_ufun=True, java_class_name=None
):
    if java_class_name is not None:
        AgentClass = lambda *args, **kwargs: GeniusNegotiator(
            *args, java_class_name=java_class_name, **kwargs
        )
        agent_class_name = java_class_name
    else:
        agent_class_name = AgentClass.__name__
    # print(f"Running {AgentClass.__name__}")
    base_folder = pkg_resources.resource_filename(
        "negmas", resource_name="tests/data/Laptop"
    )

    def do_run(
        opponent_ufun,
        agent_ufun,
        agent_starts,
        opponent_type=AspirationNegotiator,
        n_steps=None,
        time_limit=TIMELIMIT,
        outcome_type=dict,
        must_agree_if_same_ufun=True,
    ):
        neg, agent_info, issues = load_genius_domain_from_folder(
            base_folder,
            keep_issue_names=outcome_type == dict,
            keep_value_names=outcome_type == dict,
            time_limit=time_limit,
            n_steps=n_steps,
            outcome_type=outcome_type,
        )
        neg._avoid_ultimatum = False
        if neg is None:
            raise ValueError(f"Failed to load domain from {base_folder}")
        if isinstance(opponent_type, GeniusNegotiator):
            opponent = opponent_type(
                ufun=agent_info[opponent_ufun]["ufun"],
                keep_issue_names=outcome_type == dict,
                keep_issue_values=outcome_type == dict,
            )
        else:
            opponent = opponent_type(ufun=agent_info[opponent_ufun]["ufun"])
        theagent = AgentClass(ufun=agent_info[agent_ufun]["ufun"])
        if agent_starts:
            neg.add(theagent)
            neg.add(opponent)
        else:
            neg.add(opponent)
            neg.add(theagent)
        return neg.run()

    # check that it can run without errors with two different ufuns
    for outcome_type in (tuple, dict):
        for opponent_type in (AspirationNegotiator, Atlas3):
            for starts in (False, True):
                for n_steps, time_limit in ((STEPLIMIT, None), (None, TIMELIMIT)):
                    for ufuns in ((1, 0), (0, 1)):
                        try:
                            result = do_run(
                                ufuns[0],
                                ufuns[1],
                                starts,
                                opponent_type,
                                n_steps=n_steps,
                                time_limit=time_limit,
                                outcome_type=outcome_type,
                            )
                            # print(
                            #     f"{AgentClass.__name__} SUCCEEDED against {opponent_type.__name__}"
                            #     f" going {'first' if starts else 'last'} ({n_steps} steps with "
                            #     f"{time_limit} limit taking ufun {ufuns[1]} type {outcome_type}) getting {str(result)}."
                            # )
                        except Exception as e:
                            print(
                                f"{agent_class_name} FAILED against {opponent_type.__name__}"
                                f" going {'first' if starts else 'last'} ({n_steps} steps with "
                                f"{time_limit} limit taking ufun {ufuns[1]} type {outcome_type})."
                            )
                            raise e

    if not must_agree_if_same_ufun or (
        java_class_name is None and AgentClass in AGENTS_WITH_NO_AGREEMENT_ON_SAME_UFUN
    ):
        return

    # check that it will get to an agreement sometimes if the same ufun
    # is used for both agents
    from random import randint

    n_trials = 3
    for starts in (False, True):
        for _ in range(n_trials):
            indx = randint(0, 1)
            neg = do_run(indx, indx, starts)
            if neg.agreement is not None:
                break
        else:
            assert (
                False
            ), f"{agent_class_name}: failed to get an agreement in {n_trials} trials even using the same ufun"

    GeniusBridge.clean()


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
@pytest.mark.parametrize("negotiator", ALL_NEGOTIATORS)
def test_all_negotiators(negotiator):
    do_test_genius_agent(None, java_class_name=negotiator)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentX():
    do_test_genius_agent(AgentX)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_YXAgent():
    do_test_genius_agent(YXAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Caduceus():
    do_test_genius_agent(Caduceus)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_ParsCat():
    do_test_genius_agent(ParsCat)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_ParsAgent():
    do_test_genius_agent(ParsAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_PonPokoAgent():
    do_test_genius_agent(PonPokoAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_RandomDance():
    do_test_genius_agent(RandomDance)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_GrandmaAgent():
    do_test_genius_agent(GrandmaAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Atlas32016():
    do_test_genius_agent(Atlas32016)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_MyAgent():
    do_test_genius_agent(MyAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Farma():
    do_test_genius_agent(Farma)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_PokerFace():
    do_test_genius_agent(PokerFace)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_XianFaAgent():
    do_test_genius_agent(XianFaAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_PhoenixParty():
    do_test_genius_agent(PhoenixParty)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentBuyong():
    do_test_genius_agent(AgentBuyong)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Kawaii():
    do_test_genius_agent(Kawaii)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Atlas3():
    do_test_genius_agent(Atlas3)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentYK():
    do_test_genius_agent(AgentYK)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Group2():
    do_test_genius_agent(Group2)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_WhaleAgent():
    do_test_genius_agent(WhaleAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_DoNA():
    do_test_genius_agent(DoNA)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentM():
    do_test_genius_agent(AgentM)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_TMFAgent():
    do_test_genius_agent(TMFAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_OMACagent():
    do_test_genius_agent(OMACagent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentLG():
    do_test_genius_agent(AgentLG)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_CUHKAgent():
    do_test_genius_agent(CUHKAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_ValueModelAgent():
    do_test_genius_agent(ValueModelAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_NiceTitForTat():
    do_test_genius_agent(NiceTitForTat)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_TheNegotiator():
    do_test_genius_agent(TheNegotiator)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentK2():
    do_test_genius_agent(AgentK2)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_BRAMAgent():
    do_test_genius_agent(BRAMAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_IAMhaggler2011():
    do_test_genius_agent(IAMhaggler2011)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Gahboninho():
    do_test_genius_agent(Gahboninho)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_HardHeaded():
    do_test_genius_agent(HardHeaded)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentK():
    do_test_genius_agent(AgentK)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Yushu():
    do_test_genius_agent(Yushu)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Nozomi():
    do_test_genius_agent(Nozomi)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_IAMhaggler():
    do_test_genius_agent(IAMhaggler)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Terra():
    do_test_genius_agent(Terra)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Gangster():
    do_test_genius_agent(Gangster)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_TheFawkes():
    do_test_genius_agent(TheFawkes)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_AgentHP2():
    do_test_genius_agent(AgentHP2)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_KGAgent():
    do_test_genius_agent(KGAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_E2Agent():
    do_test_genius_agent(E2Agent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_MetaAgent():
    do_test_genius_agent(MetaAgent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_TheNegotiatorReloaded():
    do_test_genius_agent(TheNegotiatorReloaded)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Ngent():
    do_test_genius_agent(Ngent)


@pytest.mark.skipif(
    condition=SKIP_CONDITION,
    reason="No Genius Bridge, skipping genius-agent tests",
)
def test_Simpatico():
    do_test_genius_agent(Simpatico)


#### agents after this line are not very robust

# @pytest.mark.skipif(
#     condition=SKIP_CONDITION,
#     reason="No Genius Bridge, skipping genius-agent tests",
# )
# def test_Rubick():
#     do_test_genius_agent(Rubick)
#
#
# @pytest.mark.skipif(
#     condition=SKIP_CONDITION,
#     reason="No Genius Bridge, skipping genius-agent tests",
# )
# def test_CaduceusDC16():
#     do_test_genius_agent(CaduceusDC16)
#
#
# @pytest.mark.skipif(
#     condition=SKIP_CONDITION,
#     reason="No Genius Bridge, skipping genius-agent tests",
# )
# def test_BetaOne():
#     do_test_genius_agent(BetaOne)
#
#
# @pytest.mark.skipif(
#     condition=SKIP_CONDITION,
#     reason="No Genius Bridge, skipping genius-agent tests",
# )
# def test_AgreeableAgent2018():
#     do_test_genius_agent(AgreeableAgent2018)
#
#
# @pytest.mark.skipif(
#     condition=SKIP_CONDITION,
#     reason="No Genius Bridge, skipping genius-agent tests",
# )
# def test_MengWan():
#     do_test_genius_agent(MengWan)


if __name__ == "__main__":
    pytest.main(args=[__file__])