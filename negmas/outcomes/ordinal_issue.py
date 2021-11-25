import random
from typing import Generator

from negmas.helpers import unique_name
from negmas.outcomes.base_issue import DiscreteIssue

__all__ = ["OrdinalIssue"]


class OrdinalIssue(DiscreteIssue):
    def __init__(self, values, name=None, id=None) -> None:
        super().__init__(values, name, id)
        values = list(values)
        types = set(type(_) for _ in values)
        if len(types) != 1:
            raise ValueError(
                f"Found the following types in the list of values for an "
                f"ordinal issue ({types}). Can only have one type. Try "
                f"CategoricalIssue"
            )
        self._value_type = type(values[0])
        self._n_values = len(values)
        self.min_value, self.max_value = min(values), max(values)

    def _to_xml_str(self, indx, enumerate_integer=False):
        output = f'    <issue etype="discrete" index="{indx + 1}" name="{self.name}" type="discrete" vtype="discrete">\n'

        for i, v in enumerate(self._values):
            output += f'        <item index="{i + 1}" value="{v}" cost="0" description="{v}">\n        </item>\n'
        output += "    </issue>\n"
        return output

    @property
    def all(self) -> Generator:
        yield from self._values  # type: ignore

    def rand_invalid(self):
        """Pick a random *invalid* value"""

        if self.is_float():
            return random.random() * self.max_value + self.max_value * 1.1

        if self.is_integer():
            return random.randint(self.max_value + 1, self.max_value * 2)

        return unique_name("") + str(random.choice(self._values)) + unique_name("")