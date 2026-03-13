"""
Unit tests for Webserver HTML generation and button registration.
"""
import pytest
from XRPLib.webserver import Webserver


class TestWebserverButtons:
    def test_add_button(self):
        ws = Webserver()
        ws.add_button("test_btn", lambda: None)
        assert "test_btn" in ws.buttons

    def test_register_forward_enables_arrows(self):
        ws = Webserver()
        assert ws.display_arrows is False
        ws.registerForwardButton(lambda: None)
        assert ws.display_arrows is True

    def test_register_all_arrow_buttons(self):
        ws = Webserver()
        ws.registerForwardButton(lambda: None)
        ws.registerBackwardButton(lambda: None)
        ws.registerLeftButton(lambda: None)
        ws.registerRightButton(lambda: None)
        ws.registerStopButton(lambda: None)
        assert ws.display_arrows is True
        assert callable(ws.buttons["forwardButton"])
        assert callable(ws.buttons["backButton"])
        assert callable(ws.buttons["leftButton"])
        assert callable(ws.buttons["rightButton"])
        assert callable(ws.buttons["stopButton"])


class TestWebserverHTML:
    def test_html_contains_title(self):
        ws = Webserver()
        html = ws._generateHTML()
        assert "XRP control page" in html

    def test_html_contains_custom_button(self):
        ws = Webserver()
        ws.add_button("my_action", lambda: None)
        html = ws._generateHTML()
        assert "my_action" in html

    def test_html_excludes_arrow_buttons_from_custom_list(self):
        ws = Webserver()
        ws.registerForwardButton(lambda: None)
        html = ws._generateHTML()
        # Arrow buttons should be in the arrow HTML, not duplicated as custom buttons
        # Check that forwardButton isn't in a user-button form
        assert 'class="user-button" name=forwardButton' not in html

    def test_html_contains_logged_data(self):
        ws = Webserver()
        ws.log_data("Speed", 42)
        html = ws._generateHTML()
        assert "Speed" in html
        assert "42" in html

    def test_html_arrows_included_when_enabled(self):
        ws = Webserver()
        ws.registerForwardButton(lambda: None)
        html = ws._generateHTML()
        assert "&#8593;" in html  # up arrow

    def test_html_arrows_excluded_when_disabled(self):
        ws = Webserver()
        html = ws._generateHTML()
        assert "&#8593;" not in html


class TestWebserverLogData:
    def test_log_data_stores(self):
        ws = Webserver()
        ws.log_data("distance", 25.3)
        assert ws.logged_data["distance"] == 25.3

    def test_log_data_overwrites(self):
        ws = Webserver()
        ws.log_data("speed", 10)
        ws.log_data("speed", 20)
        assert ws.logged_data["speed"] == 20


class TestWebserverFunctionHandler:
    def test_handle_valid_function(self):
        ws = Webserver()
        called = []
        ws.add_button("test", lambda: called.append(True))
        result = ws._handleUserFunctionRequest("test")
        assert result is True
        assert len(called) == 1

    def test_handle_invalid_function(self):
        ws = Webserver()
        # Unknown button name should raise KeyError, caught internally
        # but the method catches RuntimeError, not KeyError, so this actually raises
        with pytest.raises(KeyError):
            ws._handleUserFunctionRequest("nonexistent")
