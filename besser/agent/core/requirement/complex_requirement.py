from enum import Enum

from besser.agent.core.requirement.requirement import Requirement, RequirementDefinition
from besser.agent.core.session import Session


class BooleanOperator(Enum):
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'


class ComplexRequirement(Requirement):

    def __init__(self, operator: BooleanOperator, requirements: list[Requirement]):
        # TODO: Run SAT solver to evaluate satisfiability of expression
        # Some libraries: pip install z3-solver, python-sat, pyminisat, pycosat
        # TODO: Convert to CNF? (OR conjunctions only)

        super().__init__()
        if operator in [BooleanOperator.AND, BooleanOperator.OR] and len(requirements) < 2:
            raise ValueError(f'Operator {operator} requires at least 2 expressions')
        if operator == BooleanOperator.NOT and len(requirements) != 1:
            raise ValueError(f'Operator {operator} requires 1 expression')
        self.operator: BooleanOperator = operator
        self.requirements: list[Requirement] = requirements

    def __str__(self):
        return f'{self.operator}{[expression.__str__() for expression in self.requirements]}'

    def evaluate(self, session: Session) -> bool:
        if self.operator == BooleanOperator.AND:
            return all([requirement.evaluate(session) for requirement in self.requirements])
        if self.operator == BooleanOperator.OR:
            return any([requirement.evaluate(session) for requirement in self.requirements])
        if self.operator == BooleanOperator.NOT:
            return not self.requirements[0].evaluate(session)


def AND(requirements: list[Requirement]) -> ComplexRequirement:
    return ComplexRequirement(operator=BooleanOperator.AND, requirements=requirements)


def OR(requirements: list[Requirement]) -> ComplexRequirement:
    return ComplexRequirement(operator=BooleanOperator.OR, requirements=requirements)


def NOT(requirement: Requirement) -> ComplexRequirement:
    return ComplexRequirement(operator=BooleanOperator.NOT, requirements=[requirement])
