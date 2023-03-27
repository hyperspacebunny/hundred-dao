import brownie


def test_balance_of_with_single_measured_token(accounts, ocb_gauge_v1, mock_hcontroller, token, token2):
    mock_hcontroller._registerBorrowGauge(1, token, ocb_gauge_v1)

    assert ocb_gauge_v1.balanceOf(accounts[1]) == 0
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token, 10 ** 23)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token2, 10 ** 23)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token, 10 ** 22)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 10 ** 22

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token2, 10 ** 22)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 10 ** 22


def test_balance_of_with_multiple_measured_tokens(accounts, ocb_gauge_v1, mock_hcontroller, token, token2):
    mock_hcontroller._registerBorrowGauge(1, token, ocb_gauge_v1)
    mock_hcontroller._registerBorrowGauge(1, token2, ocb_gauge_v1)

    assert ocb_gauge_v1.balanceOf(accounts[1]) == 0
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token, 10 ** 23)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token2, 10 ** 23)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 2 * 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token, 10 ** 22)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 2 * 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 10 ** 22

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token2, 10 ** 22)
    assert ocb_gauge_v1.balanceOf(accounts[1]) == 2 * 10 ** 23
    assert ocb_gauge_v1.balanceOf(accounts[2]) == 2 * 10 ** 22


def test_total_supply_with_single_measured_token(accounts, ocb_gauge_v1, mock_hcontroller, token, token2):
    mock_hcontroller._registerBorrowGauge(1, token, ocb_gauge_v1)

    assert ocb_gauge_v1.totalSupply() == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token, 10 ** 23)
    assert ocb_gauge_v1.totalSupply() == 10 ** 23

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token2, 10 ** 23)
    assert ocb_gauge_v1.totalSupply() == 10 ** 23

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token, 10 ** 22)
    assert ocb_gauge_v1.totalSupply() == 10 ** 23 + 10 ** 22

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token2, 10 ** 22)
    assert ocb_gauge_v1.totalSupply() == 10 ** 23 + 10 ** 22


def test_total_supply_with_multiple_measured_tokens(accounts, ocb_gauge_v1, mock_hcontroller, token, token2):
    mock_hcontroller._registerBorrowGauge(1, token, ocb_gauge_v1)
    mock_hcontroller._registerBorrowGauge(1, token2, ocb_gauge_v1)

    assert ocb_gauge_v1.totalSupply() == 0

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token, 10 ** 23)
    assert ocb_gauge_v1.totalSupply() == 10 ** 23

    mock_hcontroller.increaseBorrowPosition(1, accounts[1], token2, 10 ** 22)
    assert ocb_gauge_v1.totalSupply() == 10 ** 23 + 10 ** 22

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token, 10 ** 23)
    assert ocb_gauge_v1.totalSupply() == 2 * 10 ** 23 + 10 ** 22

    mock_hcontroller.increaseBorrowPosition(1, accounts[2], token2, 10 ** 22)
    assert ocb_gauge_v1.totalSupply() == 2 * 10 ** 23 + 2 * 10 ** 22