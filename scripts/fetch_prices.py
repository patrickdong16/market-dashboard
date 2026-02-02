#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Dashboard 数据抓取脚本
从 yfinance 获取价格数据，从 Binance 获取 crypto 数据（作为 fallback）
"""

import json
import time
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 检查并安装依赖
try:
    import yfinance as yf
    import requests
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install required packages: pip install yfinance requests")
    exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataFetcher:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.timeout = 10
        self.max_retries = 3
        
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def get_yahoo_data(self, symbol: str, name: str) -> Dict[str, Any]:
        """获取 Yahoo Finance 数据"""
        result = {
            'symbol': symbol,
            'name': name,
            'price': None,
            'change_percent_24h': None,
            'history': [],
            'error': None,
            'source': 'yahoo'
        }
        
        # 特殊处理镍的符号
        original_symbol = symbol
        if symbol == "^SPGSNI":
            # 尝试多个可能的镍符号
            symbols_to_try = ["^SPGSNI", "NI=F"]
        else:
            symbols_to_try = [symbol]
        
        for retry_count in range(self.max_retries):
            for attempt_symbol in symbols_to_try:
                try:
                    ticker = yf.Ticker(attempt_symbol)
                    
                    # 获取历史数据（8天，确保有足够数据）
                    hist = ticker.history(period="8d", interval="1d", timeout=self.timeout)
                    
                    if hist.empty:
                        logger.warning(f"No historical data for {attempt_symbol}")
                        continue
                    
                    # 获取当前价格（最新收盘价）
                    current_price = float(hist['Close'].iloc[-1])
                    
                    # 计算24h变化（与前一天比较）
                    if len(hist) >= 2:
                        prev_price = float(hist['Close'].iloc[-2])
                        change_percent = ((current_price - prev_price) / prev_price) * 100
                    else:
                        change_percent = 0.0
                    
                    # 获取最近7天的历史数据（用于sparkline）
                    history_prices = hist['Close'].tail(7).tolist()
                    history_prices = [float(p) for p in history_prices]
                    
                    result.update({
                        'price': current_price,
                        'change_percent_24h': change_percent,
                        'history': history_prices,
                        'symbol': attempt_symbol,  # 更新为实际使用的符号
                        'last_updated': datetime.now().isoformat()
                    })
                    
                    logger.info(f"✓ {name} ({attempt_symbol}): ${current_price:.4f} ({change_percent:+.2f}%)")
                    return result
                    
                except Exception as e:
                    logger.warning(f"Attempt {retry_count + 1} failed for {attempt_symbol}: {e}")
                    continue
            
            if retry_count < self.max_retries - 1:
                time.sleep(1)  # 重试前等待1秒
        
        # 如果所有尝试都失败，标记为不可用
        result['error'] = f"Failed to fetch data for {name} after {self.max_retries} retries"
        logger.error(result['error'])
        return result
    
    def get_binance_data(self, symbol: str, name: str) -> Dict[str, Any]:
        """获取 Binance 数据（作为 crypto 的 fallback）"""
        result = {
            'symbol': symbol,
            'name': name,
            'price': None,
            'change_percent_24h': None,
            'history': [],
            'error': None,
            'source': 'binance'
        }
        
        try:
            # 获取24小时价格统计
            ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            response = requests.get(ticker_url, timeout=self.timeout)
            response.raise_for_status()
            ticker_data = response.json()
            
            # 获取K线历史数据（最近7天）
            klines_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=7"
            klines_response = requests.get(klines_url, timeout=self.timeout)
            klines_response.raise_for_status()
            klines_data = klines_response.json()
            
            # 解析数据
            current_price = float(ticker_data['lastPrice'])
            change_percent = float(ticker_data['priceChangePercent'])
            
            # 历史价格（收盘价）
            history_prices = [float(kline[4]) for kline in klines_data]  # 收盘价是第5个元素
            
            result.update({
                'price': current_price,
                'change_percent_24h': change_percent,
                'history': history_prices,
                'last_updated': datetime.now().isoformat()
            })
            
            logger.info(f"✓ {name} ({symbol}): ${current_price:.4f} ({change_percent:+.2f}%)")
            
        except Exception as e:
            result['error'] = f"Failed to fetch Binance data: {e}"
            logger.error(result['error'])
        
        return result
    
    def fetch_all_data(self) -> Dict[str, Any]:
        """获取所有品种的数据"""
        all_data = {
            'categories': [],
            'last_updated': datetime.now().isoformat(),
            'meta': {
                'total_assets': 0,
                'successful_fetches': 0,
                'failed_fetches': 0
            }
        }
        
        for category in self.config['categories']:
            category_data = {
                'name': category['name'],
                'id': category['id'],
                'assets': []
            }
            
            for asset in category['assets']:
                logger.info(f"Fetching data for {asset['name']} ({asset['symbol']})...")
                
                if asset['source'] == 'yahoo':
                    data = self.get_yahoo_data(asset['symbol'], asset['name'])
                elif asset['source'] == 'binance':
                    data = self.get_binance_data(asset['symbol'], asset['name'])
                else:
                    data = {
                        'symbol': asset['symbol'],
                        'name': asset['name'],
                        'error': f"Unknown source: {asset['source']}",
                        'source': asset['source']
                    }
                    logger.error(data['error'])
                
                # 添加资产配置信息
                data.update({
                    'unit': asset['unit'],
                    'icon': asset['icon'],
                    'category': category['id']
                })
                
                category_data['assets'].append(data)
                all_data['meta']['total_assets'] += 1
                
                if data['error']:
                    all_data['meta']['failed_fetches'] += 1
                else:
                    all_data['meta']['successful_fetches'] += 1
            
            all_data['categories'].append(category_data)
        
        return all_data
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """保存数据到文件"""
        # 确保 data 目录存在
        os.makedirs('data', exist_ok=True)
        
        # 保存最新数据
        with open('data/latest.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 保存历史记录（追加到历史文件）
        history_entry = {
            'timestamp': data['last_updated'],
            'meta': data['meta']
        }
        
        try:
            with open('data/history.json', 'r', encoding='utf-8') as f:
                history = json.load(f)
            if not isinstance(history, list):
                history = []
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        
        history.append(history_entry)
        # 保留最近100条记录
        history = history[-100:]
        
        with open('data/history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        logger.info("Data saved to data/latest.json and data/history.json")


def main():
    """主函数"""
    try:
        fetcher = MarketDataFetcher()
        logger.info("Starting market data fetch...")
        
        data = fetcher.fetch_all_data()
        
        # 打印摘要
        meta = data['meta']
        logger.info(f"Fetch completed: {meta['successful_fetches']}/{meta['total_assets']} successful")
        
        if meta['failed_fetches'] > 0:
            logger.warning(f"{meta['failed_fetches']} assets failed to fetch")
        
        fetcher.save_data(data)
        logger.info("Market data fetch completed successfully!")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()