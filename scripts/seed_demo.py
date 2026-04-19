import asyncio
import logging
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.mail_config import MailConfig
from app.db.session import get_async_session_maker
from app.models import (
    Equipment,
    EquipmentType,
    EquipmentTypeParameter,
    MaintenancePlan,
    MaintenanceTask,
    Parameter,
    Role,
    TelemetryReading,
    ThresholdRule,
    User,
)
from app.repositories.equipment_parameter_state_repository import EquipmentParameterStateRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_state_repository import EquipmentStateRepository
from app.repositories.equipment_type_parameter_repository import EquipmentTypeParameterRepository
from app.repositories.event_repository import EventRepository
from app.repositories.maintenance_plan_repository import MaintenancePlanRepository
from app.repositories.maintenance_record_repository import MaintenanceRecordRepository
from app.repositories.maintenance_task_repository import MaintenanceTaskRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.telemetry_evaluation_repository import TelemetryEvaluationRepository
from app.repositories.telemetry_reading_repository import TelemetryReadingRepository
from app.repositories.threshold_rule_repository import ThresholdRuleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.maintenance import MaintenanceTaskComplete, MaintenanceTaskCreate
from app.schemas.telemetry_reading import TelemetryReadingCreate
from app.services.email_service import EmailService
from app.services.equipment_state_service import EquipmentStateService
from app.services.event_service import EventService
from app.services.maintenance_task_service import MaintenanceTaskService
from app.services.notification_service import NotificationService
from app.services.security_service import SecurityService
from app.services.telemetry_reading_service import TelemetryReadingService

DEMO_PASSWORD = "Demo12345!"

logging.basicConfig(level=logging.ERROR, format="%(message)s")


async def get_role(session: AsyncSession, name: str) -> Role:
    result = await session.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if role is None:
        raise RuntimeError(f"Role '{name}' was not found. Run Alembic migrations first.")
    return role


async def get_or_create_user(
    session: AsyncSession,
    *,
    role: Role,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
) -> User:
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if user is not None:
        user.roles = [role]
        user.is_active = True
        return user

    user = User(
        username=username,
        email=email,
        hashed_password=SecurityService.hash_password(DEMO_PASSWORD),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        roles=[role],
    )
    session.add(user)
    await session.flush()
    return user


async def get_or_create_equipment_type(
    session: AsyncSession,
    *,
    name: str,
    description: str,
) -> EquipmentType:
    result = await session.execute(select(EquipmentType).where(EquipmentType.name == name))
    equipment_type = result.scalar_one_or_none()
    if equipment_type is not None:
        return equipment_type

    equipment_type = EquipmentType(name=name, description=description, is_active=True)
    session.add(equipment_type)
    await session.flush()
    return equipment_type


async def get_or_create_parameter(
    session: AsyncSession,
    *,
    code: str,
    name: str,
    unit: str | None,
    description: str,
) -> Parameter:
    result = await session.execute(select(Parameter).where(Parameter.code == code))
    parameter = result.scalar_one_or_none()
    if parameter is not None:
        return parameter

    parameter = Parameter(
        code=code,
        name=name,
        unit=unit,
        description=description,
        is_active=True,
    )
    session.add(parameter)
    await session.flush()
    return parameter


async def ensure_binding(session: AsyncSession, equipment_type: EquipmentType, parameter: Parameter) -> None:
    result = await session.execute(
        select(EquipmentTypeParameter).where(
            EquipmentTypeParameter.equipment_type_id == equipment_type.id,
            EquipmentTypeParameter.parameter_id == parameter.id,
        )
    )
    if result.scalar_one_or_none() is not None:
        return

    session.add(
        EquipmentTypeParameter(
            equipment_type=equipment_type,
            parameter=parameter,
            is_required=True,
        )
    )
    await session.flush()


