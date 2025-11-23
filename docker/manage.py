#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Crawler Container Management Tool - supercronic
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(cmd, shell=True, capture_output=True):
    """Execute system command"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture_output, text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def manual_run():
    """Manually run crawler once"""
    print("🔄 Manually running crawler...")
    try:
        result = subprocess.run(
            ["python", "main.py"], cwd="/app", capture_output=False, text=True
        )
        if result.returncode == 0:
            print("✅ Execution completed")
        else:
            print(f"❌ Execution failed, exit code: {result.returncode}")
    except Exception as e:
        print(f"❌ Execution error: {e}")


def parse_cron_schedule(cron_expr):
    """Parse cron expression and return human-readable description"""
    if not cron_expr or cron_expr == "Not Set":
        return "Not Set"
    
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return f"Original expression: {cron_expr}"
        
        minute, hour, day, month, weekday = parts
        
        # Analyze minutes
        if minute == "*":
            minute_desc = "Every minute"
        elif minute.startswith("*/"):
            interval = minute[2:]
            minute_desc = f"Every {interval} minutes"
        elif "," in minute:
            minute_desc = f"At minute {minute}"
        else:
            minute_desc = f"At minute {minute}"

        # Analyze hours
        if hour == "*":
            hour_desc = "Every hour"
        elif hour.startswith("*/"):
            interval = hour[2:]
            hour_desc = f"Every {interval} hours"
        elif "," in hour:
            hour_desc = f"At hour {hour}"
        else:
            hour_desc = f"At hour {hour}"

        # Analyze days
        if day == "*":
            day_desc = "Every day"
        elif day.startswith("*/"):
            interval = day[2:]
            day_desc = f"Every {interval} days"
        else:
            day_desc = f"On day {day} of month"

        # Analyze months
        if month == "*":
            month_desc = "Every month"
        else:
            month_desc = f"In month {month}"

        # Analyze weekdays
        weekday_names = {
            "0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday",
            "4": "Thursday", "5": "Friday", "6": "Saturday", "7": "Sunday"
        }
        if weekday == "*":
            weekday_desc = ""
        else:
            weekday_desc = f"on {weekday_names.get(weekday, weekday)}"

        # Combine description
        if minute.startswith("*/") and hour == "*" and day == "*" and month == "*" and weekday == "*":
            # Simple interval pattern, like */30 * * * *
            return f"Runs every {minute[2:]} minutes"
        elif hour != "*" and minute != "*" and day == "*" and month == "*" and weekday == "*":
            # Specific time every day, like 0 9 * * *
            return f"Runs daily at {hour}:{minute.zfill(2)}"
        elif weekday != "*" and day == "*":
            # Specific time weekly
            return f"Runs {weekday_desc} at {hour}:{minute.zfill(2)}"
        else:
            # Complex pattern, show detailed information
            desc_parts = [part for part in [month_desc, day_desc, weekday_desc, hour_desc, minute_desc] if part and part != "Every month" and part != "Every day" and part != "Every hour"]
            if desc_parts:
                return "Runs " + " ".join(desc_parts)
            else:
                return f"Complex expression: {cron_expr}"

    except Exception as e:
        return f"Parse failed: {cron_expr}"


def show_status():
    """Display container status"""
    print("📊 Container Status:")

    # Check PID 1 status
    supercronic_is_pid1 = False
    pid1_cmdline = ""
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 PID 1 Process: {pid1_cmdline}")

        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ supercronic correctly running as PID 1")
            supercronic_is_pid1 = True
        else:
            print("  ❌ PID 1 is not supercronic")
            print(f"  📋 Actual PID 1: {pid1_cmdline}")
    except Exception as e:
        print(f"  ❌ Unable to read PID 1 info: {e}")

    # Check environment variables
    cron_schedule = os.environ.get("CRON_SCHEDULE", "Not Set")
    run_mode = os.environ.get("RUN_MODE", "Not Set")
    immediate_run = os.environ.get("IMMEDIATE_RUN", "Not Set")

    print(f"  ⚙️ Runtime Configuration:")
    print(f"    CRON_SCHEDULE: {cron_schedule}")

    # Parse and display cron expression meaning
    cron_description = parse_cron_schedule(cron_schedule)
    print(f"    ⏰ Execution Frequency: {cron_description}")

    print(f"    RUN_MODE: {run_mode}")
    print(f"    IMMEDIATE_RUN: {immediate_run}")

    # Check configuration files
    config_files = ["/app/config/config.yaml", "/app/config/frequency_words.txt"]
    print("  📁 Configuration Files:")
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"    ✅ {Path(file_path).name}")
        else:
            print(f"    ❌ {Path(file_path).name} missing")

    # Check key files
    key_files = [
        ("/usr/local/bin/supercronic-linux-amd64", "supercronic binary"),
        ("/usr/local/bin/supercronic", "supercronic symlink"),
        ("/tmp/crontab", "crontab file"),
        ("/entrypoint.sh", "entrypoint script")
    ]

    print("  📂 Key Files Check:")
    for file_path, description in key_files:
        if Path(file_path).exists():
            print(f"    ✅ {description}: exists")
            # For crontab file, display content
            if file_path == "/tmp/crontab":
                try:
                    with open(file_path, 'r') as f:
                        crontab_content = f.read().strip()
                        print(f"         Content: {crontab_content}")
                except:
                    pass
        else:
            print(f"    ❌ {description}: missing")

    # Check container runtime
    print("  ⏱️ Container Time Information:")
    try:
        # Check PID 1 start time
        with open('/proc/1/stat', 'r') as f:
            stat_content = f.read().strip().split()
            if len(stat_content) >= 22:
                # starttime is the 22nd field (index 21)
                starttime_ticks = int(stat_content[21])

                # Read system boot time
                with open('/proc/stat', 'r') as stat_f:
                    for line in stat_f:
                        if line.startswith('btime'):
                            boot_time = int(line.split()[1])
                            break
                    else:
                        boot_time = 0

                # Read system clock frequency
                clock_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

                if boot_time > 0:
                    pid1_start_time = boot_time + (starttime_ticks / clock_ticks)
                    current_time = time.time()
                    uptime_seconds = int(current_time - pid1_start_time)
                    uptime_minutes = uptime_seconds // 60
                    uptime_hours = uptime_minutes // 60

                    if uptime_hours > 0:
                        print(f"    PID 1 Uptime: {uptime_hours} hours {uptime_minutes % 60} minutes")
                    else:
                        print(f"    PID 1 Uptime: {uptime_minutes} minutes ({uptime_seconds} seconds)")
                else:
                    print(f"    PID 1 Uptime: Cannot calculate precisely")
            else:
                print("    ❌ Unable to parse PID 1 statistics")
    except Exception as e:
        print(f"    ❌ Time check failed: {e}")

    # Status summary and recommendations
    print("  📊 Status Summary:")
    if supercronic_is_pid1:
        print("    ✅ supercronic correctly running as PID 1")
        print("    ✅ Scheduled tasks should work normally")

        # Display current scheduling information
        if cron_schedule != "Not Set":
            print(f"    ⏰ Current Schedule: {cron_description}")

            # Provide some common scheduling recommendations
            if "minutes" in cron_description and "30 minutes" not in cron_description and "60 minutes" not in cron_description:
                print("    💡 Frequent execution mode, suitable for real-time monitoring")
            elif "hours" in cron_description:
                print("    💡 Hourly execution mode, suitable for regular summaries")
            elif "daily" in cron_description:
                print("    💡 Daily execution mode, suitable for daily reports")

        print("    💡 If scheduled tasks are not executing, check:")
        print("       • crontab format is correct")
        print("       • timezone settings are correct")
        print("       • application has no errors")
    else:
        print("    ❌ supercronic status abnormal")
        if pid1_cmdline:
            print(f"    📋 Current PID 1: {pid1_cmdline}")
        print("    💡 Recommended actions:")
        print("       • Restart container: docker restart trend-radar")
        print("       • Check container logs: docker logs trend-radar")

    # Display log check recommendations
    print("  📋 Runtime Status Check:")
    print("    • View full container logs: docker logs trend-radar")
    print("    • View real-time logs: docker logs -f trend-radar")
    print("    • Manual execution test: python manage.py run")
    print("    • Restart container service: docker restart trend-radar")


def show_config():
    """Display current configuration"""
    print("⚙️ Current Configuration:")

    env_vars = [
        "CRON_SCHEDULE",
        "RUN_MODE",
        "IMMEDIATE_RUN",
        "FEISHU_WEBHOOK_URL",
        "DINGTALK_WEBHOOK_URL",
        "WEWORK_WEBHOOK_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "CONFIG_PATH",
        "FREQUENCY_WORDS_PATH",
    ]

    for var in env_vars:
        value = os.environ.get(var, "Not Set")
        # Hide sensitive information
        if any(sensitive in var for sensitive in ["WEBHOOK", "TOKEN", "KEY"]):
            if value and value != "Not Set":
                masked_value = value[:10] + "***" if len(value) > 10 else "***"
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: {value}")

    crontab_file = "/tmp/crontab"
    if Path(crontab_file).exists():
        print("  📅 Crontab Content:")
        try:
            with open(crontab_file, "r") as f:
                content = f.read().strip()
                print(f"    {content}")
        except Exception as e:
            print(f"    Read failed: {e}")
    else:
        print("  📅 Crontab file does not exist")


def show_files():
    """Display output files"""
    print("📁 Output Files:")

    output_dir = Path("/app/output")
    if not output_dir.exists():
        print("  📭 Output directory does not exist")
        return

    # Display recent files
    date_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)

    if not date_dirs:
        print("  📭 Output directory is empty")
        return

    # Display files from last 2 days
    for date_dir in date_dirs[:2]:
        print(f"  📅 {date_dir.name}:")
        for subdir in ["html", "txt"]:
            sub_path = date_dir / subdir
            if sub_path.exists():
                files = list(sub_path.glob("*"))
                if files:
                    recent_files = sorted(
                        files, key=lambda x: x.stat().st_mtime, reverse=True
                    )[:3]
                    print(f"    📂 {subdir}: {len(files)} files")
                    for file in recent_files:
                        mtime = time.ctime(file.stat().st_mtime)
                        size_kb = file.stat().st_size // 1024
                        print(
                            f"      📄 {file.name} ({size_kb}KB, {mtime.split()[3][:5]})"
                        )
                else:
                    print(f"    📂 {subdir}: empty")


def show_logs():
    """Display real-time logs"""
    print("📋 Real-time logs (Press Ctrl+C to exit):")
    print("💡 Note: This will show PID 1 process output")
    try:
        # Try multiple methods to view logs
        log_files = [
            "/proc/1/fd/1",  # PID 1 standard output
            "/proc/1/fd/2",  # PID 1 standard error
        ]

        for log_file in log_files:
            if Path(log_file).exists():
                print(f"📄 Attempting to read: {log_file}")
                subprocess.run(["tail", "-f", log_file], check=True)
                break
        else:
            print("📋 Cannot find standard log files, recommend using: docker logs trend-radar")

    except KeyboardInterrupt:
        print("\n👋 Exiting log viewer")
    except Exception as e:
        print(f"❌ Failed to view logs: {e}")
        print("💡 Recommend using: docker logs trend-radar")


def restart_supercronic():
    """Restart supercronic process"""
    print("🔄 Restarting supercronic...")
    print("⚠️ Note: supercronic is PID 1, cannot be restarted directly")

    # Check current PID 1
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 Current PID 1: {pid1_cmdline}")

        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ PID 1 is supercronic")
            print("  💡 To restart supercronic, you need to restart the entire container:")
            print("    docker restart trend-radar")
        else:
            print("  ❌ PID 1 is not supercronic, this is an abnormal state")
            print("  💡 Recommend restarting container to fix the issue:")
            print("    docker restart trend-radar")
    except Exception as e:
        print(f"  ❌ Unable to check PID 1: {e}")
        print("  💡 Recommend restarting container: docker restart trend-radar")


def show_help():
    """Display help information"""
    help_text = """
