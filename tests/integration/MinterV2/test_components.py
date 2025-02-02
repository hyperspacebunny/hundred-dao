import pytest
from brownie.test import given, strategy
from hypothesis import settings

from tests.conftest import approx

WEEK = 86400 * 7
MONTH = 86400 * 30


@pytest.fixture(scope="module", autouse=True)
def minter_setup(accounts, mock_lp_token, gauge_controller, gauge_v5):

    # set type
    gauge_controller.add_type(b"Liquidity", 10 ** 18, {"from": accounts[0]})

    # add gauge
    gauge_controller.add_gauge(gauge_v5, 0, 10 ** 19, {"from": accounts[0]})

    # transfer tokens
    for acct in accounts[1:4]:
        mock_lp_token.transfer(acct, 1e18, {"from": accounts[0]})
        mock_lp_token.approve(gauge_v5, 1e18, {"from": acct})


@given(st_duration=strategy("uint[3]", min_value=WEEK, max_value=MONTH, unique=True))
@settings(max_examples=30)
def test_duration(accounts, chain, gauge_v5, minter, token, st_duration):
    accts = accounts[1:]
    chain.sleep(7 * 86400)

    deposit_time = []
    for i in range(3):
        gauge_v5.deposit(10 ** 18, {"from": accts[i]})
        deposit_time.append(chain[-1].timestamp)

    durations = []
    balances = []
    for i in range(3):
        chain.sleep(st_duration[i])
        gauge_v5.withdraw(10 ** 18, {"from": accts[i]})
        durations.append(chain[-1].timestamp - deposit_time[i])
        minter.mint(gauge_v5, {"from": accts[i]})
        balances.append(token.balanceOf(accts[i]))

    total_minted = sum(balances)
    weight1 = durations[0]
    weight2 = weight1 + (durations[1] - durations[0]) * 1.5
    weight3 = weight2 + (durations[2] - durations[1]) * 3
    total_weight = weight1 + weight2 + weight3

    assert approx(balances[0] / total_minted, weight1 / total_weight, 1e-2)
    assert approx(balances[1] / total_minted, weight2 / total_weight, 1e-2)
    assert approx(balances[2] / total_minted, weight3 / total_weight, 1e-2)


@given(st_amounts=strategy("uint[3]", min_value=10 ** 17, max_value=10 ** 18, unique=True))
@settings(max_examples=30)
def test_amounts(accounts, chain, gauge_v5, minter, token, st_amounts):
    accts = accounts[1:]

    deposit_time = []
    for i in range(3):
        gauge_v5.deposit(st_amounts[i], {"from": accts[i]})
        deposit_time.append(chain[-1].timestamp)

    chain.sleep(MONTH)
    balances = []
    for i in range(3):
        gauge_v5.withdraw(st_amounts[i], {"from": accts[i]})

    for i in range(3):
        minter.mint(gauge_v5, {"from": accts[i]})
        balances.append(token.balanceOf(accts[i]))

    total_deposited = sum(st_amounts)
    total_minted = sum(balances)

    assert approx(balances[0] / total_minted, st_amounts[0] / total_deposited, 1e-4)
    assert approx(balances[1] / total_minted, st_amounts[1] / total_deposited, 1e-4)
    assert approx(balances[2] / total_minted, st_amounts[2] / total_deposited, 1e-4)
