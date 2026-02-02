# CLAUDE.md — Market Dashboard 项目规则

## 项目概述
实时市场行情看板：贵金属/大宗/数字货币/汇率。纯前端 + GitHub Actions。

## 开发规范
- 遵循 `gemini-config/GEMINI.md` 全局规范
- 所有网络请求：timeout=10s + try-except + 重试
- 零硬编码：品种列表从 config.json 读取
- 单文件前端：index.html 内嵌 CSS/JS
- commit 规范：feat/fix/docs 前缀

## 数据源
- Yahoo Finance (yfinance): 贵金属、大宗、汇率
- Binance WebSocket: BTC、ETH

## 部署
- GitHub Pages (main 分支)
- GitHub Actions 每 15 分钟更新 data/

## 视觉
- 背景: zinc-950
- 卡片: zinc-900 border zinc-800
- 涨: emerald-400 / 跌: red-400
- 字体: Inter
