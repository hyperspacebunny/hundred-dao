import brownie


def test_add_measured_token(ocb_gauge_v1, mock_hcontroller, token):
    ocb_gauge_v1.add_measured_token(1, token, {"from": mock_hcontroller})

    assert ocb_gauge_v1.measured_tokens(0)["contract_address"] == token
    assert ocb_gauge_v1.measured_tokens(0)["chain_id"] == 1


def test_add_measured_token_from_non_hcontroller_address(accounts, ocb_gauge_v1, token):
    with brownie.reverts("dev: unauthorized"):
        ocb_gauge_v1.add_measured_token(1, token, {"from": accounts[0]})


def test_add_multiple_measured_tokens_on_same_chain(ocb_gauge_v1, mock_hcontroller, token, token2):
    ocb_gauge_v1.add_measured_token(1, token, {"from": mock_hcontroller})
    ocb_gauge_v1.add_measured_token(1, token2, {"from": mock_hcontroller})

    assert ocb_gauge_v1.measured_tokens(1)["contract_address"] == token2
    assert ocb_gauge_v1.measured_tokens(1)["chain_id"] == 1


def test_add_measured_token_on_multiple_chains(ocb_gauge_v1, mock_hcontroller, token):
    ocb_gauge_v1.add_measured_token(1, token, {"from": mock_hcontroller})
    ocb_gauge_v1.add_measured_token(2, token, {"from": mock_hcontroller})

    assert ocb_gauge_v1.measured_tokens(1)["contract_address"] == token
    assert ocb_gauge_v1.measured_tokens(1)["chain_id"] == 2


def test_add_measured_token_twice(ocb_gauge_v1, mock_hcontroller, token):
    ocb_gauge_v1.add_measured_token(1, token, {"from": mock_hcontroller})

    with brownie.reverts("dev: token already measured"):
        ocb_gauge_v1.add_measured_token(1, token, {"from": mock_hcontroller})