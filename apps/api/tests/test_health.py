import unittest
from datetime import date, timedelta
from decimal import Decimal

from pydantic import ValidationError

from app.schemas.health import WeightLogPut, WorkoutCreate
from app.services.health import health_totals


class HealthRulesTest(unittest.TestCase):
    def test_null_weights_range_average_and_duration(self) -> None:
        start = date(2026, 9, 1)
        summary = health_totals(
            [
                (start, Decimal("82.00")),
                (start + timedelta(days=1), None),
                (start + timedelta(days=2), Decimal("81.55")),
            ],
            95,
            start,
            start + timedelta(days=6),
        )
        self.assertEqual(summary.latest_weight_kg, Decimal("81.55"))
        self.assertEqual(summary.latest_weight_date, start + timedelta(days=2))
        self.assertEqual(summary.average_weight_kg, Decimal("81.78"))
        self.assertEqual(summary.recorded_weight_days, 2)
        self.assertEqual(summary.workout_minutes, 95)

        empty = health_totals([], 0, start, start)
        self.assertIsNone(empty.latest_weight_kg)
        self.assertIsNone(empty.average_weight_kg)

    def test_health_input_boundaries(self) -> None:
        with self.assertRaises(ValidationError):
            WeightLogPut(note="   ")
        with self.assertRaises(ValidationError):
            WorkoutCreate(
                id="00000000-0000-4000-8000-000000000001",
                occurred_on=date.today(),
                activity_type="walk",
                duration_minutes=0,
            )


if __name__ == "__main__":
    unittest.main()
