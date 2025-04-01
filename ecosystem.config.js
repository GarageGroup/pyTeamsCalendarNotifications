module.exports = {
  apps: [{
    name: "pyTeamsCalendarNotifications",
    script: "./main.py",
    interpreter: "./venv/bin/python",
    autorestart: true,
    env: {
      NODE_ENV: "production",
      PYTHONUNBUFFERED: "1"
    },
    watch: false,
    max_memory_restart: "1G",
    error_file: "logs/pm2-error.log",
    out_file: "logs/pm2-out.log",
    log_date_format: "YYYY-MM-DD HH:mm:ss",
    merge_logs: true
  }]
} 