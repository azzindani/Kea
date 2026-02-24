from kernel.scoring.engine import evaluate_reward_compliance
from kernel.scoring.types import Constraint, ConstraintType


def test_evaluate_reward_compliance():
    c1 = Constraint(constraint_id="c1", constraint_type=ConstraintType.MUST_CONTAIN, value="blue")
    c2 = Constraint(constraint_id="c2", constraint_type=ConstraintType.MUST_NOT_CONTAIN, value="red")

    score = evaluate_reward_compliance("the sky is blue", [c1, c2])
    assert score == 1.0 # 2/2

    score2 = evaluate_reward_compliance("the car is red", [c1, c2])
    assert score2 == 0.0 # 0/2

    score3 = evaluate_reward_compliance("the car is green", [c1, c2])
    assert score3 == 0.5 # 1/2