async def ensure_threshold_rule(
    session: AsyncSession,
    *,
    equipment_type: EquipmentType,
    parameter: Parameter,
    warning_min: Decimal | None = None,
    warning_max: Decimal | None = None,
    critical_min: Decimal | None = None,
    critical_max: Decimal | None = None,
) -> None:
    result = await session.execute(
        select(ThresholdRule).where(
            ThresholdRule.equipment_type_id == equipment_type.id,
            ThresholdRule.parameter_id == parameter.id,
        )
    )
    rule = result.scalar_one_or_none()
    if rule is not None:
        rule.warning_min = warning_min
        rule.warning_max = warning_max
        rule.critical_min = critical_min
        rule.critical_max = critical_max
        rule.is_active = True
        return

    session.add(
        ThresholdRule(
            equipment_type=equipment_type,
            parameter=parameter,
            warning_min=warning_min,
            warning_max=warning_max,
            critical_min=critical_min,
            critical_max=critical_max,
            is_active=True,
        )
    )
    await session.flush()


async def get_or_create_equipment(
    session: AsyncSession,
    *,
    equipment_type: EquipmentType,
    name: str,
    code: str,
    serial_number: str,
    location: str,
    description: str,
    specifications: dict,
) -> Equipment:
    result = await session.execute(select(Equipment).where(Equipment.code == code))
    equipment = result.scalar_one_or_none()
    if equipment is not None:
        return equipment

    equipment = Equipment(
        equipment_type=equipment_type,
        name=name,
        code=code,
        serial_number=serial_number,
        location=location,
        description=description,
        specifications=specifications,
        is_active=True,
    )
    session.add(equipment)
    await session.flush()
    return equipment


def build_telemetry_service(session: AsyncSession) -> TelemetryReadingService:
    email_service = EmailService(MailConfig(enabled=False))
    notification_service = NotificationService(
        NotificationRepository(session),
        UserRepository(session),
        email_service=email_service,
    )
    event_service = EventService(EventRepository(session), notification_service)
    equipment_state_service = EquipmentStateService(
        ThresholdRuleRepository(session),
        TelemetryEvaluationRepository(session),
        EquipmentParameterStateRepository(session),
        EquipmentStateRepository(session),
        event_service,
    )
    return TelemetryReadingService(
        TelemetryReadingRepository(session),
        EquipmentRepository(session),
        ParameterRepository(session),
        EquipmentTypeParameterRepository(session),
        equipment_state_service,
    )


def build_maintenance_service(session: AsyncSession) -> MaintenanceTaskService:
    return MaintenanceTaskService(
        MaintenanceTaskRepository(session),
        MaintenancePlanRepository(session),
        MaintenanceRecordRepository(session),
        EquipmentRepository(session),
        UserRepository(session),
        NotificationService(
            NotificationRepository(session),
            UserRepository(session),
            email_service=EmailService(MailConfig(enabled=False)),
        ),
    )


async def ensure_reading(
    session: AsyncSession,
    telemetry_service: TelemetryReadingService,
    *,
    equipment: Equipment,
    parameter: Parameter,
    value: str,
    minutes_ago: int,
) -> None:
    result = await session.execute(
        select(func.count()).select_from(TelemetryReading).where(
            TelemetryReading.equipment_id == equipment.id,
            TelemetryReading.parameter_id == parameter.id,
        )
    )
    if result.scalar_one() > 0:
        return

    await telemetry_service.create_reading(
        TelemetryReadingCreate(
            equipment_id=equipment.id,
            parameter_id=parameter.id,
            value=Decimal(value),
            measured_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
        )
    )


async def get_or_create_plan(session: AsyncSession, equipment_type: EquipmentType) -> MaintenancePlan:
    result = await session.execute(
        select(MaintenancePlan).where(
            MaintenancePlan.equipment_type_id == equipment_type.id,
            MaintenancePlan.title == "Демо: регламент диагностики ходовой части",
        )
    )
    plan = result.scalar_one_or_none()
    if plan is not None:
        return plan

    plan = MaintenancePlan(
        equipment_type=equipment_type,
        title="Демо: регламент диагностики ходовой части",
        description="Периодическая проверка узлов, связанных с нагрузкой и вибрацией.",
        interval_hours=250,
        interval_days=14,
        is_active=True,
    )
    session.add(plan)
    await session.flush()
    return plan


