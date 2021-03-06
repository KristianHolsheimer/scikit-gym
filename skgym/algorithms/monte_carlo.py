from .base import BaseValueAlgorithm
from ..utils import ExperienceCache


class MonteCarlo(BaseValueAlgorithm):
    """
    Update the Q-function according to the plain vanilla Monte Carlo algorithm,
    cf. Section 5.3 of `Sutton & Barto
    <http://incompleteideas.net/book/the-book-2nd.html>`_. The Q-function
    object can either be passed directly or implicitly by passing a value-based
    policy object.

    Parameters
    ----------
    value_function_or_policy : value function or value-based policy
        This can be either a state value function :math:`V(s)`, a state-action
        value function :math:`Q(s, a)`, or a value-based policy.

    gamma : float
        Future discount factor, value between 0 and 1.

    """
    def __init__(self, value_function_or_policy, gamma=0.9):
        self.experience_cache = ExperienceCache(overflow='grow')
        super(MonteCarlo, self).__init__(value_function_or_policy, gamma=gamma)

    def update(self, s, a, r, s_next, done):
        """
        Update the given policy and/or value function.

        Parameters
        ----------
        s : int or array
            A single observation (state).

        a : int or array
            A single action.

        r : float
            Reward associated with the transition
            :math:`(s, a)\\to s_\\text{next}`.

        s_next : int or array
            A single observation (state).

        done : bool
            Whether the episode is done. If `done` is `False`, the input
            transition is cached and no actual update will take place. Once
            `done` is `True`, however, the collected cache from the episode is
            unrolled, replaying the epsiode in reverse chronological order.
            This is when the actual updates are made.

        """
        X, A, R, X_next = self.preprocess_transition(s, a, r, s_next)
        self.experience_cache.append(X, A, R, X_next)

        # break out of function if episode hasn't yet finished
        if not done:
            return

        # initialize return
        G = 0

        # replay episode in reverse order
        while self.experience_cache:
            X, A, R, X_next = self.experience_cache.pop()

            G = R + self.gamma * G  # gamma-discounted return
            Y = self.Y(X, A, G)     # target for function approximator

            self.value_function.update(X, Y)
