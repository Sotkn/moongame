"""Frame loop. Simulation.tick() returns SimEvents; Session applies them."""

from dataclasses import dataclass

from moon_game.clock import FrameClock
from moon_game.commands import PlayerCommand
from moon_game.entities import ChooseDelivery, Delivery, DeliveryState, OrderStatus
from moon_game.game_state import GamePhase, GameState
from moon_game.simulation import (
    DayEnded,
    DeliveryCompleted,
    HazardStruck,
    SimEvent,
    Simulation,
)
from moon_game.storage import log_delivery_end, log_delivery_start, log_event
from moon_game.ui import Ui
from moon_game.window_events import WindowEventKind, poll_window_events


@dataclass(frozen=True)
class _JournalView:
    phase: GamePhase
    delivery_states: tuple[tuple[int, DeliveryState], ...]
    order_statuses: tuple[tuple[int, OrderStatus], ...]


class Session:
    def __init__(self, ui: Ui, state: GameState) -> None:
        self._ui = ui
        self._state = state
        self._simulation = Simulation()
        self._clock = FrameClock()

    def run(self) -> None:
        while True:
            dt = self._clock.dt()
            events = poll_window_events()
            if any(event.kind is WindowEventKind.QUIT for event in events):
                break
            commands: list[PlayerCommand] = self._ui.read_commands(events, self._state)
            before = self._journal_view()
            for command in commands:
                command.apply(self._state)
            if commands:
                self._write_journal(before)
            if self._should_tick():
                before = self._journal_view()
                sim_events = self._simulation.tick(self._state, dt)
                for sim_event in sim_events:
                    self._apply_sim_event(sim_event)
                self._write_journal(before, sim_events)
            self._ui.draw(self._state)

    def _should_tick(self) -> bool:
        return self._state.phase is GamePhase.RUNNING and not self._state.paused

    def _apply_sim_event(self, event: SimEvent) -> None:
        if isinstance(event, HazardStruck):
            self._state.hazard_notice = (
                f"{event.rover.name} попал в аварию на маршруте "
                f"{event.route.endpoint.name} {event.route.name}"
            )
            return
        if isinstance(event, DeliveryCompleted):
            self._state.pending_event = ChooseDelivery(rover=event.rover)
            self._state.paused = True
            return
        if isinstance(event, DayEnded):
            self._state.phase = GamePhase.DAY_END
            self._state.pending_event = None
            self._state.hazard_notice = None

    def _journal_view(self) -> _JournalView:
        return _JournalView(
            phase=self._state.phase,
            delivery_states=tuple(
                (id(delivery), delivery.state) for delivery in self._state.deliveries
            ),
            order_statuses=tuple(
                (id(order), order.status) for order in self._state.orders
            ),
        )

    def _write_journal(
        self,
        before: _JournalView,
        sim_events: list[SimEvent] | None = None,
    ) -> None:
        known_deliveries = dict(before.delivery_states)
        for delivery in self._state.deliveries:
            previous = known_deliveries.get(id(delivery))
            if previous is None:
                self._log_delivery_start(delivery)
                continue
            if delivery.state is previous:
                continue
            self._log_delivery_end(delivery)
        known_orders = dict(before.order_statuses)
        for order in self._state.orders:
            previous = known_orders.get(id(order))
            if previous is OrderStatus.AVAILABLE and order.status is OrderStatus.FAILED:
                log_event(
                    "order_failed",
                    day_number=self._state.day_number,
                    elapsed=self._state.day_elapsed,
                    order_id=order.id,
                )
        if (
            before.phase is not GamePhase.DAY_END
            and self._state.phase is GamePhase.DAY_END
        ):
            log_event(
                "day_ended",
                day_number=self._state.day_number,
                elapsed=self._state.day_elapsed,
            )
        for event in sim_events or ():
            if isinstance(event, HazardStruck):
                log_event(
                    "hazard_struck",
                    day_number=self._state.day_number,
                    elapsed=self._state.day_elapsed,
                    rover_id=event.rover.id,
                    route_id=event.route.id,
                )

    def _log_delivery_start(self, delivery: Delivery) -> None:
        log_delivery_start(
            delivery.rover.id,
            delivery.order.id,
            delivery.route.id,
            day_number=self._state.day_number,
            started_at=self._state.day_elapsed,
        )
        log_event(
            "delivery_started",
            day_number=self._state.day_number,
            elapsed=self._state.day_elapsed,
            rover_id=delivery.rover.id,
            order_id=delivery.order.id,
            route_id=delivery.route.id,
        )
        if delivery.state is not DeliveryState.ACTIVE:
            self._log_delivery_end(delivery)

    def _log_delivery_end(self, delivery: Delivery) -> None:
        completed = delivery.state is DeliveryState.COMPLETED
        log_delivery_end(
            delivery.rover.id,
            state=delivery.state.value,
            finished_at=self._state.day_elapsed,
            reward=delivery.order.reward if completed else 0,
        )
        log_event(
            "delivery_completed" if completed else "delivery_aborted",
            day_number=self._state.day_number,
            elapsed=self._state.day_elapsed,
            rover_id=delivery.rover.id,
            order_id=delivery.order.id,
            route_id=delivery.route.id,
        )
