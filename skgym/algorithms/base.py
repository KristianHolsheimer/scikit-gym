from abc import ABC, abstractmethod
import numpy as np

from ..value_functions.base import BaseValueFunction
from ..policies.value_based import ValuePolicy


class BaseAlgorithm(ABC):
    """
    Abstract base class for all algorithm objects.

    Parameters
    ----------
    gamma : float
        Future discount factor, value between 0 and 1.

    """
    def __init__(self, gamma=0.9):
        self.gamma = gamma

    @abstractmethod
    def preprocess_transition(self, s, a, r, s_next):
        """
        Prepare a single transition to be used for policy updates or experience
        caching.

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

        Returns
        -------
        X, R, X_next : tuple of arrays
            `X` is used as input to the function approximator while `R` and
            `X_next` can be used to construct the corresponding target `Y`.

        """
        pass

    @abstractmethod
    def Y(self, X, A, G):
        """
        Given a preprocessed transition `(X, A, R, X_next)`, return the target
        to train our regressor on.

        Parameters
        ----------
        X : 2d-array, shape: [batch_size, num_features]
            Scikit-learn style design matrix. This represents a batch of either
            states or state-action pairs, depending on the model type.

        A : 1d-array, shape: [batch_size]
            A batch of actions taken.

        G : 1d-array, shape: [batch_size]
            The target, which is the (estimated, discounted) return. The target
            `G` differs from algorithm to algorithm. It is typically
            implemented in an algorithm's `update` method.

        Returns
        -------
        Y : 1d- or 2d-array, depends on model type
            sklearn-style label array. Also here, the shape depends on the
            model type, if applicable. For a type-I model, the output shape is
            `[batch_size]` and for a type-II model the shape is
            `[batch_size, num_actions]`. For a policy-gradient model, the
            output shape is always `[batch_size]`.

        """
        pass

    @abstractmethod
    def update(self, s, a, r, s_next, a_next=None):
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

        a_next : int or array, typically not required
            A single action. This is typicall not required, with the SARSA
            algorithm as the notable exception.

        """
        pass


class BaseValueAlgorithm(BaseAlgorithm):
    """
    Abstract base class for algorithms that update a value function
    :math:`V(s)`, :math:`Q(s,a)` or a value-based policy.

    Parameters
    ----------
    value_function_or_policy : value function or value-based policy
        This can be either a state value function :math:`V(s)`, a state-action
        value function :math:`Q(s, a)`, or a value-based policy.

    gamma : float
        Future discount factor, value between 0 and 1.

    """
    def __init__(self, value_function_or_policy, gamma=0.9):
        if isinstance(value_function_or_policy, ValuePolicy):
            self.policy = value_function_or_policy
            self.value_function = self.policy.value_function
        elif isinstance(value_function_or_policy, BaseValueFunction):
            self.policy = None
            self.value_function = value_function_or_policy
        else:
            raise TypeError(
                "value_function_or_policy must be either a value function or "
                "a value-based policy")
        super(BaseValueAlgorithm, self).__init__(gamma=gamma)

    def preprocess_transition(self, s, a, r, s_next):
        if self.value_function.MODELTYPE == 1:
            X = self.value_function.X(s, a)
            A = np.array([a])
            R = np.array([r])
            X_next = self.value_function.preprocess_typeII(s_next)
            # X.shape == [batch_size, num_features]
            # R.shape == [batch_size]
            # X_next.shape == [batch_size, num_actions, num_features]
        elif self.value_function.MODELTYPE == 2:
            X = self.value_function.X(s)
            A = np.array([a])
            R = np.array([r])
            X_next = self.value_function.preprocess_typeII(s_next)
            # X.shape == [batch_size, num_features]
            # R.shape == [batch_size]
            # X_next.shape == [batch_size, num_features]
        else:
            raise ValueError("bad MODELTYPE")

        return X, A, R, X_next

    def Y(self, X, A, G):
        if self.value_function.MODELTYPE == 1:
            Y = G
        elif self.value_function.MODELTYPE == 2:
            Y = self.value_function.batch_eval(X)
            idx = np.arange(A.shape[0])
            Y[idx, A] = G
        return Y


class BasePolicyAlgorithm(BaseAlgorithm):
    """
    Abstract base class for algorithms that update a value function
    :math:`V(s)` or :math:`Q(s,a)`.

    Parameters
    ----------
    policy : policy object
        A policy object. Can be either a value-based policy model or a direct
        policy-gradient model.

    gamma : float
        Future discount factor, value between 0 and 1.

    TODO: write implementation, e.g. :math:`\\nabla \\log(\\pi)`

    """
    def __init__(self, policy, gamma=0.9):
        self.policy = policy
        super(BaseAlgorithm, self).__init__(gamma=gamma)
