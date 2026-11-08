"""Glicko-2 (Glickman, "Example of the Glicko-2 system", glicko.net/glicko/glicko2.pdf), step for step.

rate(rating, rd, vol, results, tau) -> (rating, rd, vol); results: [(opponent rating, opponent rd, score 0..1)].
A rating period with no games only widens the deviation.
"""
import math

SCALE = 173.7178


def _g(phi):
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi * math.pi))


def _E(mu, mu_j, phi_j):
    return 1.0 / (1.0 + math.exp(-_g(phi_j) * (mu - mu_j)))


def rate(rating, rd, vol, results, tau=0.5, eps=1e-6):
    mu = (rating - 1500.0) / SCALE
    phi = rd / SCALE
    if not results:                                   # step 6 only: the deviation grows
        phi_star = math.sqrt(phi * phi + vol * vol)
        return rating, phi_star * SCALE, vol
    opp = [((r - 1500.0) / SCALE, d / SCALE, s) for r, d, s in results]
    v_inv = 0.0
    delta_sum = 0.0
    for mu_j, phi_j, s in opp:
        g = _g(phi_j)
        e = _E(mu, mu_j, phi_j)
        v_inv += g * g * e * (1 - e)
        delta_sum += g * (s - e)
    v = 1.0 / v_inv
    delta = v * delta_sum
    # step 5: the new volatility (Illinois algorithm)
    a = math.log(vol * vol)

    def f(x):
        ex = math.exp(x)
        return ex * (delta * delta - phi * phi - v - ex) / (2 * (phi * phi + v + ex) ** 2) - (x - a) / (tau * tau)
    A = a
    if delta * delta > phi * phi + v:
        B_ = math.log(delta * delta - phi * phi - v)
    else:
        k = 1
        while f(a - k * tau) < 0:
            k += 1
        B_ = a - k * tau
    fA, fB = f(A), f(B_)
    while abs(B_ - A) > eps:
        C = A + (A - B_) * fA / (fB - fA)
        fC = f(C)
        if fC * fB <= 0:
            A, fA = B_, fB
        else:
            fA /= 2
        B_, fB = C, fC
    new_vol = math.exp(A / 2)
    phi_star = math.sqrt(phi * phi + new_vol * new_vol)
    new_phi = 1.0 / math.sqrt(1.0 / (phi_star * phi_star) + 1.0 / v)
    new_mu = mu + new_phi * new_phi * delta_sum
    return new_mu * SCALE + 1500.0, new_phi * SCALE, new_vol


def expected(rating, rd, opp_rating, opp_rd):
    """The expected score against an opponent (both deviations counted)."""
    mu, mu_j = (rating - 1500.0) / SCALE, (opp_rating - 1500.0) / SCALE
    phi = math.sqrt((rd / SCALE) ** 2 + (opp_rd / SCALE) ** 2)
    return _E(mu, mu_j, phi)
