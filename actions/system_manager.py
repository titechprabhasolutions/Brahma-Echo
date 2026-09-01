# actions/system_manager.py
"""
System Health & Resource Manager for Brahma AI.

Allows the AI to check CPU, RAM, battery, and top processes, 
as well as forcibly close non-responsive or resource-hogging apps.
"""

import json

def get_system_health() -> dict:
    import psutil
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    battery_info = None
    if hasattr(psutil, "sensors_battery"):
        battery = psutil.sensors_battery()
        if battery:
            battery_info = {"percent": battery.percent, "plugged": battery.power_plugged}
    
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    top_mem = sorted(procs, key=lambda p: p['memory_percent'] or 0, reverse=True)[:5]
    top_cpu = sorted(procs, key=lambda p: p['cpu_percent'] or 0, reverse=True)[:5]
    
    return {
        "cpu_usage_percent": cpu,
        "ram_usage_percent": mem.percent,
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "disk_usage_percent": disk.percent,
        "battery": battery_info,
        "top_processes_by_ram": top_mem,
        "top_processes_by_cpu": top_cpu
    }

def kill_process(pid: int = None, name: str = None) -> str:
    import psutil
    killed = []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if (pid and p.info['pid'] == pid) or (name and p.info['name'] and name.lower() in p.info['name'].lower()):
                p.kill()
                killed.append(f"{p.info['name']} (PID: {p.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed:
        return f"Successfully closed: {', '.join(killed)}"
    return f"No matching processes found for '{name or pid}' or access was denied."

def run(parameters: dict, player=None, session_memory=None) -> str:
    try:
        import psutil
    except ImportError:
        return "psutil library is not installed. Cannot check system health."

    action = parameters.get("action", "status")
    
    if action == "kill":
        pid = parameters.get("pid")
        name = parameters.get("process_name")
        if not pid and not name:
            return "You must provide either a pid or a process_name to kill."
        res = kill_process(pid=pid, name=name)
        if player: player.write_log(f"SYS: {res}")
        return res
    else:
        health = get_system_health()
        if player: player.write_log(f"SYS: CPU {health['cpu_usage_percent']}% | RAM {health['ram_usage_percent']}%")
        return json.dumps(health, indent=2)
