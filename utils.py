import os
import tempfile
import json
import datetime

# ==================== 文件操作工具 ====================
def save_data_to_temp_file(data, filename_prefix="scan_result", extension="json"):
    """
    将数据保存到临时文件。
    data: 要保存的数据（可以是列表、字典等可序列化对象）
    filename_prefix: 文件名前缀
    extension: 文件扩展名 (e.g., 'json', 'txt')
    """
    try:
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.{extension}"
        filepath = os.path.join(temp_dir, filename)

        if extension == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        elif extension == "txt":
            # 假设data是字符串或字符串列表
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(data, list):
                    for item in data:
                        f.write(str(item) + "\n")
                else:
                    f.write(str(data))
        else:
            # 默认保存为文本
            with open(filepath, "w", encoding="utf-8") as f:
                if isinstance(data, list):
                    for item in data:
                        f.write(str(item) + "\n")
                else:
                    f.write(str(data))
        return True, filepath
    except Exception as e:
        return False, str(e)

# ==================== 可视化工具 ====================
def generate_ascii_port_histogram(port_data, top_n=10):
    """
    生成 ASCII 格式的端口分布直方图。
    port_data: 列表，每个元素是一个字典，至少包含 'port' 和 'count'
    top_n: 显示前N个最活跃的端口
    """
    if not port_data:
        return "暂无端口分布数据。"

    # 排序并取前 top_n
    sorted_ports = sorted(port_data, key=lambda x: x.get('count', 0), reverse=True)[:top_n]

    if not sorted_ports:
        return "暂无端口分布数据。"

    max_count = max(p.get('count', 0) for p in sorted_ports)
    if max_count == 0:
        return "所有端口使用计数均为0。"

    max_port_len = max(len(str(p.get('port', ''))) for p in sorted_ports)

    chart = ["\n端口使用分布图 (TOP {}):".format(top_n)]
    chart.append("-" * (max_port_len + 30)) # 调整横线长度

    for p in sorted_ports:
        port = p.get('port', 'N/A')
        count = p.get('count', 0)

        # 计算百分比和柱状图长度
        percentage = (count / max_count) * 100 if max_count > 0 else 0
        bar_length = int(percentage / 4) # 每2.5%一个字符

        chart.append(f"{str(port).ljust(max_port_len)} | {'█' * bar_length}{'░' * (25 - bar_length)} {count} ({percentage:.1f}%)")

    chart.append("-" * (max_port_len + 30))
    chart.append("\n")
    return "\n".join(chart)

def generate_lan_topology_dot(devices):
    """
    根据局域网设备数据生成 DOT 格式的拓扑图描述。
    devices: 列表，每个元素是一个字典，至少包含 'ip', 'mac', 'hostname'
    """
    if not devices:
        return "digraph G {\n    label=\"暂无局域网设备数据。\";\n    labelloc=\"t\";\n    rankdir=LR;\n}"

    dot_graph = ["digraph G {"]
    dot_graph.append("    label=\"局域网设备拓扑 (简化版)\";")
    dot_graph.append("    labelloc=\"t\";")
    dot_graph.append("    graph [bgcolor=\"#1e1e2e\", fontname=\"Helvetica\", fontcolor=\"#cdd6f4\"];")
    dot_graph.append("    node [shape=box, style=\"filled\", fontname=\"Helvetica\", fontsize=10];")

    # 定义节点样式
    # Router/Gateway
    dot_graph.append("    node [fillcolor=\"#89b4fa\", fontcolor=\"#1e1e2e\", color=\"#89b4fa\"];")
    dot_graph.append("    Router [label=\"Router / 网关\"];")

    # Devices
    dot_graph.append("    node [fillcolor=\"#a6adc8\", fontcolor=\"#1e1e2e\", color=\"#a6adc8\"];")
    for i, dev in enumerate(devices):
        ip = dev.get('ip', f'UnknownIP_{i}')
        mac = dev.get('mac', 'N/A')
        hostname = dev.get('hostname', '未知设备')

        # 简化节点名称，避免DOT特殊字符
        node_name = f"Device_{ip.replace('.', '_')}"

        label = f"{hostname}\\nIP: {ip}\\nMAC: {mac}"
        dot_graph.append(f"    {node_name} [label=\"{label}\"];")

        # 假设所有设备都连接到Router
        dot_graph.append(f"    Router -> {node_name} [color=\"#cdd6f4\", penwidth=1.5];")

    dot_graph.append("}")
    return "\n".join(dot_graph)