import time

"""
PID controller with exit condition
"""

class PID:

    def __init__(self,
                 kp = 1.0,
                 ki = 0.0,
                 kd = 0.0,
                 minOutput = 0.0,
                 maxOutput = 1.0,
                 maxDerivative = None,
                 tolerance = 0.1,
                 toleranceCount = 1,
                 timeout = None
                 ):
        """
        :param kp: proportional gain
        :param ki: integral gain
        :param kd: derivative gain
        :param minOutput: minimum output
        :param maxOutput: maximum output
        :param maxDerivative: maximum derivative (change per second)
        :param tolerance: tolerance for exit condition
        :param numTimesInTolerance: number of times in tolerance for exit condition
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.minOutput = minOutput
        self.maxOutput = maxOutput
        self.maxDerivative = maxDerivative
        self.tolerance = tolerance
        self.toleranceCount = toleranceCount

        self.prevError = 0
        self.prevIntegral = 0
        self.prevOutput = 0

        self.timeout = timeout

        self.startTime = None
        self.prevTime = None

        # number of actual times in tolerance
        self.times = 0

    def _handle_exit_condition(self, error):

        if abs(error) < self.tolerance:
            # if error is within tolerance, increment times in tolerance
            self.times += 1
        else:
            # otherwise, reset times in tolerance, because we need to be in tolerance for numTimesInTolerance consecutive times
            self.times = 0

    def tick(self, error) -> float:

        currentTime = time.ticks_ms()
        if self.prevTime is None:
            # First tick after instantiation
            self.startTime = currentTime
            timestep = 0.01
        else:
            # get time delta in seconds
            timestep = time.ticks_diff(currentTime, self.prevTime) / 1000
        self.prevTime = currentTime # cache time for next tick

        self._handle_exit_condition(error)

        integral = self.prevIntegral + error * timestep
        derivative = (error - self.prevError) / timestep

        # derive output
        output = self.kp * error + self.ki * integral + self.kd * derivative
        self.prevError = error
        self.prevIntegral = integral

        # Bound output by minimum
        if output > 0:
            output = max(self.minOutput, output)
        else:
            output = max(-self.minOutput, output)
        
        # Bound output by maximum
        output = max(-self.maxOutput, min(self.maxOutput, output))

        # Bound output by maximum acceleration
        if self.maxDerivative is not None:
            lowerBound = self.prevOutput - self.maxDerivative * timestep
            upperBound = self.prevOutput + self.maxDerivative * timestep
            output = max(lowerBound, min(upperBound, output))

        # cache output for next tick
        self.prevOutput = output

        return output
    
    def is_done(self) -> bool:
        """
        :return: if error is within tolerance for numTimesInTolerance consecutive times, or timed out
        """
        if self.timeout is not None:
            if time.ticks_diff(time.ticks_ms(), self.startTime) / 1000 > self.timeout:
                return True

        return self.times >= self.toleranceCount