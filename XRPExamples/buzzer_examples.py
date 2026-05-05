from XRPLib.defaults import *
import time

"""
    By the end of this file students will learn how to use the Buzzer class
    to play individual notes, custom songs, and how to make the robot 
    play music while it is moving.
"""

def simple_scale():
    """Plays a basic C major scale."""
    print("Playing a simple scale...")
    notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    for note in notes:
        buzzer.play_note(note, "quarter")

def custom_song_example():
    """Demonstrates how to create and play a custom list of notes."""
    print("Playing a custom melody...")
    # A song is a list of (note, duration) tuples
    # Durations can be "whole", "half", "quarter", "eighth", "sixteenth"
    my_song = [
        ("E4", "eighth"), ("G4", "eighth"), ("E5", "quarter"),
        ("rest", "eighth"),
        ("C4", "quarter"), ("G3", "half")
    ]
    
    # Set tempo to 140 Beats Per Minute
    buzzer.set_tempo(140)
    buzzer.play_song(my_song)

def siren():
    """Simple two-tone siren effect using individual notes."""
    print("Siren started!")
    for _ in range(3):
        buzzer.play_note("A4", "quarter")
        buzzer.play_note("E4", "quarter")

def musical_robot():
    """
    Playing music while driving.
    We use blocking=False so the code continues to the next line 
    while the music plays in the background.
    """
    print("Dancing with music!")
    
    # Start 'Move It' in the background
    buzzer.play_move_it(blocking=False)
    
    # While the song is playing, the robot can perform actions
    for i in range(4):
        drivetrain.set_effort(0.6, -0.6) # Spin right
        time.sleep(0.5)
        drivetrain.set_effort(-0.6, 0.6) # Spin left
        time.sleep(0.5)
        
    drivetrain.stop()
    print("Dance finished.")

def drive_and_beep():
    """Driving forward and playing a note at the same time."""
    # Start driving forward (this is non-blocking)
    drivetrain.set_effort(0.5, 0.5)
    
    # Play a long note (blocking=True) so the robot drives for the duration of the note
    print("Driving for a whole note...")
    buzzer.play_note("C5", "whole", blocking=True)
    
    drivetrain.stop()

def main():
    # Run the examples
    simple_scale()
    time.sleep(1)
    
    siren()
    time.sleep(1)
    
    musical_robot()

main()
