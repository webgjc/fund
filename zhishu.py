import copy
import json
import requests

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

ready_money = start_money  # 手上剩余钱数
hold_money = 0  # 指数持有价值
hold_fund = []  # 持有指数钱列表


# 获取收盘价数据，目前为上证综指
def get_data():
    req = requests.Session()
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get?" \
          "secid={}&ut=fa5fd1943c7b386f172d6893dbfba10b" \
          "&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58" \
          "&klt=101&fqt=0&beg=19900101&end=20220101".format(zhishu_code)
    res = req.get(url).json()
    data = []
    date = []
    for item in res["data"]["klines"]:
        data.append(float(item.split(",")[2]))
        date.append(item.split(",")[0])
    if today_value:
        data.append(today_value)
        date.append("today")
    return data, date


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


# 买入判断
def judge_buy(now):
    cangwei = get_hold_cangwei(now)
    t = int(ready_money - ((ready_money + hold_money) * cangwei))
    return t if t > buy_min_money else 0


# 卖出判断
def judge_sale(now):
    cangwei = get_hold_cangwei(now)
    t = int(ready_money - ((ready_money + hold_money) * cangwei))
    return -t if t < -sale_min_money else 0


# 回跑
def run(days):
    global ready_money, hold_money, zhishu_low, zhishu_high
    result = {}
    data, date = get_data()
    data = data[-days:]
    date = date[-days:]
    result["data"] = data
    result["date"] = date
    result["total_money"] = []
    result["profit"] = []
    buy_sale_data = []
    for i in range(len(data)):
        print("日期: {}，指数: {}".format(date[i], data[i]))

        # if auto_low_high:
        #     if data[i] < zhishu_low:
        #         zhishu_low -= (zhishu_low - data[i]) * 0.1
        #         zhishu_high -= (zhishu_low - data[i]) * 0.1
        #     if data[i] > zhishu_high:
        #         zhishu_low += (data[i] - zhishu_high) * 0.1
        #         zhishu_high += (data[i] - zhishu_high) * 0.1
        # zhishu_low = min(zhishu_low, data[i])
        # zhishu_high = max(zhishu_high, data[i])

        # 计算收益
        if i > 0:
            tmp = 0
            for j in range(len(hold_fund)):
                hold_fund[j]["money"] = data[i] / data[hold_fund[j]["index"]] * hold_fund[j]["benjin"]
                tmp += hold_fund[j]["money"]
            hold_money = tmp

        # 买
        buy = judge_buy(data[i])
        if buy > 0:
            buy_sale_data.append({
                "type": "buy",
                "money": buy,
                "index": i
            })
            print("买入: " + str(buy))
            ready_money -= buy
            buy = buy * (1 - buy_charge_percent)
            hold_fund.append({
                "index": i,
                "benjin": buy,
                "money": buy
            })
            hold_money += buy

        # 卖
        sale = judge_sale(data[i])
        if sale > 0:
            j, k = 0, 0
            this_sale = 0
            hold_fund_copy = copy.deepcopy(hold_fund)
            while k < len(hold_fund_copy):
                if i - hold_fund_copy[j]["index"] <= sale_hold_days:
                    break
                if hold_fund_copy[j]["money"] > sale:
                    this_sale += sale
                else:
                    this_sale += hold_fund_copy[k]["money"]
                    hold_fund_copy.pop(j)
                    k -= 1
                k += 1
            if this_sale >= sale_min_money:
                this_sale = 0
                while j < len(hold_fund):
                    if i - hold_fund[j]["index"] <= sale_hold_days:
                        break
                    if hold_fund[j]["money"] > sale:
                        this_sale += sale
                        hold_fund[j]["benjin"] = (hold_fund[j]["money"] - sale) / hold_fund[j]["money"] * hold_fund[j][
                            "benjin"]
                        hold_fund[j]["money"] -= sale
                        hold_money -= sale
                        ready_money += sale * (1 - sale_charge_percent)
                        break
                    else:
                        this_sale += hold_fund[j]["money"]
                        hold_money -= hold_fund[j]["money"]
                        ready_money += hold_fund[j]["money"] * (1 - sale_charge_percent)
                        sale -= hold_fund[j]["money"]
                        hold_fund.pop(j)
                        j -= 1
                    j += 1
                if this_sale > 0:
                    buy_sale_data.append({
                        "type": "sale",
                        "money": round(this_sale, 2),
                        "index": i
                    })
                    print("卖出: " + str(this_sale))

        ready_money = round(ready_money, 4)
        hold_money = round(hold_money, 4)
        result["total_money"].append(round(ready_money + hold_money, 2))
        result["profit"].append(round((ready_money + hold_money - start_money) / start_money * 100, 2))
        print("闲钱：{}, 持有价值：{}，总钱：{}\n".format(ready_money, hold_money, hold_money + ready_money))

    result["trace_data"] = buy_sale_data

    if hold_money + ready_money > start_money:
        print("本次回跑赚: {}, 比例: {}%".format(hold_money + ready_money - start_money,
                                          round((hold_money + ready_money - start_money) / start_money * 100, 2)))
    else:
        print("本次回跑亏: {}, 比例: {}%".format(start_money - hold_money - ready_money,
                                          round((start_money - hold_money - ready_money) / start_money * 100, 2)))
    if data[-1] > data[0]:
        print("指数上涨: {}, 比例: {}%".format(data[-1] - data[0], round((data[-1] - data[0]) / data[0] * 100, 2)))
    else:
        print("指数下降: {}, 比例: {}%".format(data[0] - data[-1], round((data[0] - data[-1]) / data[0] * 100, 2)))

    return result


if __name__ == '__main__':
    result = run(run_days)
    json.dump(result, open("result.json", "w"))