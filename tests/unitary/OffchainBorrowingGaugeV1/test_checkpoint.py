import brownie

YEAR = 86400 * 365


def test_user_checkpoint(accounts, ocb_gauge_v1):
    ocb_gauge_v1.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_new_period(accounts, chain, ocb_gauge_v1):
    ocb_gauge_v1.user_checkpoint(accounts[1], {"from": accounts[1]})
    chain.sleep(int(YEAR * 1.1))
    ocb_gauge_v1.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_wrong_account(accounts, ocb_gauge_v1):
    with brownie.reverts("dev: unauthorized"):
        ocb_gauge_v1.user_checkpoint(accounts[2], {"from": accounts[1]})


def test_user_checkpoint_from_hcontroller(accounts, ocb_gauge_v1, mock_hcontroller):
    ocb_gauge_v1.user_checkpoint(accounts[1], {"from": mock_hcontroller})


def test_user_checkpoint_from_minter(accounts, ocb_gauge_v1, minter):
    ocb_gauge_v1.user_checkpoint(accounts[1], {"from": minter})
