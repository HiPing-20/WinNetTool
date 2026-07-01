import os
import sys
import tempfile
import json
import datetime


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 PyInstaller 打包"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def save_data_to_temp_file(data, filename_prefix="scan_result", extension="json"):
    try:
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.{extension}"
        filepath = os.path.join(temp_dir, filename)

        if extension == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(data, list):
                    for item in data:
                        f.write(str(item) + "\n")
                else:
                    f.write(str(data))
        return True, filepath
    except Exception as e:
        return False, str(e)


def generate_ascii_port_histogram(port_data, top_n=10):
    if not port_data:
        return "暂无端口分布数据。"

    sorted_ports = sorted(port_data, key=lambda x: x.get('count', 0), reverse=True)[:top_n]
    if not sorted_ports:
        return "暂无端口分布数据。"

    max_count = max(p.get('count', 0) for p in sorted_ports)
    if max_count == 0:
        return "所有端口使用计数均为0。"

    max_port_len = max(len(str(p.get('port', ''))) for p in sorted_ports)

    chart = ["\n端口使用分布图 (TOP {}):".format(top_n)]
    chart.append("-" * (max_port_len + 30))

    for p in sorted_ports:
        port = p.get('port', 'N/A')
        count = p.get('count', 0)
        percentage = (count / max_count) * 100 if max_count > 0 else 0
        bar_length = int(percentage / 4)
        chart.append(f"{str(port).ljust(max_port_len)} | {'█' * bar_length}{'░' * (25 - bar_length)} {count} ({percentage:.1f}%)")

    chart.append("-" * (max_port_len + 30))
    chart.append("\n")
    return "\n".join(chart)


