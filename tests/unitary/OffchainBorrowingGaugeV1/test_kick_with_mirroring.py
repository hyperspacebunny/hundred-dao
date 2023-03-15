import brownie

MAX_UINT256 = 2 ** 256 - 1
WEEK = 7 * 86400


def test_kick(chain, accounts, ocb_gauge_v1, mock_hcontroller, mirrored_voting_escrow, voting_escrow, token):
    alice, bob = accounts[:2]
    chain.sleep(2 * WEEK + 5)

    mirrored_voting_escrow.set_mirror_whitelist(accounts[0], True, {"from": accounts[0]})
    mirrored_voting_escrow.mirror_lock(alice, 250, 0, 5 * 10 ** 19, chain.time() + 4 * WEEK, {"from": accounts[0]})

    token.mint(alice, 5 * 10 ** 19)
    token.approve(voting_escrow, MAX_UINT256, {"from": alice})
    voting_escrow.create_lock(5 * 10 ** 19, chain.time() + 4 * WEEK, {"from": alice})

    mock_hcontroller.registerBorrowGauge(1, token, ocb_gauge_v1)
    mock_hcontroller.increaseBorrowPosition(1, alice, token, 10 ** 21, {"from": alice})

    assert ocb_gauge_v1.working_balances(alice) == 10 ** 21

    chain.sleep(WEEK)

    with brownie.reverts("dev: kick not allowed"):
        ocb_gauge_v1.kick(alice, {"from": bob})

    chain.sleep(4 * WEEK)

    ocb_gauge_v1.kick(alice, {"from": bob})
    assert ocb_gauge_v1.working_balances(alice) == 4 * 10 ** 20

    with brownie.reverts("dev: kick not needed"):
        ocb_gauge_v1.kick(alice, {"from": bob})
