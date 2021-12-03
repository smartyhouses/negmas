from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    MutableMapping,
    Optional,
    Type,
    Union,
)

from negmas.common import NegotiatorMechanismInterface
from negmas.generics import GenericMapping, ienumerate, iget, ivalues
from negmas.helpers import get_full_type_name, gmap, ikeys
from negmas.outcomes import Issue, Outcome, OutcomeRange, outcome_in_range
from negmas.serialization import PYTHON_CLASS_IDENTIFIER, deserialize, serialize

from .base import OutcomeUtilityMapping
from .ufun import UtilityFunction

__all__ = [
    "NonLinearUtilityAggregationFunction",
    "HyperRectangleUtilityFunction",
    "NonlinearHyperRectangleUtilityFunction",
]


class NonLinearUtilityAggregationFunction(UtilityFunction):
    r"""A nonlinear utility function.

    Allows for the modeling of a single nonlinear utility function that combines the utilities of different issues.

    Args:
        issue_utilities: A set of mappings from issue values to utility functions. These are generic mappings so
                        \ `Callable`\ (s) and \ `Mapping`\ (s) are both accepted
        f: A nonlinear function mapping from a dict of utility_function-per-issue to a float
        name: name of the utility function. If None a random name will be generated.

    Notes:

        The utility is calculated as:

        .. math::

                u = f\\left(u_0\\left(i_0\\right), u_1\\left(i_1\\right), ..., u_n\\left(i_n\\right)\\right)

        where :math:`u_j()` is the utility function for issue :math:`j` and :math:`i_j` is value of issue :math:`j` in the
        evaluated outcome.


    Examples:
        >>> issues = [make_issue((10.0, 20.0), 'price'), make_issue(['delivered', 'not delivered'], 'delivery')
        ...           , make_issue(5, 'quality')]
        >>> print(list(map(str, issues)))
        ['price: (10.0, 20.0)', "delivery: ['delivered', 'not delivered']", 'quality: (0, 4)']
        >>> g = NonLinearUtilityAggregationFunction({ 'price': lambda x: 2.0*x
        ...                                         , 'delivery': {'delivered': 10, 'not delivered': -10}
        ...                                         , 'quality': MappingUtilityFunction(lambda x: x-3)}
        ...         , f=lambda u: u['price']  + 2.0 * u['quality'])
        >>> float(g({'quality': 2, 'price': 14.0, 'delivery': 'delivered'})) - ((2.0*14)+2.0*(2.0-3.0))
        0.0
        >>> g = NonLinearUtilityAggregationFunction({'price'    : lambda x: 2.0*x
        ...                                         , 'delivery': {'delivered': 10, 'not delivered': -10}}
        ...         , f=lambda u: 2.0 * u['price'] )
        >>> float(g({'price': 14.0, 'delivery': 'delivered'})) - (2.0*(2.0*14))
        0.0

    """

    def xml(self, issues: List[Issue]) -> str:
        raise NotImplementedError(f"Cannot convert {self.__class__.__name__} to xml")

    def __init__(
        self,
        issue_utilities: MutableMapping[Any, GenericMapping],
        f: Callable[[Dict[Any, float]], float],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.issue_utilities = issue_utilities
        self.f = f

    def to_dict(self):
        d = {PYTHON_CLASS_IDENTIFIER: get_full_type_name(type(self))}
        return dict(
            **d,
            issue_utilities=self.issue_utilities,
            f=serialize(self.f),
            name=self.name,
            reserved_value=self.reserved_value,
        )

    @classmethod
    def from_dict(cls, d):
        d.pop(PYTHON_CLASS_IDENTIFIER, None)
        return cls(
            issue_utilities=d.get("issue_utilities", None),
            f=deserialize(d.get("f", None)),
            name=d.get("name", None),
            reserved_value=d.get("reserved_value", None),
            id=d.get("id", None),
        )

    def eval(self, offer: Optional["Outcome"]) -> Optional[float]:
        if offer is None:
            return self.reserved_value
        if self.issue_utilities is None:
            raise ValueError(
                "No issue utilities were set. Call set_params() or use the constructor"
            )

        u = {}
        for k in ikeys(self.issue_utilities):
            v = iget(offer, k)
            u[k] = gmap(iget(self.issue_utilities, k), v)
        return self.f(u)


class HyperRectangleUtilityFunction(UtilityFunction):
    """A utility function defined as a set of hyper-volumes.

    The utility function that is calulated by combining linearly a set of *probably nonlinear* functions applied in
    predefined hyper-volumes of the outcome space.

     Args:
          outcome_ranges: The outcome_ranges for which the `mappings` are defined
          weights: The *optional* weights to use for combining the outputs of the `mappings`
          ignore_issues_not_in_input: If a hyper-volumne local function is defined for some issue
          that is not in the outcome being evaluated ignore it.
          ignore_failing_range_utilities: If a hyper-volume local function fails, just assume it
          did not exist for this outcome.
          name: name of the utility function. If None a random name will be generated.

     Examples:
         We will use the following issue space of cardinality :math:`10 \times 5 \times 4`:

         >>> issues = [make_issue(10), make_issue(5), make_issue(4)]

         Now create the utility function with

         >>> f = HyperRectangleUtilityFunction(outcome_ranges=[
         ...                                        {0: (1.0, 2.0), 1: (1.0, 2.0)},
         ...                                        {0: (1.4, 2.0), 2: (2.0, 3.0)}]
         ...                                , utilities= [2.0, lambda x: 2 * x[2] + x[0]])
         >>> g = HyperRectangleUtilityFunction(outcome_ranges=[
         ...                                        {0: (1.0, 2.0), 1: (1.0, 2.0)},
         ...                                        {0: (1.4, 2.0), 2: (2.0, 3.0)}]
         ...                                , utilities= [2.0, lambda x: 2 * x[2] + x[0]]
         ...                                , ignore_issues_not_in_input=True)
         >>> h = HyperRectangleUtilityFunction(outcome_ranges=[
         ...                                        {0: (1.0, 2.0), 1: (1.0, 2.0)},
         ...                                        {0: (1.4, 2.0), 2: (2.0, 3.0)}]
         ...                                , utilities= [2.0, lambda x: 2 * x[2] + x[0]]
         ...                                , ignore_failing_range_utilities=True)

         We can now calcualte the utility_function of some outcomes:

         * An outcome that belongs to the both outcome_ranges:
         >>> [f({0: 1.5,1: 1.5, 2: 2.5}), g({0: 1.5,1: 1.5, 2: 2.5}), h({0: 1.5,1: 1.5, 2: 2.5})]
         [8.5, 8.5, 8.5]

         * An outcome that belongs to the first hypervolume only:
         >>> [f({0: 1.5,1: 1.5, 2: 1.0}), g({0: 1.5,1: 1.5, 2: 1.0}), h({0: 1.5,1: 1.5, 2: 1.0})]
         [2.0, 2.0, 2.0]

         * An outcome that belongs to and has the first hypervolume only:
         >>> [f({0: 1.5}), g({0: 1.5}), h({0: 1.5})]
         [None, 0.0, None]

         * An outcome that belongs to the second hypervolume only:
         >>> [f({0: 1.5,2: 2.5}), g({0: 1.5,2: 2.5}), h({0: 1.5,2: 2.5})]
         [None, 6.5, None]

         * An outcome that has and belongs to the second hypervolume only:
         >>> [f({2: 2.5}), g({2: 2.5}), h({2: 2.5})]
         [None, 0.0, None]

         * An outcome that belongs to no outcome_ranges:
         >>> [f({0: 11.5,1: 11.5, 2: 12.5}), g({0: 11.5,1: 11.5, 2: 12.5}), h({0: 11.5,1: 11.5, 2: 12.5})]
         [0.0, 0.0, 0.0]


     Remarks:
         - The number of outcome_ranges, mappings, and weights must be the same
         - if no weights are given they are all assumed to equal unity
         - mappings can either by an `OutcomeUtilityMapping` or a constant.

    """

    def xml(self, issues: List[Issue]) -> str:
        """Represents the function as XML

        Args:
            issues:

        Examples:

            >>> f = HyperRectangleUtilityFunction(outcome_ranges=[
            ...                                        {0: (1.0, 2.0), 1: (1.0, 2.0)},
            ...                                        {0: (1.4, 2.0), 2: (2.0, 3.0)}]
            ...                                , utilities= [2.0, 9.0 + 4.0])
            >>> print(f.xml([make_issue((0.0, 4.0), name='0'), make_issue((0.0, 9.0), name='1')
            ... , make_issue((0.0, 9.0), name='2')]).strip())
            <issue index="1" name="0" vtype="real" type="real" etype="real">
                <range lowerbound="0.0" upperbound="4.0"></range>
            </issue><issue index="2" name="1" vtype="real" type="real" etype="real">
                <range lowerbound="0.0" upperbound="9.0"></range>
            </issue><issue index="3" name="2" vtype="real" type="real" etype="real">
                <range lowerbound="0.0" upperbound="9.0"></range>
            </issue><utility_function maxutility="-1.0">
                <ufun type="PlainUfun" weight="1" aggregation="sum">
                    <hyperRectangle utility_function="2.0">
                        <INCLUDES index="0" min="1.0" max="2.0" />
                        <INCLUDES index="1" min="1.0" max="2.0" />
                    </hyperRectangle>
                    <hyperRectangle utility_function="13.0">
                        <INCLUDES index="0" min="1.4" max="2.0" />
                        <INCLUDES index="2" min="2.0" max="3.0" />
                    </hyperRectangle>
                </ufun>
            </utility_function>

        """
        output = ""
        for i, issue in enumerate(issues):
            name = issue.name
            if isinstance(issue.values, tuple):
                output += (
                    f'<issue index="{i+1}" name="{name}" vtype="real" type="real" etype="real">\n'
                    f'    <range lowerbound="{issue.values[0]}" upperbound="{issue.values[1]}"></range>\n'
                    f"</issue>"
                )
            elif isinstance(issue.values, int):
                output += (
                    f'<issue index="{i+1}" name="{name}" vtype="integer" type="integer" etype="integer" '
                    f'lowerbound="0" upperbound="{issue.values - 1}"/>\n'
                )
            else:
                output += (
                    f'<issue index="{i+1}" name="{name}" vtype="integer" type="integer" etype="integer" '
                    f'lowerbound="{min(issue.values)}" upperbound="{max(issue.values)}"/>\n'
                )
        # todo find the real maxutility
        output += '<utility_function maxutility="-1.0">\n    <ufun type="PlainUfun" weight="1" aggregation="sum">\n'
        for rect, u, w in zip(self.outcome_ranges, self.mappings, self.weights):
            output += f'        <hyperRectangle utility_function="{u * w}">\n'
            for key in rect.keys():
                # indx = [i for i, _ in enumerate(issues) if _.name == key][0] + 1
                indx = key + 1
                values = rect.get(key, None)
                if values is None:
                    continue
                if isinstance(values, float) or isinstance(values, int):
                    mn, mx = values, values
                elif isinstance(values, tuple):
                    mn, mx = values
                else:
                    mn, mx = min(values), max(values)
                output += (
                    f'            <INCLUDES index="{indx}" min="{mn}" max="{mx}" />\n'
                )
            output += f"        </hyperRectangle>\n"
        output += "    </ufun>\n</utility_function>"
        return output

    def __init__(
        self,
        outcome_ranges: Iterable[OutcomeRange],
        utilities: Union[List[float], List[OutcomeUtilityMapping]],
        weights: Optional[List[float]] = None,
        ignore_issues_not_in_input=False,
        ignore_failing_range_utilities=False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.outcome_ranges = outcome_ranges
        self.mappings = utilities
        self.weights = weights
        self.ignore_issues_not_in_input = ignore_issues_not_in_input
        self.ignore_failing_range_utilities = ignore_failing_range_utilities
        self.adjust_params()

    def to_dict(self):
        d = {PYTHON_CLASS_IDENTIFIER: get_full_type_name(type(self))}
        return dict(
            **d,
            outcome_ranges=self.outcome_ranges,
            utilities=self.mappings,
            weights=self.weights,
            ignore_issues_not_in_input=self.ignore_issues_not_in_input,
            ignore_failing_range_utilities=self.ignore_failing_range_utilities,
            name=self.name,
            reserved_value=self.reserved_value,
            id=self.id,
        )

    @classmethod
    def from_dict(cls, d):
        d.pop(PYTHON_CLASS_IDENTIFIER, None)
        return cls(
            outcome_ranges=d.get("outcome_ranges", None),
            utilities=d.get("utilities", None),
            weights=d.get("weights", None),
            ignore_issues_not_in_input=d.get("ignore_issues_not_in_input", None),
            ignore_failing_range_utilities=d.get(
                "ignore_failing_range_utilities", None
            ),
            name=d.get("name", None),
            reserved_value=d.get("reserved_value", None),
        )

    def adjust_params(self):
        if self.weights is None:
            self.weights = [1.0] * len(self.outcome_ranges)

    def eval(self, offer: Optional["Outcome"]) -> Optional[float]:
        if offer is None:
            return self.reserved_value
        u = float(0.0)
        for weight, outcome_range, mapping in zip(
            self.weights, self.outcome_ranges, self.mappings
        ):  # type: ignore
            # fail on any outcome_range that constrains issues not in the presented outcome
            if (
                outcome_range is not None
                and set(ikeys(outcome_range)) - set(ikeys(offer)) != set()
            ):
                if self.ignore_issues_not_in_input:
                    continue

                return None

            elif outcome_range is None or outcome_in_range(offer, outcome_range):
                if isinstance(mapping, float):
                    u += weight * mapping
                else:
                    # fail if any outcome_range utility_function cannot be calculated from the input
                    try:
                        # noinspection PyTypeChecker
                        u += weight * gmap(mapping, offer)
                    except KeyError:
                        if self.ignore_failing_range_utilities:
                            continue

                        return None

        return u


class NonlinearHyperRectangleUtilityFunction(UtilityFunction):
    """A utility function defined as a set of outcome_ranges.


    Args:
           hypervolumes: see `HyperRectangleUtilityFunction`
           mappings: see `HyperRectangleUtilityFunction`
           f: A nonlinear function to combine the results of `mappings`
           name: name of the utility function. If None a random name will be generated
    """

    def xml(self, issues: List[Issue]) -> str:
        raise NotImplementedError(f"Cannot convert {self.__class__.__name__} to xml")

    def __init__(
        self,
        hypervolumes: Iterable[OutcomeRange],
        mappings: List[OutcomeUtilityMapping],
        f: Callable[[List[float]], float],
        name: Optional[str] = None,
        reserved_value: float = float("-inf"),
        id=None,
    ) -> None:
        super().__init__(
            name=name,
            reserved_value=reserved_value,
            id=id,
        )
        self.hypervolumes = hypervolumes
        self.mappings = mappings
        self.f = f

    def to_dict(self):
        d = {PYTHON_CLASS_IDENTIFIER: get_full_type_name(type(self))}
        return dict(
            **d,
            hypervolumes=self.hypervolumes,
            mappings=self.mappings,
            f=serialize(self.f),
            name=self.name,
            reserved_value=self.reserved_value,
            id=self.id,
        )

    @classmethod
    def from_dict(cls, d):
        d.pop(PYTHON_CLASS_IDENTIFIER, None)
        return cls(
            hypervolumes=d.get("hypervolumes", None),
            mappings=d.get("mappings", None),
            f=deserialize(d.get("f", None)),
            name=d.get("name", None),
            reserved_value=d.get("reserved_value", None),
            id=d.get("id", None),
        )

    def eval(self, offer: Optional["Outcome"]) -> Optional[float]:
        if offer is None:
            return self.reserved_value
        if not isinstance(self.hypervolumes, Iterable):
            raise ValueError(
                "Hypervolumes are not set. Call set_params() or pass them through the constructor."
            )

        u = []
        for hypervolume, mapping in zip(self.hypervolumes, self.mappings):
            if outcome_in_range(offer, hypervolume):
                u.append(gmap(mapping, offer))
        return self.f(u)