async def ensure_maintenance_tasks(
    session: AsyncSession,
    maintenance_service: MaintenanceTaskService,
    *,
    plan: MaintenancePlan,
    truck: Equipment,
    excavator: Equipment,
    manager: User,
    technician: User,
) -> None:
    result = await session.execute(
        select(MaintenanceTask).where(MaintenanceTask.title == "Демо: проверить двигатель после critical")
    )
    if result.scalar_one_or_none() is None:
        await maintenance_service.create_task(
            MaintenanceTaskCreate(
                plan_id=plan.id,
                equipment_id=truck.id,
                title="Демо: проверить двигатель после critical",
                description="Создано для демонстрации очереди ТО после критического события.",
                priority="high",
                due_at=datetime.now(UTC) + timedelta(days=1),
                assigned_to_user_id=technician.id,
            ),
            actor_user_id=manager.id,
        )

    result = await session.execute(
        select(MaintenanceTask).where(MaintenanceTask.title == "Демо: завершенная диагностика экскаватора")
    )
    completed_task = result.scalar_one_or_none()
    if completed_task is None:
        completed_task = await maintenance_service.create_task(
            MaintenanceTaskCreate(
                equipment_id=excavator.id,
                title="Демо: завершенная диагностика экскаватора",
                description="Задача для демонстрации истории выполненного ТО.",
                priority="medium",
                due_at=datetime.now(UTC) - timedelta(days=1),
                assigned_to_user_id=technician.id,
            ),
            actor_user_id=manager.id,
        )
        await maintenance_service.complete_task(
            completed_task.id,
            MaintenanceTaskComplete(
                summary="Диагностика выполнена, отклонения зафиксированы в журнале.",
                details="Проверены гидравлическая система, датчики температуры и вибрации.",
                performed_at=datetime.now(UTC) - timedelta(hours=6),
                performed_by_user_id=technician.id,
            ),
            actor_user_id=technician.id,
        )


