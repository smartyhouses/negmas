import random
from typing import Any, Callable, Dict, List, Optional, Type, Union

from negmas.common import NegotiatorMechanismInterface
from negmas.helpers import get_class, get_full_type_name, make_range
from negmas.outcomes import Issue, Outcome
from negmas.serialization import PYTHON_CLASS_IDENTIFIER, deserialize, serialize

from .base import UtilityValue
from .base_crisp import UtilityFunction
from .static import DynamicPreferences

__all__ = [
    "LinDiscountedUFun",
    "ExpDiscountedUFun",
    "DiscountedUtilityFunction",
]


class DiscountedUtilityFunction(DynamicPreferences, UtilityFunction):
    """Base class for all discounted ufuns"""

    def __init__(self, ufun: UtilityFunction, **kwargs):
        super().__init__(**kwargs)
        self.ufun = ufun


class ExpDiscountedUFun(DiscountedUtilityFunction):
    """A discounted utility function based on some factor of the negotiation

    Args:
        ufun: The utility function that is being discounted
        discount: discount factor
        factor: str -> The name of the AgentMechanismInterface variable based on which discounting operate
        callable -> must receive a mechanism info object and returns a float representing the factor

    """

    def __init__(
        self,
        ufun: UtilityFunction,
        discount: Optional[float] = None,
        factor: Union[str, Callable[["NegotiatorMechanismInterface"], float]] = "step",
        name=None,
        reserved_value: UtilityValue = float("-inf"),
        dynamic_reservation=True,
        id=None,
        **kwargs,
    ):
        super().__init__(
            ufun=ufun, name=name, reserved_value=reserved_value, id=id, **kwargs
        )
        self.ufun = ufun
        self.ami = ufun.ami
        self.discount = discount
        self.factor = factor
        self.dynamic_reservation = dynamic_reservation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ufun": serialize(self.ufun),
            "discount": self.discount,
            "factor": self.factor,
            "dynamic_reservation": self.dynamic_reservation,
            "id": self.id,
            "name": self.name,
            "reserved_value": self.reserved_value,
            PYTHON_CLASS_IDENTIFIER: get_full_type_name(type(self)),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        d.pop(PYTHON_CLASS_IDENTIFIER, None)
        d["ufun"] = deserialize(d["ufun"])
        return cls(**d)

    @UtilityFunction.ami.setter
    def ami(self, value: NegotiatorMechanismInterface):
        UtilityFunction.ami.fset(self, value)
        if isinstance(self.ufun, UtilityFunction):
            self.ufun.ami = value

    @classmethod
    def random(
        cls,
        issues,
        reserved_value=(0.0, 1.0),
        normalized=True,
        discount_range=(0.8, 1.0),
        base_preferences_type: Union[
            str, Type[UtilityFunction]
        ] = "negmas.LinearUtilityAggregationFunction",
        **kwargs,
    ) -> "ExpDiscountedUFun":
        """Generates a random ufun of the given type"""
        reserved_value = make_range(reserved_value)
        discount_range = make_range(discount_range)
        kwargs["discount"] = (
            random.random() * (discount_range[1] - discount_range[0])
            + discount_range[0]
        )
        kwargs["reserved_value"] = (
            random.random() * (reserved_value[1] - reserved_value[0])
            + reserved_value[0]
        )
        return cls(
            get_class(base_preferences_type).random(
                issues, reserved_value=reserved_value, normalized=normalized
            ),
            **kwargs,
        )

    def eval(self, offer: "Outcome") -> UtilityValue:
        if offer is None and not self.dynamic_reservation:
            return self.reserved_value
        u = self.ufun(offer)
        if not self.discount or self.discount == 1.0 or u is None or self.ami is None:
            return u
        if isinstance(self.factor, str):
            factor = getattr(self.ami.state, self.factor)
        else:
            factor = self.factor(self.ami.state)
        return (self.discount ** factor) * u

    def xml(self, issues: List[Issue]) -> str:
        output = self.ufun.xml(issues)
        output += "</objective>\n"
        factor = None
        if self.factor is not None:
            factor = str(self.factor)
        if self.discount is not None:
            output += f'<discount_factor value="{self.discount}" '
            if factor is not None and factor != "step":
                output += f' variable="{factor}" '
            output += "/>\n"
        return output

    def __str__(self):
        return f"{self.ufun.type}-cost:{self.discount} based on {self.factor}"

    def __getattr__(self, item):
        return getattr(self.ufun, item)

    @property
    def base_type(self):
        return self.ufun.type

    @property
    def type(self):
        return self.ufun.type + "_exponentially_discounted"