🐳 TrendRadar Container Management Tool

📋 Command List:
  run         - Manually run crawler once
  status      - Display container running status
  config      - Display current configuration
  files       - Display output files
  logs        - View real-time logs
  restart     - Restart instructions
  help        - Display this help

📖 Usage Examples:
  # Execute in container
  python manage.py run
  python manage.py status
  python manage.py logs

  # Execute on host machine
  docker exec -it trend-radar python manage.py run
  docker exec -it trend-radar python manage.py status
  docker logs trend-radar

💡 Common Operation Guide:
  1. Check running status: status
     - Check if supercronic is PID 1
     - Check configuration files and key files
     - View cron schedule settings

  2. Manual execution test: run
     - Execute news crawling immediately
     - Test if the program works normally

  3. View logs: logs
     - Monitor running status in real-time
     - Also can use: docker logs trend-radar

  4. Restart service: restart
     - Since supercronic is PID 1, need to restart entire container
     - Use: docker restart trend-radar
"""
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]
    commands = {
        "run": manual_run,
        "status": show_status,
        "config": show_config,
        "files": show_files,
        "logs": show_logs,
        "restart": restart_supercronic,
        "help": show_help,
    }

    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n👋 Operation cancelled")
        except Exception as e:
            print(f"❌ Execution error: {e}")
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python manage.py help' to see available commands")


if __name__ == "__main__":
    main()