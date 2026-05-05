# XRP Buzzer Library
# An easy-to-use library for playing notes and songs on the XRP buzzer
# Designed to be simple and fun for kids!

import machine
import time
from machine import Timer

class Buzzer:

    """
    A class to control the buzzer on XRP robots.

    Allows for playing individual notes or songs with various durations and tempos.
    Supports natural notes, sharps, and flats.
    """

    # Note names to semitone offset (semitones from C4 = 0)
    NOTE_OFFSETS = {
        # Natural notes
        "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
        # Sharps
        "C#": 1, "D#": 3, "F#": 6, "G#": 8, "A#": 10,
        # Flats
        "DB": 1, "EB": 3, "GB": 6, "AB": 8, "BB": 10,
    }
    
    _DEFAULT_BUZZER_INSTANCE = None

    @classmethod
    def get_default_buzzer(cls):
        """
        Get the default XRP buzzer instance. This is a singleton.

        :returns: The default Buzzer instance
        :rtype: Buzzer
        """
        if cls._DEFAULT_BUZZER_INSTANCE is None:
            cls._DEFAULT_BUZZER_INSTANCE = cls()
        return cls._DEFAULT_BUZZER_INSTANCE

    def __init__(self, buzzer_pin: int|str = None):
        """
        Initialize the buzzer.

        :param buzzer_pin: The pin number for the buzzer
        :type buzzer_pin: int|str
        """
        if buzzer_pin is not None:
            pin = buzzer_pin
        else:
            if hasattr(machine.Pin.board, "BOARD_BUZZER"):
                pin = "BOARD_BUZZER"
            else:
                raise Exception("No buzzer pin defined")

        self._pin = machine.Pin(pin)
        self._pwm = machine.PWM(self._pin)
        self._pwm.duty_u16(0)  # Start silent
        
        # State variables for non-blocking playback
        self._note_end_time = 0
        self._tempo = 120  # Default BPM
        self._in_gap = False
        self._gap_end_time = 0
        
        # Song playback state
        self._song = []
        self._song_index = 0
        self._song_tempo = 120
        
        # Timer for non-blocking updates (use virtual timer -1 to not conflict with user timers)
        self._timer = Timer(-1)
        self._timer_in_use = False
        
    def _compute_frequency(self, note: str, octave: int) -> int:
        """
        Compute the frequency for a note at a given octave.
        
        Uses the formula: f = 440 * 2^((n-69)/12)
        """
        if note == "R" or note == "REST":
            return 0
            
        note_offset = self.NOTE_OFFSETS.get(note.upper(), 0)
        midi_note = 60 + (octave - 4) * 12 + note_offset
        frequency = int(440 * (2 ** ((midi_note - 69) / 12)))
        
        return frequency
    
    def _duration_to_ms(self, duration, tempo: int = None) -> int:
        """
        Convert a duration name to milliseconds.
        """
        if tempo is None:
            tempo = self._tempo
            
        if isinstance(duration, str):
            duration_lower = duration.lower()
            if duration_lower == "whole":
                beats = 4
            elif duration_lower == "half":
                beats = 2
            elif duration_lower == "quarter":
                beats = 1
            elif duration_lower == "eighth":
                beats = 0.5
            elif duration_lower == "sixteenth":
                beats = 0.25
            else:
                beats = 1
        else:
            beats = duration
            
        ms_per_beat = 60000 / tempo
        return int(beats * ms_per_beat)
    
    def _parse_note(self, note_str: str):
        """Parse a note string like "C4", "C#4", "Db4" or "rest"."""
        note_str = note_str.strip().upper()
        
        if note_str == "REST" or note_str == "R":
            return ("R", 0)
        
        note_letter = note_str[0]
        if note_letter in "ABCDEFG":
            # Check for sharp (#) or flat (b) modifier
            note_with_modifier = note_letter
            octave_pos = 1
            if len(note_str) > 1:
                if note_str[1] == "#":
                    note_with_modifier = note_letter + "#"
                    octave_pos = 2
                elif note_str[1] == "B":
                    note_with_modifier = note_letter + "B"
                    octave_pos = 2
            
            try:
                if octave_pos < len(note_str):
                    octave = int(note_str[octave_pos])
                else:
                    octave = 4  # Default octave
                return (note_with_modifier, octave)
            except (ValueError, IndexError):
                return None
        
        return None
    
    def _update(self, timer):
        """
        Internal callback for non-blocking playback.
        Called by the timer when running in non-blocking mode.
        """
        now = time.ticks_ms()

        if self._in_gap:
            # Waiting for the inter-note silence to pass before advancing
            if time.ticks_diff(self._gap_end_time, now) <= 0:
                self._in_gap = False
                self._song_index += 1
                if self._song_index < len(self._song):
                    note, duration = self._song[self._song_index]
                    self._start_note(note, duration, self._song_tempo)
                else:
                    # Song finished
                    self._timer.deinit()
                    self._timer_in_use = False
        elif time.ticks_diff(self._note_end_time, now) <= 0:
            # Note done - silence and schedule a short gap before next note
            self._pwm.duty_u16(0)
            self._in_gap = True
            self._gap_end_time = time.ticks_add(now, 20)
    
    def _start_note(self, note: str, duration: str = "quarter", tempo: int = None):
        """Start playing a note (non-blocking helper)."""
        parsed = self._parse_note(note)
        if parsed is None:
            return
            
        note_letter, octave = parsed
        
        if note_letter == "R":
            frequency = 0
        else:
            frequency = self._compute_frequency(note_letter, octave)
        
        duration_ms = self._duration_to_ms(duration, tempo)
        
        if frequency > 0:
            self._pwm.freq(frequency)
            self._pwm.duty_u16(32768)  # 50% duty cycle
        
        self._note_end_time = time.ticks_add(time.ticks_ms(), duration_ms)
    
    def _play_tone_blocking(self, frequency: int, duration_ms: int):
        """Play a tone synchronously (blocking)."""
        if frequency <= 0:
            self._pwm.duty_u16(0)
        else:
            self._pwm.freq(frequency)
            self._pwm.duty_u16(32768)
        
        time.sleep_ms(duration_ms)
        self._pwm.duty_u16(0)
        time.sleep_ms(20)
    
    def play_note(self, note: str, duration: str = "quarter", blocking: bool = True, tempo: int = None):
        """
        Play a single note on the buzzer.

        :param note: The note to play (e.g., "C4", "G5", "C#4", "Db4", "rest")
        :type note: str
        :param duration: How long to play ("whole", "half", "quarter", "eighth", "sixteenth")
        :type duration: str
        :param blocking: If True, wait for note to finish. If False, return immediately.
        :type blocking: bool
        :param tempo: BPM (optional, uses default if not specified)
        :type tempo: int
        """
        parsed = self._parse_note(note)
        if parsed is None:
            return
            
        note_letter, octave = parsed
        
        if note_letter == "R":
            frequency = 0
        else:
            frequency = self._compute_frequency(note_letter, octave)
        
        duration_ms = self._duration_to_ms(duration, tempo)
        
        if blocking:
            self._play_tone_blocking(frequency, duration_ms)
        else:
            # Non-blocking - clear any active song so _update won't advance it
            self._song = []
            self._song_index = 0
            self._in_gap = False

            if frequency > 0:
                self._pwm.freq(frequency)
                self._pwm.duty_u16(32768)

            self._note_end_time = time.ticks_add(time.ticks_ms(), duration_ms)

            if not self._timer_in_use:
                self._timer.init(freq=100, callback=lambda t: self._update(t))
                self._timer_in_use = True

    def set_tempo(self, bpm: int):
        """
        Set the tempo for songs.

        :param bpm: The tempo in beats per minute
        :type bpm: int
        """
        self._tempo = bpm

    def play_song(self, song: list, tempo: int = None, blocking: bool = True):
        """
        Play a song from a list of notes.

        :param song: A list of (note, duration) tuples
        :type song: list
        :param tempo: BPM for this song (optional, uses default)
        :type tempo: int
        :param blocking: If True, wait for song to finish. If False, play in background.
        :type blocking: bool
        """
        
        if tempo is None:
            tempo = self._tempo
        
        if not song:
            return
            
        if blocking:
            # Play all notes synchronously
            for note, duration in song:
                parsed = self._parse_note(note)
                if parsed is None:
                    continue
                note_letter, octave = parsed
                if note_letter == "R":
                    frequency = 0
                else:
                    frequency = self._compute_frequency(note_letter, octave)
                duration_ms = self._duration_to_ms(duration, tempo)
                self._play_tone_blocking(frequency, duration_ms)
        else:
            # Non-blocking - stop any existing playback before starting new song
            if self._timer_in_use:
                self._timer.deinit()
                self._timer_in_use = False
            self._in_gap = False

            self._song = song
            self._song_index = 0
            self._song_tempo = tempo

            # Start playing first note
            note, duration = song[0]
            self._start_note(note, duration, tempo)
            self._song_index = 1

            # Start the timer for non-blocking playback
            self._timer.init(freq=100, callback=lambda t: self._update(t))
            self._timer_in_use = True
    
    def reset_buzzer(self):
        """
        Stops all sounds and timers immediately. 
        Resets the buzzer to a silent state.
        """
        # Stop PWM output
        self._pwm.duty_u16(0)
        
        # Stop background timers
        if self._timer_in_use:
            self._timer.deinit()
            self._timer_in_use = False
            
        # Reset song state
        self._song = []
        self._song_index = 0
        self._in_gap = False

    def play_move_it(self, blocking: bool = True):
        """
        Play "I Like to Move It" song.

        :param blocking: If True, wait for song to finish. If False, return immediately.
        :type blocking: bool
        """
        tempo = 120
        move_it = [
            ("rest", "eighth"),
            ("C4", "eighth"), ("C4", "eighth"), ("C4", "eighth"), ("C4", "eighth"),
            ("C4", "eighth"), ("C4", "eighth"), ("G3", "eighth"),
            ("rest", "eighth"),
            ("C4", "eighth"), ("C4", "eighth"), ("C4", "eighth"), ("C4", "eighth"),
            ("C4", "eighth"), ("C4", "eighth"), ("G3", "eighth"),
            ("rest", "eighth"),
            ("C4", "eighth"), ("C4", "eighth"), ("C4", "eighth"), ("C4", "eighth"),
            ("C4", "eighth"), ("C4", "eighth"), ("G3", "eighth"),
            ("rest", "eighth"),
            ("C4", "eighth"), ("C4", "eighth"), ("C4", "eighth"),
            ("rest", "eighth"), ("rest", "eighth"),
            ("G4", "eighth"), ("G4", "eighth"),
        ]
        self.play_song(move_it, tempo, blocking)

    def play_happy_birthday(self, blocking: bool = True):
        """
        Play "Happy Birthday" song.

        :param blocking: If True, wait for song to finish. If False, return immediately.
        :type blocking: bool
        """
        tempo = 140
        happy_birthday = [
            ("G4", "quarter"), ("G4", "quarter"), ("A4", "half"), ("G4", "half"),
            ("C5", "half"), ("B4", "whole"),
            ("G4", "quarter"), ("G4", "quarter"), ("A4", "half"), ("G4", "half"),
            ("D5", "half"), ("C5", "whole"),
            ("G4", "quarter"), ("G4", "quarter"), ("G5", "half"), ("C5", "half"),
            ("B4", "quarter"), ("A4", "quarter"), ("F5", "half"), ("E5", "half"),
            ("C5", "half"), ("D5", "half"), ("C5", "whole"),
        ]
        self.play_song(happy_birthday, tempo, blocking)
    
    def play_twinkle_twinkle(self, blocking: bool = True):
        """
        Play "Twinkle Twinkle Little Star" song.

        :param blocking: If True, wait for song to finish. If False, return immediately.
        :type blocking: bool
        """
        tempo = 100
        twinkle_twinkle = [
            ("C4", "quarter"), ("C4", "quarter"), ("G4", "quarter"), ("G4", "quarter"),
            ("A4", "quarter"), ("A4", "quarter"), ("G4", "half"),
            ("F4", "quarter"), ("F4", "quarter"), ("E4", "quarter"), ("E4", "quarter"),
            ("D4", "quarter"), ("D4", "quarter"), ("C4", "half"),
            ("G4", "quarter"), ("G4", "quarter"), ("F4", "quarter"), ("F4", "quarter"),
            ("E4", "quarter"), ("E4", "quarter"), ("D4", "half"),
            ("G4", "quarter"), ("G4", "quarter"), ("F4", "quarter"), ("F4", "quarter"),
            ("E4", "quarter"), ("E4", "quarter"), ("D4", "half"),
            ("C4", "quarter"), ("C4", "quarter"), ("G4", "quarter"), ("G4", "quarter"),
            ("A4", "quarter"), ("A4", "quarter"), ("G4", "half"),
            ("F4", "quarter"), ("F4", "quarter"), ("E4", "quarter"), ("E4", "quarter"),
            ("D4", "quarter"), ("D4", "quarter"), ("C4", "half"),
        ]
        self.play_song(twinkle_twinkle, tempo, blocking)
