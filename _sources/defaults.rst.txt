XRPLib.defaults
---------------

In addition to you being able to construct any of the classes in XRPLib by 
themselves, you are also able to import all of the default objects needed for
normal robot operations, using just one line.

By running ``from XRPLib.defaults import *``, you import all of the 
pre-constructed objects, as specified and named below:

.. literalinclude:: ../XRPLib/defaults.py
    :caption: ../XRPLib/defaults.py
    :linenos:

We use this import in most of the curriculum and example programs,
which is why you will often see the DifferentialDrive class refered to as
just "drivetrain".

Here's an example of that from ``drive_examples.py``:

>>> from XRPLib.defaults import *
>>> # Follow the perimeter of a square with variable sidelength
>>> def square(sidelength):
>>> for sides in range(4):
>>>        drivetrain.straight(sidelength, 80)
>>>        drivetrain.turn(90)``