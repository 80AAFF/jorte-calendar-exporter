# Jorte Calendar Exporter

## Overview
Jorte Calendar Exporter is a Python script designed to interact with the Jorte API, fetch calendar events, and export them to iCalendar (.ics) format. This script handles the authentication with Jorte, retrieves calendar details, filters and processes events, and finally generates iCalendar files for each calendar.

## Features
- Authenticate with Jorte API using provided credentials.
- Fetch and process calendar events from Jorte.
- Remove duplicate events and group event sequences.
- Export processed events to iCalendar format.
- Support for recurring events with dynamic interval handling.
- Logging of operations and error handling.

## Requirements
- Python 3.x

## Setup and Configuration

### Python Installation
Ensure Python 3.x is installed on your system. You can verify the installation by running `python --version` in your terminal.

### Installing Dependencies
Install the required Python packages listed in the `requirements.txt` file by executing the following command in the terminal:

```bash
pip install -r requirements.txt
```

This command will automatically install all the necessary dependencies for the script.

### Configuring Settings
1. Locate the `settings.py.sample` file in the project directory. This file contains template configurations for the script.
2. Copy `settings.py.sample` to a new file named `settings.py`. You can use the following command:

   ```bash
   cp settings.py.sample settings.py
   ```

3. Open `settings.py` in a text editor and fill in your specific configuration values such as Jorte API credentials, export start and end dates, and any other required settings.

   ```python
   # Example configuration in settings.py
   USERNAME = 'your_username_here'
   PASSWORD = 'your_password_here'
   EXPORT_START_YEAR = 2024
   EXPORT_START_MONTH = 1
   EXPORT_END_YEAR = 2024
   EXPORT_END_MONTH = 12
   ```

4. Save the changes to `settings.py`.

## Usage
After completing the setup and configuration, run the script by executing:

```bash
python export-jorte-to-ical.py
```

Monitor the output and logs to ensure that the script is running as expected.

## Logging
- The script uses Python's `logging` module for logging.
- Configure logging settings in `logging.ini` file.
- Standard information and debug messages are logged for monitoring script execution.
- Logs are sent to `stdout` and the file `export-jorte-to-ical.log`

## Output
- The script generates `.ics` files in the current directory.
- Each calendar from Jorte results in a separate `.ics` file named after its calendar ID in Jorte.

## Limitations
- The script currently does not handle timezone conversions for events.
- Only supports basic recurrence rules for events that are estimated based on the interval with which the events occurred in the past.

## License
MIT License
