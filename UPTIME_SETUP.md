# 🚀 SORABOT Uptime Monitoring Setup

## 📋 Overview
Your SORABOT now includes a web server that prevents it from sleeping on Render's free tier!

## 🌐 Web Endpoints Available

### Main Endpoints:
- **`/`** - Main ping endpoint for uptime monitoring
- **`/health`** - Health check endpoint  
- **`/stats`** - Detailed bot statistics

### Example Response from `/`:
```json
{
  "message": "🤖 SORABOT is alive and running!",
  "status": "online",
  "uptime_seconds": 3600,
  "uptime_formatted": "1h 0m 0s",
  "last_ping": "2025-10-01T12:00:00",
  "total_pings": 720,
  "timestamp": "2025-10-01T12:00:00"
}
```

## ⚙️ Render Configuration

### 1. Deploy as Web Service
- Type: **Web Service** (not Worker)
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`
- Auto-Deploy: Yes

### 2. Environment Variables
Set in Render dashboard:
- `DISCORD_TOKEN` = your bot token
- `BOT_TOKEN` = your bot token (backup)

### 3. Your Service URL
After deployment, Render will give you a URL like:
```
https://sorabot-abc123.onrender.com
```

## 🔄 Free Uptime Monitoring Services

### Option 1: UptimeRobot (Recommended)
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create free account
3. Add new monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://your-sorabot-url.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
   - **Monitor Name**: SORABOT Uptime

### Option 2: Cron-job.org
1. Go to [cron-job.org](https://cron-job.org)
2. Create free account
3. Create new cronjob:
   - **URL**: `https://your-sorabot-url.onrender.com`
   - **Schedule**: Every 5 minutes
   - **Title**: SORABOT Keep-Alive

### Option 3: Pingdom (Free tier)
1. Go to [pingdom.com](https://pingdom.com)
2. Sign up for free account
3. Add uptime check:
   - **URL**: `https://your-sorabot-url.onrender.com/health`
   - **Check interval**: 5 minutes

## ✅ Verification Steps

### 1. Check Web Server
Visit your Render URL in browser - you should see:
```json
{
  "message": "🤖 SORABOT is alive and running!",
  "status": "online",
  ...
}
```

### 2. Monitor Render Logs
In Render dashboard, check logs for:
```
🌐 Web server started for uptime monitoring
🚀 SORABOT is fully operational with data protection and uptime monitoring!
```

### 3. Test Discord Bot
- Bot should appear online in Discord
- Slash commands should work
- No random disconnections

## 📊 Benefits

### ✅ What This Achieves:
- **24/7 Uptime**: Bot stays online continuously
- **Free Hosting**: No cost on Render free tier
- **Automatic Recovery**: Bot restarts if it crashes
- **Health Monitoring**: Track uptime and performance
- **Data Protection**: Database + backup system intact

### 📈 Expected Results:
- **Uptime**: 99.9%+ (only down during Render maintenance)
- **Response Time**: Bot responds instantly
- **Reliability**: No random sleep/wake cycles

## 🔧 Troubleshooting

### Bot Still Goes Offline?
1. **Check monitoring interval**: Should be 5-10 minutes max
2. **Verify URL**: Make sure uptime service hits correct URL
3. **Check Render logs**: Look for errors in deployment logs
4. **Test endpoints**: Visit `/health` manually to verify response

### Web Server Not Starting?
1. **Check requirements.txt**: Ensure `flask>=2.3.0` is included
2. **Environment**: Verify `PORT` environment variable if needed
3. **Logs**: Check Render logs for Flask startup messages

## 🎯 Final Setup Checklist

- [ ] Deploy bot as **Web Service** on Render
- [ ] Set `DISCORD_TOKEN` environment variable
- [ ] Verify web endpoints respond (visit your URL)
- [ ] Set up uptime monitoring service (UptimeRobot/Cron-job)
- [ ] Test Discord bot functionality
- [ ] Monitor for 24 hours to confirm continuous uptime

**Result**: Your SORABOT will stay online 24/7 for FREE! 🎉