async def seed_demo() -> None:
    session_maker = get_async_session_maker()
    if session_maker is None:
        raise RuntimeError("Database is not configured. Check SQLALCHEMY_URL settings.")

    async with session_maker() as session:
        admin_role = await get_role(session, "admin")
        manager_role = await get_role(session, "manager")
        technician_role = await get_role(session, "technician")

        admin = await get_or_create_user(
            session,
            role=admin_role,
            username="demo_admin",
            email="demo.admin@example.com",
            first_name="Демо",
            last_name="Администратор",
        )
        manager = await get_or_create_user(
            session,
            role=manager_role,
            username="demo_manager",
            email="demo.manager@example.com",
            first_name="Демо",
            last_name="Менеджер",
        )
        technician = await get_or_create_user(
            session,
            role=technician_role,
            username="demo_technician",
            email="demo.technician@example.com",
            first_name="Демо",
            last_name="Техник",
        )

        haul_truck_type = await get_or_create_equipment_type(
            session,
            name="Демо: карьерный самосвал",
            description="Тяжелая транспортная техника для демонстрации мониторинга.",
        )
        excavator_type = await get_or_create_equipment_type(
            session,
            name="Демо: гидравлический экскаватор",
            description="Экскаваторная техника для демонстрации состояния оборудования.",
        )
        drill_type = await get_or_create_equipment_type(
            session,
            name="Демо: буровая установка",
            description="Буровая техника для демонстрации нормальных параметров.",
        )

        temperature = await get_or_create_parameter(
            session,
            code="demo_engine_temperature",
            name="Демо: температура двигателя",
            unit="C",
            description="Температура двигателя в градусах Цельсия.",
        )
        vibration = await get_or_create_parameter(
            session,
            code="demo_vibration",
            name="Демо: вибрация",
            unit="mm/s",
            description="Уровень вибрации узлов оборудования.",
        )
        pressure = await get_or_create_parameter(
            session,
            code="demo_hydraulic_pressure",
            name="Демо: давление гидросистемы",
            unit="bar",
            description="Давление в гидравлическом контуре.",
        )

        for equipment_type in [haul_truck_type, excavator_type, drill_type]:
            await ensure_binding(session, equipment_type, temperature)
            await ensure_threshold_rule(
                session,
                equipment_type=equipment_type,
                parameter=temperature,
                warning_max=Decimal("80.0"),
                critical_max=Decimal("95.0"),
            )
            await ensure_binding(session, equipment_type, vibration)
            await ensure_threshold_rule(
                session,
                equipment_type=equipment_type,
                parameter=vibration,
                warning_max=Decimal("6.0"),
                critical_max=Decimal("10.0"),
            )

        await ensure_binding(session, drill_type, pressure)
        await ensure_threshold_rule(
            session,
            equipment_type=drill_type,
            parameter=pressure,
            warning_min=Decimal("12.0"),
            critical_min=Decimal("10.0"),
        )

        truck = await get_or_create_equipment(
            session,
            equipment_type=haul_truck_type,
            name="Демо: самосвал HT-118",
            code="DEMO-HT-118",
            serial_number="DEMO-SN-HT-118",
            location="Южная транспортная линия",
            description="Демо-единица с критическим состоянием двигателя.",
            specifications={"payload_tons": 190, "engine_power_kw": 1490},
        )
        excavator = await get_or_create_equipment(
            session,
            equipment_type=excavator_type,
            name="Демо: экскаватор EX-204",
            code="DEMO-EX-204",
            serial_number="DEMO-SN-EX-204",
            location="Северный карьер / сектор A2",
            description="Демо-единица с предупреждением по температуре.",
            specifications={"bucket_capacity_m3": 5.4, "engine_power_kw": 710},
        )
        drill = await get_or_create_equipment(
            session,
            equipment_type=drill_type,
            name="Демо: буровая установка DR-32",
            code="DEMO-DR-32",
            serial_number="DEMO-SN-DR-32",
            location="Западный уступ / взрывная зона 3",
            description="Демо-единица с нормальными параметрами.",
            specifications={"drill_depth_m": 18, "compressor_bar": 24},
        )

        await session.commit()

        telemetry_service = build_telemetry_service(session)
        await ensure_reading(
            session,
            telemetry_service,
            equipment=truck,
            parameter=temperature,
            value="99.0",
            minutes_ago=25,
        )
        await ensure_reading(
            session,
            telemetry_service,
            equipment=truck,
            parameter=vibration,
            value="8.0",
            minutes_ago=20,
        )
        await ensure_reading(
            session,
            telemetry_service,
            equipment=excavator,
            parameter=temperature,
            value="84.0",
            minutes_ago=18,
        )
        await ensure_reading(
            session,
            telemetry_service,
            equipment=drill,
            parameter=pressure,
            value="18.0",
            minutes_ago=15,
        )
        await session.commit()

        plan = await get_or_create_plan(session, haul_truck_type)
        await session.commit()
        await ensure_maintenance_tasks(
            session,
            build_maintenance_service(session),
            plan=plan,
            truck=truck,
            excavator=excavator,
            manager=manager,
            technician=technician,
        )
        await session.commit()

        print("Demo data is ready.")
        print("Users:")
        print(f"  admin:      {admin.email} / {DEMO_PASSWORD}")
        print(f"  manager:    {manager.email} / {DEMO_PASSWORD}")
        print(f"  technician: {technician.email} / {DEMO_PASSWORD}")
        print("Equipment codes: DEMO-HT-118, DEMO-EX-204, DEMO-DR-32")


if __name__ == "__main__":
    asyncio.run(seed_demo())
