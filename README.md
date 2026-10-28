# Cloudflare WARP Optimizer / Cloudflare WARP 优选工具

[English](#english) | [中文说明](#中文-chinese)

<a name="english"></a>
## 🇺🇸 English

A simple tool to find the fastest Cloudflare WARP IP endpoint and export clean configurations for **WireGuard**, **Clash Meta**, and **Loon**.

### Features
-   ✅ **Scan & Export**: Finds the lowest-latency Cloudflare WARP endpoint and exports clean configs.
-   ✅ **Smart Scan**: Pings multiple known-good endpoint ranges to find the lowest latency IP.
-   ✅ **Multi-Format**: Exports configs for:
    -   WireGuard (Native App)
    -   Clash Meta (OpenClash / Mihomo)
    -   Loon (iOS / macOS)

### Usage

#### 1. Prerequisites
-   Install the `wgcf` binary and place it next to `optimize.sh`.
-   Register a WARP account yourself (interactive, review the provider's terms):
    ```bash
    ./wgcf register --accept-tos
    ```
    `optimize.sh` will exit and tell you to do this if no local account exists.

#### 2. Run the Optimizer
Open your terminal and run the script from the cloned directory:
```bash
cd warp-optimizer
./optimize.sh
```

#### 2. Import Configuration

**Option A: WireGuard App**
-   Import the generated `wgcf-profile.conf` file directly into the WireGuard app.

**Option B: Clash Meta / Loon**
-   Open the generated `warp_proxies.txt` file:
    ```bash
    open warp_proxies.txt
    ```
-   **Clash Meta**: Copy the YAML block to your `proxies:` section.
-   **Loon**: Copy the config line to your `[Proxy]` section.

### Advanced: Automated Updates (Optional)
Since WARP IPs can degrade over time, you can set up a cron job to auto-optimize daily.

1.  Edit crontab: `crontab -e`
2.  Add this line (runs every day at 4 AM), adjusting the path to your clone:
    ```bash
    0 4 * * * cd /path/to/warp-optimizer && ./optimize.sh > /tmp/warp_opt.log 2>&1
    ```

---

<a name="中文-chinese"></a>
## 🇨🇳 中文 (Chinese)

一个简单的工具，用于扫描并寻找延迟最低的 Cloudflare WARP 优选 IP，并支持导出 **WireGuard**, **Clash Meta**, 和 **Loon** 的配置格式。

### 功能特点
-   ✅ **扫描与导出**: 扫描并筛选最低延迟的 Cloudflare WARP 节点，并导出干净的配置。
-   ✅ **智能优选**: 扫描多个高质量的 IP 段，筛选出低延迟节点。
-   ✅ **多格式导出**: 支持导出以下配置:
    -   WireGuard (官方客户端)
    -   Clash Meta (OpenClash / Mihomo)
    -   Loon (iOS / macOS)

### 使用指南

#### 1. 环境准备
-   安装 `wgcf` 二进制并放在 `optimize.sh` 同目录。
-   自己手动注册 WARP 账户（交互式，请阅读服务商的条款）:
    ```bash
    ./wgcf register --accept-tos
    ```
    如果本地没有账户，`optimize.sh` 会退出并提示你先完成这一步。

#### 2. 运行优化脚本
在克隆目录下打开终端 (Terminal) 并运行:
```bash
cd warp-optimizer
./optimize.sh
```

#### 2. 导入配置

**方案 A: WireGuard 官方客户端**
-   直接在 WireGuard 应用中导入生成的 `wgcf-profile.conf` 文件。

**方案 B: Clash Meta / Loon**
-   打开生成的代理列表文件:
    ```bash
    open warp_proxies.txt
    ```
-   **Clash Meta 用户**: 复制 `# --- Clash Meta ...` 下方的 YAML 内容到你的配置文件 `proxies:` 列表中。
-   **Loon 用户**: 复制 `# --- Loon ...` 下方的配置行到你的配置文件 `[Proxy]` 栏目下。

### 进阶：自动定时更新 (可选)
WARP 的优选 IP 可能会随时间变慢或失效，你可以设置 Crontab 定时任务来每天自动优选。

1.  编辑定时任务: `crontab -e`
2.  添加以下内容 (例如每天凌晨 4 点自动运行)，请把路径改成你的克隆目录:
    ```bash
    0 4 * * * cd /path/to/warp-optimizer && ./optimize.sh > /tmp/warp_opt.log 2>&1
    ```
    *(对于 Clash 用户，如果你使用了 File Provider 引用本地文件，这样设置后 Clash 就会每天自动获得最新节点)*

---

## Requirements / 环境要求
-   macOS (ARM64/Intel) or Linux.
-   Python 3 installed.
