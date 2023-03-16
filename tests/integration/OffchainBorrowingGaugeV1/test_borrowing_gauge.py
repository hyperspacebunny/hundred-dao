from random import random, randrange

from tests.conftest import YEAR, approx

MAX_UINT256 = 2 ** 256 - 1
WEEK = 7 * 86400
BORROW_CHAIN_ID = 1337
MAX_BORROW = 4200 * 10 ** 18


def test_gauge_integral(accounts, chain, token, token2, reward_policy_maker, ocb_gauge_v1, gauge_controller, mock_hcontroller):
    alice, bob = accounts[:2]

    # Register borrowing gauge with the comptroller
    mock_hcontroller.registerBorrowGauge(BORROW_CHAIN_ID, token2, ocb_gauge_v1)

    # Wire up Gauge to the controller to have proper rates and stuff
    gauge_controller.add_type(b"Borrowing", {"from": alice})
    gauge_controller.change_type_weight(0, 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(ocb_gauge_v1.address, 0, 10 ** 18, {"from": alice})

    alice_borrowed = 0
    bob_borrowed = 0
    integral = 0  # ∫(balance * rate(t) / totalSupply(t) dt)
    checkpoint = chain[-1].timestamp
    checkpoint_rate = reward_policy_maker.rate_at(checkpoint, token)
    checkpoint_supply = 0
    checkpoint_balance = 0

    def update_integral():
        nonlocal checkpoint, checkpoint_rate, integral, checkpoint_balance, checkpoint_supply

        t1 = chain[-1].timestamp
        rate1 = reward_policy_maker.rate_at(t1, token)
        t_epoch = reward_policy_maker.epoch_start_time(reward_policy_maker.epoch_at(t1))
        if checkpoint >= t_epoch:
            rate_x_time = (t1 - checkpoint) * rate1
        else:
            rate_x_time = (t_epoch - checkpoint) * checkpoint_rate + (t1 - t_epoch) * rate1
        if checkpoint_supply > 0:
            integral += rate_x_time * checkpoint_balance // checkpoint_supply
        checkpoint_rate = rate1
        checkpoint = t1
        checkpoint_supply = ocb_gauge_v1.totalSupply()
        checkpoint_balance = ocb_gauge_v1.balanceOf(alice)

    # Now let's have a loop where Bob always borrows or repays,
    # and Alice does so more rarely
    for i in range(40):
        is_alice = random() < 0.2
        dt = randrange(1, YEAR // 5)
        chain.sleep(dt)
        chain.mine()

        # For Bob
        is_withdraw = (i > 0) * (random() < 0.5)
        print("Bob", "repays" if is_withdraw else "borrows")
        if is_withdraw:
            amount = randrange(1, ocb_gauge_v1.balanceOf(bob) + 1)
            mock_hcontroller.reduceBorrowPosition(BORROW_CHAIN_ID, bob, token2, amount)
            update_integral()
            bob_borrowed -= amount
        else:
            amount = randrange(1, MAX_BORROW // 10 + 1)
            mock_hcontroller.increaseBorrowPosition(BORROW_CHAIN_ID, bob, token2, amount)
            update_integral()
            bob_borrowed += amount

        if is_alice:
            # For Alice
            is_withdraw_alice = (ocb_gauge_v1.balanceOf(alice) > 0) * (random() < 0.5)
            print("Alice", "repays" if is_withdraw_alice else "borrows")

            if is_withdraw_alice:
                amount_alice = randrange(1, ocb_gauge_v1.balanceOf(alice) // 10 + 1)
                mock_hcontroller.reduceBorrowPosition(BORROW_CHAIN_ID, alice, token2, amount_alice)
                update_integral()
                alice_borrowed -= amount_alice
            else:
                amount_alice = randrange(1, MAX_BORROW)
                mock_hcontroller.increaseBorrowPosition(BORROW_CHAIN_ID, alice, token2, amount_alice)
                update_integral()
                alice_borrowed += amount_alice

        # Checking that updating the checkpoint in the same second does nothing
        # Also everyone can update: that should make no difference, too
        if random() < 0.5:
            ocb_gauge_v1.user_checkpoint(alice, {"from": alice})
        if random() < 0.5:
            ocb_gauge_v1.user_checkpoint(bob, {"from": bob})

        assert ocb_gauge_v1.balanceOf(alice) == alice_borrowed
        assert ocb_gauge_v1.balanceOf(bob) == bob_borrowed
        assert ocb_gauge_v1.totalSupply() == alice_borrowed + bob_borrowed

        dt = randrange(1, YEAR // 20)
        chain.sleep(dt)
        chain.mine()

        ocb_gauge_v1.user_checkpoint(alice, {"from": alice})
        update_integral()
        print(i, dt / 86400, integral, ocb_gauge_v1.integrate_fraction(token, alice))
        assert approx(ocb_gauge_v1.integrate_fraction(token, alice), integral, 1e-15)


def test_mining_with_votelock(
    accounts,
    chain,
    history,
    token,
    token2,
    ocb_gauge_v1,
    gauge_controller,
    mock_hcontroller,
    voting_escrow,
):
    alice, bob = accounts[:2]
    chain.sleep(2 * WEEK + 5)

    # Register borrowing gauge with the comptroller
    mock_hcontroller.registerBorrowGauge(BORROW_CHAIN_ID, token2, ocb_gauge_v1)

    # Wire up Gauge to the controller to have proper rates and stuff
    gauge_controller.add_type(b"Borrowing", {"from": alice})
    gauge_controller.change_type_weight(0, 10 ** 18, {"from": alice})
    gauge_controller.add_gauge(ocb_gauge_v1.address, 0, 10 ** 18, {"from": alice})

    # Prepare tokens
    token.mint(alice, 10 ** 24)
    token.transfer(bob, 10 ** 20, {"from": alice})
    token.approve(voting_escrow, MAX_UINT256, {"from": alice})
    token.approve(voting_escrow, MAX_UINT256, {"from": bob})

    # Alice deposits to escrow. She now has a BOOST
    t = chain[-1].timestamp
    voting_escrow.create_lock(10 ** 20, t + 2 * WEEK, {"from": alice})

    # Alice and Bob borrow some tokens
    mock_hcontroller.increaseBorrowPosition(BORROW_CHAIN_ID, alice, token2, 10 ** 21)
    mock_hcontroller.increaseBorrowPosition(BORROW_CHAIN_ID, bob, token2, 10 ** 21)

    # Time travel and checkpoint
    chain.sleep(4 * WEEK)
    alice.transfer(alice, 1)
    while True:
        ocb_gauge_v1.user_checkpoint(alice, {"from": alice})
        ocb_gauge_v1.user_checkpoint(bob, {"from": bob})
        if chain[-1].timestamp != chain[-2].timestamp:
            chain.undo(2)
        else:
            break

    # 4 weeks down the road, balanceOf must be 0
    assert voting_escrow.balanceOf(alice) == 0
    assert voting_escrow.balanceOf(bob) == 0

    # Alice earned 2.5 times more CRV because she vote-locked her CRV
    rewards_alice = ocb_gauge_v1.integrate_fraction(token, alice)
    rewards_bob = ocb_gauge_v1.integrate_fraction(token, bob)
    assert approx(rewards_alice / rewards_bob, 2.5, 1e-5)

    # Time travel / checkpoint: no one has CRV vote-locked
    chain.sleep(4 * WEEK)
    alice.transfer(alice, 1)
    voting_escrow.withdraw({"from": alice})
    while True:
        ocb_gauge_v1.user_checkpoint(alice, {"from": alice})
        ocb_gauge_v1.user_checkpoint(bob, {"from": bob})
        if chain[-1].timestamp != chain[-2].timestamp:
            chain.undo(2)
        else:
            break
    old_rewards_alice = rewards_alice
    old_rewards_bob = rewards_bob

    # Alice earned the same as Bob now
    rewards_alice = ocb_gauge_v1.integrate_fraction(token, alice)
    rewards_bob = ocb_gauge_v1.integrate_fraction(token, bob)
    d_alice = rewards_alice - old_rewards_alice
    d_bob = rewards_bob - old_rewards_bob
    assert d_alice == d_bob

    # Both Alice and Bob votelock
    while True:
        t = chain[-1].timestamp
        voting_escrow.create_lock(10 ** 20, t + 2 * WEEK, {"from": alice})
        voting_escrow.create_lock(10 ** 20, t + 2 * WEEK, {"from": bob})
        if chain[-1].timestamp != chain[-2].timestamp:
            chain.undo(2)
        else:
            break

    # Time travel / checkpoint: no one has CRV vote-locked
    chain.sleep(4 * WEEK)
    alice.transfer(alice, 1)
    voting_escrow.withdraw({"from": alice})
    voting_escrow.withdraw({"from": bob})
    while True:
        ocb_gauge_v1.user_checkpoint(alice, {"from": alice})
        ocb_gauge_v1.user_checkpoint(bob, {"from": bob})
        if chain[-1].timestamp != chain[-2].timestamp:
            chain.undo(2)
        else:
            break
    old_rewards_alice = rewards_alice
    old_rewards_bob = rewards_bob

    # Alice earned the same as Bob now
    rewards_alice = ocb_gauge_v1.integrate_fraction(token, alice)
    rewards_bob = ocb_gauge_v1.integrate_fraction(token, bob)
    d_alice = rewards_alice - old_rewards_alice
    d_bob = rewards_bob - old_rewards_bob
    assert d_alice == d_bob
