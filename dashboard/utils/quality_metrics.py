"""Quality Metrics Calculation for Production Control System"""
import random
from datetime import datetime, timedelta
import pandas as pd
class QualityTracker:
    def __init__(self):
        self.defect_types = {
            'Flash': 0,
            'Short Shot': 0,
            'Sink Mark': 0,
            'Warpage': 0,
            'Contamination': 0
        }
    def generate_mock_defects(self):
        """Generate mock defect data for demonstration"""
        total_parts = random.randint(800, 1200)
        defects = {
            'Flash': random.randint(5, 15),
            'Short Shot': random.randint(2, 8),
            'Sink Mark': random.randint(3, 10),
            'Warpage': random.randint(1, 5),
            'Contamination': random.randint(1, 4)
        }
        total_defects = sum(defects.values())
        return {
            'total_parts': total_parts,
            'total_defects': total_defects,
            'defect_breakdown': defects,
            'fpy': ((total_parts - total_defects) / total_parts * 100) if total_parts > 0 else 0,
            'scrap_rate': (total_defects / total_parts * 100) if total_parts > 0 else 0
        }
    def generate_hourly_quality_data(self, hours=24):
        """Generate hourly quality data for trends"""
        data = []
        now = datetime.now()
        for i in range(hours):
            hour_time = now - timedelta(hours=hours-i-1)
            parts = random.randint(180, 260)
            defects = random.randint(5, 25)
            data.append({
                'Time': hour_time,
                'Parts Produced': parts,
                'Defects': defects,
                'FPY %': ((parts - defects) / parts * 100) if parts > 0 else 0
            })
        return pd.DataFrame(data)
    def calculate_shift_quality(self, shift: str):
        """Calculate quality metrics for a specific shift"""
        base_fpy = 97.5
        if shift == 'A':
            fpy = base_fpy + random.uniform(-1, 1)
        elif shift == 'B':
            fpy = base_fpy + random.uniform(-2, 0.5)
        else:
            fpy = base_fpy + random.uniform(-1.5, 0.5)
        return {
            'shift': shift,
            'fpy': fpy,
            'parts': random.randint(1800, 2200),
            'defects': random.randint(30, 60)
        }
def calculate_overall_oee(availability: float, performance: float, quality: float) -> float:
    """Calculate Overall Equipment Effectiveness"""
    return (availability * performance * quality) / 10000
