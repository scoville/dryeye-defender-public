"""A widget for animated clickable toggle button"""
from typing import Any
from PySide6.QtCore import (
    Qt,
    QSize,
    QPoint,
    QPointF,
    QRectF,
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Slot,
    Property,
)

from PySide6.QtWidgets import QCheckBox
from PySide6.QtGui import QColor, QBrush, QPaintEvent, QPen, QPainter


class AnimatedToggle(QCheckBox):  # pylint: disable=too-many-instance-attributes
    """A widget for animated clickable toggle button"""
    _transparent_pen: QPen = QPen(Qt.GlobalColor.transparent)
    _light_grey_pen: QPen = QPen(Qt.GlobalColor.lightGray)

    def __init__(  # pylint: disable=too-many-arguments
        self,
        parent: Any = None,
        bar_color: Qt.GlobalColor = Qt.GlobalColor.gray,
        checked_color: str = "#00B0FF",
        handle_color: Qt.GlobalColor = Qt.GlobalColor.white,
        pulse_unchecked_color: str = "#44999999",
        pulse_checked_color: str = "#4400B0EE",
    ) -> None:
        super().__init__(parent)

        # Save our properties on the object via self, so we can access them later
        # in the paintEvent.
        self._bar_brush: QBrush = QBrush(bar_color)
        self._bar_checked_brush: QBrush = QBrush(QColor(checked_color).lighter())

        self._handle_brush: QBrush = QBrush(handle_color)
        self._handle_checked_brush: QBrush = QBrush(QColor(checked_color))

        self._pulse_unchecked_animation: QBrush = QBrush(QColor(pulse_unchecked_color))
        self._pulse_checked_animation: QBrush = QBrush(QColor(pulse_checked_color))

        # Setup the rest of the widget.

        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position: float = 0

        self._pulse_radius: float = 0

        self.animation: QPropertyAnimation = QPropertyAnimation(
            self, b"handle_position", self
        )
        self.animation.setEasingCurve(
            QEasingCurve.InOutCubic
        )
        self.animation.setDuration(200)  # time in ms

        self.pulse_anim: QPropertyAnimation = QPropertyAnimation(
            self, b"pulse_radius", self
        )
        self.pulse_anim.setDuration(350)  # time in ms
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(20)

        self.animations_group: QSequentialAnimationGroup = QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self.stateChanged.connect(self.setup_animation)

    def sizeHint(self) -> QSize:
        """Return a hint as to expected size of the button"""
        return QSize(58, 45)

    def hitButton(self, pos: QPoint) -> Any:
        """Return true if the provided mouse cursor point is within the button hit box"""
        return self.contentsRect().contains(pos)

    @Slot(int)
    def setup_animation(self, value: Any) -> None:
        """Setup the animation attribute"""
        self.animations_group.stop()
        if value:
            self.animation.setEndValue(1)
        else:
            self.animation.setEndValue(0)
        self.animations_group.start()

    def paintEvent(self, _: QPaintEvent) -> None:
        """Render the button"""
        cont_rect = self.contentsRect()
        handle_radius = round(0.24 * cont_rect.height())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(self._transparent_pen)
        bar_rect = QRectF(
            0, 0, cont_rect.width() - handle_radius, 0.40 * cont_rect.height()
        )
        bar_rect.moveCenter(cont_rect.center())
        rounding = bar_rect.height() / 2

        # the handle will move along this line
        trail_length = cont_rect.width() - 2 * handle_radius

        x_pos = cont_rect.x() + handle_radius + trail_length * self._handle_position

        if self.pulse_anim.state() == QPropertyAnimation.State.Running:
            painter.setBrush(
                self._pulse_checked_animation
                if self.isChecked()
                else self._pulse_unchecked_animation
            )
            painter.drawEllipse(
                QPointF(x_pos, bar_rect.center().y()),
                self._pulse_radius,
                self._pulse_radius,
            )

        if self.isChecked():
            painter.setBrush(self._bar_checked_brush)
            painter.drawRoundedRect(bar_rect, rounding, rounding)
            painter.setBrush(self._handle_checked_brush)

        else:
            painter.setBrush(self._bar_brush)
            painter.drawRoundedRect(bar_rect, rounding, rounding)
            painter.setPen(self._light_grey_pen)
            painter.setBrush(self._handle_brush)

        painter.drawEllipse(QPointF(x_pos, bar_rect.center().y()), handle_radius, handle_radius)

        # draw a box around the widget
        # painter.setPen(Qt.red)  # You can choose a different color if you prefer
        # painter.setBrush(Qt.NoBrush)  # No brush to fill the rectangle
        # painter.drawRect(self.contentsRect())

        painter.end()

    @Property(float)
    def handle_position(self):
        """Returns the handle position"""
        return self._handle_position

    @handle_position.setter  # type: ignore
    def handle_position(self, pos):
        """change the property
        we need to trigger QWidget.update() method, either by:
            1- calling it here [ what we're doing ].
            2- connecting the QPropertyAnimation.valueChanged() signal to it.
        """
        self._handle_position = pos
        self.update()

    @Property(float)
    def pulse_radius(self):
        """Returns the radius of the animated pulse of the toggle"""
        return self._pulse_radius

    @pulse_radius.setter  # type: ignore
    def pulse_radius(self, pos):
        """Sets the radius of the animated pulse of the toggle"""
        self._pulse_radius = pos
        self.update()
