# REQUIREMENTS.md — 实时市场看板 (Market Dashboard)

## 产品概述
一个轻量级实时市场行情看板，覆盖贵金属、大宗商品、数字货币和外汇，部署在 GitHub Pages，零运营成本。

## 用户
DQ — 科技投资人，需要随时掌握核心资产价格走势。

## 核心需求

### 1. 品种覆盖（可配置）
所有品种在 `config.json` 中定义，新增/删除只改配置文件，不改代码。

| 类别 | 品种 | 数据源 |
|------|------|--------|
| 贵金属 | 黄金、白银、铜、镍、稀土ETF(REMX) | Yahoo Finance |
| 大宗商品 | WTI 原油 | Yahoo Finance |
| 数字货币 | BTC、ETH | Binance WebSocket |
| 汇率 | USD/CNY、USD/JPY、EUR/USD | Yahoo Finance |

### 2. 数据实时性
- **数字货币**：Binance WebSocket 真实时推送（毫秒级）
- **其他品种**：GitHub Actions 每 15 分钟从 Yahoo Finance 抓取，前端轮询刷新

### 3. 展示形式
每个品种一张**价格卡片**，包含：
- Icon + 品种名称
- 当前价格（大字，醒目）
- 24 小时涨跌幅（绿涨红跌）
- 迷你趋势线（sparkline，最近 7 天）

### 4. 页面布局
- 按类别分组，每组一个标题
- 响应式：手机 2 列，桌面 4 列
- 标题栏显示最后更新时间
- 底部数据来源说明

### 5. 视觉风格
- zinc 暗色系（与 Guru Tracker 一致）
- Inter 字体
- 简洁克制，信息密度高

### 6. 部署
- GitHub Pages，纯前端静态站
- GitHub Actions 定时更新数据
- 零后端、零成本

## 非需求（明确排除）
- 不做 K 线图（只要 sparkline）
- 不做交易功能
- 不做用户登录
- 不做历史数据查询（只展示最近 7 天趋势）
- 不做价格提醒/推送（V1 不做，后续可加）

## 配置驱动设计
`config.json` 结构：
```json
{
  "categories": [
    {
      "name": "贵金属",
      "id": "metals",
      "assets": [
        {"name": "黄金", "symbol": "GC=F", "source": "yahoo", "unit": "USD/oz", "icon": "🥇"}
      ]
    }
  ],
  "refresh_interval_seconds": 30,
  "history_days": 7
}
```

新增品种 = 在 assets 数组加一行，自动出现在看板上。

## 成功标准
1. 页面加载后 3 秒内显示所有价格
2. BTC/ETH 价格实时跳动
3. 非 crypto 品种数据不超过 15 分钟延迟
4. 手机访问体验良好
5. 新增品种只需改 config.json
