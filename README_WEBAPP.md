# Milk Bottle Monitoring Web Application

A real-time web dashboard for monitoring milk bottle inventory using Roboflow workflows.

## Features

- **Live Video Feed**: Real-time video stream with overlay showing current counts and missing bottle alerts
- **Analytics Dashboard**: Interactive graph showing bottle counts over the past hour
- **Alert Tracking**: Historical log of all alerts sent by Roboflow with timestamps
- **Real-time Updates**: WebSocket-based updates for instant data refresh
- **Data Persistence**: All counts and alerts saved to CSV files with timestamps
- **Clean UI**: Modern, responsive interface with tab-based navigation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your `config.env` file has the required variables:
```
ROBOFLOW_API_KEY=your_api_key_here
```

## Running the Application

### Option 1: Using the startup script (Recommended)

The startup script automatically activates the virtual environment from the parent directory:

```bash
./run_webapp.sh
```

### Option 2: Manual activation

1. Activate the virtual environment:
```bash
source ../venv/bin/activate
```

2. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5050
```

If that doesn't work, try:
```
http://127.0.0.1:5050
```

3. You'll see three tabs:
   - **Live Video**: Real-time video feed with count overlay
   - **Analytics**: Graph showing counts over time with current count cards
   - **Alerts**: Historical log of all alerts sent by Roboflow

## Architecture

- **Backend**: Flask + Flask-SocketIO for real-time communication
- **Frontend**: HTML/CSS/JavaScript with Plotly for graphing
- **Video Processing**: OpenCV for frame processing
- **ML Inference**: Roboflow workflow for bottle detection and counting
- **Data Storage**: CSV file for historical data

## Data Format

### Bottle Counts (`milk_bottle_counts.csv`)
Data is saved with the following columns:
- `timestamp`: Date and time of the count
- `flavor`: Bottle type (whole, 1pct, 2pct)
- `count`: Number of bottles detected

### Alerts (`milk_bottle_alerts.csv`)
Alert data is saved with the following columns:
- `timestamp`: Date and time when the alert was sent
- `missing_categories`: Comma-separated list of missing bottle types

## Configuration

### Alert Cooldown Period
The alert cooldown period can be adjusted in `app.py`:

```python
# Alert cooldown period (in seconds) - should match Roboflow's SMS cooldown
ALERT_COOLDOWN_SECONDS = 10
```

This value should match the cooldown period configured in your Roboflow workflow to ensure accurate alert tracking.

## Notes

- The graph shows only the past hour of data
- Data is saved every 5 seconds
- Alerts are tracked with a 10-second cooldown period (configurable)
- CSV files persist across restarts
- WebSocket connections provide real-time updates without page refresh
- New alerts appear automatically in the Alerts tab without refresh
