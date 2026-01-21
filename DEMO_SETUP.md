# Quick Demo Setup with ngrok

This guide will help you share your milk bottle monitoring app with a public URL for demos.

## Prerequisites

- Your Flask app working locally
- A webcam connected to your computer

## Step 1: Install ngrok

### macOS
```bash
brew install ngrok
```

### Windows/Linux
Download from https://ngrok.com/download

## Step 2: Sign up and authenticate (one-time setup)

1. Sign up for free at https://ngrok.com/signup
2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
3. Authenticate:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

## Step 3: Start your demo

### Terminal 1: Start the Flask app
```bash
cd "/Users/edss/Documents/Roboflow Projects/milk bottles"
./run_webapp.sh
```

Wait until you see:
```
Flask server starting...
Access the application at:
  - http://localhost:5050
```

### Terminal 2: Start ngrok tunnel
```bash
ngrok http 5050
```

You'll see output like:
```
Session Status                online
Account                       your@email.com
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5050
```

## Step 4: Share the URL

Copy the `https://abc123.ngrok-free.app` URL and share it with your audience!

## Demo Tips

1. **Test first**: Open the ngrok URL in your own browser before sharing
2. **Keep both terminals running**: Don't close either terminal during your demo
3. **URL changes**: Each time you restart ngrok, you get a new URL
4. **Free tier limits**:
   - Sessions last 2 hours
   - 40 connections/minute
   - Good enough for small demos

## Troubleshooting

### "ngrok not found"
- Make sure ngrok is installed: `which ngrok`
- If not installed, run `brew install ngrok`

### Camera not working
- Make sure your webcam is connected
- Close other apps using the camera (Zoom, FaceTime, etc.)
- Check that `video_reference=0` in app.py matches your camera

### Slow performance
- ngrok adds some latency (normal for tunneling)
- For better performance, ask viewers to refresh if video is laggy

## Stopping the Demo

1. Press `Ctrl+C` in the ngrok terminal
2. Press `Ctrl+C` in the Flask app terminal

## Optional: Get a static URL (requires paid ngrok plan)

Free tier gives you a random URL each time. For a consistent URL across demos:

```bash
ngrok http --domain=your-custom-domain.ngrok-free.app 5050
```

This requires upgrading to ngrok Pro ($8/month).

## Alternative: Cloudflare Tunnel (also free)

If ngrok doesn't work for you:

```bash
# Install
brew install cloudflare/cloudflare/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:5050
```

This gives you a `https://xyz.trycloudflare.com` URL.
