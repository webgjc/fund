# 基金策略

## 运行环境

- python3 
    - requests包

## 使用方法

打开 **zhishu.py**  
编辑上面的参数列表

```python
# 基于指数估值和持仓曲线的投资策略
start_money = 10000  # 开始钱数
sale_hold_days = 60  # 持有多少个交易日可以卖出
buy_min_money = 1000  # 最小买入限制
sale_min_money = 1000  # 最小卖出限制
zhishu_low = 2500  # 指数低值, 低于低值将满仓
zhishu_high = 3500  # 指数高值，高于高值将空仓
buy_charge_percent = 0.001  # 买入手续费
sale_charge_percent = 0.005  # 卖出手续费
run_days = 500  # 回跑天数
today_value = None  # 当天指数
zhishu_code = "1.000001"  # 上证: 1.000001 成指: 0.399001 创业板: 0.399006
# 其他行业指数数据/code来源: http://quote.eastmoney.com/center/hsbk.html
```
选择一个持仓曲线，默认为直线(也就是在高值和低值之间均匀分布持仓)
```python
# 确定持仓曲线, 返回闲钱占比
def get_hold_cangwei(now):
    # 二值
    # res = 1 if now > (zhishu_high + zhishu_low) / 2 else 0
    # 直线
    res = (1 / (zhishu_high - zhishu_low)) * (now - zhishu_low)
    # 抛物线
    # res = ((1 / (zhishu_high - zhishu_low)) * (now - zhishu_low)) ** 2
    # sqrt曲线
    # res = (max((1 / (zhishu_high - zhishu_low)) * (now - zhishu_low), 0.0001)) ** 0.5
    return min(max(res, 0), 1)
```

运行
> python3 zhishu.py

运行一个http静态环境
> python3 -m http.server 80

网页访问
> http://localhost/zhishu.html

调试技巧
- 修改参数
- 重新运行
- command + shift + r 刷新缓存刷新页面

效果如下
![trace](./static/trace.jpg)

![profit](./static/profit.jpg)