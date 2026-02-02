# TESTING.md — 测试策略

## 测试层级

### 1. 数据抓取测试（`scripts/fetch_prices.py`）

#### 单品种测试
```bash
# 测试 Yahoo Finance 品种能否正常获取
python scripts/fetch_prices.py --test GC=F
python scripts/fetch_prices.py --test SI=F
python scripts/fetch_prices.py --test CNY=X

# 测试 Binance 品种
python scripts/fetch_prices.py --test BTCUSDT
```

#### 全量测试
```bash
python scripts/fetch_prices.py
# 验证：
# 1. data/latest.json 存在且有效
# 2. data/history.json 存在且有效
# 3. 每个品种都有 price 字段（或 error 标记）
# 4. history 每个品种有 7 个数据点（交易日）
```

#### 错误处理测试
- 无效 symbol → 应标记 error，不崩溃
- 网络超时 → 10 秒后优雅失败
- yfinance 返回空数据 → 标记 N/A

### 2. 前端功能测试

#### 页面加载
- [ ] 页面 3 秒内渲染完成
- [ ] 4 个分类标题都显示
- [ ] 每个品种卡片都显示（即使数据暂时为空）

#### 数据展示
- [ ] 价格正确显示（千位分隔符）
- [ ] 涨跌幅颜色正确（绿涨红跌）
- [ ] Sparkline 绘制完成
- [ ] 最后更新时间显示

#### Binance WebSocket
- [ ] BTC/ETH 价格实时跳动
- [ ] 断线后 3 秒自动重连
- [ ] WebSocket 不可用时显示静态 fallback 价格

#### 响应式
- [ ] 桌面：4 列卡片
- [ ] 平板：3 列
- [ ] 手机：2 列

#### 配置驱动
- [ ] 在 config.json 新增一个品种 → 刷新后自动出现
- [ ] 删除一个品种 → 刷新后消失

### 3. GitHub Actions 测试

#### 手动触发
```bash
gh workflow run update-prices.yml
gh run list --limit 1  # 检查状态
```

#### 验证
- [ ] Workflow 成功执行
- [ ] data/latest.json 被更新（检查时间戳）
- [ ] data/history.json 被更新
- [ ] 只有 data/ 目录有 commit
- [ ] GitHub Pages 自动重新部署

### 4. 端到端验证

#### 本地预览
```bash
cd market-dashboard
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```

#### 线上验证
- [ ] GitHub Pages URL 可访问
- [ ] 所有品种价格显示正确
- [ ] BTC/ETH 实时更新
- [ ] 手机浏览器正常展示

## 验收标准
1. ✅ 所有品种有价格显示（或明确的 N/A 标记）
2. ✅ BTC/ETH 实时跳动
3. ✅ Sparkline 正确绘制
4. ✅ GitHub Actions 每 15 分钟自动更新
5. ✅ 新增品种只需改 config.json
6. ✅ 手机访问正常
