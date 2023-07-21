class Controller:
    """
    An abstract class to be entended to demonstrate different types of control. A PID subclass has also been provided
    """

    def update(self, input) -> float:
        """
        Handle a new update of this control loop given an effected input.

        :param error: The input to this controller for a given update. Usually an error or some other correctable value
        :type error: float

        :return: The system output from the controller, to be used as an effort value or for any other purpose
        :rtype: float
        """
        pass

    def is_done(self) -> bool:
        
        """
        :return: If the controller has reached or  settled at its desired value
        :rtype: bool
        """
        pass

    def clear_history(self):
        """
        Clears all past data, such as integral sums or any other previous data
        """
        pass