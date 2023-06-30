from machine import Pin

class Button:

    _DEFAULT_BUTTON_INSTANCE = None

    @classmethod
    def get_default_button(cls):
        """
        Get the default button instance. This is a singleton, so only one instance of the button will ever exist.
        """
        if cls._DEFAULT_BUTTON_INSTANCE is None:
            cls._DEFAULT_BUTTON_INSTANCE = cls(22)
        return cls._DEFAULT_BUTTON_INSTANCE

    def __init__(self, pin:int):
        self.callback = None
        self.button = Pin(pin, Pin.IN, Pin.PULL_UP)

    def set_callback(self, trigger, callback):
        """
        Sets an interrupt callback to be triggered on a change in button state, specified by trigger. 
        Follow the link for more information on how to write an Interrupt Service Routine (ISR). 
        https://docs.micropython.org/en/latest/reference/isr_rules.html

        : param trigger: The type of trigger to be used for the interrupt
        : type trigger: Pin.IRQ_RISING | Pin.IRQ_FALLING
        : param callback: The function to be called when the interrupt is triggered
        : type callback: function | None
        """
        self.callback = callback
        self.button.irq(trigger=trigger, handler=self.callback)

    def is_pressed(self) -> bool:
        """
        Returns the state of the button

        : return: True if the button is pressed, False otherwise
        : rtype: bool
        """
        return not self.button.value()
