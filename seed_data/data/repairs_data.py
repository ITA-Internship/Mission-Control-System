from dataclasses import dataclass
from datetime import datetime, timezone

from repairs.models import ComponentType, DefectType, Severity


@dataclass(frozen=True)
class DefectReportSeed:
    drone_serial: str
    defect_type: str
    severity: str
    description: str
    detected_at: datetime
    reporter_username: str | None


@dataclass(frozen=True)
class ComponentReplacementSeed:
    drone_serial: str
    component_type: str
    component_name: str | None
    old_serial_number: str
    new_serial_number: str
    reason: str
    replaced_at: datetime
    replaced_by_username: str | None


DEFECT_REPORTS = (
    DefectReportSeed(
        drone_serial="FPV-ATK-24004",
        defect_type=DefectType.MOTOR,
        severity=Severity.HIGH,
        description="Front-right motor shows persistent vibration after landing.",
        detected_at=datetime(2026, 5, 8, 14, 25, tzinfo=timezone.utc),
        reporter_username="operator.bravo",
    ),
    DefectReportSeed(
        drone_serial="FPV-ATK-24005",
        defect_type=DefectType.FRAME,
        severity=Severity.CRITICAL,
        description="Rear arm cracked after emergency landing and needs replacement.",
        detected_at=datetime(2026, 5, 12, 10, 40, tzinfo=timezone.utc),
        reporter_username="tech.electro",
    ),
    DefectReportSeed(
        drone_serial="FPV-AER-24007",
        defect_type=DefectType.PROPELLER,
        severity=Severity.LOW,
        description="Propeller tips chipped after debris contact during urban sortie.",
        detected_at=datetime(2026, 5, 15, 8, 55, tzinfo=timezone.utc),
        reporter_username="operator.charlie",
    ),
    DefectReportSeed(
        drone_serial="FPV-AER-24001",
        defect_type=DefectType.CAMERA,
        severity=Severity.MEDIUM,
        description="Camera feed intermittently flickers during high-speed turns.",
        detected_at=datetime(2026, 5, 19, 16, 5, tzinfo=timezone.utc),
        reporter_username="operator.alpha",
    ),
)


COMPONENT_REPLACEMENTS = (
    ComponentReplacementSeed(
        drone_serial="FPV-ATK-24004",
        component_type=ComponentType.MOTOR,
        component_name=None,
        old_serial_number="TM-F60PV-24004-A",
        new_serial_number="TM-F60PV-24004-B",
        reason="Motor replaced after abnormal vibration was confirmed in inspection.",
        replaced_at=datetime(2026, 5, 9, 9, 30, tzinfo=timezone.utc),
        replaced_by_username="tech.airframe",
    ),
    ComponentReplacementSeed(
        drone_serial="FPV-ATK-24005",
        component_type=ComponentType.FRAME,
        component_name=None,
        old_serial_number="FRAME-SPEAR1-OLD",
        new_serial_number="FRAME-SPEAR1-NEW",
        reason="Frame section replaced after structural damage from forced landing.",
        replaced_at=datetime(2026, 5, 13, 11, 15, tzinfo=timezone.utc),
        replaced_by_username="tech.electro",
    ),
    ComponentReplacementSeed(
        drone_serial="FPV-AER-24007",
        component_type=ComponentType.PROPELLER,
        component_name=None,
        old_serial_number="PROP-SCOUT1-SET-A",
        new_serial_number="PROP-SCOUT1-SET-B",
        reason="Propeller set replaced after visible edge chips from debris contact.",
        replaced_at=datetime(2026, 5, 15, 12, 20, tzinfo=timezone.utc),
        replaced_by_username="tech.airframe",
    ),
    ComponentReplacementSeed(
        drone_serial="FPV-AER-24001",
        component_type=ComponentType.OTHER,
        component_name="Coaxial signal cable",
        old_serial_number="COAX-FE1-001",
        new_serial_number="COAX-FE1-002",
        reason="Signal cable replaced to resolve intermittent camera feed flicker.",
        replaced_at=datetime(2026, 5, 20, 10, 0, tzinfo=timezone.utc),
        replaced_by_username="tech.electro",
    ),
)
