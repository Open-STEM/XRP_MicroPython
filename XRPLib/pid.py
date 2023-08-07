import time
from .controller import Controller

"""
PID controller with exit condition
"""

class PID(Controller):

    def __init__(self,
                 kp = 1.0,
                 ki = 0.0,
                 kd = 0.0,
                 min_output = 0.0,
                 max_output = 1.0,
                 max_derivative = None,
                 max_integral = None,
                 tolerance = 0.1,
                 tolerance_count = 1
                 ):
        """
        :param kp: proportional gain
        :param ki: integral gain
        :param kd: derivative gain
        :param min_output: minimum output
        :param max_output: maximum output
        :param max_derivative: maximum derivative (change per second)
        :param max_integral: maximum integral windup allowed (will cap integral at this value)
        :param tolerance: tolerance for exit condition
        :param tolerance_count: number of times the error needs to be within tolerance for is_done to return True
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_output = min_output
        self.max_output = max_output
        self.max_derivative = max_derivative
        self.max_integral = max_integral
        self.tolerance = tolerance
        self.tolerance_count = tolerance_count

        self.prev_error = 0
        self.prev_integral = 0
        self.prev_output = 0

        self.start_time = None
        self.prev_time = None

        # number of actual times in tolerance
        self.times = 0

    def _handle_exit_condition(self, error: float):
        if abs(error) < self.tolerance:
            # if error is within tolerance, increment times in tolerance
            self.times += 1
        else:
            # otherwise, reset times in tolerance, because we need to be in tolerance for numTimesInTolerance consecutive times
            self.times = 0

    def update(self, error: float) -> float:
        """
        Handle a new update of this PID loop given an error.

        :param error: The error of the system being controlled by this PID controller
        :type error: float

        :return: The system output from the controller, to be used as an effort value or for any other purpose
        :rtype: float
        """
        current_time = time.ticks_ms()
        if self.prev_time is None:
            # First update after instantiation
            self.start_time = current_time
            timestep = 0.01
        else:
            # get time delta in seconds
            timestep = time.ticks_diff(current_time, self.prev_time) / 1000
        self.prev_time = current_time # cache time for next update

        self._handle_exit_condition(error)

        integral = self.prev_integral + error * timestep
        
        if self.max_integral is not None:
            integral = max(-self.max_integral, min(self.max_integral, integral))

        derivative = (error - self.prev_error) / timestep

        # derive output
        output = self.kp * error + self.ki * integral + self.kd * derivative
        self.prev_error = error
        self.prev_integral = integral

        # Bound output by minimum
        if output > 0:
            output = max(self.min_output, output)
        else:
            output = min(-self.min_output, output)
        
        # Bound output by maximum
        output = max(-self.max_output, min(self.max_output, output))

        # Bound output by maximum acceleration
        if self.max_derivative is not None:
            lower_bound = self.prev_output - self.max_derivative * timestep
            upper_bound = self.prev_output + self.max_derivative * timestep
            output = max(lower_bound, min(upper_bound, output))

        # cache output for next update
        self.prev_output = output

        return output
    
    def is_done(self) -> bool:
        """
        :return: if error is within tolerance for numTimesInTolerance consecutive times, or timed out
        :rtype: bool
        """
        return self.times >= self.tolerance_count
    
    def clear_history(self):
        self.prev_error = 0
        self.prev_integral = 0
        self.prev_output = 0
        self.prev_time = None
        self.times = 0