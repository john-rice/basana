# Basana
#
# Copyright 2022-2023 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from decimal import Decimal
import asyncio
import datetime
import os

import pytest

from . import helpers
from basana.backtesting import charts, exchange
from basana.core.pair import Pair
from basana.external.yahoo import bars


@pytest.mark.parametrize("order_plan", [
    {
        datetime.date(2000, 1, 3): [
            # Buy market.
            lambda e: e.create_market_order(exchange.OrderOperation.BUY, Pair("ORCL", "USD"), Decimal("2")),
        ],
        datetime.date(2000, 1, 14): [
            # Sell market.
            lambda e: e.create_market_order(exchange.OrderOperation.SELL, Pair("ORCL", "USD"), Decimal("1")),
        ],
    },
])
def test_save_line_chart(order_plan, backtesting_dispatcher):
    e = exchange.Exchange(
        backtesting_dispatcher,
        {
            "USD": Decimal("1e6"),
        },
    )
    pair = Pair("ORCL", "USD")
    chart = charts.LineCharts(e, [pair], ["USD"])

    async def on_bar(bar_event):
        order_requests = order_plan.get(bar_event.when.date(), [])
        for create_order_fun in order_requests:
            created_order = await create_order_fun(e)
            assert created_order is not None

    async def impl():
        e.add_bar_source(bars.CSVBarSource(pair, helpers.abs_data_path("orcl-2000-yahoo-sorted.csv")))
        e.subscribe_to_bar_events(pair, on_bar)

        await backtesting_dispatcher.run()

        with helpers.temp_file_name(suffix=".png") as tmp_file_name:
            chart.save(tmp_file_name)
            assert os.stat(tmp_file_name).st_size > 100

    asyncio.run(impl())