class LinDiscountedUFun(DiscountedUtilityFunction):
    """A utility function with linear discounting based on some factor of the negotiation

    Args:

        ufun: The utility function that is being discounted
        cost: discount factor
        factor: str -> The name of the AgentMechanismInterface variable based on which discounting operate
        callable -> must receive a mechanism info object and returns a float representing the factor
        power: A power to raise the total cost to before discounting it from the utility_function value

    """

    def __init__(
        self,
        ufun: UtilityFunction,
        cost: Optional[float] = None,
        factor: Union[
            str, Callable[["NegotiatorMechanismInterface"], float]
        ] = "current_step",
        power: float = 1.0,
        name=None,
        reserved_value: UtilityValue = float("-inf"),
        dynamic_reservation=True,
        id=None,
        **kwargs,
    ):
        super().__init__(
            ufun=ufun, name=name, reserved_value=reserved_value, id=id, **kwargs
        )
        self.ufun = ufun
        self.ami = ufun.ami
        self.cost = cost
        self.factor = factor
        self.power = power
        self.dynamic_reservation = dynamic_reservation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ufun": serialize(self.ufun),
            "cost": self.cost,
            "power": self.power,
            "factor": self.factor,
            "dynamic_reservation": self.dynamic_reservation,
            "id": self.id,
            "name": self.name,
            "reserved_value": self.reserved_value,
            PYTHON_CLASS_IDENTIFIER: get_full_type_name(type(self)),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        d.pop(PYTHON_CLASS_IDENTIFIER, None)
        d["ufun"] = deserialize(d["ufun"])
        return cls(**d)

    @UtilityFunction.ami.setter
    def ami(self, value: NegotiatorMechanismInterface):
        UtilityFunction.ami.fset(self, value)
        if isinstance(self.ufun, UtilityFunction):
            self.ufun.ami = value

    def eval(self, offer: "Outcome") -> UtilityValue:
        if offer is None and not self.dynamic_reservation:
            return self.reserved_value
        u = self.ufun(offer)
        if not self.cost or self.cost == 0.0 or self.ami is None:
            return u
        if isinstance(self.factor, str):
            factor = getattr(self.ami.state, self.factor)
        else:
            factor = self.factor(self.ami.state)
        return u - ((factor * self.cost) ** self.power)

    def xml(self, issues: List[Issue]) -> str:
        output = self.ufun.xml(issues)
        output += "</objective>\n"
        factor = None
        if self.factor is not None:
            factor = str(self.factor)
        if self.cost is not None:
            output += f'<cost value="{self.cost}" '
            if factor is not None and factor != "step":
                output += f' variable="{factor}" '
            if self.power is not None and self.power != 1.0:
                output += f' power="{self.power}" '
            output += "/>\n"

        return output

    def __str__(self):
        return f"{self.ufun.type}-cost:{self.cost} raised to {self.power} based on {self.factor}"

    def __getattr__(self, item):
        return getattr(self.ufun, item)

    @property
    def base_type(self):
        return self.ufun.type

    @property
    def type(self):
        return self.ufun.type + "_linearly_discounted"

    @classmethod
    def random(
        cls,
        issues,
        reserved_value=(0.0, 1.0),
        normalized=True,
        cost_range=(0.8, 1.0),
        power_range=(0.0, 1.0),
        base_preferences_type: Type[
            UtilityFunction
        ] = "negmas.LinearUtilityAggregationFunction",
        **kwargs,
    ) -> "ExpDiscountedUFun":
        """Generates a random ufun of the given type"""
        reserved_value = make_range(reserved_value)
        cost_range = make_range(cost_range)
        power_range = make_range(power_range)
        kwargs["cost"] = (
            random.random() * (cost_range[1] - cost_range[0]) + cost_range[0]
        )
        kwargs["power"] = (
            random.random() * (power_range[1] - power_range[0]) + power_range[0]
        )
        kwargs["reserved_value"] = (
            random.random() * (reserved_value[1] - reserved_value[0])
            + reserved_value[0]
        )
        return cls(
            get_class(base_preferences_type)._random(
                issues, reserved_value=kwargs["reserved_value"], normalized=normalized
            ),
            **kwargs,
        )