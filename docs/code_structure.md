
# Code Structure

1. `__main__.py` is the entry point for the GUI. It creates the main window and sets up the main loop.
 `Application() --> MainWindow() --> Window()`

2. `Window()` is in `widgets/settings_window.py` and hold the 'Single Page Application'.

3. The API for the DB is held in an instance of `BlinkHistoryDryEyeDefender(get_saved_data_path())` which connects to the database (or creates it) at `get_saved_data_path()`

4. In `Window().__init__()` we first initialize this instance of `BlinkHistoryDryEyeDefender()`, then pass it to `BlinkModelThread()` which is a dedicated instance for managing inference from the submodule `blinkdetector`.link_api.update(closed_eye_img)
    assert update_dict["blink_value"] ==

The inference is done by one frame per thread, and threads are arranged in a FIFO manner where only one thread operates at a time, DryEye Defender uses a timer to schedule delay between thread invocations so we can control how resource heavy the inference is.

So on the master thread we have the GUI, and on slave thread(s) we have managing of the inference.

Both master and child share connection to an sqlite3 DB. The master thread uses `BlinkHistoryDryEyeDefender()` API to read information from the DB. The child thread writes data each frame to the DB via a subclass of `BlinkHistoryDryEyeDefender()`.