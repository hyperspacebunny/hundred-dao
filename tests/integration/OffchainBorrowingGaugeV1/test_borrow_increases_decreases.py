import brownie
from brownie import chain
from brownie.test import strategy

BORROW_CHAIN_ID = 4269

class StateMachine:
    """
    Validate that borrows and repayments/liquidations work correctly over time.

    Strategies
    ----------
    st_account : Account
        Account to perform borrow or repay/liquidate from
    st_value : int
        Amount to borrow or repay/liquidate
    st_time : int
        Amount of time to advance the clock
    """

    st_account = strategy("address", length=5)
    st_value = strategy("uint64")
    st_time = strategy("uint", max_value=86400 * 365)

    def __init__(self, accounts, ocb_gauge_v1, token, mock_hcontroller):
        self.accounts = accounts
        self.token = token
        self.ocb_gauge_v1 = ocb_gauge_v1
        self.mock_hcontroller = mock_hcontroller

    def setup(self):
        self.balances = {i: 0 for i in self.accounts}

    def rule_borrow(self, st_account, st_value):
        """
        Borrow tokens and increase your `OffchainBorrowingGauge` balance.
        """
        self.mock_hcontroller.increaseBorrowPosition(BORROW_CHAIN_ID, st_account, self.token, st_value)
        self.balances[st_account] += st_value

    def rule_repay(self, st_account, st_value):
        """
        Repay/liquidate tokens and decrease your `OffchainBorrowingGauge` balance.
        """
        if self.balances[st_account] < st_value:
            # fail path - insufficient balance
            with brownie.reverts():
                self.mock_hcontroller.reduceBorrowPosition(BORROW_CHAIN_ID, st_account, self.token, st_value)
            return

        # success path
        self.mock_hcontroller.reduceBorrowPosition(BORROW_CHAIN_ID, st_account, self.token, st_value)
        self.balances[st_account] -= st_value

    def rule_advance_time(self, st_time):
        """
        Advance the clock.
        """
        chain.sleep(st_time)

    def rule_checkpoint(self, st_account):
        """
        Create a new user checkpoint.
        """
        self.ocb_gauge_v1.user_checkpoint(st_account, {"from": st_account})

    def invariant_balances(self):
        """
        Validate expected balances against actual balances.
        """
        for account, balance in self.balances.items():
            assert self.ocb_gauge_v1.balanceOf(account) == balance

    def invariant_total_supply(self):
        """
        Validate expected total supply against actual total supply.
        """
        assert self.ocb_gauge_v1.totalSupply() == sum(self.balances.values())

    def teardown(self):
        """
        Final check to ensure that all balances may be withdrawn.
        """
        for account, balance in ((k, v) for k, v in self.balances.items() if v):
            self.mock_hcontroller.reduceBorrowPosition(BORROW_CHAIN_ID, account, self.token, balance)


def test_state_machine(state_machine, accounts, ocb_gauge_v1, token, mock_hcontroller, no_call_coverage):
    mock_hcontroller._registerBorrowGauge(BORROW_CHAIN_ID, token, ocb_gauge_v1)

    # because this is a simple state machine, we use more steps than normal
    settings = {"stateful_step_count": 25, "max_examples": 30}

    state_machine(StateMachine, accounts[:5], ocb_gauge_v1, token, mock_hcontroller, settings=settings)