def generate_lan_topology_html(devices, gateway_ip=""):
    """生成 HTML 格式的局域网拓扑图，使用 SVG 绘制，无需外部工具"""
    if not devices:
        return """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>局域网拓扑图</title></head><body style="background:#1a1b26;color:#c0caf5;font-family:sans-serif;text-align:center;padding-top:80px;">
<h2>暂无局域网设备数据</h2></body></html>"""

    # 计算布局：网关在中心，设备环绕
    n = len(devices)
    cx, cy = 500, 300  # 中心点
    router_r = 40
    circle_r = 220 if n > 1 else 0

    nodes_svg = []
    lines_svg = []

    # 网关节点
    nodes_svg.append(f'''
    <g class="node router" transform="translate({cx},{cy})">
        <circle r="{router_r}" fill="#7aa2f7" stroke="#89b4fa" stroke-width="2" filter="url(#glow)"/>
        <text y="4" text-anchor="middle" fill="#1a1b26" font-size="10" font-weight="bold">网关</text>
        <text y="18" text-anchor="middle" fill="#1a1b26" font-size="8">{gateway_ip or "Router"}</text>
    </g>''')

    # 设备节点
    for i, dev in enumerate(devices):
        ip = dev.get('ip', f'Unknown_{i}')
        mac = dev.get('mac', 'N/A')
        dev_type = dev.get('type', '')
        hostname = dev.get('hostname', '') or f'设备{i+1}'

        if n <= 1:
            angle = 0
            px, py = cx + circle_r, cy
        else:
            angle = (2 * 3.14159 * i / n) - 3.14159 / 2
            px = cx + circle_r * 1.0 * (1 if n > 4 else 1.5)
            py = cy + circle_r * (1 if n > 4 else 1.5) * 0.7
            # 重新计算圆形布局
            angle = (2 * 3.14159 * i / n) - 3.14159 / 2
            px = cx + circle_r * 1.2 * __import__('math').cos(angle)
            py = cy + circle_r * 0.8 * __import__('math').sin(angle)

        # 连线
        lines_svg.append(f'''
        <line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" stroke="#292e42" stroke-width="1.5" stroke-dasharray="4,4"/>
        <circle cx="{(cx+px)/2}" cy="{(cy+py)/2}" r="3" fill="#565f89"/>''')

        # 设备图标颜色
        colors = ['#9ece6a', '#e0af68', '#bb9af7', '#f7768e', '#7dcfff', '#73daca']
        color = colors[i % len(colors)]

        nodes_svg.append(f'''
        <g class="node device" transform="translate({px},{py})">
            <rect x="-55" y="-28" width="110" height="56" rx="10" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="1.5"/>
            <circle r="16" fill="{color}" fill-opacity="0.3" stroke="{color}" stroke-width="1"/>
            <text y="3" text-anchor="middle" fill="{color}" font-size="8" font-weight="bold">{dev_type or "PC"}</text>
            <text y="38" text-anchor="middle" fill="#c0caf5" font-size="9" font-weight="bold">{hostname}</text>
            <text y="50" text-anchor="middle" fill="#565f89" font-size="8">{ip}</text>
        </g>''')

    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="utf-8">
    <title>局域网拓扑图</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #1a1b26; font-family: "Microsoft YaHei UI", sans-serif; overflow: hidden; }}
        .header {{
            background: #16161e; border-bottom: 1px solid #292e42;
            padding: 12px 24px; display: flex; align-items: center; justify-content: space-between;
        }}
        .header h1 {{ color: #7aa2f7; font-size: 16px; font-weight: bold; }}
        .header .info {{ color: #565f89; font-size: 12px; }}
        .header .badge {{
            background: #7aa2f7; color: #1a1b26; padding: 3px 10px;
            border-radius: 12px; font-size: 11px; font-weight: bold;
        }}
        svg {{ width: 100%; height: calc(100vh - 50px); }}
        .legend {{
            position: fixed; bottom: 20px; right: 20px;
            background: #16161e; border: 1px solid #292e42; border-radius: 10px;
            padding: 14px 18px; font-size: 11px; color: #9aa5ce;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; margin: 5px 0; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .legend-line {{ width: 20px; height: 0; border-top: 1.5px dashed #292e42; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>局域网设备拓扑图</h1>
        <div class="info">
            <span class="badge">{n} 台设备</span>
        </div>
    </div>
    <svg viewBox="0 0 1000 600">
        <defs>
            <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
        </defs>
        {"".join(lines_svg)}
        {"".join(nodes_svg)}
    </svg>
    <div class="legend">
        <div style="color:#7aa2f7;font-weight:bold;margin-bottom:6px;">图例</div>
        <div class="legend-item"><div class="legend-dot" style="background:#7aa2f7;"></div> 网关/路由器</div>
        <div class="legend-item"><div class="legend-dot" style="background:#9ece6a;"></div> PC 设备</div>
        <div class="legend-item"><div class="legend-dot" style="background:#e0af68;"></div> 移动设备</div>
        <div class="legend-item"><div class="legend-line"></div> 网络连接</div>
    </div>
</body>
</html>'''
    return html


def generate_lan_topology_dot(devices):
    """保留 DOT 格式作为备用"""
    if not devices:
        return "digraph G {\n    label=\"暂无局域网设备数据。\";\n    labelloc=\"t\";\n    rankdir=LR;\n}"

    dot_graph = ["digraph G {"]
    dot_graph.append("    label=\"局域网设备拓扑 (简化版)\";")
    dot_graph.append("    labelloc=\"t\";")
    dot_graph.append("    graph [bgcolor=\"#1a1b26\", fontname=\"Helvetica\", fontcolor=\"#c0caf5\"];")
    dot_graph.append("    node [shape=box, style=\"filled\", fontname=\"Helvetica\", fontsize=10];")

    dot_graph.append("    node [fillcolor=\"#7aa2f7\", fontcolor=\"#1a1b26\", color=\"#7aa2f7\"];")
    dot_graph.append("    Router [label=\"Router / 网关\"];")

    dot_graph.append("    node [fillcolor=\"#9aa5ce\", fontcolor=\"#1a1b26\", color=\"#9aa5ce\"];")
    for i, dev in enumerate(devices):
        ip = dev.get('ip', f'UnknownIP_{i}')
        mac = dev.get('mac', 'N/A')
        hostname = dev.get('hostname', '未知设备')
        node_name = f"Device_{ip.replace('.', '_')}"
        label = f"{hostname}\\nIP: {ip}\\nMAC: {mac}"
        dot_graph.append(f"    {node_name} [label=\"{label}\"];")
        dot_graph.append(f"    Router -> {node_name} [color=\"#c0caf5\", penwidth=1.5];")

    dot_graph.append("}")
    return "\n".join(dot_graph)
